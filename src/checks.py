#!/usr/bin/env python3
"""Checks as code for P17. Recomputes every headline number from the
raw CSVs and verifies the JSON, the processed CSVs, the SQL analysis,
the workbook formulas and the LibreOffice recalc against it — four
independent paths that must agree.

    python3 src/checks.py        (after the full pipeline + recalc:
    soffice --headless --calc --convert-to xlsx --outdir outputs/.recalc
    outputs/website_traffic_report_SAMPLE.xlsx)

Exit code 0 when every check passes, 1 otherwise.
"""
import csv
import json
import re
import sqlite3
import subprocess
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

from openpyxl import load_workbook

PROJECT = Path(__file__).resolve().parent.parent
RAW = PROJECT / "data" / "raw"
SUMMARY = PROJECT / "outputs" / "summary.json"
MONTHLY_CSV = PROJECT / "data" / "processed" / "monthly_summary.csv"
CHANNEL_CSV = PROJECT / "data" / "processed" / "channel_summary.csv"
WORKBOOK = PROJECT / "outputs" / "website_traffic_report_SAMPLE.xlsx"
RECALC = PROJECT / "outputs" / ".recalc" / "website_traffic_report_SAMPLE.xlsx"
PDF = PROJECT / "outputs" / "traffic_report.pdf"
SCHEMA = PROJECT / "sql" / "schema.sql"
QUERIES = PROJECT / "sql" / "analysis_queries.sql"
DB = PROJECT / "data" / "processed" / "traffic.db"

CHANNELS = ["Organic Search", "Paid Search", "Social", "Direct",
            "Referral", "Email"]
PAGES = ["/", "/sale", "/mobile-phones", "/fashion/men",
         "/fashion/women", "/home-kitchen", "/beauty", "/electronics"]
DEVICES = ["Mobile", "Desktop", "Tablet"]
INTS = ["sessions", "users", "product_views", "add_to_cart",
        "checkout_started", "purchases", "revenue_pkr"]
fails = []
ran = []


def check(name, cond, detail=""):
    ran.append(name)
    print(("PASS " if cond else "FAIL ") + name +
          (f" — {detail}" if detail else ""))
    if not cond:
        fails.append(name)


def load(name):
    rows = list(csv.DictReader(open(RAW / name, encoding="utf-8")))
    for r in rows:
        for k in INTS:
            if k in r:
                r[k] = int(r[k])
    return rows


traffic = load("daily_traffic_SAMPLE.csv")
landing = load("landing_pages_SAMPLE.csv")
devices = load("device_split_SAMPLE.csv")

# ── raw files ──────────────────────────────────────────────────────────
check("traffic rows = 1104", len(traffic) == 1104, str(len(traffic)))
check("landing rows = 1472", len(landing) == 1472, str(len(landing)))
check("device rows = 552", len(devices) == 552, str(len(devices)))
check("dates span 2026-05-01..2026-10-31",
      min(r["date"] for r in traffic) == "2026-05-01" and
      max(r["date"] for r in traffic) == "2026-10-31")
check("184 distinct days", len({r["date"] for r in traffic}) == 184)
check("6 distinct months", len({r["month"] for r in traffic}) == 6)
check("6 channels only",
      {r["channel"] for r in traffic} == set(CHANNELS))
check("8 landing pages only",
      {r["landing_page"] for r in landing} == set(PAGES))
check("3 devices only",
      {r["device"] for r in devices} == set(DEVICES))
check("every date x channel present once",
      len({(r["date"], r["channel"]) for r in traffic}) == 1104)
check("every date x page present once",
      len({(r["date"], r["landing_page"]) for r in landing}) == 1472)
check("every date x device present once",
      len({(r["date"], r["device"]) for r in devices}) == 552)
check("funnel monotonic: views <= sessions",
      all(r["product_views"] <= r["sessions"] for r in traffic))
check("funnel monotonic: cart <= views",
      all(r["add_to_cart"] <= r["product_views"] for r in traffic))
check("funnel monotonic: checkout <= cart",
      all(r["checkout_started"] <= r["add_to_cart"] for r in traffic))
check("funnel monotonic: purchases <= checkout",
      all(r["purchases"] <= r["checkout_started"] for r in traffic))
check("users <= sessions on every row",
      all(r["users"] <= r["sessions"] for r in traffic))
check("no negative counts anywhere",
      all(r[k] >= 0 for r in traffic for k in INTS))

tot_s = sum(r["sessions"] for r in traffic)
tot_u = sum(r["users"] for r in traffic)
tot_p = sum(r["purchases"] for r in traffic)
tot_r = sum(r["revenue_pkr"] for r in traffic)
check("total sessions = 202,793", tot_s == 202793, f"{tot_s:,}")
check("total users = 150,351", tot_u == 150351, f"{tot_u:,}")
check("total purchases = 4,475", tot_p == 4475, f"{tot_p:,}")
check("total revenue = PKR 12,910,349", tot_r == 12910349, f"{tot_r:,}")
check("overall conversion = 2.21%",
      round(100.0 * tot_p / tot_s, 2) == 2.21)
check("average order value = PKR 2,885",
      round(tot_r / tot_p) == 2885)

# channel recompute
ch = {}
for c in CHANNELS:
    rs = [r for r in traffic if r["channel"] == c]
    ch[c] = {"sessions": sum(r["sessions"] for r in rs),
             "purchases": sum(r["purchases"] for r in rs),
             "revenue": sum(r["revenue_pkr"] for r in rs)}
    ch[c]["cr"] = round(100.0 * ch[c]["purchases"] / ch[c]["sessions"], 2)
    ch[c]["share"] = round(100.0 * ch[c]["sessions"] / tot_s, 2)
check("channel shares sum to 100%",
      abs(sum(ch[c]["share"] for c in CHANNELS) - 100.0) <= 0.05,
      str(sum(ch[c]["share"] for c in CHANNELS)))
check("best channel = Paid Search at 3.0%",
      max(ch, key=lambda c: ch[c]["cr"]) == "Paid Search" and
      ch["Paid Search"]["cr"] == 3.0, str(ch["Paid Search"]["cr"]))
check("worst channel = Social at 1.13%",
      min(ch, key=lambda c: ch[c]["cr"]) == "Social" and
      ch["Social"]["cr"] == 1.13, str(ch["Social"]["cr"]))
check("Organic Search revenue = 4,648,671",
      ch["Organic Search"]["revenue"] == 4648671)
check("Email AOV beats Social AOV",
      ch["Email"]["revenue"] / ch["Email"]["purchases"] >
      ch["Social"]["revenue"] / ch["Social"]["purchases"])

funnel = {k: sum(r[k] for r in traffic)
          for k in ["sessions", "product_views", "add_to_cart",
                    "checkout_started", "purchases"]}
check("funnel views = 119,691", funnel["product_views"] == 119691)
check("funnel add to cart = 14,452", funnel["add_to_cart"] == 14452)
check("funnel checkout = 7,071", funnel["checkout_started"] == 7071)
check("views rate = 59.02%",
      round(100.0 * funnel["product_views"] / funnel["sessions"], 2) == 59.02)
check("cart rate = 12.07%",
      round(100.0 * funnel["add_to_cart"] / funnel["product_views"], 2) == 12.07)
check("checkout rate = 48.93%",
      round(100.0 * funnel["checkout_started"] / funnel["add_to_cart"], 2) == 48.93)
check("purchase rate = 63.29%",
      round(100.0 * funnel["purchases"] / funnel["checkout_started"], 2) == 63.29)

# monthly recompute
months = {}
for m in sorted({r["month"] for r in traffic}):
    rs = [r for r in traffic if r["month"] == m]
    months[m] = {"sessions": sum(r["sessions"] for r in rs),
                 "purchases": sum(r["purchases"] for r in rs),
                 "revenue": sum(r["revenue_pkr"] for r in rs)}
check("best month = 2026-10 at 2,327,060",
      max(months, key=lambda m: months[m]["revenue"]) == "2026-10" and
      months["2026-10"]["revenue"] == 2327060)
check("worst month = 2026-06 at 2,010,379",
      min(months, key=lambda m: months[m]["revenue"]) == "2026-06" and
      months["2026-06"]["revenue"] == 2010379)
check("growth May->Oct = 14.64%",
      round(100.0 * (months["2026-10"]["revenue"] - months["2026-05"]["revenue"])
            / months["2026-05"]["revenue"], 2) == 14.64)
check("monthly sessions sum to total",
      sum(v["sessions"] for v in months.values()) == tot_s)
check("monthly revenue sums to total",
      sum(v["revenue"] for v in months.values()) == tot_r)

# weekend vs weekday
we_days = {r["date"] for r in traffic
           if date.fromisoformat(r["date"]).weekday() >= 4}
wd_days = {r["date"] for r in traffic
           if date.fromisoformat(r["date"]).weekday() < 4}
check("weekend + weekday days = 184",
      len(we_days) + len(wd_days) == 184,
      f"{len(we_days)} + {len(wd_days)}")
we_s = sum(r["sessions"] for r in traffic
           if date.fromisoformat(r["date"]).weekday() >= 4)
wd_s = sum(r["sessions"] for r in traffic
           if date.fromisoformat(r["date"]).weekday() < 4)
check("weekend lift = 18.7%",
      round(100.0 * (we_s / len(we_days)) / (wd_s / len(wd_days)) - 100.0, 1)
      == 18.7)

# cross-file reconciliation
check("landing sessions = traffic sessions",
      sum(r["sessions"] for r in landing) == tot_s)
check("landing purchases = traffic purchases",
      sum(r["purchases"] for r in landing) == tot_p)
check("landing revenue = traffic revenue",
      sum(r["revenue_pkr"] for r in landing) == tot_r)
check("device sessions = traffic sessions",
      sum(r["sessions"] for r in devices) == tot_s)
check("device purchases = traffic purchases",
      sum(r["purchases"] for r in devices) == tot_p)
check("device revenue = traffic revenue",
      sum(r["revenue_pkr"] for r in devices) == tot_r)
day_s = defaultdict(int)
for r in traffic:
    day_s[r["date"]] += r["sessions"]
check("landing sessions match traffic every day",
      all(sum(r["sessions"] for r in landing if r["date"] == d) == day_s[d]
          for d in day_s))
check("device sessions match traffic every day",
      all(sum(r["sessions"] for r in devices if r["date"] == d) == day_s[d]
          for d in day_s))
pg = defaultdict(int)
for r in landing:
    pg[r["landing_page"]] += r["sessions"]
check("best landing page by sessions = /",
      max(pg, key=pg.get) == "/")
check("/sale converts best (2.85%)",
      round(100.0 * sum(r["purchases"] for r in landing
                        if r["landing_page"] == "/sale")
            / pg["/sale"], 2) == 2.85)
dv = defaultdict(int)
for r in devices:
    dv[r["device"]] += r["sessions"]
check("Mobile share = 69.1%",
      round(100.0 * dv["Mobile"] / tot_s, 2) == 69.1)
check("Desktop converts better than Mobile",
      (sum(r["purchases"] for r in devices if r["device"] == "Desktop")
       / dv["Desktop"] >
       sum(r["purchases"] for r in devices if r["device"] == "Mobile")
       / dv["Mobile"]))

# ── summary JSON + processed CSVs ──────────────────────────────────────
s = json.loads(SUMMARY.read_text(encoding="utf-8"))
check("JSON sessions match recompute", s["total_sessions"] == tot_s)
check("JSON users match recompute", s["total_users"] == tot_u)
check("JSON purchases match recompute", s["total_purchases"] == tot_p)
check("JSON revenue match recompute", s["total_revenue_pkr"] == tot_r)
check("JSON CR = 2.21%", s["overall_conversion_rate_pct"] == 2.21)
check("JSON AOV = 2,885", s["avg_order_value_pkr"] == 2885)
check("JSON funnel matches recompute", s["funnel"] == funnel, str(s["funnel"]))
check("JSON best month = 2026-10",
      s["best_month"] == {"month": "2026-10", "revenue_pkr": 2327060,
                          "sessions": 36415}, str(s["best_month"]))
check("JSON worst month = 2026-06",
      s["worst_month"] == {"month": "2026-06", "revenue_pkr": 2010379,
                           "sessions": 31601})
check("JSON best channel = Paid Search",
      s["best_channel_by_conversion"] == "Paid Search")
check("JSON worst channel = Social",
      s["worst_channel_by_conversion"] == "Social")
check("JSON channel sessions match recompute",
      all(c["sessions"] == ch[c["channel"]]["sessions"]
          for c in s["channels"]))
check("JSON months match recompute",
      all(m["sessions"] == months[m["month"]]["sessions"]
          and m["revenue_pkr"] == months[m["month"]]["revenue"]
          for m in s["months"]))
check("JSON weekend lift = 18.7%", s["weekend_lift_pct"] == 18.7)
mcsv = list(csv.DictReader(open(MONTHLY_CSV, encoding="utf-8")))
check("monthly CSV has 6 rows", len(mcsv) == 6)
check("monthly CSV revenue matches recompute",
      all(int(mcsv[i]["revenue_pkr"]) ==
          months[sorted(months)[i]]["revenue"] for i in range(6)))
check("monthly CSV Oct MoM present", mcsv[5]["mom_growth_pct"] != "")
ccsv = list(csv.DictReader(open(CHANNEL_CSV, encoding="utf-8")))
check("channel CSV has 6 rows", len(ccsv) == 6)
check("channel CSV sessions match recompute",
      all(int(r["sessions"]) == ch[r["channel"]]["sessions"]
          for r in ccsv))

# ── SQL analysis (in-memory, same schema + same CSVs) ──────────────────
con = sqlite3.connect(":memory:")
con.executescript(SCHEMA.read_text())
con.executemany(
    "INSERT INTO dim_channel VALUES (?, ?, ?)",
    [(c, {"Organic Search": 0.32, "Paid Search": 0.18, "Social": 0.20,
          "Direct": 0.14, "Referral": 0.08, "Email": 0.08}[c],
     {"Organic Search": 2850, "Paid Search": 3150, "Social": 2350,
      "Direct": 2650, "Referral": 2250, "Email": 3450}[c])
     for c in CHANNELS])
con.executemany(
    "INSERT INTO fact_daily_traffic (traffic_date, month, channel, "
    "sessions, users, product_views, add_to_cart, checkout_started, "
    "purchases, revenue_pkr) VALUES (?,?,?,?,?,?,?,?,?,?)",
    [(r["date"], r["month"], r["channel"], r["sessions"], r["users"],
      r["product_views"], r["add_to_cart"], r["checkout_started"],
      r["purchases"], r["revenue_pkr"]) for r in traffic])
con.executemany(
    "INSERT INTO fact_landing_pages (traffic_date, month, landing_page, "
    "sessions, purchases, revenue_pkr) VALUES (?,?,?,?,?,?)",
    [(r["date"], r["month"], r["landing_page"], r["sessions"],
      r["purchases"], r["revenue_pkr"]) for r in landing])
con.executemany(
    "INSERT INTO fact_device_split (traffic_date, month, device, "
    "sessions, purchases, revenue_pkr) VALUES (?,?,?,?,?,?)",
    [(r["date"], r["month"], r["device"], r["sessions"],
      r["purchases"], r["revenue_pkr"]) for r in devices])
blocks = re.split(r"^-- Q\d+:.*$", QUERIES.read_text(),
                  flags=re.MULTILINE)
queries = [b.strip() for b in blocks if b.strip().startswith("SELECT")]
check("analysis_queries.sql has 7 queries", len(queries) == 7,
      str(len(queries)))
q1 = con.execute(queries[0]).fetchall()
check("SQL Q1: 6 channels",
      len(q1) == 6 and q1[0][0] == "Organic Search", str(len(q1)))
check("SQL Q1 channel sessions match recompute",
      all(row[1] == ch[row[0]]["sessions"] for row in q1))
check("SQL Q1 channel revenue matches recompute",
      all(row[4] == ch[row[0]]["revenue"] for row in q1))
q2 = con.execute(queries[1]).fetchall()
check("SQL Q2: 6 months", len(q2) == 6)
check("SQL Q2 monthly revenue matches recompute",
      all(row[4] == months[row[0]]["revenue"] for row in q2))
q3 = con.execute(queries[2]).fetchone()
check("SQL Q3 funnel sessions = 202,793", q3[0] == 202793, str(q3[0]))
check("SQL Q3 funnel purchases = 4,475", q3[4] == 4475, str(q3[4]))
check("SQL Q3 overall conversion = 2.21%", q3[9] == 2.21, str(q3[9]))
q4 = con.execute(queries[3]).fetchall()
check("SQL Q4: 8 landing pages, top = /",
      len(q4) == 8 and q4[0][0] == "/", str(len(q4)))
check("SQL Q4 landing sessions match recompute",
      all(row[1] == pg[row[0]] for row in q4))
q5 = con.execute(queries[4]).fetchall()
check("SQL Q5: 3 devices, top = Mobile",
      len(q5) == 3 and q5[0][0] == "Mobile", str(len(q5)))
check("SQL Q5 device sessions match recompute",
      all(row[1] == dv[row[0]] for row in q5))
q6 = con.execute(queries[5]).fetchall()
check("SQL Q6: weekend + weekday = 184 days",
      sum(row[1] for row in q6) == 184, str(q6))
check("SQL Q6 weekend sessions/day beats weekday",
      {row[0]: row[5] for row in q6}["weekend"] >
      {row[0]: row[5] for row in q6}["weekday"])
q7 = con.execute(queries[6]).fetchall()
check("SQL Q7: all three sources reconcile",
      q7[0][1:] == q7[1][1:] == q7[2][1:], str(q7))
con.close()

# ── on-disk SQLite db ──────────────────────────────────────────────────
check("traffic.db exists", DB.exists())
if DB.exists():
    con = sqlite3.connect(DB)
    check("db traffic rows = 1104",
          con.execute("SELECT COUNT(*) FROM fact_daily_traffic")
          .fetchone()[0] == 1104)
    check("db revenue = 12,910,349",
          con.execute("SELECT SUM(revenue_pkr) FROM fact_daily_traffic")
          .fetchone()[0] == 12910349)
    con.close()

# ── workbook (formulas) ────────────────────────────────────────────────
wb = load_workbook(WORKBOOK)
check("sheets = Dashboard, Data, LandingData, DeviceData, Channels, "
      "Landing Pages, Devices, Funnel, Method",
      wb.sheetnames == ["Dashboard", "Data", "LandingData", "DeviceData",
                        "Channels", "Landing Pages", "Devices", "Funnel",
                        "Method"], str(wb.sheetnames))
check("Data rows = 1105 incl header",
      wb["Data"].max_row == 1105, str(wb["Data"].max_row))
check("Data sessions column sums to 202,793 (values)",
      sum(wb["Data"].cell(row=r, column=4).value
          for r in range(2, 1106)) == 202793)
check("LandingData rows = 1473 incl header",
      wb["LandingData"].max_row == 1473)
check("DeviceData rows = 553 incl header",
      wb["DeviceData"].max_row == 553)
dash = wb["Dashboard"]
check("Dashboard B5 is a SUM formula over Data",
      isinstance(dash["B5"].value, str) and
      dash["B5"].value.startswith("=SUM(Data!"), str(dash["B5"].value))
check("Dashboard B11 is the conversion formula",
      dash["B11"].value == "=B9/B5", str(dash["B11"].value))
check("Dashboard B12 is the AOV formula",
      dash["B12"].value == "=B10/B9", str(dash["B12"].value))
check("Dashboard B17 is a SUMIFS formula",
      isinstance(dash["B17"].value, str) and
      dash["B17"].value.startswith("=SUMIFS("), str(dash["B17"].value))
check("Dashboard B25 uses _xlfn.MAXIFS",
      isinstance(dash["B25"].value, str) and
      dash["B25"].value.startswith("=_xlfn.MAXIFS("),
      str(dash["B25"].value))
check("Dashboard B26 uses _xlfn.MINIFS",
      isinstance(dash["B26"].value, str) and
      dash["B26"].value.startswith("=_xlfn.MINIFS("),
      str(dash["B26"].value))
check("Dashboard has a chart", len(dash._charts) >= 1)
ch_ws = wb["Channels"]
check("Channels B4 is a SUMIFS formula",
      isinstance(ch_ws["B4"].value, str) and
      ch_ws["B4"].value.startswith("=SUMIFS("), str(ch_ws["B4"].value))
check("Channels total row uses SUM",
      ch_ws["B10"].value == "=SUM(B4:B9)", str(ch_ws["B10"].value))
lp_ws = wb["Landing Pages"]
check("Landing Pages B4 is a SUMIFS over LandingData",
      isinstance(lp_ws["B4"].value, str) and
      "LandingData!" in lp_ws["B4"].value, str(lp_ws["B4"].value))
dv_ws = wb["Devices"]
check("Devices B4 is a SUMIFS over DeviceData",
      isinstance(dv_ws["B4"].value, str) and
      "DeviceData!" in dv_ws["B4"].value, str(dv_ws["B4"].value))
fu_ws = wb["Funnel"]
check("Funnel B4 is a SUM over Data",
      fu_ws["B4"].value == "=SUM(Data!D2:D1105)", str(fu_ws["B4"].value))
check("Funnel C5 is a step-conversion formula",
      fu_ws["C5"].value == "=B5/B4", str(fu_ws["C5"].value))
check("Method sheet mentions _xlfn.",
      "_xlfn." in (wb["Method"]["B6"].value or ""))

# ── LibreOffice recalculated values ────────────────────────────────────
if RECALC.exists():
    wb2 = load_workbook(RECALC, data_only=True)
    d2 = wb2["Dashboard"]
    check("recalc Dashboard sessions = 202,793",
          d2["B5"].value == 202793, str(d2["B5"].value))
    check("recalc Dashboard purchases = 4,475",
          d2["B9"].value == 4475, str(d2["B9"].value))
    check("recalc Dashboard revenue = 12,910,349",
          d2["B10"].value == 12910349, str(d2["B10"].value))
    check("recalc Dashboard conversion ≈ 2.21%",
          abs(d2["B11"].value - 0.0221) < 0.0005, str(d2["B11"].value))
    check("recalc Dashboard AOV ≈ 2,885",
          abs(d2["B12"].value - 2885) < 1, str(d2["B12"].value))
    check("recalc best month revenue = 2,327,060",
          d2["B25"].value == 2327060, str(d2["B25"].value))
    check("recalc best month = 2026-10",
          d2["C25"].value == "2026-10", str(d2["C25"].value))
    check("recalc worst month revenue = 2,010,379",
          d2["B26"].value == 2010379, str(d2["B26"].value))
    check("recalc worst month = 2026-06",
          d2["C26"].value == "2026-06", str(d2["C26"].value))
    check("recalc monthly Oct revenue = 2,327,060",
          d2["E22"].value == 2327060, str(d2["E22"].value))
    check("recalc monthly total revenue = 12,910,349",
          d2["E23"].value == 12910349, str(d2["E23"].value))
    c2 = wb2["Channels"]
    check("recalc Channels TOTAL sessions = 202,793",
          c2["B10"].value == 202793, str(c2["B10"].value))
    check("recalc Channels TOTAL revenue = 12,910,349",
          c2["E10"].value == 12910349, str(c2["E10"].value))
    check("recalc Paid Search conversion ≈ 3.0%",
          abs(c2["G5"].value - 0.03) < 0.0005, str(c2["G5"].value))
    check("recalc Social conversion ≈ 1.13%",
          abs(c2["G6"].value - 0.0113) < 0.0005, str(c2["G6"].value))
    check("recalc Channels shares sum to 100%",
          abs(sum(c2.cell(row=r, column=6).value for r in range(4, 10))
              - 1.0) < 0.001)
    l2 = wb2["Landing Pages"]
    check("recalc Landing Pages TOTAL sessions = 202,793",
          l2["B12"].value == 202793, str(l2["B12"].value))
    check("recalc Landing Pages TOTAL revenue = 12,910,349",
          l2["D12"].value == 12910349, str(l2["D12"].value))
    v2 = wb2["Devices"]
    check("recalc Devices TOTAL sessions = 202,793",
          v2["B7"].value == 202793, str(v2["B7"].value))
    check("recalc Devices TOTAL revenue = 12,910,349",
          v2["D7"].value == 12910349, str(v2["D7"].value))
    f2 = wb2["Funnel"]
    check("recalc Funnel purchases = 4,475",
          f2["B8"].value == 4475, str(f2["B8"].value))
    check("recalc Funnel cart rate ≈ 12.07%",
          abs(f2["C6"].value - 0.1207) < 0.001, str(f2["C6"].value))
    errors = []
    for ws in wb2.worksheets:
        for row in ws.iter_rows():
            for cell in row:
                if isinstance(cell.value, str) and cell.value.startswith("#"):
                    errors.append(f"{ws.title}!{cell.coordinate}={cell.value}")
    check("recalc workbook has no error values (#NAME?, #VALUE!, ...)",
          not errors, "; ".join(errors[:5]))
else:
    print(f"  NOTE: no LibreOffice recalc copy found at {RECALC} — "
          "recalc checks skipped")

# ── PDF ────────────────────────────────────────────────────────────────
check("traffic_report.pdf exists", PDF.exists())
if PDF.exists():
    info = subprocess.run(["pdfinfo", str(PDF)], capture_output=True,
                          text=True)
    pages = re.search(r"Pages:\s+(\d+)", info.stdout)
    check("PDF has exactly 2 pages",
          pages is not None and int(pages.group(1)) == 2,
          info.stdout.splitlines()[0] if info.stdout else "pdfinfo failed")
    text = subprocess.run(["pdftotext", str(PDF), "-"], capture_output=True,
                          text=True).stdout
    check("PDF text contains total sessions",
          "202,793" in text)
    check("PDF text contains total revenue",
          "12,910,349" in text)
    check("PDF text contains best channel",
          "Paid Search" in text)

print(f"\n{len(ran) - len(fails)}/{len(ran)} checks passed")
if fails:
    print("FAILURES:", fails)
    sys.exit(1)
