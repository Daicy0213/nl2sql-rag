from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from datetime import date
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


def _write_reports(results: list[tuple[RetrievalMetrics, list[dict]]], json_path: Path | None, markdown_path: Path | None) -> None:
    payload = {
        "captured_at": date.today().isoformat(),
        "results": [
            {"metrics": metrics.__dict__, "failures": failures}
            for metrics, failures in results
        ],
    }
    if json_path:
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if markdown_path:
        lines = [
            "# 检索评估报告",
            "",
            f"评估日期：{payload['captured_at']}；人工标注问题：{results[0][0].cases if results else 0} 条。",
            "",
            "| 策略 | Recall@5 | Recall@10 | MRR@10 | nDCG@10 | 上下文召回率 | 必需表覆盖率 |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
        for metrics, _failures in results:
            lines.append(
                f"| {metrics.strategy} | {metrics.recall_at_5:.4f} | {metrics.recall_at_10:.4f} | "
                f"{metrics.mrr_at_10:.4f} | {metrics.ndcg_at_10:.4f} | "
                f"{metrics.context_recall:.4f} | {metrics.table_coverage:.4f} |"
            )
        for metrics, failures in results:
            lines.extend(["", f"## {metrics.strategy} 未完全命中（{len(failures)} 条）", ""])
            if not failures:
                lines.append("全部问题的相关知识与必需表均被覆盖。")
            else:
                for failure in failures:
                    lines.append(
                        f"- `{failure['id']}`：缺少知识 {failure['missing_docs']}；"
                        f"缺少表 {failure['missing_tables']}。"
                    )
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate labeled RAG retrieval cases")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--strategies", nargs="+", choices=["lexical", "vector", "hybrid"], default=["lexical", "hybrid"])
    parser.add_argument("--show-failures", type=int, default=10)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-markdown", type=Path)
    args = parser.parse_args()
    results: list[tuple[RetrievalMetrics, list[dict]]] = []
    for strategy in args.strategies:
        metrics, failures = evaluate(args.cases, strategy)
        results.append((metrics, failures))
        print(json.dumps(metrics.__dict__, ensure_ascii=False, indent=2))
        if args.show_failures:
            print(json.dumps(failures[: args.show_failures], ensure_ascii=False, indent=2))
    _write_reports(results, args.output_json, args.output_markdown)


if __name__ == "__main__":
    main()
