#!/usr/bin/env python3
"""Plain-English rounding for Demand Pulse tiles.

Values are derived from the measured rate, not hard-coded 1-in-10 style
denominators. nearest_int keeps the already-correct "about 20%", "about 1%
high", and "about 3 weeks" labels. one_in_n turns a percentage into the
nearest whole 1-in-N (13.8% -> 7).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def nearest_int(value: float) -> int:
    return int(round(float(value)))


def one_in_n(percent: float) -> int:
    """Nearest whole 1-in-N for a percentage share. 13.8 -> 7."""
    p = float(percent)
    if p <= 0:
        raise ValueError("percent must be positive to form 1-in-N")
    return max(1, nearest_int(100.0 / p))


def about_one_in_n(percent: float) -> str:
    return f"about 1 in {one_in_n(percent)}"


def overstock_plain(percent: float) -> str:
    return f"{about_one_in_n(percent)} items over a month of stock"


def check_locked_roundings() -> list[str]:
    """Confirm current locked tiles still round the way the board already shows."""
    errors: list[str] = []
    cases = [
        ("WMAPE 19.87% -> about 20%", nearest_int(19.87), 20),
        ("bias 0.67% -> about 1%", nearest_int(0.67), 1),
        ("cover 3.248 weeks -> about 3", nearest_int(3.248), 3),
        ("overstock 13.8% -> 1 in 7", one_in_n(13.8), 7),
    ]
    for label, got, expected in cases:
        if got != expected:
            errors.append(f"{label}: got {got}, expected {expected}")
    return errors


def check_board_files() -> list[str]:
    errors: list[str] = []
    for rel in ("out/board_data.json", "docs/data/board_data.json"):
        tiles = json.loads((ROOT / rel).read_text())["tiles"]
        expected = overstock_plain(tiles["overstock_share_pct"]["value"])
        got = tiles["overstock_share_pct"]["plain"]
        if got != expected:
            errors.append(f"{rel}: plain {got!r} != {expected!r}")
        # Already-correct roundings must stay put.
        if tiles["wmape_system"]["plain"] != "Plan missed sales by 20%":
            errors.append(f"{rel}: wmape plain changed unexpectedly")
        if tiles["bias_pct"]["plain"] != "Plan ran about 1% high":
            errors.append(f"{rel}: bias plain changed unexpectedly")
        if tiles["avg_weeks_of_supply"]["plain"] != "Avg cover about 3 weeks":
            errors.append(f"{rel}: cover plain changed unexpectedly")
    return errors


def main() -> int:
    errors = check_locked_roundings() + check_board_files()
    if errors:
        for e in errors:
            print(f"  [FAIL] {e}")
        return 1
    print("  [PASS] locked roundings: 20%, about 1% high, about 3 weeks, about 1 in 7")
    print("  [PASS] board_data plain strings match derived 1-in-N")
    return 0


if __name__ == "__main__":
    sys.exit(main())
