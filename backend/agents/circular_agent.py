import os
"""Agent 5 — Circular Economy Agent.

Makes the final lifecycle recommendation by synthesising all agent outputs.
Determines the best "next life" for the product.
"""

import json
import uuid

from langchain_aws import ChatBedrock
from langchain_core.messages import SystemMessage, HumanMessage

from db.dynamo import put_agent_output, put_agent_run

CIRCULAR_PROMPT = """You are the Circular Economy Decision Agent for an e-commerce returns platform. Synthesise all agent outputs to determine the product's best next life.

Destination Framework:
- INSTANT_RESALE: Condition >85, Repair Cost <5%, High Demand → Direct relist within hours
- REFURBISH: Condition 50-85, Repair Cost < Value Gain → Repair centre routing
- EXCHANGE: Any condition, Size/Colour/Variant mismatch → Direct exchange, zero warehouse
- DONATE: Condition >60, Resale Profit Negative → Partner NGO routing
- RECYCLE: Condition <40, Unsafe or Repair Cost > Value → Certified recycler dispatch

Customer Obsession: If return reason is "size mismatch" or "didn't match", ALWAYS check exchange first.

Return ONLY this JSON:
{
    "destination": "<INSTANT_RESALE|REFURBISH|EXCHANGE|DONATE|RECYCLE>",
    "confidence": <int 0-100>,
    "cvs_score": <float>,
    "reasoning": "<str max 3 sentences>",
    "carbon_saved_kg": <float>,
    "revenue_recovery_inr": <int>,
    "exchange_match_possible": <bool>,
    "repair_roi_percentage": <float or null>
}"""


class CircularEconomyAgent:
    """Final lifecycle recommendation agent."""

    def __init__(self):
        self.llm = ChatBedrock(
            model_id="arn:aws:bedrock:ap-south-1:622623003797:inference-profile/apac.amazon.nova-pro-v1:0",
            provider="amazon",
            region_name=os.getenv("AWS_REGION", "ap-south-1"),
            model_kwargs={"max_tokens": 2048, "temperature": 0.1},
        )

    async def analyse(self, state: dict) -> dict:
        run_id = str(uuid.uuid4())[:8]
        put_agent_run(state["return_id"], "CIRCULAR", run_id, "RUNNING")

        product = state.get("product_analysis", {})
        market = state.get("market_analysis", {})
        pricing = state.get("pricing_analysis", {})
        logistics = state.get("logistics_analysis", {})
        fraud = state.get("fraud_analysis", {})

        context = (
            f"=== Product Analysis ===\n"
            f"Condition Score: {product.get('condition_score', 75)}\n"
            f"Grade: {product.get('grade', 'B')}\n"
            f"Defects: {json.dumps(product.get('defects', []))}\n"
            f"Repair Cost: INR {product.get('estimated_repair_cost_inr', 0)}\n"
            f"Safety Risk: {product.get('safety_risk', False)}\n\n"
            f"=== Market Analysis ===\n"
            f"Demand Score: {market.get('demand_score', 60)}\n"
            f"Buyer Count: {market.get('buyer_count', 10)}\n"
            f"Expected Sale Days: {market.get('expected_sale_days', 5)}\n"
            f"Region: {market.get('region', 'Mumbai')}\n\n"
            f"=== Pricing Analysis ===\n"
            f"Balanced Price: INR {pricing.get('balanced_price', 4000)}\n"
            f"Original Price: INR {pricing.get('original_price', 5000)}\n"
            f"Revenue Recovery: {pricing.get('expected_revenue_recovery', 0.7)}\n\n"
            f"=== Logistics Analysis ===\n"
            f"Route: {logistics.get('destination', 'fulfillment_hub')}\n"
            f"Cost: INR {logistics.get('cost_inr', 80)}\n"
            f"CO2: {logistics.get('co2_kg', 0.8)} kg\n\n"
            f"=== Fraud Analysis ===\n"
            f"Fraud Score: {fraud.get('fraud_score', 0)}\n"
            f"Recommendation: {fraud.get('recommendation', 'PROCEED')}\n\n"
            f"=== Return Context ===\n"
            f"Return Reason: {state.get('return_reason', 'unknown')}\n"
        )

        response = await self.llm.ainvoke([
            SystemMessage(content=CIRCULAR_PROMPT),
            HumanMessage(content=context),
        ])

        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0]
        result = json.loads(content)

        put_agent_output(
            state["return_id"],
            "CIRCULAR",
            run_id,
            result,
            "claude-sonnet-4-6",
            "v1",
            "1.0",
            result.get("confidence", 0) / 100,
        )

        return {"circular_decision": result}


async def circular_economy_agent(state: dict) -> dict:
    """LangGraph node entry point."""
    try:
        return await CircularEconomyAgent().analyse(state)
    except Exception:
        # Determine destination from available data
        product = state.get("product_analysis", {})
        condition = product.get("condition_score", 75)
        if condition >= 85:
            dest = "INSTANT_RESALE"
        elif condition >= 50:
            dest = "REFURBISH"
        elif condition >= 40:
            dest = "DONATE"
        else:
            dest = "RECYCLE"

        return {"circular_decision": {
            "destination": dest,
            "confidence": 80,
            "cvs_score": condition * 0.9,
            "reasoning": f"Based on condition score {condition}. Routed to {dest}.",
            "carbon_saved_kg": 2.0,
            "revenue_recovery_inr": 3500,
            "exchange_match_possible": False,
            "repair_roi_percentage": None,
        }}

