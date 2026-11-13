#!/usr/bin/env python3
"""P17 — generate the SAMPLE GA4-style traffic file for CityStore.pk.

Fictional Pakistani online general store, 6 months of daily traffic:
Fri 2026-05-01 → Sat 2026-10-31 (184 days). Seeded, so the files are
reproducible. Three files, all splits of the same daily session total
(so their totals reconcile exactly — checked as code):

  data/raw/daily_traffic_SAMPLE.csv   — grain: date x channel
      (6 channels; sessions, users + the full conversion funnel
       sessions -> product views -> add to cart -> checkout ->
       purchase, and revenue in PKR)
  data/raw/landing_pages_SAMPLE.csv  — grain: date x landing page
      (8 pages; sessions, purchases, revenue)
  data/raw/device_split_SAMPLE.csv   — grain: date x device
      (Mobile / Desktop / Tablet; sessions, purchases, revenue)

Weekend days (Fri–Sun) run ~18% busier and traffic grows ~3% a
month, so the report has a real trend and a real weekend pattern to
surface. Conversion rates differ by channel on purpose (Email and
Paid Search convert best, Social worst) — that is the story of the
report, not noise.

    python3 src/generate_data.py
"""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
RAW = PROJECT / "data" / "raw"

SEED = 20261113
START = date(2026, 5, 1)    # Friday
DAYS = 184                  # 2026-05-01 .. 2026-10-31

CHANNELS = ["Organic Search", "Paid Search", "Social", "Direct",
            "Referral", "Email"]
# base share of sessions, base funnel step rates (view, cart, checkout,
# purchase) and average order value in PKR, per channel
CHANNEL_PARAMS = {
    "Organic Search": (0.32, (0.60, 0.13, 0.50, 0.64), 2850),
    "Paid Search":    (0.18, (0.62, 0.14, 0.52, 0.66), 3150),
    "Social":         (0.20, (0.55, 0.09, 0.42, 0.55), 2350),
    "Direct":         (0.14, (0.58, 0.12, 0.48, 0.62), 2650),
    "Referral":       (0.08, (0.56, 0.10, 0.45, 0.58), 2250),
    "Email":          (0.08, (0.64, 0.13, 0.52, 0.66), 3450),
}

LANDING_PAGES = [
    ("/", 0.22, 1.00, 1.00),
    ("/sale", 0.14, 1.30, 0.90),
    ("/mobile-phones", 0.16, 1.10, 1.25),
    ("/fashion/men", 0.12, 0.85, 0.95),
    ("/fashion/women", 0.11, 0.90, 1.00),
    ("/home-kitchen", 0.10, 0.80, 1.05),
    ("/beauty", 0.08, 0.95, 0.85),
    ("/electronics", 0.07, 1.05, 1.30),
]

DEVICES = [
    ("Mobile", 0.68, 0.90, 0.95),
    ("Desktop", 0.26, 1.25, 1.15),
    ("Tablet", 0.06, 0.80, 0.90),
]


def allocate(total, weights):
    """Split integer `total` across `weights` (largest-remainder method):
    the parts always sum to exactly `total`."""
    wsum = sum(weights)
    raw = [total * w / wsum for w in weights]
    parts = [int(x) for x in raw]
    leftover = total - sum(parts)
    order = sorted(range(len(weights)),
                   key=lambda i: raw[i] - parts[i], reverse=True)
    for i in order[:leftover]:
        parts[i] += 1
    return parts


def main():
    rng = random.Random(SEED)
    traffic_rows, landing_rows, device_rows = [], [], []
    for day_no in range(DAYS):
        day = START + timedelta(days=day_no)
        month_no = day.month - 5  # 0 = May ... 5 = October
        weekend = 1.18 if day.weekday() >= 4 else 1.0  # Fri-Sun
        growth = 1.0 + 0.03 * month_no
        day_sessions = int(round(
            950 * growth * weekend * rng.uniform(0.90, 1.10)))

        # --- split the day across channels (noisy shares) ---
        ch_weights = [CHANNEL_PARAMS[c][0] * rng.uniform(0.90, 1.10)
                      for c in CHANNELS]
        ch_sessions = allocate(day_sessions, ch_weights)

        day_purchases = 0
        day_revenue = 0
        for ch, sessions in zip(CHANNELS, ch_sessions):
            _, rates, aov = CHANNEL_PARAMS[ch]
            users = int(round(sessions * rng.uniform(0.70, 0.78)))
            steps, prev = [], sessions
            for rate in rates:
                nxt = int(round(prev * min(0.95, rate * rng.uniform(0.92, 1.08))))
                steps.append(nxt)
                prev = nxt
            views, cart, checkout, purchases = steps
            revenue = int(round(purchases * aov * rng.uniform(0.92, 1.08)))
            day_purchases += purchases
            day_revenue += revenue
            traffic_rows.append({
                "date": day.isoformat(),
                "month": day.strftime("%Y-%m"),
                "channel": ch,
                "sessions": sessions,
                "users": users,
                "product_views": views,
                "add_to_cart": cart,
                "checkout_started": checkout,
                "purchases": purchases,
                "revenue_pkr": revenue,
            })

        # --- split the same day across landing pages ---
        pg_weights = [s * rng.uniform(0.90, 1.10)
                      for _, s, _, _ in LANDING_PAGES]
        pg_sessions = allocate(day_sessions, pg_weights)
        pg_weights_p = [s * cr for s, (_, _, cr, _) in
                        zip(pg_sessions, LANDING_PAGES)]
        pg_purchases = allocate(day_purchases, pg_weights_p)
        pg_weights_r = [p * aovm for p, (_, _, _, aovm) in
                        zip(pg_purchases, LANDING_PAGES)]
        pg_revenue = (allocate(day_revenue, pg_weights_r)
                      if day_revenue else [0] * len(LANDING_PAGES))
        for (page, _, _, _), s, p, rev in zip(
                LANDING_PAGES, pg_sessions, pg_purchases, pg_revenue):
            landing_rows.append({
                "date": day.isoformat(),
                "month": day.strftime("%Y-%m"),
                "landing_page": page,
                "sessions": s,
                "purchases": p,
                "revenue_pkr": rev,
            })

        # --- split the same day across devices (mobile share creeps up) ---
        dev_weights = []
        for name, share, _, _ in DEVICES:
            share = share + (0.005 * month_no if name == "Mobile" else
                             -0.003 * month_no if name == "Desktop" else
                             -0.002 * month_no)
            dev_weights.append(share * rng.uniform(0.92, 1.08))
        dev_sessions = allocate(day_sessions, dev_weights)
        dev_weights_p = [s * cr for s, (_, _, cr, _) in
                         zip(dev_sessions, DEVICES)]
        dev_purchases = allocate(day_purchases, dev_weights_p)
        dev_weights_r = [p * aovm for p, (_, _, _, aovm) in
                         zip(dev_purchases, DEVICES)]
        dev_revenue = (allocate(day_revenue, dev_weights_r)
                       if day_revenue else [0] * len(DEVICES))
        for (name, _, _, _), s, p, rev in zip(
                DEVICES, dev_sessions, dev_purchases, dev_revenue):
            device_rows.append({
                "date": day.isoformat(),
                "month": day.strftime("%Y-%m"),
                "device": name,
                "sessions": s,
                "purchases": p,
                "revenue_pkr": rev,
            })

    specs = [
        ("daily_traffic_SAMPLE.csv", traffic_rows),
        ("landing_pages_SAMPLE.csv", landing_rows),
        ("device_split_SAMPLE.csv", device_rows),
    ]
    for name, rows in specs:
        out = RAW / name
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        print(f"wrote {name}: {len(rows)} rows")
    tot_s = sum(r["sessions"] for r in traffic_rows)
    tot_p = sum(r["purchases"] for r in traffic_rows)
    tot_r = sum(r["revenue_pkr"] for r in traffic_rows)
    print(f"total: {tot_s:,} sessions, {tot_p:,} purchases, "
          f"PKR {tot_r:,} revenue, {DAYS} days")


if __name__ == "__main__":
    main()
