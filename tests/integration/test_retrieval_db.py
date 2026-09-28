from unittest.mock import patch

import psycopg
import pytest
from pgvector.psycopg import register_vector

from nl2sql.config import get_settings
from nl2sql.retrieval import retrieve


@pytest.mark.integration
def test_pgvector_query_and_document_expansion():
    settings = get_settings()
    vector = [0.01] * 1024
    with psycopg.connect(settings.db_admin_url) as conn:
        register_vector(conn)
        conn.execute(
            """INSERT INTO rag.documents
            (doc_id,kind,object_ref,content,aliases,related_tables,source_version,content_hash,embed_model,embedding)
            VALUES ('test.embedding','metric','test','测试指标',ARRAY['测试指标'], '{}','test','test',%s,%s)
            ON CONFLICT (doc_id) DO NOTHING""",
            (settings.qwen_embed_model, vector),
        )
    try:
        with patch("nl2sql.retrieval.QwenEmbedder") as mock_embedder:
            mock_embedder.return_value.embed.return_value = [vector]
            result = retrieve("测试指标")
        assert "test.embedding" in result["doc_ids"]
    finally:
        with psycopg.connect(settings.db_admin_url) as conn:
            conn.execute("DELETE FROM rag.documents WHERE doc_id='test.embedding'")
