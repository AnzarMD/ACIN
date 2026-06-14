"""Agent 3 — Dynamic Repricing Agent.

Generates three realistic price points based on condition grade, category,
and Indian second-hand market norms. Eliminates flat-percentage discounting.

Used-goods pricing reality in India:
- Shoes Grade C (used): 30-50% of original (heavy discounting for wear)
- Electronics Grade A: 60-75% of original
- Electronics Grade C: 30-45% of original
- Clothing Grade B: 25-40% of original

Strategy:
- Fast Sale (< 24h): Aggressive pricing at market floor
- Balanced (2-5d): Recommended middle ground
- Max Profit (7-14d): Optimistic ceiling, still realistic
"""

import os
import json
import uuid

from langchain_aws import ChatBedrock
from langchain_core.messages import SystemMessage, HumanMessage

from db.dynamo import put_agent_output, put_agent_run

# ─── Category-specific used-goods pricing bands ──────────────────────────────
# (fast_factor, balanced_factor, max_factor) per grade
# These are realistic Indian second-hand market multipliers

PRICING_BANDS = {
    "Footwear": {
        "A": (0.50, 0.60, 0.70),   # Grade A shoes: 50-70% of original
        "B": (0.35, 0.45, 0.55),   # Grade B: visible wear
        "C": (0.20, 0.30, 0.40),   # Grade C: significant wear/defects
        "D": (0.08, 0.12, 0.18),   # Grade D: major damage
    },
    "Clothing": {
        "A": (0.30, 0.40, 0.50),
        "B": (0.18, 0.25, 0.35),
        "C": (0.10, 0.15, 0.22),
        "D": (0.05, 0.08, 0.12),
    },
    "Electronics": {
        "A": (0.60, 0.70, 0.78),
        "B": (0.45, 0.55, 0.65),
        "C": (0.28, 0.38, 0.48),
        "D": (0.12, 0.18, 0.25),
    },
    "Computers": {
        "A": (0.55, 0.65, 0.75),
        "B": (0.40, 0.50, 0.60),
        "C": (0.25, 0.35, 0.45),
        "D": (0.10, 0.16, 0.22),
    },
    "Home & Kitchen": {
        "A": (0.45, 0.55, 0.65),
        "B": (0.28, 0.38, 0.48),
        "C": (0.15, 0.22, 0.30),
        "D": (0.06, 0.10, 0.15),
    },
    "Sports": {
        "A": (0.42, 0.52, 0.62),
        "B": (0.28, 0.36, 0.46),
        "C": (0.15, 0.22, 0.30),
        "D": (0.06, 0.10, 0.14),
    },
    "Beauty": {
        "A": (0.40, 0.50, 0.60),
        "B": (0.22, 0.30, 0.40),
        "C": (0.10, 0.15, 0.22),
        "D": (0.04, 0.07, 0.10),
    },
    "Luggage": {
        "A": (0.45, 0.55, 0.65),
        "B": (0.28, 0.38, 0.48),
        "C": (0.15, 0.22, 0.30),
        "D": (0.07, 0.11, 0.16),
    },
    "Toys": {
        "A": (0.35, 0.45, 0.55),
        "B": (0.20, 0.28, 0.38),
        "C": (0.10, 0.15, 0.22),
        "D": (0.04, 0.07, 0.10),
    },
    "Books": {
        "A": (0.30, 0.40, 0.55),
        "B": (0.18, 0.28, 0.38),
        "C": (0.08, 0.14, 0.20),
        "D": (0.03, 0.06, 0.09),
    },
    # Default for unknown categories
    "Other": {
        "A": (0.50, 0.60, 0.70),
        "B": (0.32, 0.42, 0.52),
        "C": (0.18, 0.26, 0.35),
        "D": (0.08, 0.13, 0.18),
    },
}

REPRICING_PROMPT = """You are a pricing expert for returned/used products on an Indian e-commerce resale platform.

IMPORTANT: You are pricing USED goods, not new ones. Used goods in India sell at steep discounts.
The prices provided to you are the CORRECT REALISTIC PRICES already calculated from market bands.
Your job is to:
1. Review the prices and confirm they make sense for the Indian used-goods market
2. Adjust slightly based on demand signals if needed (±5% max)
3. Recommend the strategy
4. Write a brief market_insight explaining why this price is fair

Rules:
- DO NOT price used/worn items close to original price — buyers know market value
- Footwear with visible wear/defects: 20-40% of original only
- High-demand products can command slightly higher prices
- Consider repair costs: deduct them from pricing if applicable
- Return ONLY valid JSON

Return ONLY this JSON:
{
    "fast_sale_price": <int INR>,
    "balanced_price": <int INR>,
    "max_profit_price": <int INR>,
    "recommended_strategy": "<fast_sale|balanced|max_profit>",
    "original_price": <int>,
    "market_floor": <int>,
    "market_median": <int>,
    "market_ceiling": <int>,
    "discount_percentage": <float — percentage off original for balanced price>,
    "expected_revenue_recovery": <float 0-1>,
    "confidence": <int 0-100>,
    "market_insight": "<1-2 sentence explanation of why this price is realistic>"
}"""


def compute_base_prices(original_price: int, grade: str, category: str,
                        demand_score: int, repair_cost: int,
                        condition_score: int = None) -> tuple:
    """Compute prices directly from condition_score.

    Formula (per user requirement):
      Max Profit  = condition_score% × original_price
      Balanced    = (condition_score - 5)% × original_price
      Fast Sale   = (condition_score - 12)% × original_price

    Demand boost: if demand_score >= 80, add +3% to all prices.
    Repair cost deducted proportionally from all prices.
    """
    # If no condition_score provided, estimate from grade
    if condition_score is None:
        grade_to_score = {"A": 90, "B": 77, "C": 60, "D": 35}
        condition_score = grade_to_score.get(grade, 70)

    # Clamp to valid range
    condition_score = max(1, min(100, condition_score))

    # Demand boost
    demand_boost = 3 if demand_score >= 80 else (1 if demand_score >= 60 else 0)

    # Core formula: condition_score% drives max price
    max_pct = (condition_score + demand_boost) / 100
    balanced_pct = (condition_score - 5 + demand_boost) / 100
    fast_pct = (condition_score - 12 + demand_boost) / 100

    # Ensure fast sale is at least 15% below max
    fast_pct = min(fast_pct, max_pct - 0.15)
    # Ensure all percentages are positive
    max_pct = max(max_pct, 0.08)
    balanced_pct = max(balanced_pct, 0.06)
    fast_pct = max(fast_pct, 0.04)

    max_p = int(original_price * max_pct)
    balanced = int(original_price * balanced_pct)
    fast = int(original_price * fast_pct)

    # Deduct repair cost proportionally
    if repair_cost > 0:
        max_p = max(int(max_p * 0.9), max_p - repair_cost)
        balanced = max(int(balanced * 0.9), balanced - repair_cost)
        fast = max(int(fast * 0.9), fast - repair_cost)

    # Round to nearest ×9 for psychological pricing
    def round_price(p: int) -> int:
        if p <= 0:
            return 99
        r = round(p / 50) * 50 - 1   # e.g. 996 → 999, 944 → 949
        return max(49, r)

    return round_price(fast), round_price(balanced), round_price(max_p)


class DynamicRepricingAgent:
    """Generate realistic optimised pricing for returned products."""

    def __init__(self):
        self.llm = ChatBedrock(
            model_id="arn:aws:bedrock:ap-south-1:622623003797:inference-profile/apac.amazon.nova-pro-v1:0",
            provider="amazon",
            region_name=os.getenv("AWS_REGION", "ap-south-1"),
            model_kwargs={"max_tokens": 512, "temperature": 0.1},
        )

    async def analyse(self, state: dict) -> dict:
        run_id = str(uuid.uuid4())[:8]
        put_agent_run(state["return_id"], "PRICING", run_id, "RUNNING")

        product = state.get("product_analysis", {})
        market = state.get("market_analysis", {})

        original_price = int(state.get("original_price") or 5000)
        grade = product.get("grade", "B")
        category = state.get("category", "Electronics")
        demand_score = int(market.get("demand_score", 60))
        repair_cost = int(product.get("estimated_repair_cost_inr", 0))
        condition_score = int(product.get("condition_score", 70))

        # Compute realistic base prices from condition_score (not static bands)
        fast, balanced, max_p = compute_base_prices(
            original_price, grade, category, demand_score, repair_cost,
            condition_score=condition_score
        )

        discount_pct = round((1 - balanced / max(original_price, 1)) * 100, 1)

        context = (
            f"Product: {state.get('product_name', category)}\n"
            f"Category: {category}\n"
            f"Original Price: INR {original_price}\n"
            f"Condition Score: {condition_score}/100 | Grade: {grade}\n"
            f"Defects: {product.get('defects', [])}\n"
            f"Repair Cost: INR {repair_cost}\n"
            f"Demand Score: {demand_score}/100 | Nearby Buyers: {market.get('buyer_count', 0)}\n"
            f"Expected Sale Days: {market.get('expected_sale_days', 5)}\n\n"
            f"Pre-calculated realistic prices for Indian used-goods market:\n"
            f"  Fast Sale (<24h): INR {fast}\n"
            f"  Balanced (2-5d): INR {balanced}\n"
            f"  Max Profit (7-14d): INR {max_p}\n"
            f"  Discount from original: {discount_pct}%\n\n"
            f"Review these prices. Adjust by ±5% max based on specific defects or demand. "
            f"Recommend a strategy. Be realistic — Grade {grade} used {category} "
            f"should NOT be priced near original."
        )

        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=REPRICING_PROMPT),
                HumanMessage(content=context),
            ])
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0]
            result = json.loads(content)

            # Safety: prevent LLM from pricing above our computed ceiling
            result["fast_sale_price"] = min(result.get("fast_sale_price", fast), int(max_p * 1.05))
            result["balanced_price"] = min(result.get("balanced_price", balanced), int(max_p * 1.05))
            result["max_profit_price"] = min(result.get("max_profit_price", max_p), int(original_price * 0.9))

        except Exception:
            # Fallback: use our computed prices directly
            result = {
                "fast_sale_price": fast,
                "balanced_price": balanced,
                "max_profit_price": max_p,
                "recommended_strategy": "balanced" if demand_score >= 60 else "fast_sale",
                "market_floor": fast,
                "market_median": balanced,
                "market_ceiling": max_p,
                "market_insight": f"Grade {grade} used {category} in Indian market. {discount_pct}% below original.",
            }

        result["original_price"] = original_price
        result["discount_percentage"] = round((1 - result["balanced_price"] / max(original_price, 1)) * 100, 1)
        result["expected_revenue_recovery"] = round(result["balanced_price"] / max(original_price, 1), 3)
        result.setdefault("confidence", 85)

        put_agent_output(
            state["return_id"],
            "PRICING",
            run_id,
            result,
            "nova-pro-v1",
            "v1",
            "1.0",
            result["confidence"] / 100,
        )

        return {"pricing_analysis": result}


async def repricing_agent(state: dict) -> dict:
    """LangGraph node entry point."""
    try:
        return await DynamicRepricingAgent().analyse(state)
    except Exception:
        original = int(state.get("original_price") or 5000)
        grade = state.get("product_analysis", {}).get("grade", "B") if state.get("product_analysis") else "B"
        condition_score = state.get("product_analysis", {}).get("condition_score", 75) if state.get("product_analysis") else 75
        category = state.get("category", "Electronics")
        demand = state.get("market_analysis", {}).get("demand_score", 60) if state.get("market_analysis") else 60

        fast, balanced, max_p = compute_base_prices(original, grade, category, demand, 0, condition_score=condition_score)
        return {"pricing_analysis": {
            "fast_sale_price": fast,
            "balanced_price": balanced,
            "max_profit_price": max_p,
            "recommended_strategy": "balanced",
            "original_price": original,
            "market_floor": fast,
            "market_median": balanced,
            "market_ceiling": max_p,
            "discount_percentage": round((1 - balanced / max(original, 1)) * 100, 1),
            "expected_revenue_recovery": round(balanced / max(original, 1), 3),
            "confidence": 80,
            "market_insight": f"Grade {grade} used {category} priced at Indian market rates.",
        }}
