# Demand Pulse

**Live board:** https://neelvadlamudi.github.io/demand-pulse/ · **Portfolio:** https://neelvadlamudi.github.io/neelresume/

Demand planning on real [M5 Walmart](https://www.kaggle.com/c/m5-forecasting-accuracy/data) unit sales.

The locked system plan is a **trailing 28-day mean** (built daily, scored weekly). A year-over-year blend lost on this holdout, so it stays in the notebook as a challenge check only.

## Locked results (holdout 2016-04-25 → 2016-05-22)

| Metric | Value |
| --- | ---: |
| Plan missed sales by (WMAPE) | 19.87% |
| Plan ran high by (bias) | 0.67% |
| Avg cover (simulated WOS) | 3.25 weeks |
| Items over a month of stock | 13.8% |

Inventory cover is **simulated** with a simple reorder policy. Public M5 has no on-hand. Not affiliated with Walmart or any retailer.

## What’s in the repo

- `docs/` — interactive board (GitHub Pages)
- `out/` — locked board JSON, KPI write-up, holdout chart
- `notebooks/demand_pulse_m5.ipynb` — methods and challenge check
- `data/processed/filter_meta.json` — the exact stores and items the filter keeps (the extract itself is rebuilt locally, not committed)
- `scripts/verify_kpis.py` — recomputes the locked tiles

No M5 rows are committed, raw or filtered. The data is Kaggle's to share, not mine, so you rebuild it: download the M5 CSVs from Kaggle (or the Hugging Face mirror `denephew/M5_Forecasting`) into `data/raw/`, then run `scripts/build_filter.py`. See `data/README.md`.

## Verify

```bash
python3 -m venv .venv && .venv/bin/pip install pandas pyarrow
# put calendar.csv, sell_prices.csv and sales_train_evaluation.csv in data/raw/ first
.venv/bin/python scripts/build_filter.py
.venv/bin/python scripts/verify_kpis.py
```

Expect `ALL PASS`.
