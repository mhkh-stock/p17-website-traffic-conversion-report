-- P17 — schema for the CityStore.pk traffic report (SAMPLE data).
-- Grain: one row per date x channel in fact_daily_traffic (the funnel
-- lives here); one row per date x landing page and per date x device
-- in the two split tables. All three splits share the same daily
-- session total, so their totals reconcile — checked as code.
-- Loaded by src/build_sqlite.py.

CREATE TABLE IF NOT EXISTS dim_channel (
    channel           TEXT PRIMARY KEY,
    base_share        REAL NOT NULL,
    avg_order_value_pkr INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_daily_traffic (
    traffic_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    traffic_date     TEXT NOT NULL,   -- yyyy-mm-dd
    month            TEXT NOT NULL,   -- yyyy-mm
    channel          TEXT NOT NULL REFERENCES dim_channel(channel),
    sessions         INTEGER NOT NULL CHECK (sessions >= 0),
    users            INTEGER NOT NULL CHECK (users >= 0),
    product_views    INTEGER NOT NULL CHECK (product_views >= 0),
    add_to_cart      INTEGER NOT NULL CHECK (add_to_cart >= 0),
    checkout_started INTEGER NOT NULL CHECK (checkout_started >= 0),
    purchases        INTEGER NOT NULL CHECK (purchases >= 0),
    revenue_pkr      INTEGER NOT NULL CHECK (revenue_pkr >= 0),
    CHECK (product_views <= sessions),
    CHECK (add_to_cart <= product_views),
    CHECK (checkout_started <= add_to_cart),
    CHECK (purchases <= checkout_started),
    CHECK (users <= sessions)
);

CREATE TABLE IF NOT EXISTS fact_landing_pages (
    landing_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    traffic_date TEXT NOT NULL,   -- yyyy-mm-dd
    month        TEXT NOT NULL,   -- yyyy-mm
    landing_page TEXT NOT NULL,
    sessions     INTEGER NOT NULL CHECK (sessions >= 0),
    purchases    INTEGER NOT NULL CHECK (purchases >= 0),
    revenue_pkr  INTEGER NOT NULL CHECK (revenue_pkr >= 0)
);

CREATE TABLE IF NOT EXISTS fact_device_split (
    device_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    traffic_date TEXT NOT NULL,   -- yyyy-mm-dd
    month        TEXT NOT NULL,   -- yyyy-mm
    device       TEXT NOT NULL,
    sessions     INTEGER NOT NULL CHECK (sessions >= 0),
    purchases    INTEGER NOT NULL CHECK (purchases >= 0),
    revenue_pkr  INTEGER NOT NULL CHECK (revenue_pkr >= 0)
);

CREATE INDEX IF NOT EXISTS idx_traffic_date_channel
    ON fact_daily_traffic (traffic_date, channel);
CREATE INDEX IF NOT EXISTS idx_traffic_month
    ON fact_daily_traffic (month);
CREATE INDEX IF NOT EXISTS idx_landing_date
    ON fact_landing_pages (traffic_date, landing_page);
CREATE INDEX IF NOT EXISTS idx_device_date
    ON fact_device_split (traffic_date, device);
