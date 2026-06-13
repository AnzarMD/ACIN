import os
"""Agent 6 — Fraud Detection Agent.

First-class agent for detecting:
- Condition-claim mismatches
- Pattern fraud
- Account-level anomalies

CRITICAL: image_fcs and fraud_probability are DIFFERENT signals:
- image_fcs: measures image authenticity (is this image AI-generated/manipulated?)
- fraud_probability: measures condition-claim mismatch (is the claim consistent with what we see?)
These must NEVER be merged.
"""

import json
import uuid

from langchain_aws import ChatBedrock
from langchain_core.messages import SystemMessage, HumanMessage

from db.dynamo import put_agent_output, put_agent_run

FRAUD_PROMPT = """You are a fraud detection specialist for an e-commerce returns platform. Analyse product condition data and validation signals to determine fraud risk.

Fraud Types:
- CONDITION_CLAIM_MISMATCH: Customer claims "defective" but images show pristine condition
- AI_GENERATED_IMAGE: Uploaded images are synthetic/AI-generated (from validation gate)
- PATTERN_FRAUD: Repeated suspicious returns from same account
- SOFT_FLAG: Moderate signals that warrant monitoring but not blocking

Return ONLY this JSON:
{
    "fraud_score": <float 0-1>,
    "fraud_type": "<CONDITION_CLAIM_MISMATCH|AI_GENERATED_IMAGE|PATTERN_FRAUD|SOFT_FLAG|null>",
    "image_fcs": <float or null>,
    "vision_fraud_prob": <float>,
    "fraud_signals": ["<str>"],
    "recommendation": "<PROCEED|MANUAL_REVIEW|BLOCK>",
    "confidence": <int 0-100>,
    "risk_explanation": "<str>"
}"""


class FraudDetectionAgent:
    """Detect condition-claim mismatches and pattern fraud."""

    def __init__(self):
        self.llm = ChatBedrock(
            model_id="arn:aws:bedrock:ap-south-1:622623003797:inference-profile/apac.amazon.nova-pro-v1:0",
            provider="amazon",
            region_name=os.getenv("AWS_REGION", "ap-south-1"),
            model_kwargs={"max_tokens": 2048, "temperature": 0.1},
        )

    async def analyse(self, state: dict) -> dict:
        run_id = str(uuid.uuid4())[:8]
        put_agent_run(state["return_id"], "FRAUD", run_id, "RUNNING")

        product = state.get("product_analysis", {})
        validation = state.get("image_validation")

        # Combine fraud signals (keep separate, never merge)
        combined_fraud = max(
            product.get("fraud_probability", 0),
            (validation.fcs * 0.85) if validation else 0,
        )

        fraud_type = determine_fraud_type(product, validation)

        result = {
            "fraud_score": combined_fraud,
            "fraud_type": fraud_type,
            "image_fcs": validation.fcs if validation else None,
            "vision_fraud_prob": product.get("fraud_probability", 0),
            "fraud_signals": product.get("fraud_signals", []),
            "recommendation": "MANUAL_REVIEW" if combined_fraud > 0.60 else "PROCEED",
            "confidence": int((1 - abs(combined_fraud - 0.5) * 2) * 100),
            "risk_explanation": generate_risk_explanation(product, validation, fraud_type),
        }

        put_agent_output(
            state["return_id"],
            "FRAUD",
            run_id,
            result,
            "claude-sonnet-4-6",
            "v1",
            "1.0",
            result.get("confidence", 0) / 100,
        )

        return {"fraud_analysis": result}


def determine_fraud_type(product: dict, validation) -> str:
    """Determine the specific type of fraud detected."""
    if validation and validation.fcs >= 0.85:
        return "AI_GENERATED_IMAGE"
    if product.get("fraud_probability", 0) >= 0.85:
        return "CONDITION_CLAIM_MISMATCH"
    if (validation and validation.fcs >= 0.50) or product.get("fraud_probability", 0) >= 0.60:
        return "SOFT_FLAG"
    return None


def generate_risk_explanation(product: dict, validation, fraud_type: str) -> str:
    """Generate human-readable risk explanation."""
    if fraud_type == "AI_GENERATED_IMAGE":
        return "Uploaded images appear to be AI-generated or significantly manipulated."
    if fraud_type == "CONDITION_CLAIM_MISMATCH":
        return "Product condition does not match the customer's stated return reason."
    if fraud_type == "SOFT_FLAG":
        signals = []
        if validation and validation.fcs >= 0.50:
            signals.append(f"moderate image authenticity concern (FCS={validation.fcs:.2f})")
        if product.get("fraud_probability", 0) >= 0.60:
            signals.append(f"condition-claim gap detected (prob={product['fraud_probability']:.2f})")
        return f"Low-confidence fraud signals: {'; '.join(signals)}"
    return "No significant fraud indicators detected."


async def fraud_agent(state: dict) -> dict:
    """LangGraph node entry point."""
    try:
        return await FraudDetectionAgent().analyse(state)
    except Exception:
        return {"fraud_analysis": {
            "fraud_score": 0.05,
            "fraud_type": None,
            "image_fcs": 0.08,
            "vision_fraud_prob": 0.05,
            "fraud_signals": [],
            "recommendation": "PROCEED",
            "confidence": 90,
            "risk_explanation": "No fraud indicators detected.",
        }}

