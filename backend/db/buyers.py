"""Buyer registry and matching for resale notifications.

Stores buyers with their product interests and location, matches them to
resale listings, and records notifications when a resale decision is made.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from boto3.dynamodb.conditions import Key

from .dynamo import table, to_decimal, now_iso
from .tables import return_pk


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


def match_buyers(city: str, category: str, price: int, limit: int = 20) -> list:
    """Find buyers in the SAME city, interested in this category, within budget.

    Strictly filters by city — no cross-city matching.
    """
    all_buyers = list_all_buyers()
    matched = []

    for b in all_buyers:
        buyer_city = b.get("city", "")
        buyer_category = b.get("category_interest", "")
        buyer_max = int(float(b.get("max_price", 0)))

        # Strict city match (case-insensitive)
        city_match = buyer_city.strip().lower() == city.strip().lower()
        # Category match or "Any"
        category_match = (
            buyer_category.strip().lower() == category.strip().lower()
            or buyer_category == "Any"
        )
        # Budget must cover the listing price
        budget_match = buyer_max >= price

        if city_match and category_match and budget_match:
            matched.append(b)

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
