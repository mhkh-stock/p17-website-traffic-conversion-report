#!/usr/bin/env python3
"""P17 — load the SAMPLE traffic files into SQLite (sql/schema.sql).

    python3 src/build_sqlite.py

The .db is NOT uploaded to GitHub (rebuildable from the pushed
scripts) — same rule as every other project in this portfolio.
"""
import csv
import sqlite3
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
RAW = PROJECT / "data" / "raw"
DB = PROJECT / "data" / "processed" / "traffic.db"

CHANNEL_AOV = {
    "Organic Search": 2850, "Paid Search": 3150, "Social": 2350,
    "Direct": 2650, "Referral": 2250, "Email": 3450,
}
CHANNEL_SHARE = {
    "Organic Search": 0.32, "Paid Search": 0.18, "Social": 0.20,
    "Direct": 0.14, "Referral": 0.08, "Email": 0.08,
}


def main():
    traffic = list(csv.DictReader(
        open(RAW / "daily_traffic_SAMPLE.csv", encoding="utf-8")))
    landing = list(csv.DictReader(
        open(RAW / "landing_pages_SAMPLE.csv", encoding="utf-8")))
    devices = list(csv.DictReader(
        open(RAW / "device_split_SAMPLE.csv", encoding="utf-8")))
    if DB.exists():
        DB.unlink()
    con = sqlite3.connect(DB)
    con.executescript((PROJECT / "sql" / "schema.sql").read_text())
    con.executemany(
        "INSERT INTO dim_channel VALUES (?, ?, ?)",
        [(c, CHANNEL_SHARE[c], CHANNEL_AOV[c])
         for c in sorted(CHANNEL_SHARE)])
    con.executemany(
        "INSERT INTO fact_daily_traffic (traffic_date, month, channel, "
        "sessions, users, product_views, add_to_cart, checkout_started, "
        "purchases, revenue_pkr) VALUES (?,?,?,?,?,?,?,?,?,?)",
        [(r["date"], r["month"], r["channel"], int(r["sessions"]),
          int(r["users"]), int(r["product_views"]), int(r["add_to_cart"]),
          int(r["checkout_started"]), int(r["purchases"]),
          int(r["revenue_pkr"])) for r in traffic])
    con.executemany(
        "INSERT INTO fact_landing_pages (traffic_date, month, "
        "landing_page, sessions, purchases, revenue_pkr) "
        "VALUES (?,?,?,?,?,?)",
        [(r["date"], r["month"], r["landing_page"], int(r["sessions"]),
          int(r["purchases"]), int(r["revenue_pkr"])) for r in landing])
    con.executemany(
        "INSERT INTO fact_device_split (traffic_date, month, device, "
        "sessions, purchases, revenue_pkr) VALUES (?,?,?,?,?,?)",
        [(r["date"], r["month"], r["device"], int(r["sessions"]),
          int(r["purchases"]), int(r["revenue_pkr"])) for r in devices])
    con.commit()
    n = con.execute("SELECT COUNT(*) FROM fact_daily_traffic").fetchone()[0]
    total = con.execute(
        "SELECT SUM(revenue_pkr) FROM fact_daily_traffic").fetchone()[0]
    con.close()
    print(f"loaded {n} traffic rows + {len(landing)} landing rows + "
          f"{len(devices)} device rows, revenue PKR {total:,}")


if __name__ == "__main__":
    main()
