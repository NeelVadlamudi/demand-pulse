#!/usr/bin/env python3
"""Filter raw M5 evaluation CSVs to CA_1/2/3 × top-80 items. Run from project root."""
from __future__ import annotations
from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW, PROC = ROOT / "data" / "raw", ROOT / "data" / "processed"
STORES = ["CA_1", "CA_2", "CA_3"]
TOP_N_ITEMS = 80
HOLDOUT_DAYS = 28

def main() -> None:
    PROC.mkdir(parents=True, exist_ok=True)
    sales = pd.read_csv(RAW / "sales_train_evaluation.csv")
    day_cols = [c for c in sales.columns if c.startswith("d_")]
    sub = sales[sales["store_id"].isin(STORES)].copy()
    sub["_vol"] = sub[day_cols].sum(axis=1)
    item_vol = sub.groupby("item_id")["_vol"].sum().sort_values(ascending=False)
    top_items = item_vol.head(TOP_N_ITEMS).index.tolist()
    sub = sub[sub["item_id"].isin(top_items)].copy()
    id_vars = ["id", "item_id", "dept_id", "cat_id", "store_id", "state_id"]
    long = sub.melt(id_vars=id_vars, value_vars=day_cols, var_name="d", value_name="sales")
    cal = pd.read_csv(RAW / "calendar.csv", parse_dates=["date"])
    cal = cal[["d", "date", "wm_yr_wk", "weekday", "wday", "month", "year",
               "event_name_1", "event_type_1", "event_name_2", "event_type_2",
               "snap_CA", "snap_TX", "snap_WI"]]
    long = long.merge(cal, on="d", how="left")
    prices = pd.read_csv(RAW / "sell_prices.csv")
    prices = prices[prices["store_id"].isin(STORES) & prices["item_id"].isin(top_items)].copy()
    long = long.merge(prices, on=["store_id", "item_id", "wm_yr_wk"], how="left")
    long = long.sort_values(["store_id", "item_id", "date"])
    long["sell_price"] = long.groupby(["store_id", "item_id"])["sell_price"].ffill().bfill()
    long.to_parquet(PROC / "m5_ca3_top80_daily.parquet", index=False)
    prices.to_parquet(PROC / "m5_ca3_top80_prices.parquet", index=False)
    cal.to_parquet(PROC / "m5_calendar.parquet", index=False)
    long[["id","item_id","dept_id","cat_id","store_id","state_id","d","date","wm_yr_wk",
          "weekday","sales","sell_price","event_name_1","event_type_1"]].to_csv(
        PROC / "m5_ca3_top80_daily.csv", index=False)
    meta = {
        "filter": {
            "description": "3 California stores (CA_1, CA_2, CA_3) × top 80 items by total unit volume across those stores over d_1..d_1941",
            "stores": STORES, "top_n_items": TOP_N_ITEMS, "items": top_items,
            "series_count": int(sub.shape[0]), "source_file": "sales_train_evaluation.csv",
            "day_span": f"d_1..d_{len(day_cols)}", "holdout_days": HOLDOUT_DAYS,
            "holdout_d": [f"d_{i}" for i in range(len(day_cols) - HOLDOUT_DAYS + 1, len(day_cols) + 1)],
            "mirror": "https://huggingface.co/datasets/denephew/M5_Forecasting",
            "kaggle": "https://www.kaggle.com/c/m5-forecasting-accuracy/data",
        },
        "date_range": {"min": str(long["date"].min().date()), "max": str(long["date"].max().date()),
                       "n_days": int(long["date"].nunique())},
        "row_counts": {"daily_rows": int(len(long)),
                       "series": int(long.groupby(["store_id","item_id"]).ngroups),
                       "stores": int(long["store_id"].nunique()),
                       "items": int(long["item_id"].nunique()),
                       "price_rows": int(len(prices))},
        "item_volume_rank": {k: float(v) for k, v in item_vol.loc[top_items].items()},
    }
    (PROC / "filter_meta.json").write_text(json.dumps(meta, indent=2))
    print("OK", meta["row_counts"])

if __name__ == "__main__":
    main()
