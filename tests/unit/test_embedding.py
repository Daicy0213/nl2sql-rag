from types import SimpleNamespace
from unittest.mock import patch

from nl2sql.config import Settings
from nl2sql.embedding import QwenEmbedder


def test_qwen_uses_asymmetric_query_and_document_modes():
    settings = Settings(qwen_api_key="test-only", qwen_embed_dim=1024)
    response = SimpleNamespace(
        status_code=200,
        output={"embeddings": [{"text_index": 0, "embedding": [0.1] * 1024}]},
    )
    with patch("dashscope.TextEmbedding.call", return_value=response) as call:
        embedder = QwenEmbedder(settings)
        assert len(embedder.embed(["订单口径"], text_type="document")[0]) == 1024
        document_kwargs = call.call_args.kwargs
        assert document_kwargs["text_type"] == "document"
        assert "instruct" not in document_kwargs
        embedder.embed(["净销售额是多少"], text_type="query")
        query_kwargs = call.call_args.kwargs
        assert query_kwargs["text_type"] == "query"
        assert "instruct" in query_kwargs
