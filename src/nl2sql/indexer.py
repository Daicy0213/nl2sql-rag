from __future__ import annotations

import psycopg
from pgvector import Vector
from pgvector.psycopg import register_vector
from psycopg.types.json import Jsonb

from nl2sql.config import get_settings
from nl2sql.embedding import QwenEmbedder
from nl2sql.knowledge import load_knowledge


def index_knowledge() -> tuple[int, int]:
    """Upsert changed cards and remove deleted IDs in one database transaction.

    Hash plus model name is the cache key: text edits and model upgrades both
    require a new embedding. API work finishes before SQL writes begin, so a
    failed embedding batch cannot leave a half-updated index.
    """
    settings = get_settings()
    docs = load_knowledge()
    with psycopg.connect(settings.db_admin_url) as conn:
        register_vector(conn)
        existing = {
            row[0]: (row[1], row[2])
            for row in conn.execute("SELECT doc_id, content_hash, embed_model FROM rag.documents")
        }
        changed = [
            doc for doc in docs
            if existing.get(doc.doc_id) != (doc.content_hash, settings.qwen_embed_model)
        ]
        vectors = QwenEmbedder(settings).embed(
            [doc.embedding_text for doc in changed], text_type="document"
        ) if changed else []
        # strict=True prevents silently skipping a document if the provider
        # returns fewer vectors than expected.
        for doc, vector in zip(changed, vectors, strict=True):
            conn.execute(
                """INSERT INTO rag.documents
                (doc_id, kind, object_ref, content, aliases, related_tables,
                 source_version, content_hash, embed_model, embedding, metadata, priority)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (doc_id) DO UPDATE SET
                  kind=EXCLUDED.kind, object_ref=EXCLUDED.object_ref,
                  content=EXCLUDED.content, aliases=EXCLUDED.aliases,
                  related_tables=EXCLUDED.related_tables,
                  source_version=EXCLUDED.source_version,
                  content_hash=EXCLUDED.content_hash,
                  embed_model=EXCLUDED.embed_model,
                  embedding=EXCLUDED.embedding, metadata=EXCLUDED.metadata,
                  priority=EXCLUDED.priority, updated_at=now()""",
                (
                    doc.doc_id, doc.kind, doc.object_ref, doc.content,
                    doc.aliases, doc.related_tables, "catalog-v2",
                    doc.content_hash, settings.qwen_embed_model, Vector(vector),
                    Jsonb(doc.metadata), doc.priority,
                ),
            )
        # Source of truth is the knowledge directory plus live schema; old IDs must not
        # remain retrievable after removal from that source.
        conn.execute("DELETE FROM rag.documents WHERE NOT (doc_id = ANY(%s))", ([d.doc_id for d in docs],))
    return len(changed), len(docs)


if __name__ == "__main__":
    changed, total = index_knowledge()
    print(f"Knowledge indexed: {changed} updated, {total} total.")
