import psycopg
import pytest
from decimal import Decimal

from nl2sql.config import get_settings
from nl2sql.sql_runner import run_query, safe_run_query


@pytest.mark.integration
def test_seed_counts_and_readonly_role():
    settings = get_settings()
    with psycopg.connect(settings.db_reader_url) as conn:
        assert conn.execute("SELECT COUNT(*) FROM analytics.orders").fetchone()[0] == 30_000
        assert conn.execute("SELECT COUNT(*) FROM analytics.customers").fetchone()[0] == 10_000
        assert conn.execute("SELECT COUNT(*) FROM analytics.web_sessions").fetchone()[0] == 100_000
        assert conn.execute("SELECT COUNT(*) FROM analytics.membership_tiers").fetchone()[0] == 4
        with pytest.raises(psycopg.Error):
            conn.execute(
                """INSERT INTO analytics.customers
                (customer_id,customer_name,city,region,signup_at,customer_segment)
                VALUES (999999,'x','x','x',now(),'MASS')"""
            )


@pytest.mark.integration
def test_net_sales_query_matches_independent_calculation():
    query = """WITH payments_by_order AS (
      SELECT order_id, SUM(amount) AS paid
      FROM analytics.payments WHERE status='SUCCEEDED'
        AND paid_at >= '2026-08-01' AND paid_at < '2026-09-01'
      GROUP BY order_id
    ), refunds_by_order AS (
      SELECT order_id, SUM(amount) AS refunded
      FROM analytics.refunds WHERE status='APPROVED' GROUP BY order_id
    )
    SELECT COALESCE(SUM(p.paid - COALESCE(r.refunded,0)),0) AS net_sales
    FROM payments_by_order p
    JOIN analytics.orders o ON o.order_id=p.order_id
    JOIN analytics.customers c ON c.customer_id=o.customer_id
    LEFT JOIN refunds_by_order r ON r.order_id=o.order_id
    WHERE c.region='华东'"""
    result = run_query(query)
    assert result["row_count"] == 1
    assert Decimal(result["rows"][0]["net_sales"]) >= 0
    # Compute the golden answer row by row, independently of the aggregate SQL.
    with psycopg.connect(get_settings().db_reader_url) as conn:
        paid_rows = conn.execute(
            """SELECT p.order_id, p.amount FROM analytics.payments p
            JOIN analytics.orders o ON o.order_id=p.order_id
            JOIN analytics.customers c ON c.customer_id=o.customer_id
            WHERE p.status='SUCCEEDED' AND c.region='华东'
              AND p.paid_at >= '2026-08-01' AND p.paid_at < '2026-09-01'"""
        ).fetchall()
        refunds = conn.execute(
            "SELECT order_id, amount FROM analytics.refunds WHERE status='APPROVED'"
        ).fetchall()
    paid: dict[int, Decimal] = {}
    for order_id, amount in paid_rows:
        paid[order_id] = paid.get(order_id, Decimal("0")) + amount
    refunded: dict[int, Decimal] = {}
    for order_id, amount in refunds:
        refunded[order_id] = refunded.get(order_id, Decimal("0")) + amount
    expected = sum(
        (amount - refunded.get(order_id, Decimal("0")) for order_id, amount in paid.items()),
        Decimal("0"),
    )
    assert expected == Decimal("752088.38")
    assert Decimal(result["rows"][0]["net_sales"]) == expected


@pytest.mark.integration
def test_rejects_write_through_tool():
    result = safe_run_query("DELETE FROM analytics.orders")
    assert not result["ok"]


@pytest.mark.integration
def test_fixed_dataset_business_goldens():
    with psycopg.connect(get_settings().db_reader_url) as conn:
        paid_august = conn.execute(
            """SELECT COUNT(DISTINCT order_id) FROM analytics.payments
            WHERE status='SUCCEEDED' AND paid_at >= '2026-08-01' AND paid_at < '2026-09-01'"""
        ).fetchone()[0]
        regions = conn.execute(
            """SELECT c.region, COUNT(DISTINCT o.order_id)
            FROM analytics.orders o JOIN analytics.customers c ON c.customer_id=o.customer_id
            WHERE o.status <> 'CANCELLED'
              AND o.ordered_at >= '2026-08-01' AND o.ordered_at < '2026-09-01'
            GROUP BY c.region"""
        ).fetchall()
    assert paid_august == 1979
    by_region = dict(regions)
    assert by_region == {
        "华东": 483,
        "华中": 238,
        "华北": 419,
        "华南": 415,
        "西北": 161,
        "西南": 262,
    }


@pytest.mark.integration
def test_membership_snapshots_discounts_and_payment_retries():
    with psycopg.connect(get_settings().db_reader_url) as conn:
        current_members = dict(conn.execute(
            """SELECT tier_code, COUNT(*) FROM analytics.customer_memberships
            WHERE valid_to IS NULL GROUP BY tier_code"""
        ).fetchall())
        august_discounts = dict(conn.execute(
            """SELECT o.membership_tier_code, SUM(oi.membership_discount_amount)
            FROM analytics.orders o JOIN analytics.order_items oi USING(order_id)
            WHERE o.status <> 'CANCELLED'
              AND o.ordered_at >= '2026-08-01' AND o.ordered_at < '2026-09-01'
            GROUP BY o.membership_tier_code"""
        ).fetchall())
        retry_succeeded = conn.execute(
            """SELECT COUNT(*) FROM (
              SELECT order_id FROM analytics.payments GROUP BY order_id
              HAVING BOOL_OR(status='FAILED') AND BOOL_OR(status='SUCCEEDED')
            ) retries"""
        ).fetchone()[0]
    assert current_members == {
        "STANDARD": 4478,
        "GOLD": 3471,
        "PLATINUM": 1507,
        "DIAMOND": 544,
    }
    assert august_discounts["STANDARD"] == Decimal("0.00")
    assert august_discounts["GOLD"] == Decimal("54648.00")
    assert august_discounts["PLATINUM"] == Decimal("57085.24")
    assert august_discounts["DIAMOND"] == Decimal("25547.61")
    assert retry_succeeded == 3397
