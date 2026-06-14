"""Backfill missing lat/lng coordinates for existing buyer records.

Buyers seeded without coordinates get their city's representative coordinates.
Existing buyer coordinates are NOT overwritten.

Run: python backfill_buyer_coords.py
"""

import boto3
from decimal import Decimal

dynamodb = boto3.resource("dynamodb", region_name="ap-south-1")
table = dynamodb.Table("ACIN_Main")

# Known buyer coordinates from seed_buyers.py
BUYER_COORDS = {
    "BUYER#B-MUM001": (18.9388, 72.8354),  # Aarav Mehta, Mumbai
    "BUYER#B-MUM002": (19.0454, 72.8280),  # Diya Shah, Mumbai
    "BUYER#B-BLR001": (12.9716, 77.5946),  # Ishaan Nair, Bangalore
    "BUYER#B-BLR002": (12.9352, 77.6245),  # Saanvi Rao, Bangalore
    "BUYER#B-DEL001": (28.6139, 77.2090),  # Ananya Reddy, Delhi
    "BUYER#B-DEL002": (28.6517, 77.3219),  # Riya Malhotra, Delhi
    "BUYER#B-CHE001": (13.0827, 80.2707),  # Chennai buyers
    "BUYER#B-HYD001": (17.3850, 78.4867),  # Hyderabad buyers
    "BUYER#B-PUN001": (18.5204, 73.8567),  # Pune buyers
    "BUYER#B-KOL001": (22.5726, 88.3639),  # Kolkata buyers
}

# City-level fallback coordinates
CITY_COORDS = {
    "Mumbai":    (19.0760, 72.8777),
    "Delhi":     (28.6139, 77.2090),
    "Bangalore": (12.9716, 77.5946),
    "Chennai":   (13.0827, 80.2707),
    "Hyderabad": (17.3850, 78.4867),
    "Pune":      (18.5204, 73.8567),
    "Kolkata":   (22.5726, 88.3639),
    "Jaipur":    (26.9124, 75.7873),
}


def backfill():
    from boto3.dynamodb.conditions import Attr
    resp = table.scan(FilterExpression=Attr("entity_type").eq("BUYER_SIGNAL"))
    buyers = resp.get("Items", [])

    updated = 0
    skipped = 0

    for b in buyers:
        pk = b.get("PK", "")
        # Skip if already has coordinates
        if b.get("lat") and b.get("lng"):
            skipped += 1
            continue

        # Try exact buyer lookup first
        lat, lng = None, None
        if pk in BUYER_COORDS:
            lat, lng = BUYER_COORDS[pk]
        else:
            # Fall back to city center
            city = b.get("city", "")
            if city in CITY_COORDS:
                lat, lng = CITY_COORDS[city]

        if lat is None:
            print(f"  ⚠ No coords for {b.get('name')} ({b.get('city')}) — skipping")
            continue

        # Update DynamoDB
        table.update_item(
            Key={"PK": pk, "SK": "PROFILE"},
            UpdateExpression="SET lat = :lat, lng = :lng",
            ExpressionAttributeValues={
                ":lat": Decimal(str(lat)),
                ":lng": Decimal(str(lng)),
            }
        )
        name = b.get('name', '?')
        city = b.get('city', '?')
        print(f"  ✅ Updated {name} ({city}): {lat}, {lng}")
        updated += 1

    print(f"\nDone. Updated: {updated}, Already had coords: {skipped}")


if __name__ == "__main__":
    print("🌍 Backfilling buyer coordinates...")
    backfill()
