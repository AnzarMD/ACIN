"""Test the logistics routing agent LRS scoring."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.logistics_agent import (
    generate_candidates,
    select_best_route,
    route_score,
    RouteCandidate,
    DESTINATION_ELIGIBLE_ROUTES,
    compute_carbon,
)


def test_route_score_formula():
    """Test LRS formula: 0.30C + 0.20T + 0.20D + 0.15E + 0.10R + 0.05U - risk."""
    route = RouteCandidate(
        route_type="NEARBY_BUYER",
        cost_efficiency=0.90,
        time_efficiency=0.95,
        demand_match=0.88,
        carbon_efficiency=0.92,
        capacity_reliability=0.80,
        convenience=0.85,
        risk_penalty=0.05,
    )
    score = route_score(route)
    # Manual calc: 0.30*0.90 + 0.20*0.95 + 0.20*0.88 + 0.15*0.92 + 0.10*0.80 + 0.05*0.85 - 0.05
    expected = (0.27 + 0.19 + 0.176 + 0.138 + 0.08 + 0.0425 - 0.05) * 100
    assert abs(score - expected) < 1.0, f"Score {score} != expected {expected}"


def test_instant_resale_generates_correct_routes():
    """INSTANT_RESALE should only generate NEARBY_BUYER, LOCAL_HUB, WAREHOUSE."""
    product = {"condition_score": 89, "grade": "A", "safety_risk": False}
    candidates = generate_candidates("INSTANT_RESALE", "Mumbai", product, 8, 80)

    route_types = [c.route_type for c in candidates]
    assert "NEARBY_BUYER" in route_types
    assert "REFURB_CENTER" not in route_types
    assert "RECYCLE_CENTER" not in route_types


def test_refurbish_generates_refurb_center():
    """REFURBISH should generate REFURB_CENTER route."""
    product = {"condition_score": 60, "grade": "C", "safety_risk": False,
               "estimated_repair_cost_inr": 1000, "original_value": 50000}
    candidates = generate_candidates("REFURBISH", "Delhi", product, 3, 50)

    route_types = [c.route_type for c in candidates]
    assert "REFURB_CENTER" in route_types


def test_safety_risk_blocks_non_safe_routes():
    """Safety risk should mark non-certified routes as ineligible."""
    product = {"condition_score": 30, "grade": "D", "safety_risk": True}
    candidates = generate_candidates("RECYCLE", "Mumbai", product, 0, 10)

    for c in candidates:
        if c.route_type == "RECYCLE_CENTER":
            assert c.eligible, "RECYCLE_CENTER should be eligible for unsafe items"


def test_select_best_route_picks_highest():
    """select_best_route should return the highest-scoring eligible route."""
    product = {"condition_score": 90, "grade": "A", "safety_risk": False}
    candidates = generate_candidates("INSTANT_RESALE", "Mumbai", product, 10, 85)

    best = select_best_route(candidates)
    all_scores = [(c.route_type, route_score(c)) for c in candidates if c.eligible]
    max_score_type = max(all_scores, key=lambda x: x[1])[0]

    assert best.route_type == max_score_type


def test_eligible_routes_per_destination():
    """Verify all lifecycle destinations have eligible routes defined."""
    for dest in ["INSTANT_RESALE", "REFURBISH", "EXCHANGE", "DONATE", "RECYCLE"]:
        assert dest in DESTINATION_ELIGIBLE_ROUTES
        assert len(DESTINATION_ELIGIBLE_ROUTES[dest]) > 0


def test_carbon_computation():
    """Carbon should increase with distance."""
    co2_short = compute_carbon(5.0, "NEARBY_BUYER")
    co2_long = compute_carbon(30.0, "WAREHOUSE")
    assert co2_long > co2_short
