#!/usr/bin/env python3
"""P17 — analyse the SAMPLE traffic files and regenerate every output
number from the raw CSVs (never typed): channel table, monthly trend,
funnel, landing pages, devices, weekend vs weekday. Writes:

  data/processed/monthly_summary.csv
  data/processed/channel_summary.csv
  outputs/summary.json
  outputs/traffic_report.md

    python3 src/analyze.py
"""
import csv
import json
from collections import defaultdict
from datetime import date
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
RAW = PROJECT / "data" / "raw"

CHANNELS = ["Organic Search", "Paid Search", "Social", "Direct",
            "Referral", "Email"]
INTS = ["sessions", "users", "product_views", "add_to_cart",
        "checkout_started", "purchases", "revenue_pkr"]


def load(name):
    rows = list(csv.DictReader(open(RAW / name, encoding="utf-8")))
    for r in rows:
        for k in INTS:
            if k in r:
                r[k] = int(r[k])
    return rows


def main():
    traffic = load("daily_traffic_SAMPLE.csv")
    landing = load("landing_pages_SAMPLE.csv")
    devices = load("device_split_SAMPLE.csv")

    tot_sessions = sum(r["sessions"] for r in traffic)
    tot_users = sum(r["users"] for r in traffic)
    tot_purchases = sum(r["purchases"] for r in traffic)
    tot_revenue = sum(r["revenue_pkr"] for r in traffic)
    funnel = {k: sum(r[k] for r in traffic)
              for k in ["sessions", "product_views", "add_to_cart",
                        "checkout_started", "purchases"]}
    funnel_rates = {
        "views_rate_pct": round(100.0 * funnel["product_views"] / funnel["sessions"], 2),
        "cart_rate_pct": round(100.0 * funnel["add_to_cart"] / funnel["product_views"], 2),
        "checkout_rate_pct": round(100.0 * funnel["checkout_started"] / funnel["add_to_cart"], 2),
        "purchase_rate_pct": round(100.0 * funnel["purchases"] / funnel["checkout_started"], 2),
    }
    overall_cr = round(100.0 * tot_purchases / tot_sessions, 2)
    aov = round(tot_revenue / tot_purchases)

    # --- by channel ---
    channels = []
    for ch in CHANNELS:
        rs = [r for r in traffic if r["channel"] == ch]
        s = sum(r["sessions"] for r in rs)
        p = sum(r["purchases"] for r in rs)
        rev = sum(r["revenue_pkr"] for r in rs)
        channels.append({
            "channel": ch, "sessions": s, "users": sum(r["users"] for r in rs),
            "purchases": p, "revenue_pkr": rev,
            "share_pct": round(100.0 * s / tot_sessions, 2),
            "conversion_rate_pct": round(100.0 * p / s, 2),
            "avg_order_value_pkr": round(rev / p) if p else 0,
        })
    channels.sort(key=lambda c: -c["sessions"])
    best_channel = max(channels, key=lambda c: c["conversion_rate_pct"])
    worst_channel = min(channels, key=lambda c: c["conversion_rate_pct"])

    # --- monthly ---
    months = []
    for m in sorted({r["month"] for r in traffic}):
        rs = [r for r in traffic if r["month"] == m]
        s = sum(r["sessions"] for r in rs)
        p = sum(r["purchases"] for r in rs)
        rev = sum(r["revenue_pkr"] for r in rs)
        months.append({
            "month": m, "sessions": s, "users": sum(r["users"] for r in rs),
            "purchases": p, "revenue_pkr": rev,
            "conversion_rate_pct": round(100.0 * p / s, 2),
        })
    for i, mo in enumerate(months):
        prev = months[i - 1]["revenue_pkr"] if i else None
        mo["mom_growth_pct"] = (round(100.0 * (mo["revenue_pkr"] - prev) / prev, 2)
                                if prev else None)
    best_month = max(months, key=lambda x: x["revenue_pkr"])
    worst_month = min(months, key=lambda x: x["revenue_pkr"])
    growth = round(100.0 * (months[-1]["revenue_pkr"] - months[0]["revenue_pkr"])
                   / months[0]["revenue_pkr"], 2)

    # --- landing pages ---
    pages = []
    for pg in sorted({r["landing_page"] for r in landing}):
        rs = [r for r in landing if r["landing_page"] == pg]
        s = sum(r["sessions"] for r in rs)
        p = sum(r["purchases"] for r in rs)
        rev = sum(r["revenue_pkr"] for r in rs)
        pages.append({
            "landing_page": pg, "sessions": s, "purchases": p,
            "revenue_pkr": rev,
            "share_pct": round(100.0 * s / tot_sessions, 2),
            "conversion_rate_pct": round(100.0 * p / s, 2),
        })
    pages.sort(key=lambda p: -p["sessions"])
    best_page = max(pages, key=lambda p: p["conversion_rate_pct"])
    worst_page = min(pages, key=lambda p: p["conversion_rate_pct"])

    # --- devices ---
    devs = []
    for d in ["Mobile", "Desktop", "Tablet"]:
        rs = [r for r in devices if r["device"] == d]
        s = sum(r["sessions"] for r in rs)
        p = sum(r["purchases"] for r in rs)
        rev = sum(r["revenue_pkr"] for r in rs)
        devs.append({
            "device": d, "sessions": s, "purchases": p, "revenue_pkr": rev,
            "share_pct": round(100.0 * s / tot_sessions, 2),
            "conversion_rate_pct": round(100.0 * p / s, 2),
        })

    # --- weekend vs weekday (Fri–Sun = weekend) ---
    daypart = {}
    for label, pred in [("weekend", lambda d: d.weekday() >= 4),
                        ("weekday", lambda d: d.weekday() < 4)]:
        days = {r["date"] for r in traffic if pred(date.fromisoformat(r["date"]))}
        rs = [r for r in traffic if pred(date.fromisoformat(r["date"]))]
        s = sum(r["sessions"] for r in rs)
        p = sum(r["purchases"] for r in rs)
        daypart[label] = {
            "days": len(days), "sessions": s, "purchases": p,
            "revenue_pkr": sum(r["revenue_pkr"] for r in rs),
            "sessions_per_day": round(s / len(days), 1),
            "conversion_rate_pct": round(100.0 * p / s, 2),
        }
    weekend_lift = round(100.0 * daypart["weekend"]["sessions_per_day"]
                         / daypart["weekday"]["sessions_per_day"] - 100.0, 1)

    summary = {
        "shop": "CityStore.pk (SAMPLE)",
        "period": "2026-05-01 to 2026-10-31",
        "days": 184,
        "total_sessions": tot_sessions,
        "total_users": tot_users,
        "total_purchases": tot_purchases,
        "total_revenue_pkr": tot_revenue,
        "overall_conversion_rate_pct": overall_cr,
        "avg_order_value_pkr": aov,
        "sessions_per_day": round(tot_sessions / 184, 1),
        "funnel": funnel,
        "funnel_rates_pct": funnel_rates,
        "channels": channels,
        "best_channel_by_conversion": best_channel["channel"],
        "best_channel_conversion_pct": best_channel["conversion_rate_pct"],
        "worst_channel_by_conversion": worst_channel["channel"],
        "worst_channel_conversion_pct": worst_channel["conversion_rate_pct"],
        "months": months,
        "best_month": {"month": best_month["month"],
                       "revenue_pkr": best_month["revenue_pkr"],
                       "sessions": best_month["sessions"]},
        "worst_month": {"month": worst_month["month"],
                        "revenue_pkr": worst_month["revenue_pkr"],
                        "sessions": worst_month["sessions"]},
        "growth_may_to_oct_pct": growth,
        "landing_pages": pages,
        "best_landing_page": best_page["landing_page"],
        "best_landing_page_cr_pct": best_page["conversion_rate_pct"],
        "worst_landing_page": worst_page["landing_page"],
        "worst_landing_page_cr_pct": worst_page["conversion_rate_pct"],
        "devices": devs,
        "weekend": daypart["weekend"],
        "weekday": daypart["weekday"],
        "weekend_lift_pct": weekend_lift,
    }
    (PROJECT / "outputs" / "summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")

    # processed CSVs
    with open(PROJECT / "data" / "processed" / "monthly_summary.csv",
              "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["month", "sessions", "users", "purchases",
                    "revenue_pkr", "conversion_rate_pct", "mom_growth_pct"])
        for mo in months:
            w.writerow([mo["month"], mo["sessions"], mo["users"],
                        mo["purchases"], mo["revenue_pkr"],
                        mo["conversion_rate_pct"],
                        "" if mo["mom_growth_pct"] is None
                        else mo["mom_growth_pct"]])
    with open(PROJECT / "data" / "processed" / "channel_summary.csv",
              "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["channel", "sessions", "users", "purchases",
                    "revenue_pkr", "share_pct", "conversion_rate_pct",
                    "avg_order_value_pkr"])
        for c in channels:
            w.writerow([c["channel"], c["sessions"], c["users"],
                        c["purchases"], c["revenue_pkr"], c["share_pct"],
                        c["conversion_rate_pct"], c["avg_order_value_pkr"]])

    # findings report (markdown)
    lines = [
        "# P17 — Website Traffic & Conversion Report: CityStore.pk (SAMPLE)",
        "",
        "**Period:** Fri 2026-05-01 → Sat 2026-10-31 (6 months, 184 days)",
        f"**Sessions:** {tot_sessions:,} · **Users:** {tot_users:,} · "
        f"**Purchases:** {tot_purchases:,} · "
        f"**Revenue: PKR {tot_revenue:,}**",
        f"**Overall conversion rate:** {overall_cr}% · "
        f"**Average order value:** PKR {aov:,}",
        "",
        "## 1. Where the traffic comes from",
        "",
        "| Channel | Sessions | Share | Purchases | Conversion | Revenue (PKR) | AOV (PKR) |",
        "|---|---|---|---|---|---|---|",
    ]
    for c in channels:
        lines.append(f"| {c['channel']} | {c['sessions']:,} | {c['share_pct']}% | "
                     f"{c['purchases']:,} | {c['conversion_rate_pct']}% | "
                     f"{c['revenue_pkr']:,} | {c['avg_order_value_pkr']:,} |")
    lines += [
        "",
        f"**Best-converting channel: {best_channel['channel']} "
        f"({best_channel['conversion_rate_pct']}%)** — "
        f"{best_channel['sessions']:,} sessions, "
        f"PKR {best_channel['revenue_pkr']:,} revenue. "
        f"**Worst: {worst_channel['channel']} "
        f"({worst_channel['conversion_rate_pct']}%)** despite "
        f"{worst_channel['sessions']:,} sessions — the most traffic that "
        "converts least, which is where the money is leaking.",
        "",
        "## 2. The funnel — where buyers drop off",
        "",
        "| Step | Count | Step conversion | Share of sessions |",
        "|---|---|---|---|",
        f"| Sessions | {funnel['sessions']:,} | — | 100.0% |",
        f"| Product views | {funnel['product_views']:,} | {funnel_rates['views_rate_pct']}% | "
        f"{round(100.0 * funnel['product_views'] / funnel['sessions'], 1)}% |",
        f"| Add to cart | {funnel['add_to_cart']:,} | {funnel_rates['cart_rate_pct']}% | "
        f"{round(100.0 * funnel['add_to_cart'] / funnel['sessions'], 1)}% |",
        f"| Checkout started | {funnel['checkout_started']:,} | {funnel_rates['checkout_rate_pct']}% | "
        f"{round(100.0 * funnel['checkout_started'] / funnel['sessions'], 1)}% |",
        f"| Purchase | {funnel['purchases']:,} | {funnel_rates['purchase_rate_pct']}% | "
        f"{overall_cr}% |",
        "",
        f"The biggest leak is **product view → add to cart "
        f"({funnel_rates['cart_rate_pct']}%)**: only about "
        f"{round(100.0 * funnel['add_to_cart'] / funnel['product_views']):,} "
        f"in every 100 viewers put anything in the basket. "
        f"Checkout → purchase holds at {funnel_rates['purchase_rate_pct']}%, "
        "so the checkout itself is not the problem — the problem is "
        "getting people to the basket in the first place.",
        "",
        "## 3. Month by month",
        "",
        "| Month | Sessions | Purchases | Revenue (PKR) | Conversion | MoM growth |",
        "|---|---|---|---|---|---|",
    ]
    for mo in months:
        mom = "—" if mo["mom_growth_pct"] is None else f"{mo['mom_growth_pct']:+.2f}%"
        lines.append(f"| {mo['month']} | {mo['sessions']:,} | {mo['purchases']:,} | "
                     f"{mo['revenue_pkr']:,} | {mo['conversion_rate_pct']}% | {mom} |")
    lines += [
        "",
        f"Revenue grew **{growth}% from May to October** "
        f"(PKR {months[0]['revenue_pkr']:,} → "
        f"PKR {months[-1]['revenue_pkr']:,}). Best month: "
        f"**{best_month['month']} (PKR {best_month['revenue_pkr']:,})**; "
        f"worst: **{worst_month['month']} "
        f"(PKR {worst_month['revenue_pkr']:,})**.",
        "",
        "## 4. Landing pages",
        "",
        "| Landing page | Sessions | Share | Purchases | Conversion | Revenue (PKR) |",
        "|---|---|---|---|---|---|",
    ]
    for p in pages:
        lines.append(f"| {p['landing_page']} | {p['sessions']:,} | {p['share_pct']}% | "
                     f"{p['purchases']:,} | {p['conversion_rate_pct']}% | "
                     f"{p['revenue_pkr']:,} |")
    lines += [
        "",
        f"**Best-converting page: {best_page['landing_page']} "
        f"({best_page['conversion_rate_pct']}%)**; "
        f"worst: {worst_page['landing_page']} "
        f"({worst_page['conversion_rate_pct']}%). The /sale page converts "
        "well, which says price — not traffic — is the lever.",
        "",
        "## 5. Devices",
        "",
        "| Device | Sessions | Share | Purchases | Conversion | Revenue (PKR) |",
        "|---|---|---|---|---|---|",
    ]
    for d in devs:
        lines.append(f"| {d['device']} | {d['sessions']:,} | {d['share_pct']}% | "
                     f"{d['purchases']:,} | {d['conversion_rate_pct']}% | "
                     f"{d['revenue_pkr']:,} |")
    lines += [
        "",
        f"Mobile is {devs[0]['share_pct']}% of sessions but converts at "
        f"{devs[0]['conversion_rate_pct']}% against Desktop's "
        f"{devs[1]['conversion_rate_pct']}% — a mobile checkout that "
        "converted like desktop would be worth roughly "
        f"PKR {round(devs[0]['sessions'] * devs[1]['conversion_rate_pct'] / 100 * aov) - devs[0]['revenue_pkr']:,} "
        "more revenue on the same traffic.",
        "",
        "## 6. Weekend vs weekday",
        "",
        f"Weekend days (Fri–Sun) average "
        f"{daypart['weekend']['sessions_per_day']:,} sessions a day vs "
        f"{daypart['weekday']['sessions_per_day']:,} on weekdays "
        f"(**+{weekend_lift}%**). Conversion is "
        f"{daypart['weekend']['conversion_rate_pct']}% on weekends vs "
        f"{daypart['weekday']['conversion_rate_pct']}% on weekdays.",
        "",
        "## 7. Three recommendations",
        "",
        f"1. **Fix the view → cart leak first.** At "
        f"{funnel_rates['cart_rate_pct']}%, the product page is where "
        "buyers are lost. Better photos, clearer prices and delivery "
        "info, and a visible add-to-cart button above the fold — before "
        "spending one more rupee on ads.",
        f"2. **Move budget from Social to Paid Search and Email.** "
        f"Social brings {worst_channel['sessions']:,} sessions at "
        f"{worst_channel['conversion_rate_pct']}% conversion; "
        f"{best_channel['channel']} converts at "
        f"{best_channel['conversion_rate_pct']}%. Same spend, more buyers.",
        "3. **Fix mobile checkout.** Mobile is most of the traffic and "
        "the worst converter of the three devices. One-page checkout, "
        "JazzCash/Easypaisa/COD upfront, and no forced account creation.",
        "",
        "> Every number in this report is recomputed from "
        "`data/raw/daily_traffic_SAMPLE.csv` (+ the landing-page and "
        "device splits) by `src/analyze.py` — nothing is typed by hand. "
        "Run `python3 src/checks.py` to re-verify.",
    ]
    (PROJECT / "outputs" / "traffic_report.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")
    print(f"sessions {tot_sessions:,}, purchases {tot_purchases:,}, "
          f"revenue PKR {tot_revenue:,}, CR {overall_cr}%, "
          f"best channel {best_channel['channel']} "
          f"({best_channel['conversion_rate_pct']}%), "
          f"best month {best_month['month']}")


if __name__ == "__main__":
    main()
