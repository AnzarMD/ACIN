"""LangGraph Workflow Design.

The Validation Gate runs at Step-0; agents then run in parallel where possible;
the Circular Economy Agent acts as a final synchronisation node.

Flow:
START → validation_gate → [blocked → END]
                        → [proceed → product_agent, market_agent, fraud_agent (parallel)]
product_agent + market_agent → pricing_agent
pricing_agent → logistics_agent
logistics_agent + fraud_agent → circular_agent
circular_agent → fusion_engine → END
"""

from langgraph.graph import StateGraph, END, START

from agents.validation_gate import validation_gate_node
from agents.product_agent import product_intelligence_agent
from agents.market_agent import market_intelligence_agent
from agents.repricing_agent import repricing_agent
from agents.logistics_agent import logistics_routing_agent
from agents.circular_agent import circular_economy_agent
from agents.fraud_agent import fraud_agent
from workflow.fusion import decision_fusion_engine
from workflow.state import ACINState

# Build the workflow graph
workflow = StateGraph(ACINState)

# Register nodes
workflow.add_node("validation_gate", validation_gate_node)
workflow.add_node("product_agent", product_intelligence_agent)
workflow.add_node("market_agent", market_intelligence_agent)
workflow.add_node("fraud_agent", fraud_agent)
workflow.add_node("pricing_agent", repricing_agent)
workflow.add_node("logistics_agent", logistics_routing_agent)
workflow.add_node("circular_agent", circular_economy_agent)
workflow.add_node("fusion_engine", decision_fusion_engine)

# Validation gate is the entry point
workflow.add_edge(START, "validation_gate")


def route_after_validation(state: ACINState) -> str:
    """Conditional routing after validation gate."""
    validation = state.get("image_validation")
    if validation and validation.fcs >= 0.85:
        return "blocked"  # → END, status=AI_DETECTED already set
    return "proceed"


workflow.add_conditional_edges(
    "validation_gate",
    route_after_validation,
    {"blocked": END, "proceed": "product_agent"},
)

# Parallel: product + market + fraud all start after validation passes
workflow.add_edge("validation_gate", "market_agent")
workflow.add_edge("validation_gate", "fraud_agent")

# Convergence: product + market → pricing
workflow.add_edge("product_agent", "pricing_agent")
workflow.add_edge("market_agent", "pricing_agent")

# Sequential: pricing → logistics
workflow.add_edge("pricing_agent", "logistics_agent")

# Convergence: logistics + fraud → circular
workflow.add_edge("logistics_agent", "circular_agent")
workflow.add_edge("fraud_agent", "circular_agent")

# Final: circular → fusion → END
workflow.add_edge("circular_agent", "fusion_engine")
workflow.add_edge("fusion_engine", END)

# Compile the graph
app = workflow.compile()
