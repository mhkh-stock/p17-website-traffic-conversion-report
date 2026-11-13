# P17 — Website Traffic & Conversion Analytics Report

**Client (SAMPLE):** CityStore.pk — Pakistani online general store,
6 months (Fri 2026-05-01 → Sat 2026-10-31, 184 days) ·
**Status: SAMPLE delivery on DEMO data**
**Tools:** GA4-style traffic data · SQL (SQLite) · Excel (live formulas) · reportlab
**Deliverable:** `outputs/traffic_report.pdf` (2 pages) +
`outputs/website_traffic_report_SAMPLE.xlsx`

> ⚠️ **What this is and is not.** The traffic file is a fictional
> store's demo data, generated to show the method. No real store,
> visitor or payment is involved. What is real is the analysis: the
> same channel table, funnel and workbook run on a real client's
> GA4 export the same way, and every number in the report is
> recomputed from the data, never typed.

## Business question it answers

> "Where does my traffic come from, and what converts?"

A store owner who only watches total visits cannot tell whether
their ads are working or their website is leaking buyers. This
delivery answers both: which channel brings buyers (not just
clicks), where the funnel loses them, which pages and devices
convert, and what to fix first — with the money attached to each
answer.

## What is inside

| File | What it does |
|---|---|
| `outputs/traffic_report.pdf` | The deliverable: 2-page client report — headline, channel table, funnel, monthly trend, 3 recommendations |
| `outputs/website_traffic_report_SAMPLE.xlsx` | The working report: Dashboard (KPIs + monthly trend, live formulas) + Channels + Landing Pages + Devices + Funnel + Data sheets |
| `outputs/traffic_report.md` | Findings report: headline numbers, all tables, the reasoning |
| `outputs/summary.json` | Machine-readable summary (KPIs + channels + funnel + months + pages + devices) |
| `outputs/monthly_revenue.png` | Monthly revenue chart (render of the same data) |
| `data/raw/daily_traffic_SAMPLE.csv` | The traffic file: 1,104 date × channel rows, sessions + users + full funnel + revenue |
| `data/raw/landing_pages_SAMPLE.csv` | 1,472 date × landing-page rows (8 pages) |
| `data/raw/device_split_SAMPLE.csv` | 552 date × device rows (Mobile / Desktop / Tablet) |
| `data/processed/monthly_summary.csv` | 6-month summary produced by `src/analyze.py` |
| `data/processed/channel_summary.csv` | 6-channel summary produced by `src/analyze.py` |
| `data/processed/traffic.db` | SQLite: dim_channel + fact_daily_traffic + fact_landing_pages + fact_device_split (NOT uploaded — rebuildable) |
| `data/README.md` | Data dictionary + known quirks |
| `sql/schema.sql` | Schema for the three fact tables (funnel monotonicity enforced by CHECKs) |
| `sql/analysis_queries.sql` | The whole report in SQL — 7 queries that must agree with the workbook |
| `src/generate_data.py` | Makes the demo files (seeded; NOT run on a real client file) |
| `src/analyze.py` | Recomputes every headline number from the raw CSVs |
| `src/build_sqlite.py` | Loads the three files into SQLite |
| `src/build_workbook.py` | Builds the workbook: 9 sheets, live formulas |
| `src/build_report.py` | Builds the 2-page PDF + chart from `outputs/summary.json` |
| `src/checks.py` | Data-quality + reconciliation checks as code — 140 checks, all passing |
| `requirements.txt` | Pinned: `openpyxl==3.1.2`, `reportlab==5.0.1`, `matplotlib==3.6.3` (Python 3.12) |

## How it fits together

```
GA4 export (client's file, same columns) ──▶ src/analyze.py ──▶ summary.json
        (1,104 rows in the demo)                 │              + traffic_report.md
                                                 ▼
                                       src/build_sqlite.py ──▶ data/processed/traffic.db
                                                 │              (NOT uploaded: rebuildable)
                                                 ▼
                                       src/build_workbook.py ──▶ website_traffic_report_SAMPLE.xlsx
                                                 │              (9 sheets, live formulas)
                                                 ▼
                                       src/build_report.py ──▶ traffic_report.pdf (2 pages)
                                                 ▲ src/checks.py verifies all of it (140 checks)
```

## Headline numbers (SAMPLE — CityStore.pk, 6 months)

- **Total sessions: 202,793** from 150,351 users · **4,475 purchases** ·
  **revenue PKR 12,910,349** · **overall conversion 2.21%** · **AOV PKR 2,885**
- **Organic Search is the biggest channel:** 64,911 sessions (32.0%),
  PKR 4,648,671 revenue — but it converts at only 2.51%
- **Paid Search converts best: 3.00%** (36,506 sessions, PKR 3,465,351);
  **Social converts worst: 1.13%** despite 40,544 sessions — the most
  traffic that converts least
- **The funnel:** 202,793 sessions → 119,691 product views (59.02%) →
  14,452 add to cart (12.07%) → 7,071 checkout started (48.93%) →
  4,475 purchases (63.29%). The leak is view → cart, not checkout
- **Best month: October 2026 (PKR 2,327,060)**; worst: June 2026
  (PKR 2,010,379); revenue grew **+14.64% from May to October**
- **Mobile is 69.1% of sessions but converts at 2.03%** against
  Desktop's 2.81% — if mobile converted like desktop, the same
  traffic would be worth roughly **PKR 3,658,444 more**
- **Weekends carry the store:** Fri–Sun average 1,209.9 sessions a day
  vs 1,019.3 on weekdays (**+18.7%**)

## The three recommendations (from the data, not from a template)

1. **Fix the view → cart leak first (12.07%).** Better photos, clearer
   prices and delivery info, a visible add-to-cart button above the
   fold — before spending one more rupee on ads.
2. **Move budget from Social to Paid Search and Email.** Social brings
   40,544 sessions at 1.13% conversion; Paid Search converts at 3.00%
   and Email at 2.95%. Same spend, more buyers.
3. **Fix mobile checkout.** Mobile is most of the traffic and the
   worst converter of the three devices. One-page checkout,
   JazzCash / Easypaisa / COD upfront, no forced account creation.

## Same logic, three ways — and they must agree

The channel, monthly and funnel totals exist in three forms: the SQL
in `sql/analysis_queries.sql`, the Python in `src/analyze.py`, and
this workbook's formulas. `src/checks.py` runs all three against the
raw files and compares them — a mistake in any one of them shows up
as a failure. The workbook's formulas were also recalculated in
LibreOffice (including the `_xlfn.MAXIFS` / `_xlfn.MINIFS` best/worst
month cells): every total matches the recompute exactly, with zero
error values.

## Reproduce it (2 minutes)

```bash
python3 src/generate_data.py   # rebuild the SAMPLE files (seed 20261113)
python3 src/analyze.py         # summary.json + traffic_report.md
python3 src/build_sqlite.py    # data/processed/traffic.db
python3 src/build_workbook.py  # outputs/website_traffic_report_SAMPLE.xlsx
python3 src/build_report.py    # outputs/traffic_report.pdf (2 pages)
python3 src/checks.py          # 140 checks — expect all passing
```

On a real client file, replace the three CSVs with the GA4 export
(same columns) and skip `generate_data.py` — everything downstream
runs unchanged.
