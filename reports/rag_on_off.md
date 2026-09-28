# RAG 开/关端到端对照

共 6 题；带检索答对 6 题，无检索答对 4 题。
判定方式：重新执行 Agent 生成的 SQL，并与金标准取值比较（率值允许百分比写法）。

| 用例 | 依赖的定义 | 金标准 | 带检索 | 无检索 |
|---|---|---|---|---|
| net_sales_east_august | 净销售额口径：实收金额扣减 APPROVED 退款 | 11261.00 | 答对 | 未答对 |
| receipts_2025 | 实收金额口径（对照组：不依赖复杂定义） | 33412444.35 | 答对 | 答对 |
| aov_all | 客单价口径：实收金额 ÷ 去重订单数 | 3574.7922416181767803 | 答对 | 答对 |
| refund_rate_amount_2026 | 退款率口径：APPROVED 退款 ÷ 实收，按支付时间选订单 | 0.05722600295283683401 | 答对 | 未答对 |
| ontime_count_june | 发货时效口径：shipped_at − ordered_at ≤ 48 小时 | 475 | 答对 | 答对 |
| top_margin_category | 毛利率口径：成交金额减主供应商采购成本 | 经济管理 | 答对 | 答对 |

## net_sales_east_august

问题：2026 年 8 月华东地区的净销售额是多少？

- **rag**：11261.00（执行 1 条 SQL）

```sql
SELECT SUM(p.amount - COALESCE(r.refund_amount, 0)) AS net_sales
FROM analytics.payments p
JOIN analytics.orders o ON o.order_id = p.order_id
JOIN analytics.customers c ON c.customer_id = o.customer_id
LEFT JOIN (
  SELECT order_id, SUM(amount) AS refund_amount
  FROM analytics.refunds
  WHERE status = 'APPROVED'
  GROUP BY order_id
) r ON r.order_id = p.order_id
WHERE p.status = 'SUCCEEDED'
  AND p.paid_at >= TIMESTAMPTZ '2026-08-01 00:00:00+00'
  AND p.paid_at <  TIMESTAMPTZ '2026-09-01 00:00:00+00'
  AND c.region = '华东';
```
- **no_rag**：2025-12（执行 13 条 SQL）

```sql
SELECT to_char(date_trunc('month', ordered_at), 'YYYY-MM') AS m, count(*) AS orders_cnt, count(DISTINCT c.region) AS regions FROM orders o JOIN customers c ON c.customer_id = o.customer_id WHERE ordered_at >= '2026-01-01+08' AND ordered_at < '2027-01-01+08' GROUP BY 1 ORDER BY 1
```

## receipts_2025

问题：2025 年全年的实收金额是多少？

- **rag**：33412444.35（执行 1 条 SQL）

```sql
SELECT SUM(amount) AS actual_received_amount, COUNT(*) AS successful_payment_cnt, MIN(paid_at) AS first_paid_at, MAX(paid_at) AS last_paid_at FROM analytics.payments WHERE status = 'SUCCEEDED' AND paid_at >= '2025-01-01' AND paid_at < '2026-01-01';
```
- **no_rag**：9084（执行 7 条 SQL）

```sql
SELECT COUNT(*) AS payment_cnt, ROUND(SUM(amount), 2) AS gross_paid
FROM analytics.payments
WHERE paid_at >= TIMESTAMP '2025-01-01 00:00:00+00' AND paid_at < TIMESTAMP '2026-01-01 00:00:00+00'
```

## aov_all

问题：全部订单的客单价是多少？

- **rag**：18045（执行 4 条 SQL）

```sql
SELECT COUNT(DISTINCT p.order_id) AS paid_order_cnt, ROUND(SUM(p.amount), 2) AS collected_amount, ROUND(SUM(p.amount) / NULLIF(COUNT(DISTINCT p.order_id), 0), 2) AS aov FROM analytics.payments p WHERE p.status = 'SUCCEEDED'
```
- **no_rag**：20000（执行 4 条 SQL）

```sql
WITH oi AS (
  SELECT oi.order_id, SUM(oi.quantity * oi.unit_price) AS item_amount
  FROM order_items oi
  GROUP BY oi.order_id
)
SELECT
  (SELECT COUNT(*) FROM orders) AS orders_total,
  (SELECT COUNT(*) FROM orders WHERE status <> 'CANCELLED') AS orders_not_cancelled,
  (SELECT COUNT(DISTINCT order_id) FROM order_items) AS orders_with_items,
  (SELECT ROUND(SUM(item_amount), 2) FROM oi) AS gmv_items_all,
  (SELECT ROUND(AVG(item_amount), 2) FROM oi) AS aov_items_all,
  (SELECT ROUND(SUM(oi.item_amount), 2) FROM oi JOIN orders o ON o.order_id = oi.order_id WHERE o.status <> 'CANCELLED') AS gmv_items_not_cancelled,
  (SELECT ROUND(AVG(oi.item_amount), 2) FROM oi JOIN orders o ON o.order_id = oi.order_id WHERE o.status <> 'CANCELLED') AS aov_items_not_cancelled,
  (SELECT ROUND(AVG(paid_amt), 2) FROM (SELECT order_id, SUM(amount) AS paid_amt FROM payments GROUP BY order_id) p) AS aov_by_payment
```

## refund_rate_amount_2026

问题：2026 年的退款率（金额口径）是多少？

- **rag**：30983899.60（执行 1 条 SQL）

```sql
WITH paid AS (
  SELECT p.order_id, p.amount
  FROM analytics.payments p
  WHERE p.status = 'SUCCEEDED'
    AND p.paid_at >= TIMESTAMPTZ '2026-01-01 00:00:00+00'
    AND p.paid_at <  TIMESTAMPTZ '2027-01-01 00:00:00+00'
),
ref AS (
  SELECT r.order_id, SUM(r.amount) AS refund_amount
  FROM analytics.refunds r
  WHERE r.status = 'APPROVED'
  GROUP BY r.order_id
)
SELECT SUM(paid.amount) AS received_amount,
       SUM(COALESCE(ref.refund_amount, 0)) AS approved_refund_amount,
       COUNT(*) AS paid_orders,
       ROUND(SUM(COALESCE(ref.refund_amount, 0)) / NULLIF(SUM(paid.amount), 0), 4) AS refund_rate_amount
FROM paid
LEFT JOIN ref ON ref.order_id = paid.order_id;
```
- **no_rag**：30983899.60（执行 4 条 SQL）

```sql
SELECT
  (SELECT sum(amount) FROM payments WHERE paid_at >= '2026-01-01' AND paid_at < '2027-01-01') AS pay_amt_2026,
  (SELECT sum(amount) FROM refunds WHERE status = 'APPROVED' AND refunded_at >= '2026-01-01' AND refunded_at < '2027-01-01') AS approved_refund_2026,
  (SELECT sum(amount) FROM refunds WHERE refunded_at >= '2026-01-01' AND refunded_at < '2027-01-01') AS all_refund_2026,
  (SELECT sum(r.amount) FROM refunds r JOIN payments p ON p.order_id = r.order_id
     WHERE r.status = 'APPROVED' AND p.paid_at >= '2026-01-01' AND p.paid_at < '2027-01-01') AS approved_refund_of_2026_pays;
```

## ontime_count_june

问题：2026 年 6 月发出的包裹中，有多少个是在下单后 48 小时内发出的？

- **rag**：688（执行 1 条 SQL）

```sql
SELECT COUNT(*) AS shipped_packages,
       COUNT(*) FILTER (WHERE EXTRACT(EPOCH FROM s.shipped_at - o.ordered_at) / 3600 <= 48) AS within_48h,
       COUNT(*) FILTER (WHERE s.status = 'DELIVERED' AND EXTRACT(EPOCH FROM s.shipped_at - o.ordered_at) / 3600 <= 48) AS within_48h_delivered_only
FROM analytics.shipments s
JOIN analytics.orders o ON o.order_id = s.order_id
WHERE s.shipped_at >= '2026-06-01' AND s.shipped_at < '2026-07-01'
  AND o.status <> 'CANCELLED';
```
- **no_rag**：688（执行 3 条 SQL）

```sql
SELECT
  count(*) AS total_shipped,
  count(*) FILTER (WHERE s.shipped_at - o.ordered_at <= INTERVAL '48 hours') AS within_48h,
  count(*) FILTER (WHERE s.shipped_at <= o.ordered_at) AS negative_lag,
  round(avg(EXTRACT(EPOCH FROM (s.shipped_at - o.ordered_at))/3600.0)::numeric, 1) AS avg_hours
FROM shipments s JOIN orders o ON o.order_id = s.order_id
WHERE s.shipped_at >= TIMESTAMPTZ '2026-06-01 00:00:00+00' AND s.shipped_at < TIMESTAMPTZ '2026-07-01 00:00:00+00'
```

## top_margin_category

问题：2026 年毛利率最高的二级品类是哪个？

- **rag**：经济管理（执行 1 条 SQL）

```sql
SELECT pc.category_name AS second_level_category,
       SUM(oi.quantity * oi.unit_price) AS revenue,
       SUM(oi.quantity * ps.purchase_price) AS cost,
       (SUM(oi.quantity * oi.unit_price) - SUM(oi.quantity * ps.purchase_price))
         / NULLIF(SUM(oi.quantity * oi.unit_price), 0) AS gross_margin_rate
FROM analytics.order_items oi
JOIN analytics.orders o ON o.order_id = oi.order_id
JOIN analytics.products p ON p.product_id = oi.product_id
JOIN analytics.product_categories pc ON pc.category_id = p.category_id AND pc.level = 2
JOIN analytics.product_suppliers ps ON ps.product_id = oi.product_id AND ps.is_primary
WHERE o.status <> 'CANCELLED'
  AND o.ordered_at >= TIMESTAMPTZ '2026-01-01'
  AND o.ordered_at < TIMESTAMPTZ '2027-01-01'
GROUP BY pc.category_name
ORDER BY gross_margin_rate DESC
```
- **no_rag**：经济管理（执行 9 条 SQL）

```sql
SELECT pc.category_name AS level2_category,
       SUM(oi.quantity * oi.unit_price) AS revenue,
       SUM(oi.quantity * ps.purchase_price) AS cost,
       ROUND((SUM(oi.quantity * oi.unit_price) - SUM(oi.quantity * ps.purchase_price))
             / SUM(oi.quantity * oi.unit_price) * 100, 2) AS gross_margin_pct
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
JOIN products p ON p.product_id = oi.product_id
JOIN product_categories pc ON pc.category_id = p.category_id AND pc.level = 2
JOIN product_suppliers ps ON ps.product_id = p.product_id AND ps.is_primary
WHERE o.ordered_at >= TIMESTAMPTZ '2026-01-01 00:00:00+00'
  AND o.ordered_at <  TIMESTAMPTZ '2027-01-01 00:00:00+00'
  AND o.status <> 'CANCELLED'
GROUP BY pc.category_name
ORDER BY gross_margin_pct DESC, revenue DESC
```
