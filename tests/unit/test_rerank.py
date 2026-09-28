import io
import json
from types import SimpleNamespace

import pytest

from nl2sql import rerank


def test_rerank_maps_provider_indexes_back_to_stable_doc_ids(monkeypatch):
    monkeypatch.setattr(rerank, "get_settings", lambda: SimpleNamespace(
        embedding_key="test-key",
        dashscope_base_url="https://workspace.cn-beijing.maas.aliyuncs.com/api/v1",
    ))
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        seen["payload"] = json.loads(request.data)
        assert timeout == 30
        return io.BytesIO(json.dumps({"output": {"results": [
            {"index": 1, "relevance_score": 0.9},
            {"index": 0, "relevance_score": 0.3},
        ]}}).encode())

    monkeypatch.setattr(rerank, "urlopen", fake_urlopen)
    assert rerank.rerank_documents("退款后收入", [("metric.gross_sales", "总销售额"),
                                             ("metric.net_sales", "净销售额")]) == [
        ("metric.net_sales", 0.9), ("metric.gross_sales", 0.3)]
    assert seen["url"].endswith("/api/v1/services/rerank/text-rerank/text-rerank")
    assert seen["payload"]["input"]["documents"] == ["总销售额", "净销售额"]


def test_rerank_rejects_bad_candidate_ids():
    with pytest.raises(ValueError, match="unique"):
        rerank.rerank_documents("问题", [("same", "一"), ("same", "二")])
