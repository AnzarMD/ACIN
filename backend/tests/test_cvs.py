"""Test the CVS formula and destination logic."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from workflow.fusion import compute_cvs, determine_destination


def test_cvs_formula_basic():
    """Test CVS computation matches the spec formula."""
    product = {"condition_score": 92}
    market = {"demand_score": 87}
    pricing = {"balanced_price": 4199, "original_price": 4999}
    logistics = {"carbon_kg": 0.3, "co2_kg": 0.3}
    circular = {}

    cvs = compute_cvs(product, market, pricing, logistics, circular)

    # CVS should be high for excellent condition + high demand
    assert cvs > 75, f"CVS should be > 75 for Grade A product, got {cvs}"
    assert cvs < 100, f"CVS should be < 100, got {cvs}"


def test_cvs_low_condition():
    """Low condition should produce low CVS."""
    product = {"condition_score": 30}
    market = {"demand_score": 20}
    pricing = {"balanced_price": 500, "original_price": 5000}
    logistics = {"carbon_kg": 2.0, "co2_kg": 2.0}
    circular = {}

    cvs = compute_cvs(product, market, pricing, logistics, circular)
    assert cvs < 40, f"CVS should be < 40 for poor product, got {cvs}"


def test_destination_defective_refurbish():
    """Defective products with repair ROI should go to REFURBISH."""
    product = {"condition_score": 55, "safety_risk": False,
               "estimated_repair_cost_inr": 1000}
    pricing = {"balanced_price": 3000, "original_price": 5000}
    state = {"return_reason": "defective", "original_price": 5000}

    dest = determine_destination(60, state, product, pricing)
    assert dest == "REFURBISH"


def test_destination_size_mismatch_exchange():
    """Size mismatch always goes to EXCHANGE."""
    product = {"condition_score": 95, "safety_risk": False,
               "estimated_repair_cost_inr": 0}
    pricing = {"balanced_price": 4000, "original_price": 5000}
    state = {"return_reason": "size_mismatch", "original_price": 5000}

    dest = determine_destination(85, state, product, pricing)
    assert dest == "EXCHANGE"


def test_destination_changed_mind_resale():
    """Changed mind + good condition goes to INSTANT_RESALE."""
    product = {"condition_score": 90, "safety_risk": False,
               "estimated_repair_cost_inr": 0}
    pricing = {"balanced_price": 4000, "original_price": 5000}
    state = {"return_reason": "changed_mind", "original_price": 5000}

    dest = determine_destination(80, state, product, pricing)
    assert dest == "INSTANT_RESALE"


def test_destination_safety_risk_recycle():
    """Safety risk always goes to RECYCLE."""
    product = {"condition_score": 80, "safety_risk": True,
               "estimated_repair_cost_inr": 0}
    pricing = {"balanced_price": 4000, "original_price": 5000}
    state = {"return_reason": "defective", "original_price": 5000}

    dest = determine_destination(70, state, product, pricing)
    assert dest == "RECYCLE"
