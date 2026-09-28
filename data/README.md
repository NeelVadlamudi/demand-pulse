# Demand Pulse M5 — data notes

## Source
- **Competition:** [M5 Forecasting Accuracy](https://www.kaggle.com/c/m5-forecasting-accuracy/data) (Walmart unit sales)
- **Files used:** `calendar.csv`, `sell_prices.csv`, `sales_train_evaluation.csv` (d_1…d_1941)
- **Obtained via:** Hugging Face mirror [`denephew/M5_Forecasting`](https://huggingface.co/datasets/denephew/M5_Forecasting) (no Kaggle API credentials on this machine)
- **Raw copies:** `data/raw/` (full CSVs as downloaded)

## Reproducible subset filter
Full M5 is ~30k store×item series. Filter keeps **real M5 rows only**:

| Rule | Value |
|------|-------|
| Stores | `CA_1`, `CA_2`, `CA_3` (3 California stores) |
| Items | Top **80** `item_id` by **total unit volume** summed across those 3 stores over d_1…d_1941 |
| Series | 3 × 80 = **240** store×item keys |
| Days | 1941 (2011-01-29 → 2016-05-22) |
| Daily rows | 465,840 |

Filter metadata (exact item list + ranks): `data/processed/filter_meta.json`  
Long extract: `data/processed/m5_ca3_top80_daily.parquet` (+ CSV)  
Filtered prices: `data/processed/m5_ca3_top80_prices.parquet`

## Holdout
Last **28** days of the evaluation series: **2016-04-25 → 2016-05-22** (d_1914…d_1941), classic M5-style window.  
Calendar events in window include **Mother's Day** (2016-05-08), Cinco De Mayo, Pesach End, Orthodox Easter.

## What is NOT in public M5
On-hand inventory is **not** provided. Cover / WOS / stockout tiles use a **simulated** weekly reorder policy (documented in `out/kpi_lock.md`). Do not claim real Walmart inventory.
