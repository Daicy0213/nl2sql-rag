import json
from pathlib import Path

from nl2sql.catalog import ANALYTICS_TABLES
from nl2sql.sql_runner import validate_sql


ROOT = Path(__file__).resolve().parents[2]


def test_expanded_tables_are_allowed_but_seed_state_is_private():
    assert validate_sql(
        "SELECT tier_name, discount_rate FROM analytics.membership_tiers"
    ).startswith("SELECT")
    assert validate_sql(
        "SELECT COUNT(*) FROM analytics.web_sessions"
    ).startswith("SELECT")
    assert "demo_seed_state" not in ANALYTICS_TABLES


def test_knowledge_catalog_has_unique_valid_dependencies():
    items = []
    for path in sorted((ROOT / "db" / "knowledge").glob("*.json")):
        items.extend(json.loads(path.read_text(encoding="utf-8")))
    ids = [item["id"] for item in items]
    assert len(items) >= 100
    assert len(ids) == len(set(ids))
    assert len([item for item in items if item["kind"] == "metric"]) >= 25
    assert {"dimension.membership_gold", "dimension.membership_platinum", "dimension.membership_diamond"} <= set(ids)
    for item in items:
        assert set(item.get("required_docs", [])) <= set(ids)
        assert set(item["related_tables"]) <= ANALYTICS_TABLES


def test_retrieval_gold_has_broad_labeled_coverage():
    cases = json.loads((ROOT / "tests" / "eval" / "retrieval_gold.json").read_text(encoding="utf-8"))
    assert len(cases) >= 120
    assert len({case["id"] for case in cases}) == len(cases)
    categories = {case["category"] for case in cases}
    assert {"membership", "revenue", "refunds", "fulfillment", "marketing", "ambiguity"} <= categories
