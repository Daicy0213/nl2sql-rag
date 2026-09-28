"""Single source of truth for business tables exposed to the NL2SQL agent."""

ANALYTICS_TABLES = frozenset(
    {
        "sales_channels",
        "membership_tiers",
        "product_categories",
        "campaigns",
        "customers",
        "customer_memberships",
        "products",
        "orders",
        "order_items",
        "order_promotions",
        "payments",
        "refunds",
        "refund_items",
        "shipments",
        "web_sessions",
        "campaign_spend_daily",
    }
)
