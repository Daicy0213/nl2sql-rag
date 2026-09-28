import pytest

from nl2sql.sql_runner import validate_sql


@pytest.mark.parametrize(
    "query",
    [
        "DELETE FROM analytics.orders",
        "SELECT 1; DROP TABLE analytics.orders",
        "SELECT * FROM pg_catalog.pg_roles",
        "SELECT * FROM rag.documents",
        "SELECT pg_sleep(1)",
        "SELECT pg_advisory_lock(1)",
        "SELECT nextval('secret_sequence')",
        "SELECT * FROM analytics.orders FOR UPDATE",
        "WITH changed AS (DELETE FROM analytics.orders RETURNING *) SELECT * FROM changed",
    ],
)
def test_rejects_unsafe_sql(query):
    with pytest.raises(ValueError):
        validate_sql(query)


def test_accepts_read_only_cte():
    query = "WITH paid AS (SELECT order_id FROM analytics.payments WHERE status='SUCCEEDED') SELECT COUNT(*) FROM paid"
    assert validate_sql(query) == query


def test_accepts_expanded_analytics_tables():
    query = """SELECT o.membership_tier_code, SUM(i.membership_discount_amount)
    FROM analytics.orders o JOIN analytics.order_items i USING(order_id)
    GROUP BY o.membership_tier_code"""
    assert validate_sql(query) == query
