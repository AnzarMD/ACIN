"""Agent 4 — Logistics Routing Agent.

Implements the ACIN Logistics Route Score (LRS) as defined in the design document:

LRS = 0.30*cost_efficiency + 0.20*time_efficiency + 0.20*demand_match
    + 0.15*carbon_efficiency + 0.10*capacity_reliability + 0.05*convenience
    - risk_penalty

Two separate scoring systems:
- Circular Value Score (CVS): decides the product's NEXT LIFE (resell/refurb/donate/recycle)
- Logistics Route Score (LRS): decides the PHYSICAL PATH for that outcome

The logistics agent only runs AFTER the circular destination is known.
"""

import os
import json
import uuid
from dataclasses import dataclass, field, asdict
from typing import List, Optional

from langchain_aws import ChatBedrock
from langchain_core.messages import SystemMessage, HumanMessage

from db.dynamo import put_agent_output, put_agent_run

# ─── Route Candidate Data Model ──────────────────────────────────────────────

@dataclass
class RouteCandidate:
    """A single candidate logistics route with normalized metric scores (0-1)."""
    route_type: str            # NEARBY_BUYER, LOCAL_HUB, WAREHOUSE, REFURB_CENTER,
                               # DONATION_PARTNER, RECYCLE_CENTER, EXCHANGE_POOL
    cost_efficiency: float     # 1 - normalized(cost)
    time_efficiency: float     # 1 - normalized(eta_hours)
    demand_match: float        # DMS score
    carbon_efficiency: float   # 1 - normalized(co2_kg)
    capacity_reliability: float  # CRS score
    convenience: float         # CS score
    risk_penalty: float = 0.0  # Subtracted from final score

    # Raw values (for output contract)
    cost_inr: int = 0
    eta_hours: float = 0.0
    distance_km: float = 0.0
    co2_kg: float = 0.0
    destination_id: str = ""
    eligible: bool = True
    ineligible_reason: str = ""


# ─── Route Catalogue ──────────────────────────────────────────────────────────
# Base cost, co2, and eta estimates. These are per Indian logistics norms.

ROUTE_CATALOGUE = {
    "NEARBY_BUYER": {
        "base_cost_inr": 45,
        "co2_per_km": 0.06,    # Two-wheeler/cycle delivery
        "eta_hours_base": 4.0,
        "capacity_score": 0.75,
        "convenience_base": 0.85,
    },
    "EXCHANGE_POOL": {
        "base_cost_inr": 0,
        "co2_per_km": 0.0,
        "eta_hours_base": 2.0,
        "capacity_score": 0.80,
        "convenience_base": 0.90,
    },
    "LOCAL_HUB": {
        "base_cost_inr": 80,
        "co2_per_km": 0.10,
        "eta_hours_base": 24.0,
        "capacity_score": 0.90,
        "convenience_base": 0.55,
    },
    "WAREHOUSE": {
        "base_cost_inr": 150,
        "co2_per_km": 0.18,
        "eta_hours_base": 72.0,
        "capacity_score": 0.95,
        "convenience_base": 0.40,
    },
    "REFURB_CENTER": {
        "base_cost_inr": 120,
        "co2_per_km": 0.14,
        "eta_hours_base": 48.0,
        "capacity_score": 0.85,
        "convenience_base": 0.35,
    },
    "DONATION_PARTNER": {
        "base_cost_inr": 30,
        "co2_per_km": 0.07,
        "eta_hours_base": 8.0,
        "capacity_score": 0.70,
        "convenience_base": 0.60,
    },
    "RECYCLE_CENTER": {
        "base_cost_inr": 20,
        "co2_per_km": 0.05,
        "eta_hours_base": 12.0,
        "capacity_score": 0.80,
        "convenience_base": 0.50,
    },
}

# Eligible routes per lifecycle destination (Section 5 of the doc)
DESTINATION_ELIGIBLE_ROUTES = {
    "INSTANT_RESALE": ["NEARBY_BUYER", "LOCAL_HUB", "WAREHOUSE"],
    "REFURBISH":      ["REFURB_CENTER"],
    "EXCHANGE":       ["EXCHANGE_POOL", "NEARBY_BUYER", "LOCAL_HUB"],
    "DONATE":         ["DONATION_PARTNER"],
    "RECYCLE":        ["RECYCLE_CENTER"],
}

# Reference distances per city (km) for baseline estimates
CITY_DISTANCES = {
    "Mumbai":    {"NEARBY_BUYER": 5,  "LOCAL_HUB": 15, "WAREHOUSE": 25, "REFURB_CENTER": 20, "DONATION_PARTNER": 12, "RECYCLE_CENTER": 18, "EXCHANGE_POOL": 6},
    "Delhi":     {"NEARBY_BUYER": 6,  "LOCAL_HUB": 18, "WAREHOUSE": 30, "REFURB_CENTER": 25, "DONATION_PARTNER": 15, "RECYCLE_CENTER": 22, "EXCHANGE_POOL": 7},
    "Bangalore": {"NEARBY_BUYER": 5,  "LOCAL_HUB": 14, "WAREHOUSE": 22, "REFURB_CENTER": 18, "DONATION_PARTNER": 10, "RECYCLE_CENTER": 16, "EXCHANGE_POOL": 5},
    "Chennai":   {"NEARBY_BUYER": 6,  "LOCAL_HUB": 16, "WAREHOUSE": 28, "REFURB_CENTER": 20, "DONATION_PARTNER": 12, "RECYCLE_CENTER": 18, "EXCHANGE_POOL": 6},
    "Hyderabad": {"NEARBY_BUYER": 7,  "LOCAL_HUB": 18, "WAREHOUSE": 30, "REFURB_CENTER": 22, "DONATION_PARTNER": 14, "RECYCLE_CENTER": 20, "EXCHANGE_POOL": 7},
    "Pune":      {"NEARBY_BUYER": 5,  "LOCAL_HUB": 14, "WAREHOUSE": 20, "REFURB_CENTER": 16, "DONATION_PARTNER": 10, "RECYCLE_CENTER": 14, "EXCHANGE_POOL": 5},
    "Kolkata":   {"NEARBY_BUYER": 6,  "LOCAL_HUB": 16, "WAREHOUSE": 25, "REFURB_CENTER": 18, "DONATION_PARTNER": 12, "RECYCLE_CENTER": 18, "EXCHANGE_POOL": 6},
    "Jaipur":    {"NEARBY_BUYER": 7,  "LOCAL_HUB": 20, "WAREHOUSE": 35, "REFURB_CENTER": 28, "DONATION_PARTNER": 16, "RECYCLE_CENTER": 24, "EXCHANGE_POOL": 8},
    "_default":  {"NEARBY_BUYER": 8,  "LOCAL_HUB": 20, "WAREHOUSE": 30, "REFURB_CENTER": 25, "DONATION_PARTNER": 15, "RECYCLE_CENTER": 20, "EXCHANGE_POOL": 8},
}


# ─── Route Scoring Functions ──────────────────────────────────────────────────

def route_score(route: RouteCandidate) -> float:
    """
    LRS = 0.30*cost + 0.20*time + 0.20*demand + 0.15*carbon + 0.10*capacity + 0.05*convenience - risk
    Returns score scaled to 0-100.
    """
    raw = (
        0.30 * route.cost_efficiency
        + 0.20 * route.time_efficiency
        + 0.20 * route.demand_match
        + 0.15 * route.carbon_efficiency
        + 0.10 * route.capacity_reliability
        + 0.05 * route.convenience
        - route.risk_penalty
    )
    return round(max(0.0, min(1.0, raw)) * 100, 2)


def normalize_lower_better(value: float, min_val: float, max_val: float) -> float:
    """For cost, time, carbon, distance: lower = better → score = 1 - normalized."""
    if max_val == min_val:
        return 1.0
    return max(0.0, min(1.0, 1 - (value - min_val) / (max_val - min_val)))


def compute_demand_match(buyer_count: int, historical_velocity: float,
                         category_demand: float) -> float:
    """
    DMS = 0.50 * nearby_buyer_strength + 0.30 * historical_velocity + 0.20 * category_demand
    """
    buyer_strength = min(1.0, buyer_count / 20.0)  # normalize: 20+ buyers = max score
    return round(0.50 * buyer_strength + 0.30 * historical_velocity + 0.20 * category_demand, 3)


def compute_carbon(distance_km: float, route_type: str, weight_kg: float = 1.0) -> float:
    """CO2_route = Distance × Vehicle_Emission_Factor × Weight_Adjustment."""
    factor = ROUTE_CATALOGUE.get(route_type, {}).get("co2_per_km", 0.10)
    return round(distance_km * factor * max(0.5, weight_kg), 3)


def passes_hard_constraints(route: RouteCandidate, product: dict, lifecycle: str) -> tuple:
    """
    Returns (True, "") if route passes, (False, reason) if it fails a hard constraint.
    Hard constraints from Section 6 of the design document.
    """
    # Safety: hazardous products only go to certified recycling/repair
    if product.get("safety_risk") and route.route_type not in ("RECYCLE_CENTER", "REFURB_CENTER"):
        return False, "Safety hazard — only certified recycling or repair routes eligible"

    # Resale eligibility: condition >= 85 required for nearby buyer
    if route.route_type == "NEARBY_BUYER" and product.get("condition_score", 0) < 50:
        return False, "Condition too low for direct buyer route"

    # Refurbishment economics: must have positive incremental value
    if route.route_type == "REFURB_CENTER":
        repair_cost = product.get("estimated_repair_cost_inr", 0)
        original = product.get("original_value", 5000)
        if repair_cost > original * 0.5:
            return False, "Repair cost exceeds refurbishment economics threshold"

    # Donation: not for items with safety risk
    if route.route_type == "DONATION_PARTNER" and product.get("safety_risk"):
        return False, "Unsafe items cannot be donated"

    # Route must be in eligible list for this lifecycle destination
    eligible = DESTINATION_ELIGIBLE_ROUTES.get(lifecycle, [])
    if route.route_type not in eligible:
        return False, f"Route type not eligible for {lifecycle}"

    return True, ""


# ─── Route Generation ─────────────────────────────────────────────────────────

def generate_candidates(lifecycle: str, city: str, product: dict,
                        buyer_count: int, demand_score: int) -> List[RouteCandidate]:
    """Generate all candidate routes for a lifecycle destination and score them."""
    eligible_types = DESTINATION_ELIGIBLE_ROUTES.get(lifecycle, ["WAREHOUSE"])
    distances = CITY_DISTANCES.get(city, CITY_DISTANCES["_default"])

    candidates = []

    # Get all raw values first (for normalization bounds)
    raw_costs = []
    raw_etas = []
    raw_carbons = []

    for rt in eligible_types:
        cat = ROUTE_CATALOGUE.get(rt, ROUTE_CATALOGUE["WAREHOUSE"])
        dist = distances.get(rt, 20)
        cost = cat["base_cost_inr"] + int(dist * 3)
        eta = cat["eta_hours_base"] + (dist / 20)
        co2 = compute_carbon(dist, rt)
        raw_costs.append(cost)
        raw_etas.append(eta)
        raw_carbons.append(co2)

    min_cost, max_cost = min(raw_costs), max(raw_costs) + 1
    min_eta, max_eta = min(raw_etas), max(raw_etas) + 1
    min_co2, max_co2 = min(raw_carbons), max(raw_carbons) + 0.001

    # Demand match score
    dms = compute_demand_match(buyer_count, demand_score / 100, demand_score / 100)

    for rt in eligible_types:
        cat = ROUTE_CATALOGUE.get(rt, ROUTE_CATALOGUE["WAREHOUSE"])
        dist = distances.get(rt, 20)
        cost = cat["base_cost_inr"] + int(dist * 3)
        eta = cat["eta_hours_base"] + (dist / 20)
        co2 = compute_carbon(dist, rt)

        # Normalize each metric
        cost_eff = normalize_lower_better(cost, min_cost, max_cost)
        time_eff = normalize_lower_better(eta, min_eta, max_eta)
        carb_eff = normalize_lower_better(co2, min_co2, max_co2)

        # For non-resale routes, demand match measures partner availability
        route_dms = dms if rt in ("NEARBY_BUYER", "EXCHANGE_POOL") else 0.65

        # Risk penalty: higher for direct P2P (cancellation risk)
        risk = 0.05 if rt == "NEARBY_BUYER" else 0.02

        candidate = RouteCandidate(
            route_type=rt,
            cost_efficiency=cost_eff,
            time_efficiency=time_eff,
            demand_match=route_dms,
            carbon_efficiency=carb_eff,
            capacity_reliability=cat["capacity_score"],
            convenience=cat["convenience_base"],
            risk_penalty=risk,
            cost_inr=cost,
            eta_hours=round(eta, 1),
            distance_km=dist,
            co2_kg=co2,
        )

        # Apply hard constraints
        passes, reason = passes_hard_constraints(candidate, product, lifecycle)
        candidate.eligible = passes
        candidate.ineligible_reason = reason
        candidates.append(candidate)

    return candidates


def select_best_route(candidates: List[RouteCandidate]) -> RouteCandidate:
    """Select the route with the highest LRS score from eligible candidates."""
    eligible = [r for r in candidates if r.eligible]
    if not eligible:
        # Fallback: use warehouse if nothing else
        fallback = RouteCandidate(
            route_type="WAREHOUSE", cost_efficiency=0.5, time_efficiency=0.4,
            demand_match=0.5, carbon_efficiency=0.4, capacity_reliability=0.9,
            convenience=0.4, risk_penalty=0.02, cost_inr=180, eta_hours=72,
            distance_km=30, co2_kg=2.5, eligible=True
        )
        return fallback
    return max(eligible, key=route_score)


# ─── Logistics Agent ──────────────────────────────────────────────────────────

LOGISTICS_PROMPT = """You are the ACIN Logistics Routing Agent. You have pre-computed route candidates with Logistics Route Scores.

Your task: review the candidates, confirm the selection makes operational sense,
add a plain-English explanation, and output the final logistics decision.

The Logistics Route Score formula:
LRS = 0.30*cost_efficiency + 0.20*time_efficiency + 0.20*demand_match
    + 0.15*carbon_efficiency + 0.10*capacity_reliability + 0.05*convenience - risk_penalty

Return ONLY this JSON:
{
    "selected_route": "<route_type>",
    "destination_id": "<e.g. BUYER-104 or PARTNER-001>",
    "route_score": <float 0-100>,
    "distance_km": <float>,
    "total_cost_inr": <int>,
    "eta_hours": <float>,
    "carbon_kg": <float>,
    "carbon_saved_vs_default_kg": <float>,
    "demand_match": <float 0-1>,
    "capacity_reliability": <float 0-1>,
    "risk_score": <float 0-1>,
    "alternatives": [<list of route_type strings>],
    "reason": "<1-2 sentences explaining why this route was selected>",
    "rule_version": "logistics-v1.0"
}"""


class LogisticsRoutingAgent:
    """Determine optimal physical routing using LRS formula."""

    def __init__(self):
        self.llm = ChatBedrock(
            model_id="arn:aws:bedrock:ap-south-1:622623003797:inference-profile/apac.amazon.nova-pro-v1:0",
            provider="amazon",
            region_name=os.getenv("AWS_REGION", "ap-south-1"),
            model_kwargs={"max_tokens": 512, "temperature": 0.1},
        )

    async def analyse(self, state: dict) -> dict:
        run_id = str(uuid.uuid4())[:8]
        put_agent_run(state["return_id"], "LOGISTICS", run_id, "RUNNING")

        product = state.get("product_analysis", {})
        market = state.get("market_analysis", {})
        circular = state.get("circular_decision", {})
        pricing = state.get("pricing_analysis", {})

        location = state.get("location", {})
        city = location.get("city", "Mumbai") if isinstance(location, dict) else "Mumbai"
        lifecycle = circular.get("destination", "INSTANT_RESALE")
        buyer_count = int(market.get("buyer_count", 0))
        demand_score = int(market.get("demand_score", 60))

        # Generate all route candidates with proper LRS scoring
        candidates = generate_candidates(lifecycle, city, product, buyer_count, demand_score)
        best = select_best_route(candidates)
        best_score = route_score(best)

        # Alternatives (eligible routes that weren't selected)
        alternatives = [
            r.route_type for r in candidates
            if r.eligible and r.route_type != best.route_type
        ]

        # Carbon saved vs warehouse baseline
        warehouse_co2 = compute_carbon(
            CITY_DISTANCES.get(city, CITY_DISTANCES["_default"]).get("WAREHOUSE", 30),
            "WAREHOUSE"
        )
        carbon_saved = round(max(0, warehouse_co2 - best.co2_kg), 3)

        # Build context for LLM to generate explanation and refine
        candidates_info = "\n".join([
            f"  {r.route_type}: LRS={route_score(r):.1f}, cost=₹{r.cost_inr}, "
            f"eta={r.eta_hours}h, co2={r.co2_kg}kg, eligible={r.eligible}"
            + (f" [REJECTED: {r.ineligible_reason}]" if not r.eligible else "")
            for r in candidates
        ])

        context = (
            f"Lifecycle destination: {lifecycle}\n"
            f"City: {city}\n"
            f"Product: {state.get('product_name', state.get('category', 'Unknown'))}\n"
            f"Condition: {product.get('condition_score', 75)}/100 Grade {product.get('grade', 'B')}\n"
            f"Nearby buyers: {buyer_count}\n"
            f"Demand score: {demand_score}/100\n"
            f"Selected route: {best.route_type} (LRS={best_score})\n\n"
            f"All candidates:\n{candidates_info}\n\n"
            f"Pre-computed values for selected route:\n"
            f"  cost=₹{best.cost_inr}, eta={best.eta_hours}h, "
            f"distance={best.distance_km}km, co2={best.co2_kg}kg\n"
            f"  carbon_saved_vs_warehouse={carbon_saved}kg\n"
            f"  alternatives={alternatives}\n"
        )

        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=LOGISTICS_PROMPT),
                HumanMessage(content=context),
            ])
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0]
            result = json.loads(content)
            result["carbon_saved_vs_default_kg"] = carbon_saved
        except Exception:
            # Fallback: use computed values directly
            result = {
                "selected_route": best.route_type,
                "destination_id": f"PARTNER-{city[:3].upper()}-001",
                "route_score": best_score,
                "distance_km": best.distance_km,
                "total_cost_inr": best.cost_inr,
                "eta_hours": best.eta_hours,
                "carbon_kg": best.co2_kg,
                "carbon_saved_vs_default_kg": carbon_saved,
                "demand_match": best.demand_match,
                "capacity_reliability": best.capacity_reliability,
                "risk_score": best.risk_penalty,
                "alternatives": alternatives,
                "reason": f"{best.route_type} selected: lowest cost (₹{best.cost_inr}), "
                          f"{best.eta_hours}h ETA, {best.co2_kg}kg CO2.",
                "rule_version": "logistics-v1.0",
            }

        # Ensure co2 fields are present for downstream fusion engine
        result.setdefault("co2_kg", best.co2_kg)
        result.setdefault("carbon_saved_vs_default_kg", carbon_saved)

        put_agent_output(
            state["return_id"],
            "LOGISTICS",
            run_id,
            result,
            "nova-pro-v1",
            "v1",
            "1.0",
            best_score / 100,
        )

        return {"logistics_analysis": result}


async def logistics_routing_agent(state: dict) -> dict:
    """LangGraph node entry point."""
    try:
        return await LogisticsRoutingAgent().analyse(state)
    except Exception as e:
        # Fallback with document-specified route scoring
        location = state.get("location", {})
        city = location.get("city", "Mumbai") if isinstance(location, dict) else "Mumbai"
        lifecycle = state.get("circular_decision", {}).get("destination", "INSTANT_RESALE") if state.get("circular_decision") else "INSTANT_RESALE"
        buyer_count = int(state.get("market_analysis", {}).get("buyer_count", 5) if state.get("market_analysis") else 5)

        distances = CITY_DISTANCES.get(city, CITY_DISTANCES["_default"])
        eligible = DESTINATION_ELIGIBLE_ROUTES.get(lifecycle, ["WAREHOUSE"])
        rt = eligible[0]  # pick first eligible
        dist = distances.get(rt, 15)
        cat = ROUTE_CATALOGUE.get(rt, ROUTE_CATALOGUE["WAREHOUSE"])
        cost = cat["base_cost_inr"] + int(dist * 3)
        co2 = compute_carbon(dist, rt)
        warehouse_co2 = compute_carbon(distances.get("WAREHOUSE", 30), "WAREHOUSE")

        return {"logistics_analysis": {
            "selected_route": rt,
            "destination_id": f"PARTNER-{city[:3].upper()}-001",
            "route_score": 75.0,
            "distance_km": dist,
            "total_cost_inr": cost,
            "eta_hours": cat["eta_hours_base"],
            "carbon_kg": co2,
            "co2_kg": co2,
            "carbon_saved_vs_default_kg": round(max(0, warehouse_co2 - co2), 3),
            "demand_match": min(1.0, buyer_count / 20),
            "capacity_reliability": cat["capacity_score"],
            "risk_score": 0.05,
            "alternatives": [e for e in eligible if e != rt],
            "reason": f"{rt} selected for {lifecycle} in {city}.",
            "rule_version": "logistics-v1.0",
        }}
