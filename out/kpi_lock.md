# Demand Pulse (M5) — Locked KPI Pack

**Project:** Demand Pulse — demand planning on **real Walmart M5** sales  
**Disclaimer:** Public M5 Walmart sales data (Kaggle) Inventory cover is simulated with a simple reorder policy — not real on-hand. Not affiliated with Walmart, or any retailer.

## Dataset
- **Source:** [M5 Forecasting Accuracy](https://www.kaggle.com/c/m5-forecasting-accuracy/data)
- **Mirror used:** Hugging Face `denephew/M5_Forecasting` (no Kaggle CLI credentials on this machine)
- **Raw files:** `data/raw/calendar.csv`, `sell_prices.csv`, `sales_train_evaluation.csv`
- **Subset filter:** stores `CA_1`, `CA_2`, `CA_3` × **top 80 items** by total unit volume across those stores over d_1…d_1941 → **240 series**, **465,840** daily rows (2011-01-29 → 2016-05-22)
- **Documented in:** `data/README.md`, `data/processed/filter_meta.json`
- All rows are **real M5 Walmart sales** — no synthetic invention

## Holdout window
- **2016-04-25 → 2016-05-22** (28 days, d_1914…d_1941) — M5-style last-28-days of the evaluation series
- Events in window: Mother's Day (2016-05-08), Cinco De Mayo, Pesach End, Orthodox Easter

## Methods (Excel / planning-tool friendly) — locked the winner
| Role | Method |
|------|--------|
| **System plan (locked)** | Daily: **pure trailing 28-day mean** of *prior* days (no leakage). Locked WMAPE/bias scored after **summing plan & sales to weeks**. |
| Challenge check (notebook only) | 50/50 same-weekday-last-year (364-day lag) + trailing 28-day mean — **LOST** on this holdout (~27.45% vs ~19.87% WMAPE; level drift vs last year) |
| Cover / stockouts | **Simulated** weekly inventory (below) — not real Walmart on-hand |

No neural nets, Prophet, XGBoost, LightGBM, or deep learning.  
**Rule applied:** simple methods that deliver more effective solutions — the weaker YoY blend is not the hero plan.

### Inventory simulation formulas
Public M5 has **no on-hand**. For WOS / overstock story:

1. Aggregate daily sales & plan to weeks (`W-SUN` period start).
2. **Start inventory** (week 0): `on_hand = 3 × mean(pre-holdout weekly sales)` for that store×item.
3. Each week `t`:
   - Receive prior week's order (`lead_time = 1 week`).
   - `demand = actual weekly sales`; `sold = min(on_hand, demand)`; `unmet = demand − sold`; `on_hand -= sold`.
   - **Reorder to target cover:** `target = 3 × max(weekly_plan, 0)` using the **trailing-28 system plan**; `order = max(0, target − on_hand)`; arrives next week.
4. **Weeks of supply:** `WOS = on_hand_end / weekly_sales` (items with sales > 0 on the scored week).
5. **Overstock share:** share of store×item keys with `WOS > 4` on the last week in the file.

## Locked tiles
| Tile | Value | Definition |
|------|------:|------------|
| WMAPE (system plan) | **19.87%** | Weekly WMAPE of trailing-28 plan vs actual on the 28-day holdout. |
| Bias % (system plan) | **0.67%** | sum(plan − actual) / sum(actual) on weekly holdout rollups. Positive = slight over-forecast. |
| Avg weeks of supply | **3.248** | Simulated ending inventory ÷ that week's sales, averaged across items with sales on last week (**2016-05-16** week start). |
| Overstock share (WOS > 4) | **13.8%** | Share of keys with more than four weeks of simulated cover (~1 in 10). |

**Tile-4 choice:** Overstock share. Simulated unmet demand on holdout weeks was **0.12%** (< 0.5% cutoff).

## Scenario
A **+10% FOODS** lift over the holdout (Mother's Day / spring-holiday style) adds **~7,394 units (~$14,819)** vs FOODS units actually sold in the window (prices from `sell_prices`).

## Exceptions
Eight store×item rows in `out/board_data.json` with plain-English trim / lift / hold actions from weekly holdout bias (trail-28 plan) + last-week simulated WOS. Labels use real M5 `item_id` / `dept_id` / `cat_id` / `store_id`.

## Verify
```bash
cd /workspace/demand-pulse-m5 && .venv/bin/python scripts/verify_kpis.py
```
Expect `ALL PASS`.

