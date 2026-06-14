"""Test the dynamic repricing agent pricing logic.

compute_base_prices formula (condition_score-driven):
  max_pct      = (condition_score + demand_boost) / 100
  balanced_pct = (condition_score - 5  + demand_boost) / 100
  fast_pct     = (condition_score - 12 + demand_boost) / 100   (capped at max_pct - 0.15)

demand_boost: +3 if demand >= 80, +1 if demand >= 60, else 0

Grade-to-score fallback when condition_score not passed:
  A → 90, B → 77, C → 60, D → 35
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.repricing_agent import compute_base_prices, PRICING_BANDS


def test_pricing_bands_exist():
    """All major categories should have pricing bands defined (used as reference data)."""
    required = ["Footwear", "Electronics", "Clothing", "Computers", "Home & Kitchen"]
    for cat in required:
        assert cat in PRICING_BANDS, f"Missing pricing band for {cat}"


def test_grade_a_footwear_pricing():
    """Grade A (condition≈90) shoes with high demand should be priced 70-95% of original.

    condition_score=90, demand_boost=+3 (demand=80)
    fast_pct  = (90-12+3)/100 = 0.81  → 5000*0.81 = 4050 → ~3999 after rounding
    balanced  = (90-5+3)/100  = 0.88  → 5000*0.88 = 4400 → ~4399
    max_p     = (90+3)/100    = 0.93  → 5000*0.93 = 4650 → ~4649
    """
    fast, balanced, max_p = compute_base_prices(5000, "A", "Footwear", 80, 0)
    assert 3000 <= fast <= 4500, f"Fast sale price out of range: {fast}"
    assert 3500 <= balanced <= 5000, f"Balanced price out of range: {balanced}"
    assert 4000 <= max_p <= 5000, f"Max profit price out of range: {max_p}"
    assert fast <= balanced <= max_p, "Price ordering must be fast ≤ balanced ≤ max"


def test_grade_d_pricing_very_low():
    """Grade D (condition≈35) products should be priced low (under 40% of original).

    condition_score=35, demand_boost=0 (demand=30)
    fast_pct  = max((35-12)/100, 0.04) = 0.23  → 10000*0.23 = 2299
    balanced  = (35-5)/100 = 0.30              → 10000*0.30 = 2999
    max_p     = 35/100     = 0.35              → 10000*0.35 = 3499
    """
    fast, balanced, max_p = compute_base_prices(10000, "D", "Electronics", 30, 0)
    assert fast < 3000, f"Grade D fast_sale too high: {fast}"
    assert balanced < 3500, f"Grade D balanced too high: {balanced}"
    assert max_p < 4000, f"Grade D max_profit too high: {max_p}"
    assert fast <= balanced <= max_p, "Price ordering must be fast ≤ balanced ≤ max"


def test_repair_cost_reduces_price():
    """Repair cost should reduce the listing prices."""
    fast_no_repair, balanced_no_repair, _ = compute_base_prices(5000, "C", "Electronics", 60, 0)
    fast_with_repair, balanced_with_repair, _ = compute_base_prices(5000, "C", "Electronics", 60, 1000)

    assert balanced_with_repair < balanced_no_repair, "Repair cost should reduce price"


def test_high_demand_increases_price():
    """Higher demand score should result in slightly higher prices."""
    _, balanced_low, _ = compute_base_prices(5000, "B", "Electronics", 40, 0)
    _, balanced_high, _ = compute_base_prices(5000, "B", "Electronics", 90, 0)

    assert balanced_high >= balanced_low, "High demand should equal or increase price"


def test_prices_always_positive():
    """Prices should never be zero or negative, and ordering must hold."""
    for cat in PRICING_BANDS:
        for grade in ["A", "B", "C", "D"]:
            fast, balanced, max_p = compute_base_prices(1000, grade, cat, 50, 0)
            assert fast > 0, f"{cat}/{grade} fast <= 0"
            assert balanced > 0, f"{cat}/{grade} balanced <= 0"
            assert max_p > 0, f"{cat}/{grade} max <= 0"
            assert fast <= balanced <= max_p, f"{cat}/{grade} price ordering wrong"


def test_condition_score_drives_price():
    """Explicit condition_score should override grade-based fallback."""
    _, balanced_low, _ = compute_base_prices(10000, "A", "Electronics", 60, 0, condition_score=40)
    _, balanced_high, _ = compute_base_prices(10000, "A", "Electronics", 60, 0, condition_score=85)

    assert balanced_high > balanced_low, "Higher condition score should yield higher price"


def test_price_ceiling_below_original():
    """Max profit price should never exceed the original price."""
    for grade in ["A", "B", "C", "D"]:
        fast, balanced, max_p = compute_base_prices(5000, grade, "Electronics", 70, 0)
        assert max_p <= 5000, f"Grade {grade} max_p {max_p} exceeds original 5000"
