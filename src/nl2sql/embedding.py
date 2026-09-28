from __future__ import annotations

from http import HTTPStatus

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from nl2sql.config import Settings, get_settings


class TransientEmbeddingError(RuntimeError):
    """A retryable Qwen transport or rate-limit failure."""


class QwenEmbedder:
    """Thin provider adapter with batching, bounded retries and shape checks."""
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        if not self.settings.embedding_key:
            raise RuntimeError("QWEN_API_KEY (or DASHSCOPE_API_KEY) is required for embeddings")

    def embed(self, texts: list[str], *, text_type: str) -> list[list[float]]:
        """Embed documents for storage or queries for retrieval.

        The two text types are intentionally asymmetric. Mixing them or using
        a different model at query time invalidates similarity comparisons.
        """
        if not texts:
            return []
        if text_type not in {"query", "document"}:
            raise ValueError("text_type must be query or document")
        results: list[list[float]] = []
        # Bound each request size; preserve input order across batches.
        for start in range(0, len(texts), 10):
            batch = texts[start : start + 10]
            results.extend(self._embed_batch(batch, text_type))
        return results

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        retry=retry_if_exception_type(TransientEmbeddingError),
        reraise=True,
    )
    def _embed_batch(self, batch: list[str], text_type: str) -> list[list[float]]:
        import dashscope

        # The native API supports text_type and query instructions. The
        # OpenAI-compatible chat URL is not interchangeable with this base.
        dashscope.base_http_api_url = self.settings.dashscope_base_url
        try:
            kwargs = {
                "model": self.settings.qwen_embed_model,
                "input": batch,
                "api_key": self.settings.embedding_key,
                "dimension": self.settings.qwen_embed_dim,
                "text_type": text_type,
                "output_type": "dense",
            }
            if text_type == "query":
                # Query-only instruction makes the retrieval task explicit;
                # document embeddings are produced without this instruction.
                kwargs["instruct"] = "Retrieve database schema and business rules needed to write correct SQL for this question."
            response = dashscope.TextEmbedding.call(**kwargs)
        except (TimeoutError, ConnectionError) as exc:
            raise TransientEmbeddingError("Qwen embedding transport failed") from exc
        if response.status_code in {429, 500, 502, 503, 504}:
            raise TransientEmbeddingError(f"Qwen embedding temporarily unavailable: {response.status_code}")
        if response.status_code != HTTPStatus.OK:
            raise RuntimeError(f"Qwen embedding failed: {response.code}: {response.message}")
        # Provider responses can be ordered by text_index rather than position.
        # Validate both cardinality and dimensions before associating a vector
        # with a doc ID in the indexer.
        vectors = sorted(response.output["embeddings"], key=lambda row: row["text_index"])
        if len(vectors) != len(batch):
            raise RuntimeError("Qwen embedding response length mismatch")
        result = []
        for row in vectors:
            vector = row["embedding"]
            if len(vector) != self.settings.qwen_embed_dim:
                raise RuntimeError("Qwen embedding dimension mismatch")
            result.append(vector)
        return result
