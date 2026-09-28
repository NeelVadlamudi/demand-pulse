#!/usr/bin/env python3
"""Recompute Demand Pulse M5 locked tiles; system plan = pure trailing 28-day mean."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "m5_ca3_top80_daily.parquet"
BOARD = ROOT / "out" / "board_data.json"
TOL = 0.05

TRAIL_DAYS = 28
HOLDOUT_DAYS = 28
START_COVER_WEEKS = 3.0
TARGET_COVER_WEEKS = 3.0
OVERSTOCK_WOS = 4.0
SCENARIO_LIFT = 0.10
SCENARIO_CAT = "FOODS"


def wmape(y, f) -> float:
    y = np.asarray(y, float)
    f = np.asarray(f, float)
    m = np.isfinite(y) & np.isfinite(f)
    y, f = y[m], f[m]
    denom = np.abs(y).sum()
    return float(np.abs(y - f).sum() / denom) if denom else float("nan")


def bias_pct(y, f) -> float:
    y = np.asarray(y, float)
    f = np.asarray(f, float)
    m = np.isfinite(y) & np.isfinite(f)
    y, f = y[m], f[m]
    denom = y.sum()
    return float((f - y).sum() / denom) if denom else float("nan")


def build_system_plan(frame: pd.DataFrame) -> pd.DataFrame:
    """Locked system plan = pure trailing 28-day mean of prior days."""
    out = []
    for (_, _), g in frame.groupby(["store_id", "item_id"], sort=False):
        g = g.copy()
        s = g["sales"].astype(float)
        trail = s.shift(1).rolling(TRAIL_DAYS, min_periods=7).mean()
        g["plan"] = trail.clip(lower=0)
        out.append(g)
    return pd.concat(out, ignore_index=True)


def main() -> int:
    if not DATA.exists():
        print("FAIL: missing", DATA)
        return 1
    if not BOARD.exists():
        print("FAIL: missing", BOARD)
        return 1

    board = json.loads(BOARD.read_text())
    tiles = board["tiles"]
    holdout_min = pd.Timestamp(board["meta"]["date_window"]["holdout_min"])
    holdout_max = pd.Timestamp(board["meta"]["date_window"]["holdout_max"])

    df = pd.read_parquet(DATA)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["store_id", "item_id", "date"]).reset_index(drop=True)
    df = build_system_plan(df)

    hold = df[(df["date"] >= holdout_min) & (df["date"] <= holdout_max)].copy()
    hold = hold[hold["plan"].notna()].copy()
    hold["week"] = hold["date"].dt.to_period("W-SUN").dt.start_time
    hold_w = hold.groupby(["store_id", "item_id", "week"], as_index=False).agg(
        sales=("sales", "sum"), plan=("plan", "sum")
    )

    checks: list[bool] = []

    def check(name, got, expected, tol=TOL):
        ok = abs(got - expected) <= tol
        status = "PASS" if ok else "FAIL"
        checks.append(ok)
        print(f"  [{status}] {name}: got={got} expected={expected} (tol={tol})")

    print("Demand Pulse M5 KPI verify (system = trailing 28-day mean)")
    print(f"  daily_rows={len(df)} holdout_daily={len(hold)} holdout_weekly={len(hold_w)}")
    print(f"  holdout={holdout_min.date()} → {holdout_max.date()}")

    required = ["wmape_system", "bias_pct", "avg_weeks_of_supply"]
    for k in required:
        if k not in tiles:
            print(f"  [FAIL] missing tile key: {k}")
            checks.append(False)
    tile4_ok = ("overstock_share_pct" in tiles) or ("stockout_rate_pct" in tiles)
    if not tile4_ok:
        print("  [FAIL] missing tile4 (overstock_share_pct or stockout_rate_pct)")
        checks.append(False)
    else:
        print("  [PASS] tile4 present")
        checks.append(True)

    obsolete = {"in_stock_pct", "wmape_baseline", "wmape_improved", "wmape_system_plan", "bias_pct_system_plan"}
    if obsolete & set(tiles):
        print("  [FAIL] obsolete tile keys still present:", sorted(obsolete & set(tiles)))
        checks.append(False)
    else:
        print("  [PASS] obsolete tiles absent")
        checks.append(True)

    # Confirm meta says trail won / blend lost
    methods = board["meta"].get("methods", {})
    sys_txt = methods.get("system_plan", "").lower()
    chal_txt = methods.get("challenge_check", "").lower()
    if "trailing" in sys_txt and "28" in sys_txt:
        print("  [PASS] meta.system_plan is trailing-28")
        checks.append(True)
    else:
        print("  [FAIL] meta.system_plan should be trailing-28")
        checks.append(False)
    if "lost" in chal_txt or "50/50" in chal_txt or "yoy" in chal_txt:
        print("  [PASS] meta.challenge_check documents YoY blend loss")
        checks.append(True)
    else:
        print("  [FAIL] meta.challenge_check should document YoY blend as loser")
        checks.append(False)

    wmape_sys = round(wmape(hold_w["sales"], hold_w["plan"]) * 100, 2)
    bias_sys = round(bias_pct(hold_w["sales"], hold_w["plan"]) * 100, 2)
    check("wmape_system", wmape_sys, tiles["wmape_system"]["value"])
    check("bias_pct", bias_sys, tiles["bias_pct"]["value"])

    w = df.copy()
    w["week"] = w["date"].dt.to_period("W-SUN").dt.start_time
    weekly = w.groupby(["store_id", "item_id", "week"], as_index=False).agg(
        sales=("sales", "sum"), plan=("plan", "sum")
    ).sort_values(["store_id", "item_id", "week"])
    holdout_week_min = pd.Timestamp(holdout_min.to_period("W-SUN").start_time)
    pre = weekly[weekly["week"] < holdout_week_min]
    avg_weekly = pre.groupby(["store_id", "item_id"])["sales"].mean()

    inv_rows = []
    for (store, item), g in weekly.groupby(["store_id", "item_id"]):
        g = g.sort_values("week").reset_index(drop=True)
        avg_s = float(avg_weekly.get((store, item), g["sales"].mean()))
        if not np.isfinite(avg_s) or avg_s < 0:
            avg_s = 0.0
        on_hand = START_COVER_WEEKS * avg_s
        incoming = 0.0
        for _, row in g.iterrows():
            on_hand += incoming
            incoming = 0.0
            demand = float(row["sales"])
            sold = min(on_hand, demand)
            unmet = demand - sold
            on_hand -= sold
            plan_w = float(row["plan"]) if np.isfinite(row["plan"]) else avg_s
            target = TARGET_COVER_WEEKS * max(plan_w, 0.0)
            order = max(0.0, target - on_hand)
            incoming = order
            wos = on_hand / demand if demand > 0 else (np.nan if on_hand <= 0 else 99.0)
            inv_rows.append({
                "store_id": store, "item_id": item, "week": row["week"],
                "sales": demand, "on_hand_end": on_hand, "unmet": unmet, "wos": wos,
            })
    inv = pd.DataFrame(inv_rows)
    inv["week"] = pd.to_datetime(inv["week"])
    last_week = inv["week"].max()
    last = inv[inv["week"] == last_week]
    avg_wos = round(float(last.loc[last["sales"] > 0, "wos"].mean()), 3)
    overstock = round(float((last["wos"] > OVERSTOCK_WOS).fillna(False).mean()) * 100, 1)
    check("avg_weeks_of_supply", avg_wos, tiles["avg_weeks_of_supply"]["value"])

    if "overstock_share_pct" in tiles:
        check("overstock_share_pct", overstock, tiles["overstock_share_pct"]["value"])
    if "stockout_rate_pct" in tiles:
        hw = inv[inv["week"] >= holdout_week_min]
        rate = round(float(hw["unmet"].sum() / hw["sales"].sum()) * 100, 2) if hw["sales"].sum() else 0.0
        check("stockout_rate_pct", rate, tiles["stockout_rate_pct"]["value"])

    foods = hold[hold["cat_id"] == SCENARIO_CAT]
    base_u = round(float(foods["sales"].sum()), 1)
    delta_u = round(base_u * SCENARIO_LIFT, 1)
    check("scenario_baseline_units", base_u, board["scenario"]["baseline_units"], tol=0.5)
    check("scenario_delta_units", delta_u, board["scenario"]["delta_units"], tol=0.5)
    check("rows_kept_daily", float(len(df)), float(board["meta"]["row_counts"]["rows_kept_daily"]), tol=0)

    disc = board["meta"].get("disclaimer", "")
    if "M5" in disc and "simulated" in disc.lower() and "Walmart" in disc:
        print("  [PASS] disclaimer mentions M5 + simulated + Walmart")
        checks.append(True)
    else:
        print("  [FAIL] disclaimer missing required spirit")
        checks.append(False)

    if all(checks):
        print("ALL PASS")
        return 0
    print("FAIL")
    return 1


if __name__ == "__main__":
    sys.exit(main())
