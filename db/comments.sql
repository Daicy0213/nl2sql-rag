-- Database documentation kept separately so it can be audited and reapplied.
COMMENT ON SCHEMA analytics IS '电商经营分析演示数据域';
COMMENT ON SCHEMA rag IS 'RAG 知识文档与向量索引数据域';

COMMENT ON TABLE analytics.sales_channels IS '销售与获客渠道维表';
COMMENT ON COLUMN analytics.sales_channels.channel_id IS '渠道主键';
COMMENT ON COLUMN analytics.sales_channels.channel_code IS '稳定的英文渠道编码';
COMMENT ON COLUMN analytics.sales_channels.channel_name IS '渠道中文名称';
COMMENT ON COLUMN analytics.sales_channels.channel_group IS '渠道分组：ONLINE 或 OFFLINE';

COMMENT ON TABLE analytics.membership_tiers IS '会员等级及权益配置表';
COMMENT ON COLUMN analytics.membership_tiers.tier_code IS '会员等级编码';
COMMENT ON COLUMN analytics.membership_tiers.tier_name IS '会员等级中文名称';
COMMENT ON COLUMN analytics.membership_tiers.min_annual_spend IS '达到该等级所需最低年度消费额';
COMMENT ON COLUMN analytics.membership_tiers.discount_rate IS '会员折扣率，成交价按一减该值计算';
COMMENT ON COLUMN analytics.membership_tiers.points_multiplier IS '会员积分倍率';
COMMENT ON COLUMN analytics.membership_tiers.tier_rank IS '会员等级排序，数值越大等级越高';

COMMENT ON TABLE analytics.product_categories IS '商品两级分类维表';
COMMENT ON COLUMN analytics.product_categories.category_id IS '商品分类主键';
COMMENT ON COLUMN analytics.product_categories.category_name IS '分类名称';
COMMENT ON COLUMN analytics.product_categories.parent_category_id IS '父分类主键，一级分类为空';
COMMENT ON COLUMN analytics.product_categories.category_level IS '分类层级：1 为一级，2 为二级';

COMMENT ON TABLE analytics.campaigns IS '营销活动定义表';
COMMENT ON COLUMN analytics.campaigns.campaign_id IS '营销活动主键';
COMMENT ON COLUMN analytics.campaigns.campaign_name IS '营销活动名称';
COMMENT ON COLUMN analytics.campaigns.campaign_type IS '活动类型：平台、品类、拉新或留存';
COMMENT ON COLUMN analytics.campaigns.starts_at IS '活动开始时间，含该时刻';
COMMENT ON COLUMN analytics.campaigns.ends_at IS '活动结束时间，不含该时刻';
COMMENT ON COLUMN analytics.campaigns.discount_rate IS '活动商品折扣率';
COMMENT ON COLUMN analytics.campaigns.budget IS '活动预算金额，币种为人民币';

COMMENT ON TABLE analytics.warehouses IS '履约仓库维表';
COMMENT ON COLUMN analytics.warehouses.warehouse_id IS '仓库主键';
COMMENT ON COLUMN analytics.warehouses.warehouse_name IS '仓库名称';
COMMENT ON COLUMN analytics.warehouses.city IS '仓库所在城市';
COMMENT ON COLUMN analytics.warehouses.region IS '仓库所属大区';

COMMENT ON TABLE analytics.suppliers IS '供应商维表';
COMMENT ON COLUMN analytics.suppliers.supplier_id IS '供应商主键';
COMMENT ON COLUMN analytics.suppliers.supplier_name IS '供应商名称';
COMMENT ON COLUMN analytics.suppliers.region IS '供应商所在大区';
COMMENT ON COLUMN analytics.suppliers.lead_time_days IS '标准供货提前期天数';

COMMENT ON TABLE analytics.fiscal_calendar IS '按七月开始的财务日历维表';
COMMENT ON COLUMN analytics.fiscal_calendar.calendar_date IS '自然日期主键';
COMMENT ON COLUMN analytics.fiscal_calendar.fiscal_year IS '财年结束年份，例如 2025 财年从 2024 年 7 月开始';
COMMENT ON COLUMN analytics.fiscal_calendar.fiscal_month IS '财年月份，七月为第 1 月';
COMMENT ON COLUMN analytics.fiscal_calendar.is_month_end IS '是否为自然月最后一天';

COMMENT ON TABLE analytics.customers IS '客户主数据表';
COMMENT ON COLUMN analytics.customers.customer_id IS '客户主键';
COMMENT ON COLUMN analytics.customers.customer_name IS '客户显示名称';
COMMENT ON COLUMN analytics.customers.city IS '客户所在城市';
COMMENT ON COLUMN analytics.customers.region IS '客户所属大区';
COMMENT ON COLUMN analytics.customers.signup_at IS '客户注册时间';
COMMENT ON COLUMN analytics.customers.acquired_channel_id IS '首次获客渠道主键';
COMMENT ON COLUMN analytics.customers.customer_segment IS '客户分群：大众、成长或高价值';

COMMENT ON TABLE analytics.customer_memberships IS '客户会员等级生效历史表';
COMMENT ON COLUMN analytics.customer_memberships.membership_id IS '会员历史记录主键';
COMMENT ON COLUMN analytics.customer_memberships.customer_id IS '客户主键';
COMMENT ON COLUMN analytics.customer_memberships.tier_code IS '该有效期内的会员等级编码';
COMMENT ON COLUMN analytics.customer_memberships.valid_from IS '会员等级生效时间，含该时刻';
COMMENT ON COLUMN analytics.customer_memberships.valid_to IS '会员等级失效时间，不含该时刻，空值表示当前有效';
COMMENT ON COLUMN analytics.customer_memberships.change_reason IS '会员等级变更原因';

COMMENT ON TABLE analytics.products IS '商品主数据与成本标价表';
COMMENT ON COLUMN analytics.products.product_id IS '商品主键';
COMMENT ON COLUMN analytics.products.product_name IS '商品名称';
COMMENT ON COLUMN analytics.products.category IS '一级分类名称的冗余快照';
COMMENT ON COLUMN analytics.products.list_price IS '商品当前标价';
COMMENT ON COLUMN analytics.products.category_id IS '商品所属二级分类主键';
COMMENT ON COLUMN analytics.products.brand IS '商品品牌';
COMMENT ON COLUMN analytics.products.standard_cost IS '商品标准单位成本';
COMMENT ON COLUMN analytics.products.is_active IS '商品当前是否在售';

COMMENT ON TABLE analytics.product_suppliers IS '商品与供应商关系及采购价格表';
COMMENT ON COLUMN analytics.product_suppliers.product_id IS '商品主键';
COMMENT ON COLUMN analytics.product_suppliers.supplier_id IS '供应商主键';
COMMENT ON COLUMN analytics.product_suppliers.purchase_price IS '该供应商的商品采购单价';
COMMENT ON COLUMN analytics.product_suppliers.is_primary IS '是否为该商品的主供应商';

COMMENT ON TABLE analytics.orders IS '订单头事实表';
COMMENT ON COLUMN analytics.orders.order_id IS '订单主键';
COMMENT ON COLUMN analytics.orders.customer_id IS '下单客户主键';
COMMENT ON COLUMN analytics.orders.ordered_at IS '下单时间';
COMMENT ON COLUMN analytics.orders.status IS '订单状态：已支付、已发货、已完成或已取消';
COMMENT ON COLUMN analytics.orders.channel_id IS '成交渠道主键';
COMMENT ON COLUMN analytics.orders.membership_tier_code IS '下单时会员等级快照';
COMMENT ON COLUMN analytics.orders.shipping_fee IS '订单向客户收取的运费';
COMMENT ON COLUMN analytics.orders.currency IS '订单币种编码';

COMMENT ON TABLE analytics.order_items IS '订单商品明细事实表';
COMMENT ON COLUMN analytics.order_items.item_id IS '订单明细主键';
COMMENT ON COLUMN analytics.order_items.order_id IS '订单主键';
COMMENT ON COLUMN analytics.order_items.product_id IS '商品主键';
COMMENT ON COLUMN analytics.order_items.quantity IS '购买数量';
COMMENT ON COLUMN analytics.order_items.unit_price IS '活动及会员优惠后的成交单价';
COMMENT ON COLUMN analytics.order_items.list_unit_price IS '下单时商品标价快照';
COMMENT ON COLUMN analytics.order_items.campaign_discount_amount IS '该明细由营销活动产生的优惠金额';
COMMENT ON COLUMN analytics.order_items.membership_discount_amount IS '该明细由会员权益产生的优惠金额';
COMMENT ON COLUMN analytics.order_items.cost_unit_price IS '下单时商品标准单位成本快照';

COMMENT ON TABLE analytics.order_promotions IS '订单参与活动及分摊优惠关系表';
COMMENT ON COLUMN analytics.order_promotions.order_id IS '订单主键';
COMMENT ON COLUMN analytics.order_promotions.campaign_id IS '营销活动主键';
COMMENT ON COLUMN analytics.order_promotions.allocated_discount_amount IS '分摊到该订单的活动优惠金额';

COMMENT ON TABLE analytics.payments IS '订单支付尝试事实表，一单可有多次尝试或拆分支付';
COMMENT ON COLUMN analytics.payments.payment_id IS '支付记录主键';
COMMENT ON COLUMN analytics.payments.order_id IS '订单主键';
COMMENT ON COLUMN analytics.payments.amount IS '本次支付尝试金额';
COMMENT ON COLUMN analytics.payments.paid_at IS '支付成功时间，失败记录为空';
COMMENT ON COLUMN analytics.payments.status IS '支付状态：成功或失败';
COMMENT ON COLUMN analytics.payments.attempt_no IS '订单内支付尝试序号';
COMMENT ON COLUMN analytics.payments.attempted_at IS '支付尝试发起时间';
COMMENT ON COLUMN analytics.payments.payment_method IS '支付方式';

COMMENT ON TABLE analytics.refunds IS '订单退款申请事实表';
COMMENT ON COLUMN analytics.refunds.refund_id IS '退款申请主键';
COMMENT ON COLUMN analytics.refunds.order_id IS '订单主键';
COMMENT ON COLUMN analytics.refunds.amount IS '申请退款金额';
COMMENT ON COLUMN analytics.refunds.refunded_at IS '实际退款完成时间，未批准时为空';
COMMENT ON COLUMN analytics.refunds.status IS '退款状态：已批准、已拒绝或待处理';
COMMENT ON COLUMN analytics.refunds.requested_at IS '退款申请时间';
COMMENT ON COLUMN analytics.refunds.reason IS '退款原因';

COMMENT ON TABLE analytics.refund_items IS '退款申请对应的订单明细表';
COMMENT ON COLUMN analytics.refund_items.refund_item_id IS '退款明细主键';
COMMENT ON COLUMN analytics.refund_items.refund_id IS '退款申请主键';
COMMENT ON COLUMN analytics.refund_items.item_id IS '原订单明细主键';
COMMENT ON COLUMN analytics.refund_items.quantity IS '申请退款数量';
COMMENT ON COLUMN analytics.refund_items.amount IS '该退款明细金额';

COMMENT ON TABLE analytics.shipments IS '订单包裹履约事实表，一单可拆为多个包裹';
COMMENT ON COLUMN analytics.shipments.shipment_id IS '包裹主键';
COMMENT ON COLUMN analytics.shipments.order_id IS '订单主键';
COMMENT ON COLUMN analytics.shipments.warehouse_id IS '发货仓库主键';
COMMENT ON COLUMN analytics.shipments.shipment_no IS '订单内包裹序号';
COMMENT ON COLUMN analytics.shipments.carrier IS '承运商名称';
COMMENT ON COLUMN analytics.shipments.status IS '包裹状态：待发货、运输中、已送达或丢失';
COMMENT ON COLUMN analytics.shipments.shipped_at IS '实际发货时间';
COMMENT ON COLUMN analytics.shipments.promised_delivery_at IS '承诺送达时间';
COMMENT ON COLUMN analytics.shipments.delivered_at IS '实际送达时间';
COMMENT ON COLUMN analytics.shipments.freight_amount IS '分摊到该包裹的客户运费';

COMMENT ON TABLE analytics.inventory_snapshots IS '商品仓库月末库存快照事实表';
COMMENT ON COLUMN analytics.inventory_snapshots.snapshot_date IS '库存快照日期';
COMMENT ON COLUMN analytics.inventory_snapshots.product_id IS '商品主键';
COMMENT ON COLUMN analytics.inventory_snapshots.warehouse_id IS '仓库主键';
COMMENT ON COLUMN analytics.inventory_snapshots.on_hand_qty IS '快照时点可用库存数量';
COMMENT ON COLUMN analytics.inventory_snapshots.unit_cost IS '快照时点单位库存成本';

COMMENT ON TABLE analytics.product_reviews IS '已完成订单的商品评分事实表';
COMMENT ON COLUMN analytics.product_reviews.review_id IS '商品评价主键';
COMMENT ON COLUMN analytics.product_reviews.order_id IS '评价来源订单主键';
COMMENT ON COLUMN analytics.product_reviews.product_id IS '被评价商品主键';
COMMENT ON COLUMN analytics.product_reviews.rating IS '整数评分，范围 1 至 5';
COMMENT ON COLUMN analytics.product_reviews.created_at IS '评价创建时间';

COMMENT ON TABLE analytics.web_sessions IS '站点和应用访问会话事实表';
COMMENT ON COLUMN analytics.web_sessions.session_id IS '访问会话主键';
COMMENT ON COLUMN analytics.web_sessions.customer_id IS '已识别客户主键，匿名会话为空';
COMMENT ON COLUMN analytics.web_sessions.channel_id IS '访问渠道主键';
COMMENT ON COLUMN analytics.web_sessions.campaign_id IS '归因营销活动主键';
COMMENT ON COLUMN analytics.web_sessions.session_started_at IS '会话开始时间';
COMMENT ON COLUMN analytics.web_sessions.traffic_source IS '流量来源';
COMMENT ON COLUMN analytics.web_sessions.converted_order_id IS '该会话转化的订单主键，未转化为空';

COMMENT ON TABLE analytics.campaign_spend_daily IS '营销活动按日按渠道投放事实表';
COMMENT ON COLUMN analytics.campaign_spend_daily.spend_date IS '投放自然日期';
COMMENT ON COLUMN analytics.campaign_spend_daily.campaign_id IS '营销活动主键';
COMMENT ON COLUMN analytics.campaign_spend_daily.channel_id IS '投放渠道主键';
COMMENT ON COLUMN analytics.campaign_spend_daily.spend_amount IS '当日渠道投放金额';
COMMENT ON COLUMN analytics.campaign_spend_daily.impressions IS '当日广告曝光次数';
COMMENT ON COLUMN analytics.campaign_spend_daily.clicks IS '当日广告点击次数';

COMMENT ON TABLE analytics.demo_seed_state IS '确定性演示数据版本状态表';
COMMENT ON COLUMN analytics.demo_seed_state.state_id IS '固定为 1 的单行主键';
COMMENT ON COLUMN analytics.demo_seed_state.seed_version IS '当前演示数据生成器版本';
COMMENT ON COLUMN analytics.demo_seed_state.seeded_at IS '最近一次完成数据装载的时间';

-- Compatibility objects retained until their historical rows are explicitly
-- approved for deletion. They are deliberately excluded from the NL2SQL catalog.
DO $$ BEGIN
  IF to_regclass('analytics.channels') IS NOT NULL THEN
    COMMENT ON TABLE analytics.channels IS '已弃用的旧渠道维表；新查询请使用 sales_channels';
    COMMENT ON COLUMN analytics.channels.channel_id IS '旧渠道主键';
    COMMENT ON COLUMN analytics.channels.channel_name IS '旧渠道名称';
    COMMENT ON COLUMN analytics.channels.channel_type IS '旧渠道类型';
    COMMENT ON COLUMN analytics.channels.is_active IS '旧渠道是否启用';
  END IF;
  IF to_regclass('analytics.customer_tiers') IS NOT NULL THEN
    COMMENT ON TABLE analytics.customer_tiers IS '已弃用的旧会员历史表；新查询请使用 customer_memberships';
    COMMENT ON COLUMN analytics.customer_tiers.customer_id IS '客户主键';
    COMMENT ON COLUMN analytics.customer_tiers.tier IS '旧会员等级名称';
    COMMENT ON COLUMN analytics.customer_tiers.effective_from IS '旧等级生效时间';
    COMMENT ON COLUMN analytics.customer_tiers.effective_to IS '旧等级失效时间';
  END IF;
  IF to_regclass('analytics.order_discounts') IS NOT NULL THEN
    COMMENT ON TABLE analytics.order_discounts IS '已弃用的旧优惠表；新查询请使用订单明细优惠字段与 order_promotions';
    COMMENT ON COLUMN analytics.order_discounts.discount_id IS '旧优惠记录主键';
    COMMENT ON COLUMN analytics.order_discounts.order_id IS '订单主键';
    COMMENT ON COLUMN analytics.order_discounts.campaign_id IS '营销活动主键';
    COMMENT ON COLUMN analytics.order_discounts.discount_type IS '旧优惠类型';
    COMMENT ON COLUMN analytics.order_discounts.amount IS '旧优惠金额';
  END IF;
  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='analytics' AND table_name='product_categories' AND column_name='parent_id') THEN
    COMMENT ON COLUMN analytics.product_categories.parent_id IS '已弃用的父分类字段；请使用 parent_category_id';
  END IF;
  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='analytics' AND table_name='product_categories' AND column_name='level') THEN
    COMMENT ON COLUMN analytics.product_categories.level IS '已弃用的分类层级字段；请使用 category_level';
  END IF;
  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='analytics' AND table_name='payments' AND column_name='method') THEN
    COMMENT ON COLUMN analytics.payments.method IS '已弃用的支付方式字段；请使用 payment_method';
  END IF;
END $$;

COMMENT ON TABLE rag.documents IS '供检索增强生成使用的知识文档向量表';
COMMENT ON COLUMN rag.documents.doc_id IS '稳定的知识文档主键';
COMMENT ON COLUMN rag.documents.kind IS '文档类型，例如表、指标、连接、规则或示例';
COMMENT ON COLUMN rag.documents.object_ref IS '文档描述的业务对象引用';
COMMENT ON COLUMN rag.documents.content IS '供检索与提示词使用的知识正文';
COMMENT ON COLUMN rag.documents.aliases IS '用户可能使用的同义词和别名';
COMMENT ON COLUMN rag.documents.related_tables IS '文档涉及的分析表名数组';
COMMENT ON COLUMN rag.documents.source_version IS '生成该记录的知识目录版本';
COMMENT ON COLUMN rag.documents.content_hash IS '用于增量索引的规范化内容哈希';
COMMENT ON COLUMN rag.documents.embed_model IS '生成向量时使用的嵌入模型';
COMMENT ON COLUMN rag.documents.embedding IS '1024 维语义检索向量';
COMMENT ON COLUMN rag.documents.updated_at IS '知识记录最近更新时间';
COMMENT ON COLUMN rag.documents.metadata IS '结构化检索与排序元数据';
COMMENT ON COLUMN rag.documents.priority IS '检索排序优先级，数值越大越优先';
