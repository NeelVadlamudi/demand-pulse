# Demand Pulse

Weekly demand plans for a selected subset of Walmart M5 sales, scored against a historical holdout.

[Live board](https://neelvadlamudi.github.io/demand-pulse/) · [Methods notebook](notebooks/demand_pulse_m5.ipynb) · [Portfolio](https://neelvadlamudi.github.io/neelresume/)

## Result

The trailing **28-day mean** produced **19.87% weekly WMAPE** and **+0.67% aggregate bias** on the **April 25–May 22, 2016** holdout. The daily plan is built from prior observed sales, then summed to weeks for scoring. It is a rolling plan updated as observations arrive, not a fixed forecast made for the entire holdout at once.

These values are in the published [`data/board_data.json`](https://neelvadlamudi.github.io/demand-pulse/data/board_data.json), checked November 9, 2026. This is a fixed historical evaluation, not a live retail feed.

**Low bias does not mean low error.** The plan was slightly high in total, while item-store-week misses were much larger. Positive and negative errors cancel in bias; WMAPE keeps their absolute size. A buyer needs both views before trusting the total.

## What was compared

The data are M5 Walmart unit sales for **3 California stores and 80 selected items: 240 store-item series**. The notebook compares the trailing mean with a year-over-year blend. The blend performed worse on this holdout, so it remains a challenge check rather than the headline method.

The subset is selected by total sales volume over the full available history, including the evaluation period. That limits claims about out-of-sample generalization, even though each day's trailing mean uses earlier observations. This is a selected-subset analysis, not an official M5 leaderboard result or a representative store-wide benchmark.

## What the numbers mean

| Measure | Published value | Practical reading |
| --- | ---: | --- |
| Weekly WMAPE | 19.87% | Sum of absolute weekly plan errors divided by total actual sales. It is not the percentage of individual forecasts that were correct. |
| Aggregate bias | +0.67% | Total planned units were above actual units by this share of actual sales. |
| Average simulated cover | 3.25 weeks | Rounded from 3.248; ending simulated stock divided by sales in the final week, averaged over selling series. |
| Simulated overstock share | 13.8% | Share of store-item positions above four weeks of cover in the final week. |

Public M5 data do **not** include on-hand inventory. Cover and overstock come from a simple weekly reorder simulation, not observed Walmart stock. They illustrate which positions a planner would review; they do not establish that an order policy is safe to deploy.

## Follow the calculation

- [`scripts/build_filter.py`](scripts/build_filter.py) builds the local subset from source CSVs.
- [`data/processed/filter_meta.json`](data/processed/filter_meta.json) lists the exact stores and items the subset keeps.
- [`scripts/verify_kpis.py`](scripts/verify_kpis.py) reconstructs daily plans, weekly errors and simulated cover, then checks them against the board.
- [`out/kpi_lock.md`](out/kpi_lock.md) records the fixed evaluation.
- [`docs/`](docs/) contains the static board; `out/` holds its published aggregates.

WMAPE is `sum(abs(plan - sales)) / sum(abs(sales))`. Bias is `sum(plan - sales) / sum(sales)`. Both are calculated on weekly store-item rollups, not averaged from per-item percentages.

## Reproduce locally

Obtain the M5 source files through [Kaggle](https://www.kaggle.com/c/m5-forecasting-accuracy/data) under the applicable competition terms. Place `sales_train_evaluation.csv`, `calendar.csv` and `sell_prices.csv` in `data/raw/`. The repository holds no M5 rows, raw or filtered. Do not republish source or derived row-level files as part of the reproduction.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pandas numpy pyarrow
python scripts/build_filter.py
python scripts/verify_kpis.py
```

The verifier exits unsuccessfully if a required file is missing or a locked figure does not reconcile. Generated local data belong outside version control.

## Limits

The inventory simulation omits real lead-time variation, purchasing constraints and unavailable demand during stockouts. One historical holdout cannot establish performance in a new market or season. The project is independent and not affiliated with Walmart.
