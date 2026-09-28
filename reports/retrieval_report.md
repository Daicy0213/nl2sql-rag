# 检索评估报告

评估日期：2026-09-29；人工标注问题：150 条。

| 策略 | Recall@5 | Recall@10 | MRR@10 | nDCG@10 | 上下文召回率 | 必需表覆盖率 |
|---|---:|---:|---:|---:|---:|---:|
| lexical | 0.2678 | 0.2744 | 0.2844 | 0.2721 | 0.3411 | 0.4322 |
| vector | 0.9767 | 0.9867 | 0.8455 | 0.8786 | 1.0000 | 1.0000 |
| hybrid | 0.9733 | 0.9867 | 0.8015 | 0.8445 | 1.0000 | 1.0000 |

## lexical 未完全命中（112 条）

- `r001`：缺少知识 ['join.current_membership']；缺少表 ['customer_memberships', 'membership_tiers']。
- `r004`：缺少知识 ['dimension.membership_diamond']；缺少表 ['membership_tiers']。
- `r007`：缺少知识 ['metric.member_order_count']；缺少表 ['membership_tiers']。
- `r009`：缺少知识 ['metric.membership_discount']；缺少表 ['membership_tiers', 'order_items', 'orders']。
- `r010`：缺少知识 ['rule.membership_discount_order']；缺少表 ['membership_tiers', 'order_items']。
- `r011`：缺少知识 ['rule.discount_not_double_count']；缺少表 ['order_items', 'payments']。
- `r012`：缺少知识 ['rule.membership_snapshot']；缺少表 ['customer_memberships', 'orders']。
- `r013`：缺少知识 ['rule.membership_effective_interval']；缺少表 ['customer_memberships']。
- `r014`：缺少知识 ['glossary.member_ambiguity']；缺少表 []。
- `r015`：缺少知识 ['metric.membership_upgrade_count']；缺少表 ['customer_memberships', 'membership_tiers']。
- `r017`：缺少知识 ['join.order_membership_snapshot']；缺少表 ['membership_tiers', 'orders']。
- `r018`：缺少知识 ['rule.membership_shipping']；缺少表 ['orders']。
- `r020`：缺少知识 ['metric.member_sales']；缺少表 ['membership_tiers', 'orders']。
- `r021`：缺少知识 ['join.current_membership']；缺少表 []。
- `r022`：缺少知识 ['rule.membership_effective_interval']；缺少表 ['customer_memberships']。
- `r023`：缺少知识 ['rule.discount_not_double_count']；缺少表 ['order_items']。
- `r024`：缺少知识 ['example.membership_discount']；缺少表 ['membership_tiers', 'order_items', 'orders']。
- `r025`：缺少知识 ['glossary.member_ambiguity']；缺少表 []。
- `r026`：缺少知识 ['metric.order_count']；缺少表 []。
- `r027`：缺少知识 ['join.customer_orders']；缺少表 ['customers']。
- `r028`：缺少知识 ['metric.paid_order_count']；缺少表 ['orders', 'payments']。
- `r029`：缺少知识 ['metric.paid_order_count']；缺少表 ['orders', 'payments']。
- `r031`：缺少知识 ['rule.payment_time']；缺少表 []。
- `r032`：缺少知识 ['rule.payment_status']；缺少表 ['payments']。
- `r035`：缺少知识 ['join.customer_orders']；缺少表 ['customers']。
- `r036`：缺少知识 ['rule.net_sales_window']；缺少表 []。
- `r037`：缺少知识 ['rule.net_sales_window']；缺少表 ['payments', 'refunds']。
- `r039`：缺少知识 ['metric.average_order_value']；缺少表 ['payments']。
- `r041`：缺少知识 ['metric.units_sold']；缺少表 ['order_items', 'orders']。
- `r043`：缺少知识 ['metric.sku_count']；缺少表 ['order_items', 'orders']。
- `r044`：缺少知识 ['metric.active_customers']；缺少表 ['orders']。
- `r047`：缺少知识 ['join.first_purchase']；缺少表 []。
- `r048`：缺少知识 ['metric.repeat_purchase_rate']；缺少表 ['orders']。
- `r049`：缺少知识 ['rule.repeat_purchase_window']；缺少表 []。
- `r051`：缺少知识 ['metric.payment_success_rate']；缺少表 ['payments']。
- `r052`：缺少知识 ['rule.payment_attempt_time']；缺少表 ['payments']。
- `r053`：缺少知识 ['example.payment_retry']；缺少表 ['payments']。
- `r054`：缺少知识 ['rule.payment_status']；缺少表 []。
- `r055`：缺少知识 ['rule.refund_status']；缺少表 ['refunds']。
- `r056`：缺少知识 ['rule.refund_request_time']；缺少表 ['refunds']。
- `r057`：缺少知识 ['rule.refund_completion_time']；缺少表 ['refunds']。
- `r058`：缺少知识 ['metric.refund_amount_rate']；缺少表 ['refunds']。
- `r059`：缺少知识 ['join.payment_refunds_safe']；缺少表 ['orders', 'payments', 'refunds']。
- `r060`：缺少知识 ['metric.refund_order_rate']；缺少表 ['payments', 'refunds']。
- `r061`：缺少知识 ['metric.refund_item_rate']；缺少表 ['refund_items', 'refunds']。
- `r062`：缺少知识 ['join.refund_items']；缺少表 ['order_items', 'products', 'refund_items', 'refunds']。
- `r063`：缺少知识 ['rule.refund_status']；缺少表 []。
- `r064`：缺少知识 ['dimension.refund_statuses']；缺少表 ['refunds']。
- `r066`：缺少知识 ['dimension.payment_statuses']；缺少表 []。
- `r067`：缺少知识 ['table.refund_items']；缺少表 ['order_items', 'refund_items', 'refunds']。
- `r069`：缺少知识 ['example.region_net_sales']；缺少表 ['customers', 'orders', 'payments', 'refunds']。
- `r070`：缺少知识 ['rule.preaggregate_many_to_many']；缺少表 ['order_promotions', 'payments', 'refunds', 'shipments']。
- `r071`：缺少知识 ['join.category_hierarchy']；缺少表 ['product_categories', 'products']。
- `r072`：缺少知识 ['table.order_items', 'table.products']；缺少表 ['order_items', 'products']。
- `r075`：缺少知识 ['example.category_gross_margin']；缺少表 ['product_categories', 'products']。
- `r076`：缺少知识 ['join.order_products']；缺少表 ['order_items', 'products']。
- `r079`：缺少知识 ['glossary.channel_ambiguity']；缺少表 ['customers', 'orders', 'sales_channels']。
- `r082`：缺少知识 ['join.customer_orders']；缺少表 ['customers', 'orders']。
- `r083`：缺少知识 ['table.order_items']；缺少表 ['products']。
- `r084`：缺少知识 ['table.order_promotions']；缺少表 ['campaigns', 'order_promotions', 'orders']。
- `r086`：缺少知识 ['metric.on_time_delivery_rate']；缺少表 ['shipments']。
- `r087`：缺少知识 ['rule.delivery_status']；缺少表 []。
- `r088`：缺少知识 ['example.on_time_delivery']；缺少表 ['orders', 'sales_channels', 'shipments']。
- `r089`：缺少知识 ['metric.average_fulfillment_hours']；缺少表 []。
- `r090`：缺少知识 ['join.payment_shipments']；缺少表 ['orders', 'payments', 'shipments']。
- `r091`：缺少知识 ['table.shipments']；缺少表 ['orders', 'shipments']。
- `r092`：缺少知识 ['dimension.shipment_statuses']；缺少表 ['shipments']。
- `r093`：缺少知识 ['table.shipments']；缺少表 ['orders', 'shipments']。
- `r094`：缺少知识 ['rule.membership_shipping']；缺少表 []。
- `r095`：缺少知识 ['rule.delivery_status']；缺少表 ['shipments']。
- `r098`：缺少知识 ['metric.visitor_conversion_rate']；缺少表 ['web_sessions']。
- `r099`：缺少知识 ['rule.session_time']；缺少表 ['web_sessions']。
- `r100`：缺少知识 ['join.sessions_orders']；缺少表 ['orders', 'web_sessions']。
- `r101`：缺少知识 ['metric.roas']；缺少表 ['campaign_spend_daily', 'campaigns', 'order_promotions', 'payments']。
- `r102`：缺少知识 ['join.campaign_revenue_spend']；缺少表 []。
- `r103`：缺少知识 ['rule.campaign_attribution']；缺少表 ['campaigns', 'order_promotions', 'orders']。
- `r106`：缺少知识 ['metric.cost_per_click']；缺少表 ['campaign_spend_daily']。
- `r107`：缺少知识 ['dimension.campaign_types']；缺少表 ['campaigns']。
- `r109`：缺少知识 ['example.campaign_roas']；缺少表 ['campaign_spend_daily', 'campaigns', 'order_promotions', 'orders', 'payments']。
- `r110`：缺少知识 ['table.campaign_spend_daily']；缺少表 ['campaign_spend_daily', 'campaigns', 'sales_channels']。
- `r111`：缺少知识 ['rule.month_half_open']；缺少表 ['orders', 'payments']。
- `r113`：缺少知识 ['rule.safe_ratio']；缺少表 []。
- `r114`：缺少知识 ['metric.first_purchase_customers']；缺少表 ['orders']。
- `r115`：缺少知识 ['metric.refund_amount_rate', 'metric.refund_item_rate', 'metric.refund_order_rate']；缺少表 ['order_items', 'payments', 'refund_items', 'refunds']。
- `r116`：缺少知识 ['metric.net_sales']；缺少表 ['refunds']。
- `r117`：缺少知识 ['example.first_purchase_cohort']；缺少表 ['customers', 'orders']。
- `r118`：缺少知识 ['example.refund_rate']；缺少表 []。
- `r119`：缺少知识 ['rule.membership_discount_order']；缺少表 ['order_items']。
- `r122`：缺少知识 ['rule.latest_inventory_snapshot']；缺少表 ['inventory_snapshots']。
- `r123`：缺少知识 ['rule.inventory_snapshot_not_flow']；缺少表 ['inventory_snapshots']。
- `r124`：缺少知识 ['example.warehouse_inventory_value']；缺少表 ['inventory_snapshots', 'warehouses']。
- `r127`：缺少知识 ['example.low_stock_products']；缺少表 ['inventory_snapshots', 'products']。
- `r128`：缺少知识 ['join.inventory_product_warehouse']；缺少表 ['inventory_snapshots', 'products', 'warehouses']。
- `r129`：缺少知识 ['table.inventory_snapshots']；缺少表 ['inventory_snapshots', 'products', 'warehouses']。
- `r130`：缺少知识 ['join.shipment_warehouse']；缺少表 ['warehouses']。
- `r132`：缺少知识 ['rule.primary_supplier']；缺少表 ['product_suppliers']。
- `r133`：缺少知识 ['join.product_supplier']；缺少表 ['product_suppliers', 'products', 'suppliers']。
- `r134`：缺少知识 ['metric.average_lead_time']；缺少表 ['product_suppliers', 'suppliers']。
- `r135`：缺少知识 ['example.supplier_purchase_cost']；缺少表 ['inventory_snapshots', 'product_suppliers', 'suppliers']。
- `r136`：缺少知识 ['table.product_suppliers']；缺少表 ['products']。
- `r137`：缺少知识 ['table.suppliers']；缺少表 ['suppliers']。
- `r139`：缺少知识 ['metric.review_count']；缺少表 ['product_reviews']。
- `r141`：缺少知识 ['rule.review_denominator']；缺少表 []。
- `r142`：缺少知识 ['join.review_order_product']；缺少表 ['orders', 'product_reviews', 'products']。
- `r143`：缺少知识 ['example.category_rating']；缺少表 ['product_categories', 'products']。
- `r144`：缺少知识 ['table.product_reviews']；缺少表 ['orders', 'product_reviews', 'products']。
- `r145`：缺少知识 ['rule.fiscal_year']；缺少表 ['fiscal_calendar']。
- `r146`：缺少知识 ['example.fiscal_sales']；缺少表 ['fiscal_calendar']。
- `r147`：缺少知识 ['join.fiscal_calendar']；缺少表 ['fiscal_calendar', 'orders']。
- `r148`：缺少知识 ['table.fiscal_calendar']；缺少表 ['fiscal_calendar']。
- `r149`：缺少知识 ['table.warehouses']；缺少表 ['warehouses']。
- `r150`：缺少知识 ['join.shipment_warehouse']；缺少表 ['shipments', 'warehouses']。

## vector 未完全命中（3 条）

- `r001`：缺少知识 ['join.current_membership']；缺少表 []。
- `r027`：缺少知识 ['join.customer_orders']；缺少表 []。
- `r035`：缺少知识 ['join.customer_orders']；缺少表 []。

## hybrid 未完全命中（3 条）

- `r001`：缺少知识 ['join.current_membership']；缺少表 []。
- `r027`：缺少知识 ['join.customer_orders']；缺少表 []。
- `r035`：缺少知识 ['join.customer_orders']；缺少表 []。
