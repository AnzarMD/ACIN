"""LangGraph state definition for the ACIN multi-agent workflow."""

from typing import TypedDict, Optional, List
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Step-0 AI Image Validation Gate result."""
    fcs: float
    status: str  # AUTHENTIC | LOW | MODERATE | HIGH | AI_DETECTED
    signals: dict
    flagged_image_urls: List[str]
    reason: str
    pipeline_blocked: bool


class ACINState(TypedDict):
    """Complete workflow state passed through LangGraph."""
    return_id: str
    images: List[str]  # S3 URLs
    return_reason: str
    product_id: Optional[str]
    customer_id: Optional[str]
    location: Optional[dict]
    category: Optional[str]
    original_price: Optional[int]
    product_name: Optional[str]

    # Step-0 gate result
    image_validation: Optional[ValidationResult]

    # Agent outputs
    product_analysis: Optional[dict]
    market_analysis: Optional[dict]
    pricing_analysis: Optional[dict]
    logistics_analysis: Optional[dict]
    fraud_analysis: Optional[dict]

    # Final decisions
    circular_decision: Optional[dict]
    final_decision: Optional[dict]
