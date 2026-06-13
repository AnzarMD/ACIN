"""Test the dynamic repricing agent pricing bands."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.repricing_agent import compute_base_prices, PRICING_BANDS


def test_pricing_bands_exist():
    """All major categories should have pricing bands."""
    required = ["Footwear", "Electronics", "Clothing", "Computers", "Home & Kitchen"]
    for cat in required:
        assert cat in PRICING_BANDS, f"Missing pricing band for {cat}"


def test_grade_a_footwear_pricing():
    """Grade A shoes should be 50-70% of original."""
    fast, balanced, max_p = compute_base_prices(5000, "A", "Footwear", 80, 0)
    assert 2000 <= fast <= 3500, f"Fast sale price out of range: {fast}"
    assert 2500 <= balanced <= 4000, f"Balanced price out of range: {balanced}"
    assert 3000 <= max_p <= 4500, f"Max profit price out of range: {max_p}"


def test_grade_d_pricing_very_low():
    """Grade D products should be priced very low (under 20% of original)."""
    fast, balanced, max_p = compute_base_prices(10000, "D", "Electronics", 30, 0)
    assert fast < 2000, f"Grade D fast_sale too high: {fast}"
    assert balanced < 2500, f"Grade D balanced too high: {balanced}"


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
    """Prices should never be zero or negative."""
    for cat in PRICING_BANDS:
        for grade in ["A", "B", "C", "D"]:
            fast, balanced, max_p = compute_base_prices(1000, grade, cat, 50, 0)
            assert fast > 0, f"{cat}/{grade} fast <= 0"
            assert balanced > 0, f"{cat}/{grade} balanced <= 0"
            assert max_p > 0, f"{cat}/{grade} max <= 0"
            assert fast <= balanced <= max_p, f"{cat}/{grade} price ordering wrong"
