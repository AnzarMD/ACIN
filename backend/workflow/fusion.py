"""Decision Fusion Engine & CVS Formula.

Aggregates all agent outputs into a single Circular Value Score (CVS).

CVS = (
    0.30 * condition_score (from Product Intelligence Agent, 0-100)
    + 0.25 * demand_score (from Market Intelligence Agent, 0-100)
    + 0.20 * profitability_score (balanced_price / original_price * 100, capped at 100)
    + 0.15 * sustainability_score (100 - carbon_kg * 15)
    + 0.10 * customer_value (50 + demand_score * 0.5)
)

CVS Thresholds:
- CVS >= 75 → INSTANT_RESALE
- CVS 55-74 → REFURBISH
- CVS 40-54 → DONATE
- CVS < 40  → RECYCLE
- Exchange flag overrides when size/color mismatch detected
"""

import os

import uuid
from typing import Optional

from langchain_aws import ChatBedrock
from langchain_core.messages import SystemMessage, HumanMessage

from db.dynamo import (
    put_decision,
    update_return_status,
    update_features_latest,
    record_carbon_txn,
    put_trust_badge,
)
from models.return_model import ReturnStatus


def compute_cvs(product: dict, market: dict, pricing: dict, logistics: dict, circular: dict) -> float:
    """Compute Circular Value Score from agent outputs.

    Formula:
        CVS = 0.30 * condition_score
            + 0.25 * demand_score
            + 0.20 * profitability_score
            + 0.15 * sustainability_score
            + 0.10 * customer_value
    """
    # condition_score from Product Intelligence Agent (0-100)
    condition_score = product.get("condition_score", 50)

    # demand_score from Market Intelligence Agent (0-100)
    demand_score = market.get("demand_score", 50)

    # profitability_score = balanced_price / original_price * 100, capped at 100
    original_price = pricing.get("original_price", 5000)
    balanced_price = pricing.get("balanced_price", 3500)
    profitability_score = min(100, (balanced_price / max(original_price, 1)) * 100)

    # sustainability_score = 100 - carbon_kg * 15
    carbon_kg = logistics.get("carbon_kg", logistics.get("co2_kg", 0.8))
    sustainability_score = 100 - (carbon_kg * 15)

    # customer_value = 50 + demand_score * 0.5
    customer_value = 50 + (demand_score * 0.5)

    # Weighted CVS calculation
    cvs = (
        0.30 * condition_score
        + 0.25 * demand_score
        + 0.20 * profitability_score
        + 0.15 * sustainability_score
        + 0.10 * customer_value
    )

    return round(cvs, 2)


def determine_destination(cvs: float, state: dict, product: dict, pricing: dict) -> str:
    """Determine final destination from CVS, return reason, and product context.

    Return reason heavily influences the decision:
    - size/colour/variant mismatch → EXCHANGE (always override)
    - defective/damaged + positive repair ROI → REFURBISH
    - changed_mind + good condition → INSTANT_RESALE preferred
    - very low condition or unsafe → RECYCLE

    CVS thresholds (as fallback when reason doesn't override):
    >= 75 → INSTANT_RESALE
    55-74 → REFURBISH
    40-54 → DONATE
    < 40  → RECYCLE
    """
    return_reason = (state.get("return_reason", "") or "").lower()
    condition_score = product.get("condition_score", 50)
    safety_risk = product.get("safety_risk", False)
    repair_cost = product.get("estimated_repair_cost_inr", 0)
    original_price = state.get("original_price", 5000) or 5000
    balanced_price = pricing.get("balanced_price", 0)

    # Rule 1: Safety risk → RECYCLE always
    if safety_risk:
        return "RECYCLE"

    # Rule 2: Size/colour/variant mismatch → EXCHANGE (customer obsession override)
    mismatch_signals = ["size", "colour", "color", "variant", "didn't match", "wrong size",
                        "size_mismatch", "didnt_fit", "wrong item", "not_as_described"]
    if any(kw in return_reason for kw in mismatch_signals):
        return "EXCHANGE"

    # Rule 3: Defective/damaged + positive repair ROI → REFURBISH
    defective_signals = ["defective", "not working", "damaged", "broken", "faulty",
                         "damaged_in_transit", "not_as_described"]
    if any(kw in return_reason for kw in defective_signals):
        if repair_cost > 0 and balanced_price > repair_cost:
            return "REFURBISH"
        if condition_score >= 50 and repair_cost < original_price * 0.3:
            return "REFURBISH"

    # Rule 4: Changed mind + good condition → push toward INSTANT_RESALE
    if "changed_mind" in return_reason or "changed mind" in return_reason or "better_price" in return_reason:
        if condition_score >= 80:
            return "INSTANT_RESALE"
        if condition_score >= 60:
            return "INSTANT_RESALE" if cvs >= 60 else "REFURBISH"

    # Rule 5: Very poor condition → force RECYCLE
    if condition_score < 30:
        return "RECYCLE"

    # Rule 6: CVS-based routing (spec thresholds)
    if cvs >= 75:
        return "INSTANT_RESALE"
    elif cvs >= 55:
        return "REFURBISH"
    elif cvs >= 40:
        return "DONATE"
    else:
        return "RECYCLE"


def determine_review_reason(features: dict) -> Optional[str]:
    """Keep image_fcs and fraud_probability SEPARATE — different signals."""
    if features.get("image_fcs", 0) >= 0.85:
        return "AI_GENERATED_IMAGE"  # authenticity issue
    if features.get("fraud_probability", 0) >= 0.85:
        return "CONDITION_CLAIM_MISMATCH"  # condition-vs-claim issue
    if features.get("image_fcs", 0) >= 0.50 or features.get("fraud_probability", 0) >= 0.60:
        return "SOFT_FLAG"
    return None


def generate_trust_badges(product: dict, fraud: dict, validation) -> list:
    """Generate trust badges for the decision."""
    badges = []

    # AI Verified badge
    if validation and validation.fcs < 0.30:
        badges.append("AI_VERIFIED")

    # Low fraud risk badge
    if fraud.get("fraud_score", 1.0) < 0.30:
        badges.append("LOW_FRAUD_RISK")

    # Grade badge
    grade = product.get("grade", "")
    if grade == "A":
        badges.append("GRADE_A")
    elif grade == "B":
        badges.append("GRADE_B")

    return badges


EXPLANATION_PROMPT = """You are the ACIN Decision Explanation Engine. Given the following analysis results, generate a clear, concise, customer-friendly explanation for the routing decision.

Rules:
- Maximum 3 sentences
- Use specific numbers (condition score, buyer count, CO2 saved)
- Explain WHY this destination was chosen — mention the return reason if it influenced the decision
- NEVER mention "AI detection", "forgery", or internal FCS scores
- Positive framing — focus on best outcome for customer and environment
- End with the environmental impact

Examples by return reason:
- defective: "Due to reported defect, the item scored {condition_score}/100 and repair cost of Rs {repair_cost} gives {repair_roi}% ROI at the refurb centre."
- size_mismatch: "Size mismatch returns qualify for direct exchange with no warehouse time."
- changed_mind: "Item is in {grade} condition with {buyer_count} buyers nearby making instant resale the best option."

Input:
- Return Reason: {return_reason}
- Destination: {destination}
- CVS Score: {cvs_score}/100
- Condition Score: {condition_score}
- Grade: {grade}
- Nearby Buyers: {buyer_count}
- Expected Sale Days: {expected_sale_days}
- Recovery Price: Rs {listing_price}
- CO2 Saved: {carbon_saved_kg} kg
- Repair Cost: Rs {repair_cost}
- Repair ROI: {repair_roi}%

Return ONLY the plain-language explanation string."""


async def generate_explanation(decision_data: dict) -> str:
    """Generate customer-friendly explanation using Claude."""
    try:
        llm = ChatBedrock(
            model_id="arn:aws:bedrock:ap-south-1:622623003797:inference-profile/apac.amazon.nova-pro-v1:0",
            provider="amazon",
            region_name=os.getenv("AWS_REGION", "ap-south-1"),
            model_kwargs={"max_tokens": 256, "temperature": 0.3},
        )

        prompt = EXPLANATION_PROMPT.format(**decision_data)
        response = await llm.ainvoke([
            SystemMessage(content=prompt),
            HumanMessage(content="Generate the explanation now."),
        ])
        return response.content.strip().strip('"')
    except Exception:
        # Fallback explanation
        return (
            f"Product scored {decision_data.get('condition_score', 'N/A')}/100 condition. "
            f"{decision_data.get('buyer_count', 0)} buyers nearby. "
            f"This decision saves {decision_data.get('carbon_saved_kg', 0)} kg CO2."
        )


async def decision_fusion_engine(state: dict) -> dict:
    """LangGraph node: compute CVS, determine destination, generate explanation.

    CVS Formula (from design doc):
        CVS = 0.30 × condition_score   (Product Intelligence Agent, 0-100)
            + 0.25 × demand_score      (Market Intelligence Agent, 0-100)
            + 0.20 × profitability     (balanced_price / original_price × 100, capped 100)
            + 0.15 × sustainability    (100 - carbon_kg × 15)
            + 0.10 × customer_value    (50 + demand_score × 0.5)

    Return Reason influences destination BEFORE CVS thresholds:
        - size_mismatch / didnt_fit → EXCHANGE (override)
        - defective + repair ROI > 0 → REFURBISH preferred
        - damaged_in_transit → REFURBISH
        - changed_mind + condition >= 85 → INSTANT_RESALE preferred
    """
    product = state.get("product_analysis", {})
    market = state.get("market_analysis", {})
    pricing = state.get("pricing_analysis", {})
    logistics = state.get("logistics_analysis", {})
    circular = state.get("circular_decision", {})
    fraud = state.get("fraud_analysis", {})
    validation = state.get("image_validation")

    # Check if fraud requires manual review
    if fraud.get("recommendation") == "MANUAL_REVIEW":
        update_return_status(state["return_id"], ReturnStatus.MANUAL_REVIEW)

    # Compute CVS using the exact formula from the design document
    cvs = compute_cvs(product, market, pricing, logistics, circular)

    # Determine destination — return reason drives this, not just CVS
    destination = determine_destination(cvs, state, product, pricing)

    # Circular agent can further refine if it has high confidence
    circular_dest = circular.get("destination", "")
    circular_conf = int(circular.get("confidence", 0))
    if circular_conf > 90 and circular_dest:
        destination = circular_dest

    # Carbon savings: logistics agent provides the real number.
    # Fallback: estimate from logistics route vs warehouse baseline (NOT hardcoded 2.4)
    logistics_co2 = float(logistics.get("carbon_kg", logistics.get("co2_kg", 0.8)))
    # Warehouse baseline: ~30km × 0.18 kg/km = 5.4 kg CO2
    warehouse_baseline = 5.4
    carbon_saved = float(logistics.get("carbon_saved_vs_default_kg",
                    max(0, warehouse_baseline - logistics_co2)))

    # Listing price and recovery
    listing_price = int(pricing.get("balanced_price", 0))

    # Confidence: use circular agent's real confidence, not hardcoded 85
    confidence = circular_conf if circular_conf > 0 else (
        90 if cvs >= 75 else 80 if cvs >= 55 else 70 if cvs >= 40 else 60
    )

    # Generate trust badges
    trust_badges = generate_trust_badges(product, fraud, validation)

    # Prepare explanation data — include return_reason for context-aware explanation
    explanation_data = {
        "destination": destination,
        "return_reason": state.get("return_reason", "unknown"),
        "condition_score": product.get("condition_score", 0),
        "grade": product.get("grade", "B"),
        "buyer_count": market.get("buyer_count", 0),
        "expected_sale_days": market.get("expected_sale_days", 5),
        "listing_price": listing_price,
        "carbon_saved_kg": round(carbon_saved, 2),
        "repair_cost": product.get("estimated_repair_cost_inr", 0),
        "repair_roi": circular.get("repair_roi_percentage", 0) or 0,
        "cvs_score": cvs,
    }

    # Generate explanation
    explanation = await generate_explanation(explanation_data)

    # Build final decision
    final_decision = {
        "destination": destination,
        "cvs_score": cvs,
        "confidence": confidence,
        "fraud_check": "CLEAR" if fraud.get("fraud_score", 0) < 0.30 else "FLAGGED",
        "image_fcs": validation.fcs if validation else 0.0,
        "fraud_probability": product.get("fraud_probability", 0),
        "listing_price": listing_price,
        "carbon_saved_kg": round(carbon_saved, 2),
        "revenue_recovery_inr": listing_price,
        "trust_badges": trust_badges,
        "explanation": explanation,
        "grade": product.get("grade", "B"),
        "return_reason": state.get("return_reason", ""),
    }

    # Persist decision
    put_decision(state["return_id"], final_decision)

    # Update features latest
    update_features_latest(state["return_id"], {
        "condition_score": product.get("condition_score", 0),
        "demand_score": market.get("demand_score", 0),
        "pricing_score": round(listing_price / max(int(state.get("original_price") or 5000), 1), 3),
        "carbon_score": round(carbon_saved, 2),
        "fraud_score": fraud.get("fraud_score", 0),
        "image_fcs": validation.fcs if validation else 0.0,
    })

    # Record carbon transaction
    record_carbon_txn(
        state["return_id"],
        carbon_saved,
        destination.split("_")[0] if "_" in destination else destination,
    )

    # Add trust badges to DB
    for badge in trust_badges:
        put_trust_badge(state["return_id"], badge, f"Auto-assigned: {destination}")

    # Update status to DECIDED
    update_return_status(state["return_id"], ReturnStatus.DECIDED)

    return {"final_decision": final_decision}

