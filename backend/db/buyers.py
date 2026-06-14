"""Buyer registry and matching for resale notifications.

Stores buyers with their product interests and location, matches them to
resale listings, and records notifications when a resale decision is made.
"""

import math
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from boto3.dynamodb.conditions import Key

from .dynamo import table, to_decimal, now_iso
from .tables import return_pk


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance between two coordinates using Haversine formula."""
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlng / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


# ─── Buyer Registration ──────────────────────────────────────────────────────


def register_buyer(name: str, email: str, phone: str, city: str,
                   category_interest: str, max_price: int = 100000) -> str:
    """Register a buyer with their product interest and location.

    Stored as: PK=BUYER#<id>, SK=PROFILE
    GSI: GSI for city + category lookup
    """
    buyer_id = f"B-{str(uuid.uuid4())[:8].upper()}"
    ts = now_iso()

    table.put_item(Item=to_decimal({
        "PK": f"BUYER#{buyer_id}",
        "SK": "PROFILE",
        "entity_type": "BUYER_SIGNAL",
        "buyer_id": buyer_id,
        "name": name,
        "email": email,
        "phone": phone,
        "city": city,
        "category_interest": category_interest,
        "max_price": max_price,
        "created_at": ts,
        # GSI for matching by city + category
        "GSI9PK": f"BUYER_MATCH#{city}#{category_interest}",
        "GSI9SK": f"PRICE#{max_price:08d}",
    }))

    return buyer_id


def list_all_buyers() -> list:
    """Scan all registered buyers."""
    from boto3.dynamodb.conditions import Attr
    resp = table.scan(
        FilterExpression=Attr("entity_type").eq("BUYER_SIGNAL")
    )
    return resp.get("Items", [])


# ─── Buyer Matching ──────────────────────────────────────────────────────────


def count_active_buyers(city: str, category: str) -> int:
    """Count active buyers for a city/category from DynamoDB."""
    all_buyers = list_all_buyers()
    count = 0
    for b in all_buyers:
        if not b.get("active", True):
            continue
        city_match = b.get("city", "").lower() == city.lower()
        cat = b.get("category_interest", "")
        category_match = cat.lower() == category.lower() or cat == "Any"
        if city_match and category_match:
            count += 1
    # Also count buyers in the same city with "Any" category
    any_count = sum(
        1 for b in all_buyers
        if b.get("city", "").lower() == city.lower() and b.get("category_interest") == "Any"
    )
    return count


def match_buyers(city: str, category: str, price: int, limit: int = 20,
                 seller_lat: float = None, seller_lng: float = None) -> list:
    """Find buyers interested in this category, within budget.

    When seller_lat/lng are provided, calculates distance and computes a
    composite match_score. Falls back to city-only matching otherwise.

    Match score weights:
      0.40 * interest + 0.25 * distance_score + 0.15 * price_affinity
      + 0.10 * reliability + 0.10 * activity
    """
    all_buyers = list_all_buyers()
    matched = []

    for b in all_buyers:
        buyer_city = b.get("city", "")
        buyer_category = b.get("category_interest", "")
        buyer_max = int(float(b.get("max_price", 0)))

        # Category match or "Any"
        category_match = (
            buyer_category.strip().lower() == category.strip().lower()
            or buyer_category == "Any"
        )
        # Budget must cover the listing price
        budget_match = buyer_max >= price

        # If no seller coordinates, use strict city matching (backward compat)
        if seller_lat is None or seller_lng is None:
            city_match = buyer_city.strip().lower() == city.strip().lower()
            if city_match and category_match and budget_match:
                matched.append(b)
            continue

        # With coordinates: compute distance if buyer has lat/lng
        buyer_lat = b.get("lat")
        buyer_lng = b.get("lng")

        if buyer_lat is not None and buyer_lng is not None:
            distance_km = haversine_km(
                seller_lat, seller_lng,
                float(buyer_lat), float(buyer_lng)
            )
        else:
            # No buyer coords — fall back to city match with default distance
            city_match = buyer_city.strip().lower() == city.strip().lower()
            if not city_match:
                continue
            distance_km = 10.0  # assume ~10km for same-city without coords

        # Interest score: 1.0 for exact category, 0.7 for "Any"
        if buyer_category.strip().lower() == category.strip().lower():
            interest_score = 1.0
        elif buyer_category == "Any":
            interest_score = 0.7
        else:
            continue  # no category match at all

        if not budget_match:
            continue

        # Distance score: closer is better, 50km = zero
        distance_score = max(0.0, 1.0 - distance_km / 50.0)

        # Price affinity: how well buyer's budget covers the price
        price_affinity = min(1.0, buyer_max / max(price, 1))

        # Reliability and activity: default 0.8 (future: from buyer history)
        reliability = 0.8
        activity = 0.8

        # Composite match score
        match_score = round(
            0.40 * interest_score +
            0.25 * distance_score +
            0.15 * price_affinity +
            0.10 * reliability +
            0.10 * activity,
            3
        )

        # Add computed fields to buyer dict
        buyer_with_score = dict(b)
        buyer_with_score["distance_km"] = round(distance_km, 2)
        buyer_with_score["match_score"] = match_score
        matched.append(buyer_with_score)

    # Sort by match_score descending when scores are available
    if seller_lat is not None and seller_lng is not None:
        matched.sort(key=lambda x: x.get("match_score", 0), reverse=True)

    return matched[:limit]


# ─── Resale Notifications ────────────────────────────────────────────────────


def notify_buyers_of_resale(return_id: str, listing: dict, matched_buyers: list) -> int:
    """Create notification records for each matched buyer when a resale is listed.

    Each notification is stored under the return AND under the buyer.
    Returns the count of buyers notified.
    """
    ts = now_iso()
    count = 0

    for buyer in matched_buyers:
        buyer_id = buyer.get("buyer_id", "UNKNOWN")
        notif_id = str(uuid.uuid4())[:8]

        # Store notification under the return record
        table.put_item(Item=to_decimal({
            "PK": return_pk(return_id),
            "SK": f"NOTIFICATION#{ts}#{notif_id}",
            "entity_type": "BUYER_NOTIFICATION",
            "buyer_id": buyer_id,
            "buyer_name": buyer.get("name", ""),
            "buyer_email": buyer.get("email", ""),
            "buyer_phone": buyer.get("phone", ""),
            "product_title": listing.get("title", ""),
            "listing_price": listing.get("price", 0),
            "status": "SENT",
            "channel": "email",
            "created_at": ts,
        }))

        # Store notification under the buyer (inbox)
        table.put_item(Item=to_decimal({
            "PK": f"BUYER#{buyer_id}",
            "SK": f"INBOX#{ts}#{notif_id}",
            "entity_type": "BUYER_INBOX",
            "return_id": return_id,
            "product_title": listing.get("title", ""),
            "listing_price": listing.get("price", 0),
            "city": listing.get("city", ""),
            "status": "UNREAD",
            "created_at": ts,
        }))

        # Attempt real email notification (SES) — best effort
        send_email_notification(buyer, listing)
        count += 1

    return count


def send_email_notification(buyer: dict, listing: dict):
    """Send an email to a buyer via Amazon SES. Best-effort (fails silently)."""
    import boto3
    import os

    try:
        ses = boto3.client("ses", region_name=os.getenv("AWS_REGION", "ap-south-1"))
        ses.send_email(
            Source=os.getenv("SES_SENDER", "noreply@acin.example.com"),
            Destination={"ToAddresses": [buyer.get("email", "")]},
            Message={
                "Subject": {"Data": f"New listing matches your interest: {listing.get('title', '')}"},
                "Body": {"Text": {"Data": (
                    f"Hi {buyer.get('name', 'there')},\n\n"
                    f"A product you may be interested in is now available for resale:\n\n"
                    f"  {listing.get('title', '')}\n"
                    f"  Price: Rs {listing.get('price', 0):,}\n"
                    f"  Location: {listing.get('city', '')}\n\n"
                    f"This is a verified, AI-graded item from ACIN.\n\n"
                    f"View it now in the ACIN marketplace.\n"
                )}},
            },
        )
        return True
    except Exception:
        # SES not configured / sandbox — notification still recorded in DB
        return False


def get_buyer_notifications(return_id: str) -> list:
    """Get all notifications sent for a return."""
    resp = table.query(
        KeyConditionExpression=Key("PK").eq(return_pk(return_id))
        & Key("SK").begins_with("NOTIFICATION#")
    )
    return resp.get("Items", [])
