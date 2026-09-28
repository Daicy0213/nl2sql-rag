--
-- PostgreSQL database dump
--

\restrict PYFodp9B8ueK1LmBvrbmNtrEmTPzr309Ad1XJlgdUhC2x8Wxk6PcYy0agKFfBKg

-- Dumped from database version 17.11 (Debian 17.11-1.pgdg12+2)
-- Dumped by pg_dump version 17.11 (Debian 17.11-1.pgdg12+2)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: channels; Type: TABLE; Schema: analytics; Owner: -
--

CREATE TABLE analytics.channels (
    channel_id integer NOT NULL,
    channel_name text NOT NULL,
    channel_type text NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    CONSTRAINT channels_channel_type_check CHECK ((channel_type = ANY (ARRAY['线上'::text, '线下'::text])))
);


--
-- Name: TABLE channels; Type: COMMENT; Schema: analytics; Owner: -
--

COMMENT ON TABLE analytics.channels IS '已弃用的旧渠道维表；新查询请使用 sales_channels';


--
-- Name: COLUMN channels.channel_id; Type: COMMENT; Schema: analytics; Owner: -
--

COMMENT ON COLUMN analytics.channels.channel_id IS '旧渠道主键';


--
-- Name: COLUMN channels.channel_name; Type: COMMENT; Schema: analytics; Owner: -
--

COMMENT ON COLUMN analytics.channels.channel_name IS '旧渠道名称';


--
-- Name: COLUMN channels.channel_type; Type: COMMENT; Schema: analytics; Owner: -
--

COMMENT ON COLUMN analytics.channels.channel_type IS '旧渠道类型';


--
-- Name: COLUMN channels.is_active; Type: COMMENT; Schema: analytics; Owner: -
--

COMMENT ON COLUMN analytics.channels.is_active IS '旧渠道是否启用';


--
-- Name: customer_tiers; Type: TABLE; Schema: analytics; Owner: -
--

CREATE TABLE analytics.customer_tiers (
    customer_id integer NOT NULL,
    tier text NOT NULL,
    effective_from timestamp with time zone NOT NULL,
    effective_to timestamp with time zone,
    CONSTRAINT customer_tiers_tier_check CHECK ((tier = ANY (ARRAY['普通'::text, '银卡'::text, '金卡'::text, '钻石'::text])))
);


--
-- Name: TABLE customer_tiers; Type: COMMENT; Schema: analytics; Owner: -
--

COMMENT ON TABLE analytics.customer_tiers IS '已弃用的旧会员历史表；新查询请使用 customer_memberships';


--
-- Name: COLUMN customer_tiers.customer_id; Type: COMMENT; Schema: analytics; Owner: -
--

COMMENT ON COLUMN analytics.customer_tiers.customer_id IS '客户主键';


--
-- Name: COLUMN customer_tiers.tier; Type: COMMENT; Schema: analytics; Owner: -
--

COMMENT ON COLUMN analytics.customer_tiers.tier IS '旧会员等级名称';


--
-- Name: COLUMN customer_tiers.effective_from; Type: COMMENT; Schema: analytics; Owner: -
--

COMMENT ON COLUMN analytics.customer_tiers.effective_from IS '旧等级生效时间';


--
-- Name: COLUMN customer_tiers.effective_to; Type: COMMENT; Schema: analytics; Owner: -
--

COMMENT ON COLUMN analytics.customer_tiers.effective_to IS '旧等级失效时间';


--
-- Name: order_discounts; Type: TABLE; Schema: analytics; Owner: -
--

CREATE TABLE analytics.order_discounts (
    discount_id integer NOT NULL,
    order_id integer NOT NULL,
    campaign_id integer,
    discount_type text NOT NULL,
    amount numeric(12,2) NOT NULL,
    CONSTRAINT order_discounts_amount_check CHECK ((amount > (0)::numeric)),
    CONSTRAINT order_discounts_discount_type_check CHECK ((discount_type = ANY (ARRAY['折扣'::text, '优惠券'::text, '满减'::text])))
);


--
-- Name: TABLE order_discounts; Type: COMMENT; Schema: analytics; Owner: -
--

COMMENT ON TABLE analytics.order_discounts IS '已弃用的旧优惠表；新查询请使用订单明细优惠字段与 order_promotions';


--
-- Name: COLUMN order_discounts.discount_id; Type: COMMENT; Schema: analytics; Owner: -
--

COMMENT ON COLUMN analytics.order_discounts.discount_id IS '旧优惠记录主键';


--
-- Name: COLUMN order_discounts.order_id; Type: COMMENT; Schema: analytics; Owner: -
--

COMMENT ON COLUMN analytics.order_discounts.order_id IS '订单主键';


--
-- Name: COLUMN order_discounts.campaign_id; Type: COMMENT; Schema: analytics; Owner: -
--

COMMENT ON COLUMN analytics.order_discounts.campaign_id IS '营销活动主键';


--
-- Name: COLUMN order_discounts.discount_type; Type: COMMENT; Schema: analytics; Owner: -
--

COMMENT ON COLUMN analytics.order_discounts.discount_type IS '旧优惠类型';


--
-- Name: COLUMN order_discounts.amount; Type: COMMENT; Schema: analytics; Owner: -
--

COMMENT ON COLUMN analytics.order_discounts.amount IS '旧优惠金额';


--
-- Data for Name: channels; Type: TABLE DATA; Schema: analytics; Owner: -
--

COPY analytics.channels (channel_id, channel_name, channel_type, is_active) FROM stdin;
1	天猫	线上	t
2	京东	线上	t
3	抖音	线上	t
4	官网商城	线上	t
5	线下门店	线下	t
\.


--
-- Data for Name: customer_tiers; Type: TABLE DATA; Schema: analytics; Owner: -
--

COPY analytics.customer_tiers (customer_id, tier, effective_from, effective_to) FROM stdin;
\.


--
-- Data for Name: order_discounts; Type: TABLE DATA; Schema: analytics; Owner: -
--

COPY analytics.order_discounts (discount_id, order_id, campaign_id, discount_type, amount) FROM stdin;
\.


--
-- Name: channels channels_channel_name_key; Type: CONSTRAINT; Schema: analytics; Owner: -
--

ALTER TABLE ONLY analytics.channels
    ADD CONSTRAINT channels_channel_name_key UNIQUE (channel_name);


--
-- Name: channels channels_pkey; Type: CONSTRAINT; Schema: analytics; Owner: -
--

ALTER TABLE ONLY analytics.channels
    ADD CONSTRAINT channels_pkey PRIMARY KEY (channel_id);


--
-- Name: customer_tiers customer_tiers_pkey; Type: CONSTRAINT; Schema: analytics; Owner: -
--

ALTER TABLE ONLY analytics.customer_tiers
    ADD CONSTRAINT customer_tiers_pkey PRIMARY KEY (customer_id, effective_from);


--
-- Name: order_discounts order_discounts_pkey; Type: CONSTRAINT; Schema: analytics; Owner: -
--

ALTER TABLE ONLY analytics.order_discounts
    ADD CONSTRAINT order_discounts_pkey PRIMARY KEY (discount_id);


--
-- Name: customer_tiers_customer_id_idx; Type: INDEX; Schema: analytics; Owner: -
--

CREATE INDEX customer_tiers_customer_id_idx ON analytics.customer_tiers USING btree (customer_id);


--
-- Name: order_discounts_order_id_idx; Type: INDEX; Schema: analytics; Owner: -
--

CREATE INDEX order_discounts_order_id_idx ON analytics.order_discounts USING btree (order_id);


--
-- Name: customer_tiers customer_tiers_customer_id_fkey; Type: FK CONSTRAINT; Schema: analytics; Owner: -
--

ALTER TABLE ONLY analytics.customer_tiers
    ADD CONSTRAINT customer_tiers_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES analytics.customers(customer_id);


--
-- Name: order_discounts order_discounts_campaign_id_fkey; Type: FK CONSTRAINT; Schema: analytics; Owner: -
--

ALTER TABLE ONLY analytics.order_discounts
    ADD CONSTRAINT order_discounts_campaign_id_fkey FOREIGN KEY (campaign_id) REFERENCES analytics.campaigns(campaign_id);


--
-- Name: order_discounts order_discounts_order_id_fkey; Type: FK CONSTRAINT; Schema: analytics; Owner: -
--

ALTER TABLE ONLY analytics.order_discounts
    ADD CONSTRAINT order_discounts_order_id_fkey FOREIGN KEY (order_id) REFERENCES analytics.orders(order_id);


--
-- PostgreSQL database dump complete
--

\unrestrict PYFodp9B8ueK1LmBvrbmNtrEmTPzr309Ad1XJlgdUhC2x8Wxk6PcYy0agKFfBKg

