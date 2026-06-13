"""Decision data models."""

from typing import List, Optional
from pydantic import BaseModel


class Destination(str):
    INSTANT_RESALE = "INSTANT_RESALE"
    REFURBISH = "REFURBISH"
    EXCHANGE = "EXCHANGE"
    DONATE = "DONATE"
    RECYCLE = "RECYCLE"


class DecisionResponse(BaseModel):
    """Final decision output schema."""
    return_id: str
    destination: str
    cvs_score: float
    confidence: int
    fraud_check: str
    image_fcs: float
    fraud_probability: float
    listing_price: Optional[int] = None
    carbon_saved_kg: float
    revenue_recovery_inr: Optional[int] = None
    trust_badges: List[str] = []
    explanation: str
