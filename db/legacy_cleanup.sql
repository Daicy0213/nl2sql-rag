-- Apply only after backing up an upgraded v1 database. These objects are not
-- created by schema.sql and are superseded by the canonical v3 model.
DROP TABLE IF EXISTS analytics.order_discounts;
DROP TABLE IF EXISTS analytics.customer_tiers;
DROP TABLE IF EXISTS analytics.channels;

ALTER TABLE analytics.product_categories DROP COLUMN IF EXISTS parent_id;
ALTER TABLE analytics.product_categories DROP COLUMN IF EXISTS level;
ALTER TABLE analytics.payments DROP COLUMN IF EXISTS method;
