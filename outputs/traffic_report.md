# P17 — Website Traffic & Conversion Report: CityStore.pk (SAMPLE)

**Period:** Fri 2026-05-01 → Sat 2026-10-31 (6 months, 184 days)
**Sessions:** 202,793 · **Users:** 150,351 · **Purchases:** 4,475 · **Revenue: PKR 12,910,349**
**Overall conversion rate:** 2.21% · **Average order value:** PKR 2,885

## 1. Where the traffic comes from

| Channel | Sessions | Share | Purchases | Conversion | Revenue (PKR) | AOV (PKR) |
|---|---|---|---|---|---|---|
| Organic Search | 64,911 | 32.01% | 1,628 | 2.51% | 4,648,671 | 2,855 |
| Social | 40,544 | 19.99% | 459 | 1.13% | 1,080,756 | 2,355 |
| Paid Search | 36,506 | 18.0% | 1,095 | 3.0% | 3,465,351 | 3,165 |
| Direct | 28,420 | 14.01% | 585 | 2.06% | 1,553,520 | 2,656 |
| Referral | 16,230 | 8.0% | 231 | 1.42% | 518,968 | 2,247 |
| Email | 16,182 | 7.98% | 477 | 2.95% | 1,643,083 | 3,445 |

**Best-converting channel: Paid Search (3.0%)** — 36,506 sessions, PKR 3,465,351 revenue. **Worst: Social (1.13%)** despite 40,544 sessions — the most traffic that converts least, which is where the money is leaking.

## 2. The funnel — where buyers drop off

| Step | Count | Step conversion | Share of sessions |
|---|---|---|---|
| Sessions | 202,793 | — | 100.0% |
| Product views | 119,691 | 59.02% | 59.0% |
| Add to cart | 14,452 | 12.07% | 7.1% |
| Checkout started | 7,071 | 48.93% | 3.5% |
| Purchase | 4,475 | 63.29% | 2.21% |

The biggest leak is **product view → add to cart (12.07%)**: only about 12 in every 100 viewers put anything in the basket. Checkout → purchase holds at 63.29%, so the checkout itself is not the problem — the problem is getting people to the basket in the first place.

## 3. Month by month

| Month | Sessions | Purchases | Revenue (PKR) | Conversion | MoM growth |
|---|---|---|---|---|---|
| 2026-05 | 32,139 | 701 | 2,029,953 | 2.18% | — |
| 2026-06 | 31,601 | 697 | 2,010,379 | 2.21% | -0.96% |
| 2026-07 | 33,440 | 738 | 2,142,270 | 2.21% | +6.56% |
| 2026-08 | 34,805 | 776 | 2,224,324 | 2.23% | +3.83% |
| 2026-09 | 34,393 | 757 | 2,176,363 | 2.2% | -2.16% |
| 2026-10 | 36,415 | 806 | 2,327,060 | 2.21% | +6.92% |

Revenue grew **14.64% from May to October** (PKR 2,029,953 → PKR 2,327,060). Best month: **2026-10 (PKR 2,327,060)**; worst: **2026-06 (PKR 2,010,379)**.

## 4. Landing pages

| Landing page | Sessions | Share | Purchases | Conversion | Revenue (PKR) |
|---|---|---|---|---|---|
| / | 44,614 | 22.0% | 976 | 2.19% | 2,720,205 |
| /mobile-phones | 32,300 | 15.93% | 769 | 2.38% | 2,678,654 |
| /sale | 28,438 | 14.02% | 810 | 2.85% | 2,032,786 |
| /fashion/men | 24,423 | 12.04% | 440 | 1.8% | 1,165,181 |
| /fashion/women | 22,286 | 10.99% | 425 | 1.91% | 1,185,035 |
| /home-kitchen | 20,254 | 9.99% | 375 | 1.85% | 1,097,757 |
| /beauty | 16,189 | 7.98% | 345 | 2.13% | 818,352 |
| /electronics | 14,289 | 7.05% | 335 | 2.34% | 1,212,379 |

**Best-converting page: /sale (2.85%)**; worst: /fashion/men (1.8%). The /sale page converts well, which says price — not traffic — is the lever.

## 5. Devices

| Device | Sessions | Share | Purchases | Conversion | Revenue (PKR) |
|---|---|---|---|---|---|
| Mobile | 140,130 | 69.1% | 2,845 | 2.03% | 7,701,685 |
| Desktop | 51,423 | 25.36% | 1,443 | 2.81% | 4,728,818 |
| Tablet | 11,240 | 5.54% | 187 | 1.66% | 479,846 |

Mobile is 69.1% of sessions but converts at 2.03% against Desktop's 2.81% — a mobile checkout that converted like desktop would be worth roughly PKR 3,658,444 more revenue on the same traffic.

## 6. Weekend vs weekday

Weekend days (Fri–Sun) average 1,209.9 sessions a day vs 1,019.3 on weekdays (**+18.7%**). Conversion is 2.23% on weekends vs 2.18% on weekdays.

## 7. Three recommendations

1. **Fix the view → cart leak first.** At 12.07%, the product page is where buyers are lost. Better photos, clearer prices and delivery info, and a visible add-to-cart button above the fold — before spending one more rupee on ads.
2. **Move budget from Social to Paid Search and Email.** Social brings 40,544 sessions at 1.13% conversion; Paid Search converts at 3.0%. Same spend, more buyers.
3. **Fix mobile checkout.** Mobile is most of the traffic and the worst converter of the three devices. One-page checkout, JazzCash/Easypaisa/COD upfront, and no forced account creation.

> Every number in this report is recomputed from `data/raw/daily_traffic_SAMPLE.csv` (+ the landing-page and device splits) by `src/analyze.py` — nothing is typed by hand. Run `python3 src/checks.py` to re-verify.
