from decimal import Decimal

import psycopg
import pytest

from nl2sql.config import get_settings


@pytest.mark.integration
def test_order_membership_snapshot_matches_effective_history():
    with psycopg.connect(get_settings().db_reader_url) as conn:
        mismatches = conn.execute(
            """SELECT COUNT(*) FROM analytics.orders o
            LEFT JOIN analytics.customer_memberships cm
              ON cm.customer_id=o.customer_id
             AND cm.valid_from<=o.ordered_at
             AND (cm.valid_to IS NULL OR o.ordered_at<cm.valid_to)
             AND cm.tier_code=o.membership_tier_code
            WHERE cm.membership_id IS NULL"""
        ).fetchone()[0]
    assert mismatches == 0


@pytest.mark.integration
def test_successful_payments_reconcile_to_final_items_and_shipping():
    with psycopg.connect(get_settings().db_reader_url) as conn:
        mismatches = conn.execute(
            """WITH paid AS (
              SELECT order_id,SUM(amount) amount FROM analytics.payments
              WHERE status='SUCCEEDED' GROUP BY order_id
            ), merchandise AS (
              SELECT order_id,SUM(quantity*unit_price) amount
              FROM analytics.order_items GROUP BY order_id
            )
            SELECT COUNT(*) FROM analytics.orders o
            JOIN paid p USING(order_id) JOIN merchandise m USING(order_id)
            WHERE p.amount <> m.amount + o.shipping_fee"""
        ).fetchone()[0]
    assert mismatches == 0


@pytest.mark.integration
def test_refunds_reconcile_to_item_level_and_include_edge_statuses():
    with psycopg.connect(get_settings().db_reader_url) as conn:
        mismatches = conn.execute(
            """SELECT COUNT(*) FROM analytics.refunds r
            JOIN (SELECT refund_id,SUM(amount) amount FROM analytics.refund_items GROUP BY refund_id) i
              USING(refund_id)
            WHERE r.amount<>i.amount"""
        ).fetchone()[0]
        statuses = dict(conn.execute(
            "SELECT status,COUNT(*) FROM analytics.refunds GROUP BY status"
        ).fetchall())
    assert mismatches == 0
    assert statuses == {"APPROVED": 2975, "PENDING": 436, "REJECTED": 813}


@pytest.mark.integration
def test_august_session_conversion_and_campaign_spend_are_stable():
    with psycopg.connect(get_settings().db_reader_url) as conn:
        converted, sessions = conn.execute(
            """SELECT COUNT(*) FILTER (WHERE converted_order_id IS NOT NULL),COUNT(*)
            FROM analytics.web_sessions
            WHERE session_started_at>='2026-08-01' AND session_started_at<'2026-09-01'"""
        ).fetchone()
        spend = conn.execute(
            "SELECT SUM(spend_amount) FROM analytics.campaign_spend_daily"
        ).fetchone()[0]
    assert (converted, sessions) == (2118, 5086)
    assert spend == Decimal("3592319.06")
