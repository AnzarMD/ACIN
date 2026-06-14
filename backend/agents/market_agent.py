import os
"""Agent 2 — Market Intelligence Agent.

Estimates real-time demand for the returned product in the customer's region.
"""

import json
import uuid

from langchain_aws import ChatBedrock
from langchain_core.messages import SystemMessage, HumanMessage

from db.dynamo import put_agent_output, put_agent_run

MARKET_PROMPT = """You are a market intelligence analyst for an e-commerce returns platform. Given product and location data, estimate real-time demand.

Analyse:
1. Local active buyer count for this product category
2. Historical velocity score (how fast similar items sell)
3. Seasonality multiplier (current demand vs average)
4. Category demand index (category-level popularity)
5. Social trend signal (trending or declining interest)

Demand scoring formula:
demand_score = (
    0.35 * local_active_buyers_normalized +
    0.25 * historical_velocity_score +
    0.20 * seasonality_multiplier +
    0.15 * category_demand_index +
    0.05 * social_trend_signal
)

Return ONLY this JSON:
{
    "demand_score": <int 0-100>,
    "buyer_count": <int>,
    "expected_sale_days": <int>,
    "region": "<str>",
    "seasonality_factor": <float>,
    "category_demand_index": <float>,
    "velocity_score": <float>,
    "demand_trend": "<rising|stable|declining>",
    "confidence": <int 0-100>
}"""


class MarketIntelligenceAgent:
    """Estimate real-time demand for returned product."""

    def __init__(self):
        self.llm = ChatBedrock(
            model_id="arn:aws:bedrock:ap-south-1:622623003797:inference-profile/apac.amazon.nova-pro-v1:0",
            provider="amazon",
            region_name=os.getenv("AWS_REGION", "ap-south-1"),
            model_kwargs={"max_tokens": 2048, "temperature": 0.2},
        )

    async def analyse(self, state: dict) -> dict:
        run_id = str(uuid.uuid4())[:8]
        put_agent_run(state["return_id"], "MARKET", run_id, "RUNNING")

        location = state.get("location", {})
        city = location.get("city", "Mumbai") if isinstance(location, dict) else "Mumbai"

        # ── Query real buyer count from DynamoDB ──────────────────────────
        from db.buyers import count_active_buyers, canonical_city
        city = canonical_city(city)  # normalise "Bengaluru" → "Bangalore" etc.
        category = state.get("category", "Electronics")
        real_buyer_count = count_active_buyers(city, category)

        context = (
            f"Product: {state.get('product_name', state.get('product_id', 'N/A'))}\n"
            f"Product ID/ASIN: {state.get('product_id', 'N/A')}\n"
            f"Category: {category}\n"
            f"Original Price: INR {state.get('original_price', 5000)}\n"
            f"Return reason: {state['return_reason']}\n"
            f"Customer City: {city}\n"
            f"Country: India\n"
            f"REAL active buyers in {city} for {category}: {real_buyer_count} "
            f"(use this EXACT number for buyer_count)\n"
            f"Demand score formula: "
            f"0.35×buyer_strength + 0.25×velocity + 0.20×seasonality + 0.15×category_index + 0.05×social\n"
            f"buyer_strength = min(1.0, {real_buyer_count}/25) — normalize against 25 as city max\n"
            f"If buyer_count >= 10, demand_score must be at least 55.\n"
            f"If buyer_count >= 20, demand_score must be at least 70.\n"
            f"Region must be '{city}'. Expected sale days 1-14.\n"
        )

        response = await self.llm.ainvoke([
            SystemMessage(content=MARKET_PROMPT),
            HumanMessage(content=context),
        ])

        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0]
        result = json.loads(content)

        put_agent_output(
            state["return_id"],
            "MARKET",
            run_id,
            result,
            "claude-sonnet-4-6",
            "v1",
            "1.0",
            result.get("demand_score", 0) / 100,
        )

        return {"market_analysis": result}


async def market_intelligence_agent(state: dict) -> dict:
    """LangGraph node entry point."""
    try:
        return await MarketIntelligenceAgent().analyse(state)
    except Exception:
        from db.buyers import count_active_buyers
        location = state.get("location", {})
        city = location.get("city", "Mumbai") if isinstance(location, dict) else "Mumbai"
        category = state.get("category", "Electronics")
        real_buyers = count_active_buyers(city, category)
        # Demand score: floor at 55 if 10+ buyers, 70 if 20+ buyers
        if real_buyers >= 20:
            base_score = 70 + min(25, real_buyers - 20)
        elif real_buyers >= 10:
            base_score = 55 + (real_buyers - 10) * 1.5
        else:
            base_score = min(50, 30 + real_buyers * 3)
        demand_score = int(min(95, base_score))
        return {"market_analysis": {
            "demand_score": demand_score,
            "buyer_count": real_buyers,
            "expected_sale_days": max(1, 14 - real_buyers // 2),
            "region": city,
            "seasonality_factor": 1.0,
            "category_demand_index": 0.7,
            "velocity_score": 0.6,
            "demand_trend": "rising" if real_buyers >= 15 else "stable" if real_buyers >= 5 else "declining",
            "confidence": 75,
        }}

