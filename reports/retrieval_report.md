# 检索评估报告

知识库规模：40 题金标；k 与模式见各表。

## 模式：hybrid（k=9）

| 范围 | 用例 | 上下文完整率 | 上下文召回 | Precision@k | Recall@k | MRR | nDCG@k | 平均上下文字符 |
|---|---|---|---|---|---|---|---|---|
| 全部 | 40 | 1.00 | 1.00 | 0.33 | 0.92 | 0.96 | 0.87 | 2812 |
| confusable | 10 | 1.00 | 1.00 | 0.31 | 0.93 | 0.95 | 0.87 | 3012 |
| multihop | 12 | 1.00 | 1.00 | 0.38 | 0.85 | 0.96 | 0.81 | 2859 |
| rule | 8 | 1.00 | 1.00 | 0.29 | 1.00 | 0.92 | 0.92 | 2576 |
| single | 10 | 1.00 | 1.00 | 0.31 | 0.92 | 1.00 | 0.93 | 2746 |

全部用例的必需卡都进入了上下文。

## 模式：vector（k=9）

| 范围 | 用例 | 上下文完整率 | 上下文召回 | Precision@k | Recall@k | MRR | nDCG@k | 平均上下文字符 |
|---|---|---|---|---|---|---|---|---|
| 全部 | 40 | 1.00 | 1.00 | 0.33 | 0.92 | 0.97 | 0.88 | 2782 |
| confusable | 10 | 1.00 | 1.00 | 0.31 | 0.93 | 0.95 | 0.89 | 2922 |
| multihop | 12 | 1.00 | 1.00 | 0.38 | 0.85 | 0.96 | 0.79 | 2859 |
| rule | 8 | 1.00 | 1.00 | 0.29 | 1.00 | 1.00 | 0.96 | 2534 |
| single | 10 | 1.00 | 1.00 | 0.31 | 0.92 | 1.00 | 0.92 | 2746 |

全部用例的必需卡都进入了上下文。

## 模式：lexical（k=9）

| 范围 | 用例 | 上下文完整率 | 上下文召回 | Precision@k | Recall@k | MRR | nDCG@k | 平均上下文字符 |
|---|---|---|---|---|---|---|---|---|
| 全部 | 40 | 0.57 | 0.66 | 0.17 | 0.47 | 0.90 | 0.56 | 969 |
| confusable | 10 | 0.70 | 0.75 | 0.13 | 0.42 | 0.90 | 0.50 | 1073 |
| multihop | 12 | 0.42 | 0.67 | 0.20 | 0.45 | 0.96 | 0.55 | 1160 |
| rule | 8 | 0.25 | 0.25 | 0.12 | 0.40 | 0.69 | 0.45 | 746 |
| single | 10 | 0.90 | 0.90 | 0.19 | 0.61 | 1.00 | 0.70 | 814 |

未完整覆盖必需卡的用例：

- `paid_orders`（single）缺 ['metric.order_count']：2026 年 8 月有多少笔已支付订单？
- `net_sales_by_category`（multihop）缺 ['join.products_categories']：按一级品类统计净销售额。
- `ontime_by_channel`（multihop）缺 ['join.orders_channels']：各渠道的准时发货率是多少？
- `campaign_roi`（multihop）缺 ['join.orders_discounts_campaigns']：各活动的 ROI 是多少？
- `return_by_warehouse`（multihop）缺 ['join.shipments_warehouses']：各仓库的退货率是多少？
- `tier_active_customers`（multihop）缺 ['join.customer_tiers']：各会员等级的活跃客户数是多少？
- `fiscal_sales`（multihop）缺 ['rule.fiscal_year']：按财年统计实收金额。
- `inventory_by_warehouse`（multihop）缺 ['join.inventory_products']：各仓库的库存金额是多少？
- `list_vs_receipts`（confusable）缺 ['rule.sales_caliber']：标价金额和实收金额差多少？
- `channel_share`（confusable）缺 ['metric.channel_share']：各渠道的占比是多少？
- `campaign_sales`（confusable）缺 ['metric.campaign_sales']：双11 活动的销售额是多少？
- `fiscal_year_rule`（rule）缺 ['rule.fiscal_year']：2026 年 1 月属于哪个财年？
- `cancelled_rule`（rule）缺 ['rule.cancelled_orders']：取消订单要不要计入订单量？
- `refund_status_rule`（rule）缺 ['rule.refund_status']：被拒绝的退款申请要计入退款金额吗？
- `freight_rule`（rule）缺 ['rule.freight_policy']：运费算进销售额吗？
- `amplification_rule`（rule）缺 ['rule.aggregation_first']：为什么多笔退款会让支付金额被重复计算？
- `freshness_rule`（rule）缺 ['rule.data_freshness']：有 2027 年的数据吗？
