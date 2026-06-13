"""Return data models and status state machine."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel


class ReturnStatus(str, Enum):
    """Status state machine for return lifecycle."""
    PENDING_REVIEW = "PENDING_REVIEW"       # FCS 0.70–0.84 — soft block
    ANALYZING = "ANALYZING"                  # Passed validation, agents running
    MANUAL_REVIEW = "MANUAL_REVIEW"          # fraud_score > threshold
    AI_DETECTED = "AI_DETECTED"              # FCS >= 0.85 — hard block (terminal)
    DECIDED = "DECIDED"                      # Fusion Engine produced DECISION#
    COMPLETED = "COMPLETED"                  # Listing/job created (terminal)


class LocationData(BaseModel):
    lat: float
    lng: float
    city: str
    pincode: str


class ReturnCreate(BaseModel):
    """Input schema for POST /returns."""
    product_id: str
    customer_id: str
    return_reason: str
    image_urls: List[str]
    location: Optional[LocationData] = None
    product_name: Optional[str] = None
    category: Optional[str] = None
    original_price: Optional[int] = 5000


class ReturnResponse(BaseModel):
    """Response schema for return submission."""
    return_id: str
    status: str
    message: Optional[str] = None
