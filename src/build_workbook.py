#!/usr/bin/env python3
"""P17 — build the deliverable workbook for CityStore.pk:

  Dashboard      — KPIs + monthly trend, all live formulas over Data;
                   best/worst month via MAXIFS/MINIFS (written with the
                   _xlfn. prefix so LibreOffice and Excel calculate them)
  Channels       — 6 channels x sessions/share/purchases/conversion/
                   revenue/AOV, live SUMIFS over Data
  Landing Pages  — 8 pages, live SUMIFS over LandingData
  Devices        — 3 devices, live SUMIFS over DeviceData
  Funnel         — the 5-step funnel, live SUMs + step conversions
  Data           — all 1,104 date x channel rows (values)
  LandingData    — all 1,472 date x landing-page rows (values)
  DeviceData     — all 552 date x device rows (values)
  Method         — how to read it, parameters, how to re-verify

    python3 src/build_workbook.py
"""
import csv
import json
from pathlib import Path

from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Alignment, Font, PatternFill

PROJECT = Path(__file__).resolve().parent.parent
RAW = PROJECT / "data" / "raw"
SUMMARY = PROJECT / "outputs" / "summary.json"
OUT = PROJECT / "outputs" / "website_traffic_report_SAMPLE.xlsx"

CHANNELS = ["Organic Search", "Paid Search", "Social", "Direct",
            "Referral", "Email"]
PAGES = ["/", "/sale", "/mobile-phones", "/fashion/men",
         "/fashion/women", "/home-kitchen", "/beauty", "/electronics"]
DEVICES = ["Mobile", "Desktop", "Tablet"]
MONTHS = ["2026-05", "2026-06", "2026-07", "2026-08", "2026-09", "2026-10"]
HDR_FILL = PatternFill("solid", fgColor="1F4E79")
HDR_FONT = Font(bold=True, color="FFFFFF", size=11)
TITLE_FONT = Font(bold=True, size=14, color="1F4E79")
MONEY_FMT = "#,##0"
PCT_FMT = "0.00%"


def style_header(ws, ncols, row=1):
    for c in range(1, ncols + 1):
        cell = ws.cell(row=row, column=c)
        cell.fill = HDR_FILL
        cell.font = HDR_FONT


def main():
    traffic = list(csv.DictReader(
        open(RAW / "daily_traffic_SAMPLE.csv", encoding="utf-8")))
    landing = list(csv.DictReader(
        open(RAW / "landing_pages_SAMPLE.csv", encoding="utf-8")))
    devices = list(csv.DictReader(
        open(RAW / "device_split_SAMPLE.csv", encoding="utf-8")))
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    n, nl, nd = len(traffic), len(landing), len(devices)
    last, last_l, last_d = n + 1, nl + 1, nd + 1  # last data rows

    wb = Workbook()

    # ── Data (date x channel, values) ──────────────────────────────────
    data = wb.active
    data.title = "Data"
    data.append(["date", "month", "channel", "sessions", "users",
                 "product_views", "add_to_cart", "checkout_started",
                 "purchases", "revenue_pkr"])
    for r in traffic:
        data.append([r["date"], r["month"], r["channel"],
                     int(r["sessions"]), int(r["users"]),
                     int(r["product_views"]), int(r["add_to_cart"]),
                     int(r["checkout_started"]), int(r["purchases"]),
                     int(r["revenue_pkr"])])
    style_header(data, 10)
    data.freeze_panes = "A2"
    for col, w in zip("ABCDEFGHIJ",
                      [12, 9, 16, 11, 10, 14, 12, 16, 11, 13]):
        data.column_dimensions[col].width = w
    for r in range(2, last + 1):
        for c in range(4, 11):
            data.cell(row=r, column=c).number_format = MONEY_FMT

    # ── LandingData / DeviceData (values) ──────────────────────────────
    ld = wb.create_sheet("LandingData")
    ld.append(["date", "month", "landing_page", "sessions", "purchases",
               "revenue_pkr"])
    for r in landing:
        ld.append([r["date"], r["month"], r["landing_page"],
                   int(r["sessions"]), int(r["purchases"]),
                   int(r["revenue_pkr"])])
    style_header(ld, 6)
    ld.freeze_panes = "A2"
    for col, w in zip("ABCDEF", [12, 9, 16, 11, 11, 13]):
        ld.column_dimensions[col].width = w

    dd = wb.create_sheet("DeviceData")
    dd.append(["date", "month", "device", "sessions", "purchases",
               "revenue_pkr"])
    for r in devices:
        dd.append([r["date"], r["month"], r["device"],
                   int(r["sessions"]), int(r["purchases"]),
                   int(r["revenue_pkr"])])
    style_header(dd, 6)
    dd.freeze_panes = "A2"
    for col, w in zip("ABCDEF", [12, 9, 12, 11, 11, 13]):
        dd.column_dimensions[col].width = w

    # ── Dashboard ──────────────────────────────────────────────────────
    dash = wb.create_sheet("Dashboard", 0)
    dash["A1"] = "Website Traffic & Conversion — CityStore.pk (SAMPLE)"
    dash["A1"].font = TITLE_FONT
    dash["A2"] = ("6 months, 2026-05-01 → 2026-10-31 · every number below "
                  "is a live formula over the Data sheets — change the "
                  "data and the report rebuilds itself.")
    dash["A2"].font = Font(italic=True, size=10, color="595959")
    dash["A4"] = "Key metrics"
    dash["A4"].font = Font(bold=True, size=12, color="1F4E79")
    kpis = [
        ("Total sessions", f"=SUM(Data!D2:D{last})", MONEY_FMT),
        ("Total users", f"=SUM(Data!E2:E{last})", MONEY_FMT),
        ("Product views", f"=SUM(Data!F2:F{last})", MONEY_FMT),
        ("Add to cart", f"=SUM(Data!G2:G{last})", MONEY_FMT),
        ("Purchases", f"=SUM(Data!I2:I{last})", MONEY_FMT),
        ("Total revenue (PKR)", f"=SUM(Data!J2:J{last})", MONEY_FMT),
        ("Overall conversion rate", "=B9/B5", PCT_FMT),
        ("Average order value (PKR)", "=B10/B9", MONEY_FMT),
    ]
    for i, (label, formula, fmt) in enumerate(kpis):
        r = 5 + i
        dash.cell(row=r, column=1, value=label)
        c = dash.cell(row=r, column=2, value=formula)
        c.number_format = fmt
        c.font = Font(bold=True)
    # KPI rows: 5 sessions, 6 users, 7 views, 8 cart, 9 purchases,
    # 10 revenue, 11 conversion (=B9/B5), 12 AOV (=B10/B9)
    dash.column_dimensions["A"].width = 28
    dash.column_dimensions["B"].width = 18
    dash.column_dimensions["C"].width = 44
    dash["C5"] = "Sessions = every visit to the store, GA4-style."
    dash["C11"] = "Purchases ÷ sessions — the headline number."
    dash["C12"] = "Revenue ÷ purchases."

    tr = 15  # monthly trend table header row
    dash.cell(row=tr, column=1, value="Monthly trend").font = Font(
        bold=True, size=12, color="1F4E79")
    headers = ["Month", "Sessions", "Users", "Purchases", "Revenue (PKR)",
               "Conversion", "MoM growth"]
    for c, h in enumerate(headers, start=1):
        dash.cell(row=tr + 1, column=c, value=h)
    style_header(dash, 7, row=tr + 1)
    dash.freeze_panes = "A17"
    for i, m in enumerate(MONTHS):
        r = tr + 2 + i  # rows 17..22
        dash.cell(row=r, column=1, value=m)
        dash.cell(row=r, column=2).value = (
            f"=SUMIFS(Data!$D$2:$D${last},Data!$B$2:$B${last},A{r})")
        dash.cell(row=r, column=3).value = (
            f"=SUMIFS(Data!$E$2:$E${last},Data!$B$2:$B${last},A{r})")
        dash.cell(row=r, column=4).value = (
            f"=SUMIFS(Data!$I$2:$I${last},Data!$B$2:$B${last},A{r})")
        dash.cell(row=r, column=5).value = (
            f"=SUMIFS(Data!$J$2:$J${last},Data!$B$2:$B${last},A{r})")
        dash.cell(row=r, column=5).number_format = MONEY_FMT
        dash.cell(row=r, column=6).value = f"=IF(B{r}=0,0,D{r}/B{r})"
        dash.cell(row=r, column=6).number_format = PCT_FMT
        if i == 0:
            dash.cell(row=r, column=7, value="—")
        else:
            dash.cell(row=r, column=7).value = (
                f"=IF(E{r-1}=0,\"—\",E{r}/E{r-1}-1)")
            dash.cell(row=r, column=7).number_format = PCT_FMT
    t = tr + 2 + len(MONTHS)  # total row = 23
    dash.cell(row=t, column=1, value="TOTAL (6 months)").font = Font(bold=True)
    for col, letter in [(2, "B"), (3, "C"), (4, "D"), (5, "E")]:
        dash.cell(row=t, column=col).value = (
            f"=SUM({letter}{tr+2}:{letter}{t-1})")
        if col == 5:
            dash.cell(row=t, column=col).number_format = MONEY_FMT
    dash.cell(row=t, column=6).value = f"=D{t}/B{t}"
    dash.cell(row=t, column=6).number_format = PCT_FMT

    # best / worst month via MAXIFS / MINIFS over the monthly table
    bw = t + 2  # row 25
    dash.cell(row=bw, column=1,
             value="Best month revenue (PKR)").font = Font(bold=True)
    dash.cell(row=bw, column=2).value = (
        f"=_xlfn.MAXIFS(E{tr+2}:E{t-1},B{tr+2}:B{t-1},\">0\")")
    dash.cell(row=bw, column=2).number_format = MONEY_FMT
    dash.cell(row=bw, column=3).value = (
        f"=INDEX(A{tr+2}:A{t-1},MATCH(B{bw},E{tr+2}:E{t-1},0))")
    dash.cell(row=bw + 1, column=1,
             value="Worst month revenue (PKR)").font = Font(bold=True)
    dash.cell(row=bw + 1, column=2).value = (
        f"=_xlfn.MINIFS(E{tr+2}:E{t-1},B{tr+2}:B{t-1},\">0\")")
    dash.cell(row=bw + 1, column=2).number_format = MONEY_FMT
    dash.cell(row=bw + 1, column=3).value = (
        f"=INDEX(A{tr+2}:A{t-1},MATCH(B{bw+1},E{tr+2}:E{t-1},0))")
    for col, w in zip("ABCDEFG", [14, 13, 12, 12, 15, 12, 12]):
        dash.column_dimensions[col].width = w

    chart = BarChart()
    chart.type = "col"
    chart.title = "Monthly revenue (PKR)"
    chart.y_axis.title = "PKR"
    chart.x_axis.title = "Month"
    chart.data = Reference(dash, min_col=5, min_row=tr + 1, max_row=t - 1)
    chart.categories = Reference(dash, min_col=1, min_row=tr + 2,
                                 max_row=t - 1)
    chart.height, chart.width = 7.5, 15
    dash.add_chart(chart, f"A{bw + 3}")

    # ── Channels ───────────────────────────────────────────────────────
    ch = wb.create_sheet("Channels")
    ch["A1"] = "Sessions by channel — live SUMIFS over Data"
    ch["A1"].font = TITLE_FONT
    for c, h in enumerate(["Channel", "Sessions", "Users", "Purchases",
                           "Revenue (PKR)", "Share", "Conversion",
                           "AOV (PKR)"], start=1):
        ch.cell(row=3, column=c, value=h)
    style_header(ch, 8, row=3)
    ch.freeze_panes = "A4"
    for i, name in enumerate(CHANNELS):
        r = 4 + i
        ch.cell(row=r, column=1, value=name)
        ch.cell(row=r, column=2).value = (
            f"=SUMIFS(Data!$D$2:$D${last},Data!$C$2:$C${last},A{r})")
        ch.cell(row=r, column=3).value = (
            f"=SUMIFS(Data!$E$2:$E${last},Data!$C$2:$C${last},A{r})")
        ch.cell(row=r, column=4).value = (
            f"=SUMIFS(Data!$I$2:$I${last},Data!$C$2:$C${last},A{r})")
        ch.cell(row=r, column=5).value = (
            f"=SUMIFS(Data!$J$2:$J${last},Data!$C$2:$C${last},A{r})")
        ch.cell(row=r, column=5).number_format = MONEY_FMT
        ch.cell(row=r, column=6).value = f"=B{r}/B$10"
        ch.cell(row=r, column=6).number_format = PCT_FMT
        ch.cell(row=r, column=7).value = f"=IF(B{r}=0,0,D{r}/B{r})"
        ch.cell(row=r, column=7).number_format = PCT_FMT
        ch.cell(row=r, column=8).value = f"=IF(D{r}=0,0,E{r}/D{r})"
        ch.cell(row=r, column=8).number_format = MONEY_FMT
    t = 4 + len(CHANNELS)  # total row = 10
    ch.cell(row=t, column=1, value="TOTAL").font = Font(bold=True)
    for col, letter in [(2, "B"), (3, "C"), (4, "D"), (5, "E")]:
        ch.cell(row=t, column=col).value = f"=SUM({letter}4:{letter}{t-1})"
        if col == 5:
            ch.cell(row=t, column=col).number_format = MONEY_FMT
    ch.cell(row=t, column=6).value = f"=B{t}/B{t}"
    ch.cell(row=t, column=6).number_format = PCT_FMT
    ch.cell(row=t, column=7).value = f"=D{t}/B{t}"
    ch.cell(row=t, column=7).number_format = PCT_FMT
    ch.cell(row=t, column=8).value = f"=E{t}/D{t}"
    ch.cell(row=t, column=8).number_format = MONEY_FMT
    for col, w in zip("ABCDEFGH", [16, 12, 11, 11, 15, 9, 11, 11]):
        ch.column_dimensions[col].width = w

    # ── Landing Pages ──────────────────────────────────────────────────
    lp = wb.create_sheet("Landing Pages")
    lp["A1"] = "Top landing pages — live SUMIFS over LandingData"
    lp["A1"].font = TITLE_FONT
    for c, h in enumerate(["Landing page", "Sessions", "Purchases",
                           "Revenue (PKR)", "Share", "Conversion"],
                          start=1):
        lp.cell(row=3, column=c, value=h)
    style_header(lp, 6, row=3)
    lp.freeze_panes = "A4"
    order = [p["landing_page"] for p in sorted(
        summary["landing_pages"], key=lambda x: -x["sessions"])]
    for i, page in enumerate(order):
        r = 4 + i
        lp.cell(row=r, column=1, value=page)
        lp.cell(row=r, column=2).value = (
            f"=SUMIFS(LandingData!$D$2:$D${last_l},"
            f"LandingData!$C$2:$C${last_l},A{r})")
        lp.cell(row=r, column=3).value = (
            f"=SUMIFS(LandingData!$E$2:$E${last_l},"
            f"LandingData!$C$2:$C${last_l},A{r})")
        lp.cell(row=r, column=4).value = (
            f"=SUMIFS(LandingData!$F$2:$F${last_l},"
            f"LandingData!$C$2:$C${last_l},A{r})")
        lp.cell(row=r, column=4).number_format = MONEY_FMT
        lp.cell(row=r, column=5).value = f"=B{r}/B$12"
        lp.cell(row=r, column=5).number_format = PCT_FMT
        lp.cell(row=r, column=6).value = f"=IF(B{r}=0,0,C{r}/B{r})"
        lp.cell(row=r, column=6).number_format = PCT_FMT
    t = 4 + len(order)  # total row = 12
    lp.cell(row=t, column=1, value="TOTAL").font = Font(bold=True)
    for col, letter in [(2, "B"), (3, "C"), (4, "D")]:
        lp.cell(row=t, column=col).value = f"=SUM({letter}4:{letter}{t-1})"
        if col == 4:
            lp.cell(row=t, column=col).number_format = MONEY_FMT
    lp.cell(row=t, column=5).value = f"=B{t}/B{t}"
    lp.cell(row=t, column=5).number_format = PCT_FMT
    lp.cell(row=t, column=6).value = f"=C{t}/B{t}"
    lp.cell(row=t, column=6).number_format = PCT_FMT
    for col, w in zip("ABCDEF", [16, 12, 11, 15, 9, 11]):
        lp.column_dimensions[col].width = w

    # ── Devices ────────────────────────────────────────────────────────
    dv = wb.create_sheet("Devices")
    dv["A1"] = "Sessions by device — live SUMIFS over DeviceData"
    dv["A1"].font = TITLE_FONT
    for c, h in enumerate(["Device", "Sessions", "Purchases",
                           "Revenue (PKR)", "Share", "Conversion"],
                          start=1):
        dv.cell(row=3, column=c, value=h)
    style_header(dv, 6, row=3)
    dv.freeze_panes = "A4"
    for i, name in enumerate(DEVICES):
        r = 4 + i
        dv.cell(row=r, column=1, value=name)
        dv.cell(row=r, column=2).value = (
            f"=SUMIFS(DeviceData!$D$2:$D${last_d},"
            f"DeviceData!$C$2:$C${last_d},A{r})")
        dv.cell(row=r, column=3).value = (
            f"=SUMIFS(DeviceData!$E$2:$E${last_d},"
            f"DeviceData!$C$2:$C${last_d},A{r})")
        dv.cell(row=r, column=4).value = (
            f"=SUMIFS(DeviceData!$F$2:$F${last_d},"
            f"DeviceData!$C$2:$C${last_d},A{r})")
        dv.cell(row=r, column=4).number_format = MONEY_FMT
        dv.cell(row=r, column=5).value = f"=B{r}/B$7"
        dv.cell(row=r, column=5).number_format = PCT_FMT
        dv.cell(row=r, column=6).value = f"=IF(B{r}=0,0,C{r}/B{r})"
        dv.cell(row=r, column=6).number_format = PCT_FMT
    t = 4 + len(DEVICES)  # total row = 7
    dv.cell(row=t, column=1, value="TOTAL").font = Font(bold=True)
    for col, letter in [(2, "B"), (3, "C"), (4, "D")]:
        dv.cell(row=t, column=col).value = f"=SUM({letter}4:{letter}{t-1})"
        if col == 4:
            dv.cell(row=t, column=col).number_format = MONEY_FMT
    dv.cell(row=t, column=5).value = f"=B{t}/B{t}"
    dv.cell(row=t, column=5).number_format = PCT_FMT
    dv.cell(row=t, column=6).value = f"=C{t}/B{t}"
    dv.cell(row=t, column=6).number_format = PCT_FMT
    for col, w in zip("ABCDEF", [12, 12, 11, 15, 9, 11]):
        dv.column_dimensions[col].width = w

    # ── Funnel ─────────────────────────────────────────────────────────
    fu = wb.create_sheet("Funnel")
    fu["A1"] = "Conversion funnel — live SUMs over Data"
    fu["A1"].font = TITLE_FONT
    for c, h in enumerate(["Step", "Count", "Step conversion",
                           "Share of sessions"], start=1):
        fu.cell(row=3, column=c, value=h)
    style_header(fu, 4, row=3)
    fu.freeze_panes = "A4"
    steps = [("Sessions", "D"), ("Product views", "F"),
             ("Add to cart", "G"), ("Checkout started", "H"),
             ("Purchases", "I")]
    for i, (label, col) in enumerate(steps):
        r = 4 + i
        fu.cell(row=r, column=1, value=label)
        fu.cell(row=r, column=2).value = f"=SUM(Data!{col}2:{col}{last})"
        fu.cell(row=r, column=2).number_format = MONEY_FMT
        if i == 0:
            fu.cell(row=r, column=3, value="—")
        else:
            fu.cell(row=r, column=3).value = f"=B{r}/B{r-1}"
            fu.cell(row=r, column=3).number_format = PCT_FMT
        fu.cell(row=r, column=4).value = f"=B{r}/B$4"
        fu.cell(row=r, column=4).number_format = PCT_FMT
    for col, w in zip("ABCD", [18, 13, 17, 18]):
        fu.column_dimensions[col].width = w
    fu["A10"] = ("Biggest leak: product view → add to cart. Only about "
                 "12 in every 100 viewers reach the basket — fix the "
                 "product page before spending more on ads.")
    fu["A10"].alignment = Alignment(wrap_text=True, vertical="top")
    fu.merge_cells("A10:D11")
    fu.row_dimensions[10].height = 30

    # ── Method ─────────────────────────────────────────────────────────
    m = wb.create_sheet("Method")
    m["A1"] = "How this report is built"
    m["A1"].font = TITLE_FONT
    lines = [
        ("What this is", "A GA4-style traffic & conversion report for "
         "CityStore.pk, a fictional Pakistani online general store. "
         "6 months, 2026-05-01 → 2026-10-31, 184 days, 6 channels, "
         "8 landing pages, 3 devices."),
        ("Data", f"SAMPLE: {n:,} date x channel rows, {nl:,} landing-page "
         f"rows, {nd:,} device rows. Generated by src/generate_data.py "
         "(seed 20261113). Demo data, never claimed as real client work."),
        ("Live formulas", "Every KPI, channel, page, device and funnel "
         "number is a live SUMIFS/SUM formula over the Data sheets — "
         "paste a real GA4 export in the same columns and the report "
         "rebuilds itself."),
        ("MAXIFS / MINIFS", "Best/worst month revenue on the Dashboard "
         "use MAXIFS/MINIFS, written with the _xlfn. prefix "
         "(=_xlfn.MAXIFS(...)) so LibreOffice and Excel calculate "
         "them — the plain form shows #NAME? in LibreOffice."),
        ("Check it", "Every number here is recomputed from the raw CSVs "
         "by src/analyze.py and verified by src/checks.py — run it: "
         "python3 src/checks.py"),
        ("Same logic, three ways", "The channel, monthly and funnel "
         "totals exist in three forms that must agree: the SQL in "
         "sql/analysis_queries.sql, the Python in src/analyze.py, and "
         "this workbook's formulas. src/checks.py verifies all three "
         "against the raw files, including a LibreOffice recalc."),
    ]
    r = 3
    for title, text in lines:
        m.cell(row=r, column=1, value=title).font = Font(bold=True)
        m.cell(row=r, column=2, value=text)
        m.cell(row=r, column=2).alignment = Alignment(wrap_text=True,
                                                      vertical="top")
        r += 1
    m.column_dimensions["A"].width = 22
    m.column_dimensions["B"].width = 110

    wb.save(OUT)
    print(f"wrote {OUT.name}: sheets {wb.sheetnames}")


if __name__ == "__main__":
    main()
