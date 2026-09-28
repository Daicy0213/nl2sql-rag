from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import psycopg

from nl2sql.config import get_settings


KNOWLEDGE_DIR = Path(__file__).resolve().parents[2] / "db" / "knowledge"
ALLOWED_KINDS = {"table", "metric", "join", "rule", "dimension", "example", "glossary"}


@dataclass(frozen=True)
class KnowledgeDoc:
    """One retrievable business rule with a stable ID and dependency metadata.

    The unit of retrieval is a complete rule/table/metric, not an arbitrary
    character chunk. ``related_tables`` is consumed after ranking so a metric
    hit brings the field definitions required to write SQL.
    """
    doc_id: str
    kind: str
    object_ref: str
    content: str
    aliases: list[str]
    related_tables: list[str]
    required_docs: list[str]
    priority: int
    metadata: dict

    @property
    def embedding_text(self) -> str:
        # Keep the exact embedded representation in one place: the hash below
        # must change whenever meaning visible to the embedding model changes.
        structured = []
        for key in ("grain", "time_column", "formula", "exclusions"):
            value = self.metadata.get(key)
            if value:
                structured.append(f"{key}：{value}")
        return (
            f"类型：{self.kind}\n对象：{self.object_ref}\n"
            f"别名：{'、'.join(self.aliases)}\n说明：{self.content}\n"
            + "\n".join(structured)
        )

    @property
    def content_hash(self) -> str:
        stored = {
            "embedding_text": self.embedding_text,
            "related_tables": self.related_tables,
            "required_docs": self.required_docs,
            "priority": self.priority,
            "metadata": self.metadata,
        }
        canonical = json.dumps(stored, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _columns_for_table(conn: psycopg.Connection, table_name: str) -> str:
    """Read live columns so indexed table cards follow schema migrations."""
    rows = conn.execute(
        """SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema='analytics' AND table_name=%s
        ORDER BY ordinal_position""",
        (table_name,),
    ).fetchall()
    if not rows:
        raise RuntimeError(f"Missing analytics table: {table_name}")
    return "; ".join(f"{name} {dtype}{' nullable' if nullable == 'YES' else ''}" for name, dtype, nullable in rows)


def load_knowledge() -> list[KnowledgeDoc]:
    """Combine reviewed business definitions with current database structure."""
    if not KNOWLEDGE_DIR.exists():
        raise RuntimeError(f"Knowledge directory does not exist: {KNOWLEDGE_DIR}")
    raw: list[dict] = []
    for path in sorted(KNOWLEDGE_DIR.glob("*.json")):
        items = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(items, list):
            raise ValueError(f"Knowledge file must contain a JSON array: {path.name}")
        raw.extend(items)
    if not raw:
        raise RuntimeError("Knowledge catalog is empty")
    ids = [item.get("id") for item in raw]
    if len(set(ids)) != len(ids):
        duplicates = sorted({doc_id for doc_id in ids if ids.count(doc_id) > 1})
        raise ValueError(f"Duplicate knowledge IDs: {duplicates}")
    docs: list[KnowledgeDoc] = []
    with psycopg.connect(get_settings().db_admin_url) as conn:
        for item in raw:
            missing = {"id", "kind", "object_ref", "content", "aliases", "related_tables"} - item.keys()
            if missing:
                raise ValueError(f"Knowledge item {item.get('id', '<unknown>')} is missing {sorted(missing)}")
            if item["kind"] not in ALLOWED_KINDS:
                raise ValueError(f"Unsupported knowledge kind: {item['kind']}")
            content = item["content"]
            if item["kind"] == "table":
                # A manually curated card explains semantics; information_schema
                # supplies the actual column names and types used by the agent.
                table_name = item["object_ref"].split(".")[-1]
                content += "\n当前数据库字段：" + _columns_for_table(conn, table_name)
            required_docs = item.get("required_docs", [])
            priority = int(item.get("priority", 50))
            if not 0 <= priority <= 100:
                raise ValueError(f"Priority must be 0..100: {item['id']}")
            metadata = dict(item.get("metadata", {}))
            metadata["required_docs"] = required_docs
            metadata["source_file"] = item.get("source_file", "catalog")
            docs.append(
                KnowledgeDoc(
                    doc_id=item["id"],
                    kind=item["kind"],
                    object_ref=item["object_ref"],
                    content=content,
                    aliases=item["aliases"],
                    related_tables=item["related_tables"],
                    required_docs=required_docs,
                    priority=priority,
                    metadata=metadata,
                )
            )
    known_ids = {doc.doc_id for doc in docs}
    unknown_dependencies = sorted({dep for doc in docs for dep in doc.required_docs if dep not in known_ids})
    if unknown_dependencies:
        raise ValueError(f"Unknown required knowledge IDs: {unknown_dependencies}")
    return docs
