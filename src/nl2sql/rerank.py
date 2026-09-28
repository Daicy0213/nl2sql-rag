"""Optional reranking experiment used by chapter 3, not the ADK runtime path."""

from __future__ import annotations

import json
import math
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from nl2sql.config import get_settings


def rerank_documents(question: str, documents: list[tuple[str, str]]) -> list[tuple[str, float]]:
    """Score a small retrieved candidate set with Qwen and preserve its stable IDs.

    The provider returns *positions* in the supplied list, not our doc IDs. We
    validate those positions before mapping back; otherwise a malformed or
    partial response could silently attribute a score to the wrong document.
    """
    if not question.strip():
        raise ValueError("Question cannot be empty")
    if not documents:
        return []
    if len(documents) > 20:
        raise ValueError("Teaching reranker accepts at most 20 candidates")
    ids = [doc_id for doc_id, _ in documents]
    if len(set(ids)) != len(ids) or any(not text.strip() for _, text in documents):
        raise ValueError("Candidate IDs must be unique and texts nonempty")

    settings = get_settings()
    if not settings.embedding_key:
        raise RuntimeError("QWEN_API_KEY is required for reranking")
    base_url = settings.dashscope_base_url.rstrip("/")
    if not base_url.startswith("https://") or not base_url.endswith("/api/v1"):
        raise ValueError("DASHSCOPE_BASE_URL must be the HTTPS native /api/v1 URL")
    url = base_url + "/services/rerank/text-rerank/text-rerank"
    payload = {
        "model": "qwen3.7-text-rerank",
        "input": {"query": question, "documents": [text for _, text in documents]},
        "parameters": {"top_n": len(documents)},
    }
    request = Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": f"Bearer {settings.embedding_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=30) as response:
            data = json.load(response)
    except HTTPError as exc:
        # Avoid including the provider's response body, which might echo inputs.
        raise RuntimeError(f"Qwen rerank HTTP {exc.code}") from exc
    except URLError as exc:
        raise RuntimeError("Qwen rerank transport failed") from exc

    try:
        results = data["output"]["results"]
        ranked = [(ids[int(row["index"])], float(row["relevance_score"])) for row in results]
    except (KeyError, TypeError, ValueError, IndexError) as exc:
        raise RuntimeError("Qwen rerank response format mismatch") from exc
    if len(ranked) != len(documents) or len({doc_id for doc_id, _ in ranked}) != len(documents):
        raise RuntimeError("Qwen rerank returned incomplete or duplicate candidate indexes")
    if any(not math.isfinite(score) for _, score in ranked):
        raise RuntimeError("Qwen rerank returned a non-finite score")
    return sorted(ranked, key=lambda item: (-item[1], item[0]))
