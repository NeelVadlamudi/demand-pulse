#!/usr/bin/env python3
"""Plain-English rounding for Demand Pulse tiles.

Values are derived from the measured rate, not hard-coded 1-in-10 style
denominators. nearest_int keeps the already-correct "about 20%", "about 1%
high", and "about 3 weeks" labels. one_in_n turns a positive finite
percentage into the nearest whole 1-in-N (13.8% -> 7). Zero, missing,
negative, or non-finite rates return None from one_in_n so callers never
emit "1 in null", "Infinity", or "NaN".
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EM_DASH = "—"
NONE_OVERSTOCK = "none over a month of stock"


def nearest_int(value: float) -> int:
    return int(round(float(value)))


def parse_rate(percent) -> float | None:
    """Return a finite float, or None if the rate is missing or non-finite."""
    if percent is None or isinstance(percent, bool):
        return None
    if isinstance(percent, str) and percent.strip() == "":
        return None
    try:
        p = float(percent)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(p):
        return None
    return p


def one_in_n(percent) -> int | None:
    """Nearest whole 1-in-N for a percentage share. 13.8 -> 7.

    Returns None for 0, missing, negative, or non-finite rates so we
    never divide by zero or invent a denominator.
    """
    p = parse_rate(percent)
    if p is None or p <= 0:
        return None
    return max(1, nearest_int(100.0 / p))


def about_one_in_n(percent) -> str | None:
    n = one_in_n(percent)
    if n is None:
        return None
    return f"about 1 in {n}"


def percent_text(percent, digits: int = 1) -> str | None:
    """Plain percentage text for a finite rate, or None if missing/non-finite."""
    p = parse_rate(percent)
    if p is None:
        return None
    return f"{p:.{digits}f}%"


def overstock_number(percent) -> str:
    """Big-number text for the overstock tile."""
    p = parse_rate(percent)
    if p is None:
        return EM_DASH
    if p == 0:
        return NONE_OVERSTOCK
    phrase = about_one_in_n(p)
    if phrase is not None:
        return phrase
    return percent_text(p) or EM_DASH


def overstock_plain(percent) -> str:
    """Board `plain` string for the overstock tile."""
    p = parse_rate(percent)
    if p is None:
        return EM_DASH
    if p == 0:
        return NONE_OVERSTOCK
    phrase = about_one_in_n(p)
    if phrase is not None:
        return f"{phrase} items over a month of stock"
    return percent_text(p) or EM_DASH


def _output_strings(percent) -> list[str]:
    """Every user-facing string these helpers may emit for a rate."""
    values = [
        about_one_in_n(percent),
        percent_text(percent),
        overstock_number(percent),
        overstock_plain(percent),
    ]
    return [v for v in values if v is not None]


def check_locked_roundings() -> list[str]:
    """Confirm current locked tiles still round the way the board already shows."""
    errors: list[str] = []
    cases = [
        ("WMAPE 19.87% -> about 20%", nearest_int(19.87), 20),
        ("bias 0.67% -> about 1%", nearest_int(0.67), 1),
        ("cover 3.248 weeks -> about 3", nearest_int(3.248), 3),
        ("overstock 13.8% -> 1 in 7", one_in_n(13.8), 7),
        ("about 13.8%", about_one_in_n(13.8), "about 1 in 7"),
        ("overstock number 13.8%", overstock_number(13.8), "about 1 in 7"),
        ("overstock plain 13.8%", overstock_plain(13.8), "about 1 in 7 items over a month of stock"),
    ]
    for label, got, expected in cases:
        if got != expected:
            errors.append(f"{label}: got {got!r}, expected {expected!r}")
    return errors


def check_guards() -> list[str]:
    errors: list[str] = []
    if overstock_number(0) != NONE_OVERSTOCK or overstock_plain(0) != NONE_OVERSTOCK:
        errors.append(f"0% should be {NONE_OVERSTOCK!r}, got number={overstock_number(0)!r} plain={overstock_plain(0)!r}")
    if one_in_n(0) is not None or about_one_in_n(0) is not None:
        errors.append(f"0% one_in_n/about should be None, got {one_in_n(0)!r} {about_one_in_n(0)!r}")

    missing = [None, ""]
    for val in missing:
        if one_in_n(val) is not None or about_one_in_n(val) is not None:
            errors.append(f"missing {val!r}: one_in_n/about should be None")
        if overstock_number(val) != EM_DASH or overstock_plain(val) != EM_DASH:
            errors.append(f"missing {val!r}: expected em dash, got {overstock_number(val)!r} {overstock_plain(val)!r}")
        if percent_text(val) is not None:
            errors.append(f"missing {val!r}: percent_text should be None, not a made-up value")

    nan_vals = [math.nan, math.inf, -math.inf]
    for val in nan_vals:
        if one_in_n(val) is not None or about_one_in_n(val) is not None:
            errors.append(f"non-finite {val!r}: one_in_n/about should be None")
        if percent_text(val) is not None:
            errors.append(f"non-finite {val!r}: percent_text should be None")
        if overstock_number(val) != EM_DASH or overstock_plain(val) != EM_DASH:
            errors.append(f"non-finite {val!r}: expected em dash, got {overstock_number(val)!r}")

    # Negative finite rate: no 1-in-N, fall back to plain percentage.
    if one_in_n(-3.0) is not None:
        errors.append("negative rate should not form 1-in-N")
    if percent_text(-3.0) != "-3.0%":
        errors.append(f"negative rate percent_text: got {percent_text(-3.0)!r}")
    if overstock_number(-3.0) != "-3.0%":
        errors.append(f"negative rate should fall back to percentage, got {overstock_number(-3.0)!r}")

    forbidden = ("1 in null", "Infinity", "NaN")
    sample_rates = [13.8, 0, None, "", math.nan, math.inf, -math.inf, -3.0, 100]
    for val in sample_rates:
        for s in _output_strings(val):
            for bad in forbidden:
                if bad in s:
                    errors.append(f"output {s!r} for {val!r} contains {bad!r}")
    return errors


def check_board_files() -> list[str]:
    errors: list[str] = []
    for rel in ("out/board_data.json", "docs/data/board_data.json"):
        tiles = json.loads((ROOT / rel).read_text())["tiles"]
        expected = overstock_plain(tiles["overstock_share_pct"]["value"])
        got = tiles["overstock_share_pct"]["plain"]
        if got != expected:
            errors.append(f"{rel}: plain {got!r} != {expected!r}")
        if tiles["overstock_share_pct"]["value"] != 13.8:
            errors.append(f"{rel}: overstock value changed unexpectedly")
        if tiles["wmape_system"]["plain"] != "Plan missed sales by 20%":
            errors.append(f"{rel}: wmape plain changed unexpectedly")
        if tiles["bias_pct"]["plain"] != "Plan ran about 1% high":
            errors.append(f"{rel}: bias plain changed unexpectedly")
        if tiles["avg_weeks_of_supply"]["plain"] != "Avg cover about 3 weeks":
            errors.append(f"{rel}: cover plain changed unexpectedly")
    return errors


def main() -> int:
    errors = check_locked_roundings() + check_guards() + check_board_files()
    if errors:
        for e in errors:
            print(f"  [FAIL] {e}")
        return 1
    print("  [PASS] locked roundings: 20%, about 1% high, about 3 weeks, about 1 in 7")
    print("  [PASS] 0% overstock is 'none over a month of stock'")
    print("  [PASS] missing/NaN/non-finite rates use an em dash; no 1 in null/Infinity/NaN")
    print("  [PASS] board_data plain strings still match 13.8% → about 1 in 7")
    return 0


if __name__ == "__main__":
    sys.exit(main())
