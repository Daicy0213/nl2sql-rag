from __future__ import annotations

import random
from collections.abc import Iterable, Sequence
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP

import psycopg

from nl2sql.config import get_settings


DATA_START = datetime(2024, 10, 1, tzinfo=timezone.utc)
DATA_END = datetime(2026, 10, 1, tzinfo=timezone.utc)
CUSTOMER_COUNT = 10_000
PRODUCT_COUNT = 500
ORDER_COUNT = 30_000
SESSION_COUNT = 100_000
SEED_VERSION = "commerce-v2-20260928"
MONEY = Decimal("0.01")

REGIONS = {
    "华东": ["上海", "杭州", "南京", "苏州", "宁波"],
    "华北": ["北京", "天津", "石家庄", "青岛"],
    "华南": ["广州", "深圳", "厦门", "珠海"],
    "西南": ["成都", "重庆", "昆明", "贵阳"],
    "华中": ["武汉", "长沙", "郑州"],
    "西北": ["西安", "兰州", "乌鲁木齐"],
}

CHANNELS = [
    (1, "APP", "手机应用", "ONLINE"),
    (2, "WEB", "网页商城", "ONLINE"),
    (3, "MINI_PROGRAM", "微信小程序", "ONLINE"),
    (4, "STORE", "线下门店", "OFFLINE"),
]

TIERS = [
    ("STANDARD", "普通会员", Decimal("0"), Decimal("0.00"), Decimal("1.00"), 0),
    ("GOLD", "黄金会员", Decimal("5000"), Decimal("0.05"), Decimal("1.20"), 1),
    ("PLATINUM", "白金会员", Decimal("15000"), Decimal("0.10"), Decimal("1.50"), 2),
    ("DIAMOND", "钻石会员", Decimal("30000"), Decimal("0.15"), Decimal("2.00"), 3),
]
TIER_DISCOUNTS = {row[0]: row[3] for row in TIERS}
TIER_ORDER = [row[0] for row in TIERS]

PARENT_CATEGORIES = ["数码", "家居", "服饰", "图书", "运动"]
SUBCATEGORIES = {
    "数码": ["手机配件", "电脑办公", "影音设备", "智能设备"],
    "家居": ["厨房用品", "家纺", "收纳", "家装工具"],
    "服饰": ["男装", "女装", "鞋靴", "箱包"],
    "图书": ["文学", "科技", "经管", "少儿"],
    "运动": ["健身", "户外", "球类", "运动服饰"],
}
BASE_PRICES = {"数码": 420, "家居": 160, "服饰": 220, "图书": 70, "运动": 260}

CAMPAIGNS = [
    (1, "2024双十一", "PLATFORM", datetime(2024, 11, 1, tzinfo=timezone.utc), datetime(2024, 11, 12, tzinfo=timezone.utc), Decimal("0.12")),
    (2, "2025年货节", "CATEGORY", datetime(2025, 1, 1, tzinfo=timezone.utc), datetime(2025, 1, 21, tzinfo=timezone.utc), Decimal("0.08")),
    (3, "2025六一八", "PLATFORM", datetime(2025, 6, 1, tzinfo=timezone.utc), datetime(2025, 6, 19, tzinfo=timezone.utc), Decimal("0.10")),
    (4, "2025双十一", "PLATFORM", datetime(2025, 11, 1, tzinfo=timezone.utc), datetime(2025, 11, 12, tzinfo=timezone.utc), Decimal("0.15")),
    (5, "2026新春会员日", "RETENTION", datetime(2026, 2, 1, tzinfo=timezone.utc), datetime(2026, 2, 16, tzinfo=timezone.utc), Decimal("0.07")),
    (6, "2026六一八", "PLATFORM", datetime(2026, 6, 1, tzinfo=timezone.utc), datetime(2026, 6, 19, tzinfo=timezone.utc), Decimal("0.12")),
    (7, "2026暑期运动季", "CATEGORY", datetime(2026, 7, 1, tzinfo=timezone.utc), datetime(2026, 8, 16, tzinfo=timezone.utc), Decimal("0.06")),
    (8, "2026新客专享", "ACQUISITION", datetime(2026, 8, 1, tzinfo=timezone.utc), datetime(2026, 9, 1, tzinfo=timezone.utc), Decimal("0.05")),
]


def _money(value: Decimal | float | int) -> Decimal:
    return Decimal(value).quantize(MONEY, rounding=ROUND_HALF_UP)


def _random_time(rng: random.Random, start: datetime, end: datetime) -> datetime:
    seconds = int((end - start).total_seconds())
    return start + timedelta(seconds=rng.randrange(seconds))


def _upsert_rows(
    cursor: psycopg.Cursor,
    table: str,
    columns: Sequence[str],
    conflict_columns: Sequence[str],
    rows: Iterable[Sequence[object]],
) -> None:
    """Stage a batch with COPY, then safely upsert without deleting other rows."""
    staging = f"seed_{table}"
    cursor.execute(f"CREATE TEMP TABLE {staging} (LIKE analytics.{table} INCLUDING DEFAULTS) ON COMMIT DROP")
    with cursor.copy(f"COPY {staging} ({','.join(columns)}) FROM STDIN") as copy:
        for row in rows:
            copy.write_row(row)
    update_columns = [column for column in columns if column not in conflict_columns]
    assignments = ",".join(f"{column}=EXCLUDED.{column}" for column in update_columns)
    cursor.execute(
        f"INSERT INTO analytics.{table} ({','.join(columns)}) "
        f"SELECT {','.join(columns)} FROM {staging} "
        f"ON CONFLICT ({','.join(conflict_columns)}) DO UPDATE SET {assignments}"
    )


def _active_campaign(moment: datetime) -> tuple | None:
    return next((row for row in CAMPAIGNS if row[3] <= moment < row[4]), None)


def build_demo_data() -> dict[str, list[tuple]]:
    """Build a deterministic, non-uniform two-year commerce dataset."""
    rng = random.Random(20260928)
    categories: list[tuple] = []
    subcategory_lookup: dict[str, list[int]] = {}
    next_category_id = 1
    for parent in PARENT_CATEGORIES:
        parent_id = next_category_id
        categories.append((parent_id, parent, None, 1))
        next_category_id += 1
        subcategory_lookup[parent] = []
        for child in SUBCATEGORIES[parent]:
            categories.append((next_category_id, child, parent_id, 2))
            subcategory_lookup[parent].append(next_category_id)
            next_category_id += 1

    customers: list[tuple] = []
    memberships: list[tuple] = []
    membership_periods: dict[int, list[tuple[datetime, datetime | None, str]]] = {}
    membership_id = 1
    region_names = list(REGIONS)
    for customer_id in range(1, CUSTOMER_COUNT + 1):
        region = rng.choices(region_names, weights=[25, 20, 20, 14, 13, 8])[0]
        signup_at = DATA_START - timedelta(days=rng.randrange(1, 901), hours=rng.randrange(24))
        acquired_channel = rng.choices([1, 2, 3, 4], weights=[42, 25, 25, 8])[0]
        segment = rng.choices(["MASS", "GROWTH", "HIGH_VALUE"], weights=[68, 24, 8])[0]
        customers.append((customer_id, f"客户{customer_id:05d}", rng.choice(REGIONS[region]), region, signup_at, acquired_channel, segment))

        initial_tier = rng.choices(TIER_ORDER, weights=[58, 27, 12, 3])[0]
        periods: list[tuple[datetime, datetime | None, str]] = []
        if initial_tier != "DIAMOND" and rng.random() < 0.24:
            upgrade_at = datetime(2025, 5, 1, tzinfo=timezone.utc) + timedelta(days=rng.randrange(330))
            upgraded_tier = TIER_ORDER[TIER_ORDER.index(initial_tier) + 1]
            periods.append((signup_at, upgrade_at, initial_tier))
            periods.append((upgrade_at, None, upgraded_tier))
            memberships.append((membership_id, customer_id, initial_tier, signup_at, upgrade_at, "INITIAL_ENROLLMENT"))
            membership_id += 1
            memberships.append((membership_id, customer_id, upgraded_tier, upgrade_at, None, "ANNUAL_SPEND_UPGRADE"))
            membership_id += 1
        else:
            periods.append((signup_at, None, initial_tier))
            memberships.append((membership_id, customer_id, initial_tier, signup_at, None, "INITIAL_ENROLLMENT"))
            membership_id += 1
        membership_periods[customer_id] = periods

    products: list[tuple] = []
    for product_id in range(1, PRODUCT_COUNT + 1):
        parent = PARENT_CATEGORIES[(product_id - 1) % len(PARENT_CATEGORIES)]
        category_id = rng.choice(subcategory_lookup[parent])
        list_price = _money(BASE_PRICES[parent] * rng.uniform(0.35, 2.8))
        cost = _money(list_price * Decimal(str(rng.uniform(0.45, 0.72))))
        brand = f"品牌{((product_id - 1) % 25) + 1:02d}"
        products.append((product_id, f"{parent}商品{product_id:03d}", parent, list_price, category_id, brand, cost, product_id % 29 != 0))

    orders: list[tuple] = []
    items: list[tuple] = []
    promotions: list[tuple] = []
    payments: list[tuple] = []
    refunds: list[tuple] = []
    refund_items: list[tuple] = []
    shipments: list[tuple] = []
    order_details: dict[int, list[tuple[int, int, Decimal]]] = {}
    order_campaign: dict[int, int | None] = {}

    item_id = payment_id = refund_id = refund_item_id = shipment_id = 1
    for order_id in range(1, ORDER_COUNT + 1):
        if rng.random() < 0.22:
            campaign = rng.choice(CAMPAIGNS)
            ordered_at = _random_time(rng, campaign[3], campaign[4])
        else:
            ordered_at = _random_time(rng, DATA_START, DATA_END)
            campaign = _active_campaign(ordered_at) if rng.random() < 0.62 else None
        customer_id = rng.randint(1, CUSTOMER_COUNT)
        channel_id = rng.choices([1, 2, 3, 4], weights=[44, 24, 24, 8])[0]
        status = rng.choices(["PAID", "SHIPPED", "COMPLETED", "CANCELLED"], weights=[10, 15, 68, 7])[0]
        tier_code = next(tier for start, end, tier in membership_periods[customer_id] if start <= ordered_at and (end is None or ordered_at < end))
        shipping_fee = Decimal("0.00") if tier_code in {"PLATINUM", "DIAMOND"} or rng.random() < 0.38 else rng.choice([Decimal("8.00"), Decimal("12.00")])
        orders.append((order_id, customer_id, ordered_at, status, channel_id, tier_code, shipping_fee, "CNY"))
        order_campaign[order_id] = campaign[0] if campaign else None

        campaign_rate = campaign[5] if campaign else Decimal("0")
        member_rate = TIER_DISCOUNTS[tier_code]
        order_total = shipping_fee
        order_campaign_discount = Decimal("0")
        detail_rows: list[tuple[int, int, Decimal]] = []
        for _ in range(rng.randint(1, 4)):
            product_id = rng.randint(1, PRODUCT_COUNT)
            product = products[product_id - 1]
            quantity = rng.randint(1, 3)
            list_unit_price = product[3]
            after_campaign = _money(list_unit_price * (Decimal("1") - campaign_rate))
            final_unit_price = _money(after_campaign * (Decimal("1") - member_rate))
            campaign_discount = _money((list_unit_price - after_campaign) * quantity)
            membership_discount = _money((after_campaign - final_unit_price) * quantity)
            items.append((item_id, order_id, product_id, quantity, final_unit_price, list_unit_price, campaign_discount, membership_discount, product[6]))
            detail_rows.append((item_id, quantity, final_unit_price))
            order_total += final_unit_price * quantity
            order_campaign_discount += campaign_discount
            item_id += 1
        order_details[order_id] = detail_rows
        if campaign:
            promotions.append((order_id, campaign[0], order_campaign_discount))

        attempt_no = 1
        if status == "CANCELLED":
            if rng.random() < 0.35:
                attempted_at = ordered_at + timedelta(minutes=rng.randint(2, 40))
                payments.append((payment_id, order_id, _money(order_total), None, "FAILED", attempt_no, attempted_at, rng.choice(["ALIPAY", "WECHAT", "CARD"])))
                payment_id += 1
            continue
        if rng.random() < 0.12:
            attempted_at = ordered_at + timedelta(minutes=rng.randint(2, 20))
            payments.append((payment_id, order_id, _money(order_total), None, "FAILED", attempt_no, attempted_at, rng.choice(["ALIPAY", "WECHAT", "CARD"])))
            payment_id += 1
            attempt_no += 1
        paid_at = ordered_at + timedelta(minutes=rng.randint(5, 180))
        if rng.random() < 0.06 and order_total >= Decimal("10"):
            first_amount = _money(order_total * Decimal("0.60"))
            second_amount = _money(order_total - first_amount)
            payments.append((payment_id, order_id, first_amount, paid_at, "SUCCEEDED", attempt_no, paid_at, "CARD"))
            payment_id += 1
            payments.append((payment_id, order_id, second_amount, paid_at + timedelta(minutes=3), "SUCCEEDED", attempt_no + 1, paid_at + timedelta(minutes=3), "WECHAT"))
            payment_id += 1
        else:
            method = "CASH" if channel_id == 4 and rng.random() < 0.55 else rng.choice(["ALIPAY", "WECHAT", "CARD"])
            payments.append((payment_id, order_id, _money(order_total), paid_at, "SUCCEEDED", attempt_no, paid_at, method))
            payment_id += 1

        shipment_count = 2 if len(detail_rows) >= 3 and rng.random() < 0.12 else 1
        for shipment_no in range(1, shipment_count + 1):
            promised = paid_at + timedelta(days=rng.randint(3, 6))
            if status == "PAID":
                shipment_status, shipped_at, delivered_at = "PENDING", None, None
            elif status == "SHIPPED":
                shipped_at = paid_at + timedelta(hours=rng.randint(8, 72))
                shipment_status, delivered_at = ("LOST", None) if rng.random() < 0.01 else ("SHIPPED", None)
            else:
                shipped_at = paid_at + timedelta(hours=rng.randint(6, 60))
                delay_days = rng.randint(1, 4) if rng.random() < 0.84 else rng.randint(6, 10)
                delivered_at = shipped_at + timedelta(days=delay_days)
                shipment_status = "DELIVERED"
            shipments.append((shipment_id, order_id, shipment_no, rng.choice(["顺丰", "京东物流", "中通", "圆通"]), shipment_status, shipped_at, promised, delivered_at))
            shipment_id += 1

        if status in {"SHIPPED", "COMPLETED"} and rng.random() < 0.15:
            request_count = 2 if len(detail_rows) > 1 and rng.random() < 0.18 else 1
            for selected_item in rng.sample(detail_rows, k=min(request_count, len(detail_rows))):
                source_item_id, purchased_quantity, unit_price = selected_item
                refund_quantity = rng.randint(1, purchased_quantity)
                refund_amount = _money(unit_price * refund_quantity)
                requested_at = paid_at + timedelta(days=rng.randint(2, 35))
                refund_status = rng.choices(["APPROVED", "REJECTED", "PENDING"], weights=[72, 18, 10])[0]
                refunded_at = requested_at + timedelta(days=rng.randint(1, 5)) if refund_status == "APPROVED" else None
                refunds.append((refund_id, order_id, refund_amount, refunded_at, refund_status, requested_at, rng.choice(["不喜欢", "质量问题", "尺寸不合适", "重复购买", "物流破损"])))
                refund_items.append((refund_item_id, refund_id, source_item_id, refund_quantity, refund_amount))
                refund_id += 1
                refund_item_id += 1

    sessions: list[tuple] = []
    session_id = 1
    for order_id, customer_id, ordered_at, _status, channel_id, *_rest in orders:
        campaign_id = order_campaign[order_id]
        sessions.append((session_id, customer_id, channel_id, campaign_id, ordered_at - timedelta(minutes=rng.randint(5, 150)), rng.choice(["DIRECT", "SEARCH", "SOCIAL", "AD", "EMAIL"]), order_id))
        session_id += 1
    while session_id <= SESSION_COUNT:
        started_at = _random_time(rng, DATA_START, DATA_END)
        active = _active_campaign(started_at)
        campaign_id = active[0] if active and rng.random() < 0.42 else None
        customer_id = rng.randint(1, CUSTOMER_COUNT) if rng.random() < 0.72 else None
        channel_id = rng.choices([1, 2, 3], weights=[47, 27, 26])[0]
        sessions.append((session_id, customer_id, channel_id, campaign_id, started_at, rng.choice(["DIRECT", "SEARCH", "SOCIAL", "AD", "EMAIL"]), None))
        session_id += 1

    spend: list[tuple] = []
    for campaign in CAMPAIGNS:
        current = campaign[3].date()
        end = campaign[4].date()
        while current < end:
            for channel_id in (1, 2, 3):
                amount = _money(rng.uniform(2500, 12000))
                impressions = rng.randint(80_000, 400_000)
                clicks = int(impressions * rng.uniform(0.008, 0.045))
                spend.append((current, campaign[0], channel_id, amount, impressions, clicks))
            current += timedelta(days=1)

    return {
        "sales_channels": CHANNELS,
        "membership_tiers": TIERS,
        "product_categories": categories,
        "campaigns": CAMPAIGNS,
        "customers": customers,
        "customer_memberships": memberships,
        "products": products,
        "orders": orders,
        "order_items": items,
        "order_promotions": promotions,
        "payments": payments,
        "refunds": refunds,
        "refund_items": refund_items,
        "shipments": shipments,
        "web_sessions": sessions,
        "campaign_spend_daily": spend,
    }


TABLE_COLUMNS = {
    "sales_channels": ("channel_id", "channel_code", "channel_name", "channel_group"),
    "membership_tiers": ("tier_code", "tier_name", "min_annual_spend", "discount_rate", "points_multiplier", "tier_rank"),
    "product_categories": ("category_id", "category_name", "parent_category_id", "category_level"),
    "campaigns": ("campaign_id", "campaign_name", "campaign_type", "starts_at", "ends_at", "discount_rate"),
    "customers": ("customer_id", "customer_name", "city", "region", "signup_at", "acquired_channel_id", "customer_segment"),
    "customer_memberships": ("membership_id", "customer_id", "tier_code", "valid_from", "valid_to", "change_reason"),
    "products": ("product_id", "product_name", "category", "list_price", "category_id", "brand", "standard_cost", "is_active"),
    "orders": ("order_id", "customer_id", "ordered_at", "status", "channel_id", "membership_tier_code", "shipping_fee", "currency"),
    "order_items": ("item_id", "order_id", "product_id", "quantity", "unit_price", "list_unit_price", "campaign_discount_amount", "membership_discount_amount", "cost_unit_price"),
    "order_promotions": ("order_id", "campaign_id", "allocated_discount_amount"),
    "payments": ("payment_id", "order_id", "amount", "paid_at", "status", "attempt_no", "attempted_at", "payment_method"),
    "refunds": ("refund_id", "order_id", "amount", "refunded_at", "status", "requested_at", "reason"),
    "refund_items": ("refund_item_id", "refund_id", "item_id", "quantity", "amount"),
    "shipments": ("shipment_id", "order_id", "shipment_no", "carrier", "status", "shipped_at", "promised_delivery_at", "delivered_at"),
    "web_sessions": ("session_id", "customer_id", "channel_id", "campaign_id", "session_started_at", "traffic_source", "converted_order_id"),
    "campaign_spend_daily": ("spend_date", "campaign_id", "channel_id", "spend_amount", "impressions", "clicks"),
}

CONFLICT_COLUMNS = {
    "sales_channels": ("channel_id",),
    "membership_tiers": ("tier_code",),
    "product_categories": ("category_id",),
    "campaigns": ("campaign_id",),
    "customers": ("customer_id",),
    "customer_memberships": ("membership_id",),
    "products": ("product_id",),
    "orders": ("order_id",),
    "order_items": ("item_id",),
    "order_promotions": ("order_id", "campaign_id"),
    "payments": ("payment_id",),
    "refunds": ("refund_id",),
    "refund_items": ("refund_item_id",),
    "shipments": ("shipment_id",),
    "web_sessions": ("session_id",),
    "campaign_spend_daily": ("spend_date", "campaign_id", "channel_id"),
}


def seed_demo(*, reset: bool = False) -> dict[str, int]:
    """Load the deterministic dataset; resetting an older dataset is explicit."""
    settings = get_settings()
    with psycopg.connect(settings.db_admin_url) as conn:
        with conn.cursor() as cursor:
            state = cursor.execute(
                "SELECT seed_version FROM analytics.demo_seed_state WHERE state_id=1"
            ).fetchone()
            existing_orders = cursor.execute(
                "SELECT EXISTS (SELECT 1 FROM analytics.orders LIMIT 1)"
            ).fetchone()[0]
            if existing_orders and state is None and not reset:
                raise RuntimeError(
                    "Existing pre-v2 demo data detected. Re-run with --reset to replace "
                    "the generated analytics dataset explicitly."
                )
            if state is not None and state[0] != SEED_VERSION and not reset:
                raise RuntimeError(
                    f"Demo seed version {state[0]} differs from {SEED_VERSION}; use --reset."
                )
            if reset:
                cursor.execute(
                    """TRUNCATE TABLE
                    analytics.campaign_spend_daily, analytics.web_sessions,
                    analytics.shipments, analytics.refund_items, analytics.refunds,
                    analytics.payments, analytics.order_promotions, analytics.order_items,
                    analytics.orders, analytics.customer_memberships, analytics.customers,
                    analytics.products, analytics.product_categories, analytics.campaigns,
                    analytics.membership_tiers, analytics.sales_channels
                    RESTART IDENTITY CASCADE"""
                )
    data = build_demo_data()
    with psycopg.connect(settings.db_admin_url) as conn:
        with conn.cursor() as cursor:
            for table, rows in data.items():
                _upsert_rows(
                    cursor,
                    table,
                    TABLE_COLUMNS[table],
                    CONFLICT_COLUMNS[table],
                    rows,
                )
            cursor.execute(
                """INSERT INTO analytics.demo_seed_state (state_id,seed_version,seeded_at)
                VALUES (1,%s,now()) ON CONFLICT (state_id) DO UPDATE SET
                seed_version=EXCLUDED.seed_version, seeded_at=EXCLUDED.seeded_at""",
                (SEED_VERSION,),
            )
    return {table: len(rows) for table, rows in data.items()}
