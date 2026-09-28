from __future__ import annotations

import re
from dataclasses import dataclass
from dataclasses import field

import psycopg
from pgvector import Vector
from pgvector.psycopg import register_vector

from nl2sql.config import get_settings
from nl2sql.embedding import QwenEmbedder
from nl2sql.rerank import rerank_documents


@dataclass(frozen=True)
class RetrievedDoc:
    doc_id: str
    kind: str
    object_ref: str
    content: str
    aliases: list[str]
    related_tables: list[str]
    required_docs: list[str] = field(default_factory=list)
    priority: int = 50


def lexical_score(question: str, doc: RetrievedDoc) -> int:
    """Prefer explicit business aliases; this score is not a probability."""
    question_norm = re.sub(r"\s+", "", question).lower()
    score = 0
    for alias in doc.aliases:
        alias_norm = re.sub(r"\s+", "", alias).lower()
        if alias_norm and alias_norm in question_norm:
            score += 6 + len(alias_norm)
            if alias_norm == question_norm:
                score += 8
    for part in re.split(r"[._]", doc.object_ref.lower()):
        if len(part) >= 3 and part in question_norm:
            score += 4
    return score


def rrf_rank(
    vector_ids: list[str],
    lexical_ids: list[str],
    k: int = 60,
    vector_weight: float = 2.0,
    lexical_weight: float = 1.0,
) -> list[str]:
    """Fuse incomparable scores by weighted reciprocal rank.

    Semantic retrieval receives a modest default weight because the lexical
    channel is intentionally sparse and may otherwise over-promote table cards.
    A document absent from one channel receives zero from that channel.
    Stable doc-ID tie breaking keeps regression tests reproducible.
    """
    scores: dict[str, float] = {}
    for ranking, weight in ((vector_ids, vector_weight), (lexical_ids, lexical_weight)):
        for rank, doc_id in enumerate(ranking, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + weight / (k + rank)
    return sorted(scores, key=lambda doc_id: (-scores[doc_id], doc_id))


def retrieve(question: str, *, limit: int = 8, strategy: str = "hybrid") -> dict:
    """Recall by vector and aliases, fuse rankings, then add table dependencies."""
    if not question.strip():
        raise ValueError("Question cannot be empty")
    if strategy not in {"vector", "lexical", "hybrid"}:
        raise ValueError("strategy must be vector, lexical, or hybrid")
    if limit < 1 or limit > 20:
        raise ValueError("limit must be between 1 and 20")
    settings = get_settings()
    vector = None
    if strategy in {"vector", "hybrid"}:
        vector = QwenEmbedder(settings).embed([question], text_type="query")[0]
    with psycopg.connect(settings.db_reader_url) as conn:
        if vector is not None:
            register_vector(conn)
        rows = conn.execute(
            """SELECT doc_id, kind, object_ref, content, aliases, related_tables,
                      metadata, priority
            FROM rag.documents WHERE embed_model=%s""",
            (settings.qwen_embed_model,),
        ).fetchall()
        if not rows:
            raise RuntimeError("Knowledge index is empty or uses another model; run the index command")
        docs = {
            row[0]: RetrievedDoc(
                row[0], row[1], row[2], row[3], row[4], row[5],
                list((row[6] or {}).get("required_docs", [])), row[7],
            )
            for row in rows
        }
        # <=> is cosine distance in pgvector: smaller values rank first.
        # Top-15 is a candidate cap; it is not a relevance threshold.
        vector_ids = []
        if vector is not None:
            vector_ids = [
                row[0]
                for row in conn.execute(
                    """SELECT doc_id FROM rag.documents WHERE embed_model=%s
                    ORDER BY embedding <=> %s LIMIT %s""",
                    (settings.qwen_embed_model, Vector(vector), settings.retrieval_candidate_limit),
                ).fetchall()
            ]
    lexical_ids = [
        doc_id for doc_id, score in sorted(
            ((doc_id, lexical_score(question, doc)) for doc_id, doc in docs.items()),
            key=lambda item: (-item[1], -docs[item[0]].priority, item[0]),
        # Table cards are added deterministically by dependency expansion.
        # Keeping their broad aliases out of the lexical rank prevents words
        # such as "会员" or "订单" from displacing the actual metric/rule.
        ) if score > 0 and docs[doc_id].kind != "table"
    ][:settings.retrieval_candidate_limit]
    if strategy == "vector":
        ranked = vector_ids
    elif strategy == "lexical":
        ranked = lexical_ids
    else:
        ranked = rrf_rank(vector_ids, lexical_ids)
    if settings.enable_rag_rerank and strategy == "hybrid" and ranked:
        rerank_ids = ranked[:20]
        reranked = rerank_documents(
            question,
            [(doc_id, f"{docs[doc_id].object_ref}\n{docs[doc_id].content}") for doc_id in rerank_ids],
        )
        reranked_ids = [doc_id for doc_id, _score in reranked]
        ranked = reranked_ids + [doc_id for doc_id in ranked if doc_id not in reranked_ids]
    selected = ranked[:limit]
    # Dependency expansion happens after ranking so a selected metric or join
    # has the actual table cards required for SQL generation.
    expanded = list(selected)
    queue = list(selected)
    while queue:
        doc_id = queue.pop(0)
        for required_id in docs[doc_id].required_docs:
            if required_id in docs and required_id not in expanded:
                expanded.append(required_id)
                queue.append(required_id)
    related_tables = {table for doc_id in expanded for table in docs[doc_id].related_tables}
    for table in sorted(related_tables):
        table_id = f"table.{table}"
        if table_id in docs and table_id not in expanded:
            expanded.append(table_id)
    context_parts = []
    used_chars = 0
    included: list[str] = []
    for doc_id in expanded:
        doc = docs[doc_id]
        part = f"[{doc.doc_id}] {doc.content}"
        if context_parts and used_chars + len(part) + 2 > settings.retrieval_context_chars:
            continue
        context_parts.append(part)
        included.append(doc_id)
        used_chars += len(part) + 2
    context = "\n\n".join(context_parts)
    return {
        "doc_ids": included,
        "ranked_doc_ids": ranked[:limit],
        "dependency_doc_ids": [doc_id for doc_id in included if doc_id not in selected],
        "strategy": strategy,
        "context": context,
    }
