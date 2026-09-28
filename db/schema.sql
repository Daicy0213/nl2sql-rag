CREATE EXTENSION IF NOT EXISTS vector;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS rag;

CREATE TABLE IF NOT EXISTS analytics.customers (
  customer_id integer PRIMARY KEY,
  customer_name text NOT NULL,
  city text NOT NULL,
  region text NOT NULL,
  signup_at timestamptz NOT NULL
);
CREATE TABLE IF NOT EXISTS analytics.products (
  product_id integer PRIMARY KEY,
  product_name text NOT NULL,
  category text NOT NULL,
  list_price numeric(12,2) NOT NULL CHECK (list_price >= 0)
);
CREATE TABLE IF NOT EXISTS analytics.orders (
  order_id integer PRIMARY KEY,
  customer_id integer NOT NULL REFERENCES analytics.customers(customer_id),
  ordered_at timestamptz NOT NULL,
  status text NOT NULL CHECK (status IN ('PAID','SHIPPED','COMPLETED','CANCELLED'))
);
CREATE TABLE IF NOT EXISTS analytics.order_items (
  item_id integer PRIMARY KEY,
  order_id integer NOT NULL REFERENCES analytics.orders(order_id),
  product_id integer NOT NULL REFERENCES analytics.products(product_id),
  quantity integer NOT NULL CHECK (quantity > 0),
  unit_price numeric(12,2) NOT NULL CHECK (unit_price >= 0)
);
CREATE TABLE IF NOT EXISTS analytics.payments (
  payment_id integer PRIMARY KEY,
  order_id integer NOT NULL UNIQUE REFERENCES analytics.orders(order_id),
  amount numeric(12,2) NOT NULL CHECK (amount >= 0),
  paid_at timestamptz NOT NULL,
  status text NOT NULL CHECK (status IN ('SUCCEEDED','FAILED'))
);
CREATE TABLE IF NOT EXISTS analytics.refunds (
  refund_id integer PRIMARY KEY,
  order_id integer NOT NULL REFERENCES analytics.orders(order_id),
  amount numeric(12,2) NOT NULL CHECK (amount >= 0),
  refunded_at timestamptz NOT NULL,
  status text NOT NULL CHECK (status IN ('APPROVED','REJECTED'))
);
CREATE INDEX IF NOT EXISTS orders_ordered_at_idx ON analytics.orders(ordered_at);
CREATE INDEX IF NOT EXISTS orders_customer_id_idx ON analytics.orders(customer_id);
CREATE INDEX IF NOT EXISTS order_items_order_id_idx ON analytics.order_items(order_id);
CREATE INDEX IF NOT EXISTS payments_paid_at_idx ON analytics.payments(paid_at);
CREATE INDEX IF NOT EXISTS refunds_order_id_idx ON analytics.refunds(order_id);

CREATE TABLE IF NOT EXISTS rag.documents (
  doc_id text PRIMARY KEY,
  kind text NOT NULL,
  object_ref text NOT NULL,
  content text NOT NULL,
  aliases text[] NOT NULL DEFAULT '{}',
  related_tables text[] NOT NULL DEFAULT '{}',
  source_version text NOT NULL,
  content_hash text NOT NULL,
  embed_model text NOT NULL,
  embedding vector(1024) NOT NULL,
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS rag_documents_hnsw_idx
  ON rag.documents USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS rag_documents_aliases_idx
  ON rag.documents USING gin (aliases);

-- Expanded business domains ---------------------------------------------------

CREATE TABLE IF NOT EXISTS analytics.sales_channels (
  channel_id integer PRIMARY KEY,
  channel_code text NOT NULL UNIQUE,
  channel_name text NOT NULL,
  channel_group text NOT NULL CHECK (channel_group IN ('ONLINE','OFFLINE'))
);

CREATE TABLE IF NOT EXISTS analytics.membership_tiers (
  tier_code text PRIMARY KEY,
  tier_name text NOT NULL UNIQUE,
  min_annual_spend numeric(12,2) NOT NULL CHECK (min_annual_spend >= 0),
  discount_rate numeric(5,4) NOT NULL CHECK (discount_rate >= 0 AND discount_rate < 1),
  points_multiplier numeric(5,2) NOT NULL CHECK (points_multiplier >= 1),
  tier_rank integer NOT NULL UNIQUE CHECK (tier_rank >= 0)
);

CREATE TABLE IF NOT EXISTS analytics.product_categories (
  category_id integer PRIMARY KEY,
  category_name text NOT NULL UNIQUE,
  parent_category_id integer REFERENCES analytics.product_categories(category_id),
  category_level integer NOT NULL CHECK (category_level IN (1,2))
);

CREATE TABLE IF NOT EXISTS analytics.campaigns (
  campaign_id integer PRIMARY KEY,
  campaign_name text NOT NULL,
  campaign_type text NOT NULL CHECK (campaign_type IN ('PLATFORM','CATEGORY','ACQUISITION','RETENTION')),
  starts_at timestamptz NOT NULL,
  ends_at timestamptz NOT NULL,
  discount_rate numeric(5,4) NOT NULL CHECK (discount_rate >= 0 AND discount_rate < 1),
  CHECK (ends_at > starts_at)
);

-- Normalize older experimental versions of these tables without dropping
-- their extra columns. New canonical columns are used by this repository.
ALTER TABLE analytics.product_categories ADD COLUMN IF NOT EXISTS parent_category_id integer REFERENCES analytics.product_categories(category_id);
ALTER TABLE analytics.product_categories ADD COLUMN IF NOT EXISTS category_level integer;
DO $$ BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='analytics' AND table_name='product_categories' AND column_name='level'
  ) THEN
    UPDATE analytics.product_categories SET category_level=COALESCE(category_level, level) WHERE category_level IS NULL;
  ELSE
    UPDATE analytics.product_categories SET category_level=1 WHERE category_level IS NULL;
  END IF;
END $$;
ALTER TABLE analytics.product_categories ALTER COLUMN category_level SET NOT NULL;
ALTER TABLE analytics.product_categories ALTER COLUMN category_level SET DEFAULT 1;
DO $$ BEGIN
  ALTER TABLE analytics.product_categories ALTER COLUMN level SET DEFAULT 1;
EXCEPTION WHEN undefined_column THEN NULL; END $$;

ALTER TABLE analytics.campaigns ADD COLUMN IF NOT EXISTS discount_rate numeric(5,4) NOT NULL DEFAULT 0;
DO $$ BEGIN
  ALTER TABLE analytics.campaigns ALTER COLUMN budget SET DEFAULT 0;
EXCEPTION WHEN undefined_column THEN NULL; END $$;
ALTER TABLE analytics.campaigns DROP CONSTRAINT IF EXISTS campaigns_campaign_type_check;
ALTER TABLE analytics.campaigns DROP CONSTRAINT IF EXISTS campaigns_campaign_type_v2_check;
ALTER TABLE analytics.campaigns ADD CONSTRAINT campaigns_campaign_type_v2_check
  CHECK (campaign_type IN ('PLATFORM','CATEGORY','ACQUISITION','RETENTION')) NOT VALID;

-- ALTER statements make this schema usable against an existing demo volume.
ALTER TABLE analytics.customers ADD COLUMN IF NOT EXISTS acquired_channel_id integer REFERENCES analytics.sales_channels(channel_id);
ALTER TABLE analytics.customers ADD COLUMN IF NOT EXISTS customer_segment text NOT NULL DEFAULT 'MASS';
ALTER TABLE analytics.products ADD COLUMN IF NOT EXISTS category_id integer REFERENCES analytics.product_categories(category_id);
ALTER TABLE analytics.products ADD COLUMN IF NOT EXISTS brand text NOT NULL DEFAULT '自有品牌';
ALTER TABLE analytics.products ADD COLUMN IF NOT EXISTS standard_cost numeric(12,2) NOT NULL DEFAULT 0;
ALTER TABLE analytics.products ADD COLUMN IF NOT EXISTS is_active boolean NOT NULL DEFAULT true;
ALTER TABLE analytics.orders ADD COLUMN IF NOT EXISTS channel_id integer REFERENCES analytics.sales_channels(channel_id);
ALTER TABLE analytics.orders ADD COLUMN IF NOT EXISTS membership_tier_code text REFERENCES analytics.membership_tiers(tier_code);
ALTER TABLE analytics.orders ADD COLUMN IF NOT EXISTS shipping_fee numeric(12,2) NOT NULL DEFAULT 0;
ALTER TABLE analytics.orders ADD COLUMN IF NOT EXISTS currency text NOT NULL DEFAULT 'CNY';
ALTER TABLE analytics.order_items ADD COLUMN IF NOT EXISTS list_unit_price numeric(12,2);
UPDATE analytics.order_items SET list_unit_price=unit_price WHERE list_unit_price IS NULL;
ALTER TABLE analytics.order_items ALTER COLUMN list_unit_price SET NOT NULL;
ALTER TABLE analytics.order_items ADD COLUMN IF NOT EXISTS campaign_discount_amount numeric(12,2) NOT NULL DEFAULT 0;
ALTER TABLE analytics.order_items ADD COLUMN IF NOT EXISTS membership_discount_amount numeric(12,2) NOT NULL DEFAULT 0;
ALTER TABLE analytics.order_items ADD COLUMN IF NOT EXISTS cost_unit_price numeric(12,2) NOT NULL DEFAULT 0;

CREATE TABLE IF NOT EXISTS analytics.customer_memberships (
  membership_id integer PRIMARY KEY,
  customer_id integer NOT NULL REFERENCES analytics.customers(customer_id),
  tier_code text NOT NULL REFERENCES analytics.membership_tiers(tier_code),
  valid_from timestamptz NOT NULL,
  valid_to timestamptz,
  change_reason text NOT NULL,
  CHECK (valid_to IS NULL OR valid_to > valid_from),
  UNIQUE (customer_id, valid_from)
);

CREATE TABLE IF NOT EXISTS analytics.order_promotions (
  order_id integer NOT NULL REFERENCES analytics.orders(order_id),
  campaign_id integer NOT NULL REFERENCES analytics.campaigns(campaign_id),
  allocated_discount_amount numeric(12,2) NOT NULL CHECK (allocated_discount_amount >= 0),
  PRIMARY KEY (order_id, campaign_id)
);

ALTER TABLE analytics.payments DROP CONSTRAINT IF EXISTS payments_order_id_key;
ALTER TABLE analytics.payments DROP CONSTRAINT IF EXISTS payments_status_check;
ALTER TABLE analytics.payments ALTER COLUMN paid_at DROP NOT NULL;
ALTER TABLE analytics.payments ADD COLUMN IF NOT EXISTS attempt_no integer NOT NULL DEFAULT 1;
ALTER TABLE analytics.payments ADD COLUMN IF NOT EXISTS attempted_at timestamptz;
UPDATE analytics.payments SET attempted_at=COALESCE(paid_at, now()) WHERE attempted_at IS NULL;
ALTER TABLE analytics.payments ALTER COLUMN attempted_at SET NOT NULL;
ALTER TABLE analytics.payments ADD COLUMN IF NOT EXISTS payment_method text NOT NULL DEFAULT 'ALIPAY';
DO $$ BEGIN
  ALTER TABLE analytics.payments ADD CONSTRAINT payments_status_check CHECK (status IN ('SUCCEEDED','FAILED'));
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
ALTER TABLE analytics.payments DROP CONSTRAINT IF EXISTS payments_order_attempt_key;
ALTER TABLE analytics.payments ADD CONSTRAINT payments_order_attempt_key UNIQUE (order_id, attempt_no);

ALTER TABLE analytics.refunds DROP CONSTRAINT IF EXISTS refunds_status_check;
ALTER TABLE analytics.refunds ALTER COLUMN refunded_at DROP NOT NULL;
ALTER TABLE analytics.refunds ADD COLUMN IF NOT EXISTS requested_at timestamptz;
UPDATE analytics.refunds SET requested_at=COALESCE(refunded_at, now()) WHERE requested_at IS NULL;
ALTER TABLE analytics.refunds ALTER COLUMN requested_at SET NOT NULL;
ALTER TABLE analytics.refunds ADD COLUMN IF NOT EXISTS reason text NOT NULL DEFAULT 'OTHER';
DO $$ BEGIN
  ALTER TABLE analytics.refunds ADD CONSTRAINT refunds_status_check CHECK (status IN ('APPROVED','REJECTED','PENDING'));
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS analytics.refund_items (
  refund_item_id integer PRIMARY KEY,
  refund_id integer NOT NULL REFERENCES analytics.refunds(refund_id),
  item_id integer NOT NULL REFERENCES analytics.order_items(item_id),
  quantity integer NOT NULL CHECK (quantity > 0),
  amount numeric(12,2) NOT NULL CHECK (amount >= 0),
  UNIQUE (refund_id, item_id)
);

CREATE TABLE IF NOT EXISTS analytics.shipments (
  shipment_id integer PRIMARY KEY,
  order_id integer NOT NULL REFERENCES analytics.orders(order_id),
  shipment_no integer NOT NULL,
  carrier text NOT NULL,
  status text NOT NULL CHECK (status IN ('PENDING','SHIPPED','DELIVERED','LOST')),
  shipped_at timestamptz,
  promised_delivery_at timestamptz,
  delivered_at timestamptz,
  UNIQUE (order_id, shipment_no)
);

ALTER TABLE analytics.shipments ADD COLUMN IF NOT EXISTS shipment_no integer NOT NULL DEFAULT 1;
ALTER TABLE analytics.shipments ADD COLUMN IF NOT EXISTS promised_delivery_at timestamptz;
ALTER TABLE analytics.shipments ALTER COLUMN shipped_at DROP NOT NULL;
DO $$ BEGIN
  ALTER TABLE analytics.shipments ALTER COLUMN warehouse_id DROP NOT NULL;
  ALTER TABLE analytics.shipments ALTER COLUMN freight_amount SET DEFAULT 0;
EXCEPTION WHEN undefined_column THEN NULL; END $$;
ALTER TABLE analytics.shipments DROP CONSTRAINT IF EXISTS shipments_status_check;
ALTER TABLE analytics.shipments DROP CONSTRAINT IF EXISTS shipments_status_v2_check;
ALTER TABLE analytics.shipments ADD CONSTRAINT shipments_status_v2_check
  CHECK (status IN ('PENDING','SHIPPED','DELIVERED','LOST')) NOT VALID;
ALTER TABLE analytics.shipments DROP CONSTRAINT IF EXISTS shipments_order_no_key;
ALTER TABLE analytics.shipments ADD CONSTRAINT shipments_order_no_key UNIQUE (order_id, shipment_no);

CREATE TABLE IF NOT EXISTS analytics.web_sessions (
  session_id bigint PRIMARY KEY,
  customer_id integer REFERENCES analytics.customers(customer_id),
  channel_id integer NOT NULL REFERENCES analytics.sales_channels(channel_id),
  campaign_id integer REFERENCES analytics.campaigns(campaign_id),
  session_started_at timestamptz NOT NULL,
  traffic_source text NOT NULL,
  converted_order_id integer REFERENCES analytics.orders(order_id)
);

CREATE TABLE IF NOT EXISTS analytics.campaign_spend_daily (
  spend_date date NOT NULL,
  campaign_id integer NOT NULL REFERENCES analytics.campaigns(campaign_id),
  channel_id integer NOT NULL REFERENCES analytics.sales_channels(channel_id),
  spend_amount numeric(12,2) NOT NULL CHECK (spend_amount >= 0),
  impressions integer NOT NULL CHECK (impressions >= 0),
  clicks integer NOT NULL CHECK (clicks >= 0),
  PRIMARY KEY (spend_date, campaign_id, channel_id)
);

CREATE TABLE IF NOT EXISTS analytics.demo_seed_state (
  state_id integer PRIMARY KEY CHECK (state_id = 1),
  seed_version text NOT NULL,
  seeded_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS orders_channel_id_idx ON analytics.orders(channel_id);
CREATE INDEX IF NOT EXISTS orders_membership_tier_idx ON analytics.orders(membership_tier_code);
CREATE INDEX IF NOT EXISTS customer_memberships_effective_idx
  ON analytics.customer_memberships(customer_id, valid_from, valid_to);
CREATE INDEX IF NOT EXISTS order_items_product_id_idx ON analytics.order_items(product_id);
CREATE INDEX IF NOT EXISTS payments_order_id_idx ON analytics.payments(order_id);
CREATE INDEX IF NOT EXISTS refunds_refunded_at_idx ON analytics.refunds(refunded_at);
CREATE INDEX IF NOT EXISTS shipments_order_id_idx ON analytics.shipments(order_id);
CREATE INDEX IF NOT EXISTS web_sessions_started_at_idx ON analytics.web_sessions(session_started_at);
CREATE INDEX IF NOT EXISTS web_sessions_campaign_idx ON analytics.web_sessions(campaign_id);

ALTER TABLE rag.documents ADD COLUMN IF NOT EXISTS metadata jsonb NOT NULL DEFAULT '{}';
ALTER TABLE rag.documents ADD COLUMN IF NOT EXISTS priority integer NOT NULL DEFAULT 50;
CREATE INDEX IF NOT EXISTS rag_documents_kind_idx ON rag.documents(kind);
