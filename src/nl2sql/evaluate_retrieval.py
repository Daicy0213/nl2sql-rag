from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path

from nl2sql.retrieval import retrieve


DEFAULT_CASES = Path(__file__).resolve().parents[2] / "tests" / "eval" / "retrieval_gold.json"


@dataclass(frozen=True)
class RetrievalMetrics:
    strategy: str
    cases: int
    recall_at_5: float
    recall_at_10: float
    mrr_at_10: float
    ndcg_at_10: float
    context_recall: float
    table_coverage: float


def _recall(ranked: list[str], relevant: set[str], k: int) -> float:
    return len(set(ranked[:k]) & relevant) / len(relevant) if relevant else 1.0


def _reciprocal_rank(ranked: list[str], relevant: set[str], k: int) -> float:
    for rank, doc_id in enumerate(ranked[:k], start=1):
        if doc_id in relevant:
            return 1.0 / rank
    return 0.0


def _ndcg(ranked: list[str], relevant: set[str], k: int) -> float:
    dcg = sum(1.0 / math.log2(rank + 1) for rank, doc_id in enumerate(ranked[:k], start=1) if doc_id in relevant)
    ideal_hits = min(len(relevant), k)
    ideal = sum(1.0 / math.log2(rank + 1) for rank in range(1, ideal_hits + 1))
    return dcg / ideal if ideal else 1.0


def evaluate(cases_path: Path, strategy: str) -> tuple[RetrievalMetrics, list[dict]]:
    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    totals = dict(recall5=0.0, recall10=0.0, mrr=0.0, ndcg=0.0, context=0.0, tables=0.0)
    failures: list[dict] = []
    for case in cases:
        result = retrieve(case["question"], limit=10, strategy=strategy)
        ranked = result["ranked_doc_ids"]
        relevant = set(case["relevant_docs"])
        required_tables = set(case.get("required_tables", []))
        returned_tables = {doc_id.removeprefix("table.") for doc_id in result["doc_ids"] if doc_id.startswith("table.")}
        recall5 = _recall(ranked, relevant, 5)
        recall10 = _recall(ranked, relevant, 10)
        table_coverage = len(returned_tables & required_tables) / len(required_tables) if required_tables else 1.0
        totals["recall5"] += recall5
        totals["recall10"] += recall10
        totals["mrr"] += _reciprocal_rank(ranked, relevant, 10)
        totals["ndcg"] += _ndcg(ranked, relevant, 10)
        totals["context"] += len(set(result["doc_ids"]) & relevant) / len(relevant) if relevant else 1.0
        totals["tables"] += table_coverage
        if recall10 < 1 or table_coverage < 1:
            failures.append({
                "id": case["id"],
                "question": case["question"],
                "missing_docs": sorted(relevant - set(ranked[:10])),
                "missing_tables": sorted(required_tables - returned_tables),
                "top10": ranked[:10],
            })
    count = len(cases)
    metrics = RetrievalMetrics(
        strategy=strategy,
        cases=count,
        recall_at_5=totals["recall5"] / count,
        recall_at_10=totals["recall10"] / count,
        mrr_at_10=totals["mrr"] / count,
        ndcg_at_10=totals["ndcg"] / count,
        context_recall=totals["context"] / count,
        table_coverage=totals["tables"] / count,
    )
    return metrics, failures


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate labeled RAG retrieval cases")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--strategies", nargs="+", choices=["lexical", "vector", "hybrid"], default=["lexical", "hybrid"])
    parser.add_argument("--show-failures", type=int, default=10)
    args = parser.parse_args()
    for strategy in args.strategies:
        metrics, failures = evaluate(args.cases, strategy)
        print(json.dumps(metrics.__dict__, ensure_ascii=False, indent=2))
        if args.show_failures:
            print(json.dumps(failures[: args.show_failures], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
