#!/usr/bin/env python3
"""Build the P17 deliverables from the SAMPLE traffic data.

Recomputes every number from outputs/summary.json (itself recomputed
from the raw CSVs by src/analyze.py — nothing is typed in by hand)
and produces:
  * outputs/monthly_revenue.png — monthly revenue chart (matplotlib)
  * outputs/traffic_report.pdf — 2-page client report (key findings,
    channel table, funnel, monthly table, 3 recommendations)

Run:  python3 src/build_report.py
"""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parent.parent
SUMMARY = ROOT / "outputs" / "summary.json"
CHART = ROOT / "outputs" / "monthly_revenue.png"
PDF = ROOT / "outputs" / "traffic_report.pdf"

s = json.loads(SUMMARY.read_text(encoding="utf-8"))
TOT_S = s["total_sessions"]
TOT_P = s["total_purchases"]
TOT_R = s["total_revenue_pkr"]
CR = s["overall_conversion_rate_pct"]
AOV = s["avg_order_value_pkr"]
F = s["funnel"]
FR = s["funnel_rates_pct"]
CH = s["channels"]
BEST_CH = max(CH, key=lambda c: c["conversion_rate_pct"])
WORST_CH = min(CH, key=lambda c: c["conversion_rate_pct"])
MO = s["months"]
PAGES = s["landing_pages"]
DEVS = s["devices"]
MOBILE = DEVS[0]
DESKTOP = DEVS[1]

# monthly revenue chart
plt.figure(figsize=(8, 3.2))
plt.bar([m["month"] for m in MO], [m["revenue_pkr"] for m in MO],
        color="#1F4E79")
plt.title("Monthly revenue — CityStore.pk (SAMPLE, May–Oct 2026)")
plt.ylabel("PKR")
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig(CHART, dpi=150)
plt.close()

styles = getSampleStyleSheet()
hdr = colors.HexColor("#1F4E79")


def table(rows, widths, size=9):
    t = Table(rows, colWidths=widths)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), hdr),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), size),
    ]))
    return t


story = [
    Paragraph("CityStore.pk — Website Traffic &amp; Conversion Report",
              styles["Title"]),
    Paragraph("GA4-style analytics · 1 May – 31 Oct 2026 (6 months, "
              "184 days) · SAMPLE data — fictional online store, "
              "generated for this delivery (seed 20261113)",
              styles["Normal"]),
    Spacer(1, 0.4 * cm),
    Paragraph(
        f"Headline: <b>{TOT_S:,} sessions</b> from "
        f"<b>{s['total_users']:,} users</b> produced "
        f"<b>{TOT_P:,} purchases</b> worth "
        f"<b>PKR {TOT_R:,}</b> — an overall conversion rate of "
        f"<b>{CR}%</b> and an average order value of "
        f"<b>PKR {AOV:,}</b>. Revenue grew "
        f"<b>{s['growth_may_to_oct_pct']}% from May to October</b>.",
        styles["Normal"]),
    Spacer(1, 0.4 * cm),
    Paragraph("<b>Where the traffic comes from</b>", styles["Heading2"]),
]
ch_rows = [["Channel", "Sessions", "Share", "Purchases", "Conv.",
            "Revenue (PKR)", "AOV (PKR)"]]
for c in CH:
    ch_rows.append([c["channel"], f"{c['sessions']:,}",
                    f"{c['share_pct']}%", f"{c['purchases']:,}",
                    f"{c['conversion_rate_pct']}%",
                    f"{c['revenue_pkr']:,}",
                    f"{c['avg_order_value_pkr']:,}"])
story.append(table(ch_rows, [3.4 * cm, 2.2 * cm, 1.4 * cm, 2.0 * cm,
                            1.6 * cm, 3.0 * cm, 2.2 * cm]))
story.append(Spacer(1, 0.3 * cm))
story.append(Paragraph(
    f"<b>{BEST_CH['channel']}</b> converts best at "
    f"<b>{BEST_CH['conversion_rate_pct']}%</b>; "
    f"<b>{WORST_CH['channel']}</b> converts worst at "
    f"<b>{WORST_CH['conversion_rate_pct']}%</b> despite "
    f"{WORST_CH['sessions']:,} sessions — the most traffic that "
    "converts least. That gap is the first budget decision.",
    styles["Normal"]))
story.append(Spacer(1, 0.4 * cm))
story.append(Paragraph("<b>The funnel — where buyers drop off</b>",
                       styles["Heading2"]))
fu_rows = [["Step", "Count", "Step conversion", "Share of sessions"]]
labels = [("Sessions", "sessions"), ("Product views", "product_views"),
          ("Add to cart", "add_to_cart"),
          ("Checkout started", "checkout_started"),
          ("Purchase", "purchases")]
rates = ["—", f"{FR['views_rate_pct']}%",
         f"{FR['cart_rate_pct']}%", f"{FR['checkout_rate_pct']}%",
         f"{FR['purchase_rate_pct']}%"]
for (label, key), rate in zip(labels, rates):
    fu_rows.append([label, f"{F[key]:,}", rate,
                    f"{round(100.0 * F[key] / F['sessions'], 1)}%"])
story.append(table(fu_rows, [4.5 * cm, 3.0 * cm, 4.0 * cm, 4.3 * cm]))
story.append(Spacer(1, 0.3 * cm))
story.append(Paragraph(
    f"The biggest leak is <b>product view → add to cart "
    f"({FR['cart_rate_pct']}%)</b>: only about "
    f"{round(FR['cart_rate_pct']):,} in every 100 viewers reach the "
    "basket. Checkout → purchase holds at "
    f"{FR['purchase_rate_pct']}%, so the checkout itself is not the "
    "problem — the product page is.",
    styles["Normal"]))
story.append(Spacer(1, 0.4 * cm))
story.append(Paragraph("<b>Month by month</b>", styles["Heading2"]))
mo_rows = [["Month", "Sessions", "Purchases", "Revenue (PKR)", "Conv.",
            "MoM growth"]]
for m in MO:
    mom = "—" if m["mom_growth_pct"] is None else f"{m['mom_growth_pct']:+.2f}%"
    mo_rows.append([m["month"], f"{m['sessions']:,}",
                    f"{m['purchases']:,}", f"{m['revenue_pkr']:,}",
                    f"{m['conversion_rate_pct']}%", mom])
story.append(table(mo_rows, [2.4 * cm, 2.6 * cm, 2.4 * cm, 3.2 * cm,
                            1.8 * cm, 2.6 * cm]))
story.append(Spacer(1, 0.3 * cm))
story.append(Image(str(CHART), width=15.5 * cm, height=6.2 * cm))
story.append(Spacer(1, 0.4 * cm))
story.append(Paragraph(
    f"Best month: <b>{s['best_month']['month']} "
    f"(PKR {s['best_month']['revenue_pkr']:,})</b>; worst: "
    f"<b>{s['worst_month']['month']} "
    f"(PKR {s['worst_month']['revenue_pkr']:,})</b>. Weekend days "
    f"(Fri–Sun) average {s['weekend']['sessions_per_day']:,} sessions "
    f"a day vs {s['weekday']['sessions_per_day']:,} on weekdays "
    f"(+{s['weekend_lift_pct']}%).",
    styles["Normal"]))
story.append(Spacer(1, 0.4 * cm))
story.append(Paragraph("<b>Landing pages &amp; devices</b>",
                       styles["Heading2"]))
story.append(Paragraph(
    f"Best-converting page: <b>{s['best_landing_page']} "
    f"({s['best_landing_page_cr_pct']}%)</b>; worst: "
    f"{s['worst_landing_page']} ({s['worst_landing_page_cr_pct']}%). "
    f"Mobile is {MOBILE['share_pct']}% of sessions but converts at "
    f"{MOBILE['conversion_rate_pct']}% against Desktop's "
    f"{DESKTOP['conversion_rate_pct']}%. If mobile converted like "
    f"desktop, the same traffic would be worth roughly "
    f"PKR {round(MOBILE['sessions'] * DESKTOP['conversion_rate_pct'] / 100 * AOV) - MOBILE['revenue_pkr']:,} "
    "more revenue.",
    styles["Normal"]))
story.append(Spacer(1, 0.4 * cm))
story.append(Paragraph("<b>3 recommendations</b>", styles["Heading2"]))
recs = [
    f"1. <b>Fix the view → cart leak first ({FR['cart_rate_pct']}%).</b> "
    "Better photos, clearer prices and delivery info, and a visible "
    "add-to-cart button above the fold — before spending one more "
    "rupee on ads.",
    f"2. <b>Move budget from {WORST_CH['channel']} to "
    f"{BEST_CH['channel']}.</b> {WORST_CH['channel']} brings "
    f"{WORST_CH['sessions']:,} sessions at "
    f"{WORST_CH['conversion_rate_pct']}% conversion; "
    f"{BEST_CH['channel']} converts at "
    f"{BEST_CH['conversion_rate_pct']}%. Same spend, more buyers.",
    "3. <b>Fix mobile checkout.</b> Mobile is most of the traffic "
    "and the worst converter of the three devices. One-page checkout, "
    "JazzCash / Easypaisa / COD upfront, no forced account creation.",
]
for r in recs:
    story.append(Paragraph(r, styles["Normal"]))
    story.append(Spacer(1, 0.15 * cm))
story.append(Spacer(1, 0.3 * cm))
story.append(Paragraph(
    "Method: every number above is recomputed from "
    "data/raw/daily_traffic_SAMPLE.csv (+ the landing-page and device "
    "splits) by src/analyze.py and verified by src/checks.py. The "
    "workbook (outputs/website_traffic_report_SAMPLE.xlsx) carries the "
    "same numbers as live formulas. Chart is a render of the same "
    "data, not a GA4 screenshot.",
    styles["Normal"]))
SimpleDocTemplate(str(PDF), pagesize=A4,
                  title="CityStore.pk — Website Traffic & Conversion "
                        "Report (SAMPLE)",
                  author="Muhammad Hashir",
                  topMargin=1.6 * cm, bottomMargin=1.6 * cm).build(story)
print(f"chart: {CHART}")
print(f"report: {PDF}")
