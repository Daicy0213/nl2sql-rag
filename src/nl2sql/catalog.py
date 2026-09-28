"""Single source of truth for business tables exposed to the NL2SQL agent."""

ANALYTICS_TABLES = frozenset(
    {
        "sales_channels",
        "membership_tiers",
        "product_categories",
        "campaigns",
        "fiscal_calendar",
        "warehouses",
        "suppliers",
        "customers",
        "customer_memberships",
        "products",
        "product_suppliers",
        "orders",
        "order_items",
        "order_promotions",
        "payments",
        "refunds",
        "refund_items",
        "shipments",
        "inventory_snapshots",
        "product_reviews",
        "web_sessions",
        "campaign_spend_daily",
    }
)
