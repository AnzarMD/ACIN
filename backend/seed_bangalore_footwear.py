"""Seed additional Footwear buyers in Bangalore for demo purposes.

These buyers are spread across Bangalore's real neighbourhoods with
coordinates, realistic budgets, and high match scores for footwear listings.

Run: python seed_bangalore_footwear.py
"""

import boto3
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal

dynamodb = boto3.resource("dynamodb", region_name="ap-south-1")
table = dynamodb.Table("ACIN_Main")


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def past_iso(days_ago):
    return (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()


def to_decimal(obj):
    if isinstance(obj, float):
        return Decimal(str(round(obj, 4)))
    if isinstance(obj, dict):
        return {k: to_decimal(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [to_decimal(i) for i in obj]
    return obj


# ─── 20 Footwear buyers spread across Bangalore neighbourhoods ────────────────
# Coordinates are real Bangalore locations for accurate Haversine matching.

BANGALORE_FOOTWEAR_BUYERS = [
    # Koramangala
    {"name": "Arjun Shetty",       "email": "arjun.shetty@gmail.com",       "phone": "+91-9880223344", "pincode": "560034", "lat": 12.9352, "lng": 77.6245, "max_price": 6000,  "days": 0},
    {"name": "Divya Krishnan",     "email": "divya.krishnan@gmail.com",     "phone": "+91-9880334455", "pincode": "560034", "lat": 12.9312, "lng": 77.6278, "max_price": 4500,  "days": 1},
    # Indiranagar
    {"name": "Rohit Bhat",         "email": "rohit.bhat@gmail.com",         "phone": "+91-9844445566", "pincode": "560038", "lat": 12.9784, "lng": 77.6408, "max_price": 8000,  "days": 0},
    {"name": "Sneha Murthy",       "email": "sneha.murthy@gmail.com",       "phone": "+91-9844556677", "pincode": "560038", "lat": 12.9763, "lng": 77.6382, "max_price": 5500,  "days": 0},
    {"name": "Kiran Rao",          "email": "kiran.rao@yahoo.com",          "phone": "+91-9844667788", "pincode": "560038", "lat": 12.9801, "lng": 77.6431, "max_price": 12000, "days": 1},
    # HSR Layout
    {"name": "Pooja Naik",         "email": "pooja.naik@gmail.com",         "phone": "+91-9886778899", "pincode": "560102", "lat": 12.9116, "lng": 77.6389, "max_price": 7000,  "days": 0},
    {"name": "Aman Jain",          "email": "aman.jain@gmail.com",          "phone": "+91-9886889900", "pincode": "560102", "lat": 12.9082, "lng": 77.6411, "max_price": 3500,  "days": 2},
    # Whitefield
    {"name": "Priya Reddy",        "email": "priya.reddy.wf@gmail.com",     "phone": "+91-9845990011", "pincode": "560066", "lat": 12.9698, "lng": 77.7499, "max_price": 9000,  "days": 0},
    {"name": "Suresh Gowda",       "email": "suresh.gowda@gmail.com",       "phone": "+91-9845001122", "pincode": "560066", "lat": 12.9672, "lng": 77.7521, "max_price": 5000,  "days": 1},
    # Electronic City
    {"name": "Naveen Kumar",       "email": "naveen.kumar.ec@gmail.com",    "phone": "+91-9886112233", "pincode": "560100", "lat": 12.8399, "lng": 77.6770, "max_price": 4000,  "days": 0},
    {"name": "Harini Subramaniam", "email": "harini.subramaniam@gmail.com", "phone": "+91-9886223344", "pincode": "560100", "lat": 12.8421, "lng": 77.6748, "max_price": 6500,  "days": 1},
    # JP Nagar
    {"name": "Meghana Patil",      "email": "meghana.patil@gmail.com",      "phone": "+91-9900334455", "pincode": "560078", "lat": 12.9063, "lng": 77.5857, "max_price": 5000,  "days": 0},
    {"name": "Rahul Hegde",        "email": "rahul.hegde@gmail.com",        "phone": "+91-9900445566", "pincode": "560078", "lat": 12.9041, "lng": 77.5879, "max_price": 8500,  "days": 2},
    # Rajajinagar
    {"name": "Anita Pai",          "email": "anita.pai@gmail.com",          "phone": "+91-9845556677", "pincode": "560010", "lat": 12.9922, "lng": 77.5530, "max_price": 7500,  "days": 0},
    {"name": "Venkat Swamy",       "email": "venkat.swamy@yahoo.com",       "phone": "+91-9845667788", "pincode": "560010", "lat": 12.9901, "lng": 77.5551, "max_price": 4000,  "days": 1},
    # Malleshwaram
    {"name": "Deepa Sharma",       "email": "deepa.sharma.blr@gmail.com",   "phone": "+91-9845778899", "pincode": "560003", "lat": 13.0031, "lng": 77.5718, "max_price": 6000,  "days": 0},
    {"name": "Girish Nagaraj",     "email": "girish.nagaraj@gmail.com",     "phone": "+91-9880889900", "pincode": "560003", "lat": 13.0014, "lng": 77.5736, "max_price": 10000, "days": 0},
    # Bannerghatta Road
    {"name": "Nandini Bose",       "email": "nandini.bose@gmail.com",       "phone": "+91-9886990011", "pincode": "560076", "lat": 12.8897, "lng": 77.5975, "max_price": 5500,  "days": 1},
    # Yelahanka
    {"name": "Santosh Reddy",      "email": "santosh.reddy@gmail.com",      "phone": "+91-9845101112", "pincode": "560064", "lat": 13.1005, "lng": 77.5963, "max_price": 4500,  "days": 0},
    # BTM Layout
    {"name": "Kavitha Nair",       "email": "kavitha.nair.btm@gmail.com",   "phone": "+91-9900121314", "pincode": "560029", "lat": 12.9165, "lng": 77.6101, "max_price": 7000,  "days": 0},
]


def seed():
    print("\n👟 Seeding Bangalore Footwear Buyers")
    print("=" * 50)
    seeded = 0

    for b in BANGALORE_FOOTWEAR_BUYERS:
        buyer_id = f"B-BLR-{str(uuid.uuid4())[:6].upper()}"
        ts_active  = past_iso(b["days"])
        ts_created = past_iso(b["days"] + 14)

        table.put_item(Item=to_decimal({
            "PK": f"BUYER#{buyer_id}",
            "SK": "PROFILE",
            "entity_type": "BUYER_SIGNAL",
            "buyer_id": buyer_id,
            "name": b["name"],
            "email": b.get("email", ""),
            "phone": b.get("phone", ""),
            "city": "Bangalore",
            "pincode": b["pincode"],
            "lat": b["lat"],
            "lng": b["lng"],
            "category_interest": "Footwear",
            "max_price": b["max_price"],
            "active": True,
            "last_active": ts_active,
            "created_at": ts_created,
            # GSI9 — city + category lookup used by match_buyers
            "GSI9PK": "BUYER_MATCH#Bangalore#Footwear",
            "GSI9SK": f"PRICE#{b['max_price']:08d}",
        }))

        seeded += 1
        print(f"  ✓ {b['name']:<25} | {b['pincode']} | ₹{b['max_price']:,} max | "
              f"lat={b['lat']}, lng={b['lng']}")

    print(f"\n✅ Seeded {seeded} Bangalore footwear buyers")
    print("   These will now appear in buyer match results for Bangalore footwear listings.")


if __name__ == "__main__":
    seed()
