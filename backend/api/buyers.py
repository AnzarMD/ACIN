"""Buyers API — registration, matching, and resale notifications.

Endpoints:
- POST /buyers/register            Register a buyer with product interest
- GET  /buyers                     List all registered buyers
- POST /buyers/match               Find buyers matching a product
- POST /returns/{id}/list-resale   Approve & list for resale (notifies buyers)
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from db.buyers import (
    register_buyer,
    list_all_buyers,
    match_buyers,
    notify_buyers_of_resale,
    get_buyer_notifications,
)
from db.dynamo import table, return_pk

router = APIRouter()


class BuyerRegister(BaseModel):
    name: str
    email: str
    phone: str = ""
    city: str
    category_interest: str
    max_price: int = 100000


class MatchRequest(BaseModel):
    city: str
    category: str
    price: int


@router.post("/register")
async def register(buyer: BuyerRegister):
    """Register a new buyer interested in receiving resale notifications."""
    buyer_id = register_buyer(
        name=buyer.name,
        email=buyer.email,
        phone=buyer.phone,
        city=buyer.city,
        category_interest=buyer.category_interest,
        max_price=buyer.max_price,
    )
    return {"buyer_id": buyer_id, "status": "registered"}


@router.get("")
async def get_buyers():
    """List all registered buyers."""
    buyers = list_all_buyers()
    return {"count": len(buyers), "buyers": buyers}


@router.post("/match")
async def find_matches(req: MatchRequest):
    """Find buyers matching a product (city + category + budget)."""
    matched = match_buyers(req.city, req.category, req.price)
    return {"matched_count": len(matched), "buyers": matched}
