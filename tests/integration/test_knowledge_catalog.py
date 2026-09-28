import pytest

from nl2sql.knowledge import load_knowledge


@pytest.mark.integration
def test_expanded_knowledge_catalog_matches_live_schema():
    docs = load_knowledge()
    by_id = {doc.doc_id: doc for doc in docs}
    assert len(docs) == 142
    assert "当前数据库字段" in by_id["table.membership_tiers"].content
    assert "discount_rate" in by_id["table.membership_tiers"].content
    assert by_id["metric.member_sales"].required_docs == [
        "rule.membership_snapshot",
        "metric.gross_sales",
    ]
    assert by_id["metric.net_sales"].priority > by_id["table.orders"].priority
