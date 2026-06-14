"""Seed Bangalore buyers across all remaining categories for demo.

Adds ~5 buyers per category across real Bangalore neighbourhoods.
Categories: Electronics, Clothing, Computers, Home & Kitchen,
            Sports, Beauty, Luggage, Toys, Books

Run: python seed_bangalore_all_categories.py
"""

import boto3
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal

dynamodb = boto3.resource("dynamodb", region_name="ap-south-1")
table = dynamodb.Table("ACIN_Main")


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


BANGALORE_BUYERS = [

    # ── Electronics ──────────────────────────────────────────────────────────
    {"name": "Aditya Rao",         "email": "aditya.rao.blr@gmail.com",         "phone": "+91-9880001111", "pincode": "560001", "lat": 12.9716, "lng": 77.5946, "cat": "Electronics", "max_price": 35000, "days": 0},
    {"name": "Shreya Nambiar",     "email": "shreya.nambiar@gmail.com",         "phone": "+91-9880112222", "pincode": "560038", "lat": 12.9784, "lng": 77.6408, "cat": "Electronics", "max_price": 50000, "days": 1},
    {"name": "Vivek Iyer",         "email": "vivek.iyer.blr@gmail.com",         "phone": "+91-9844223333", "pincode": "560095", "lat": 13.0358, "lng": 77.5970, "cat": "Electronics", "max_price": 20000, "days": 0},
    {"name": "Tanvi Shetty",       "email": "tanvi.shetty@gmail.com",           "phone": "+91-9886334444", "pincode": "560078", "lat": 12.9063, "lng": 77.5857, "cat": "Electronics", "max_price": 80000, "days": 0},
    {"name": "Prakash Hegde",      "email": "prakash.hegde@yahoo.com",          "phone": "+91-9848445555", "pincode": "560043", "lat": 12.9592, "lng": 77.7209, "cat": "Electronics", "max_price": 45000, "days": 2},
    {"name": "Lavanya Suresh",     "email": "lavanya.suresh@gmail.com",         "phone": "+91-9860556666", "pincode": "560066", "lat": 12.8941, "lng": 77.5973, "cat": "Electronics", "max_price": 15000, "days": 0},
    {"name": "Nikhil Bhat",        "email": "nikhil.bhat@gmail.com",            "phone": "+91-9880667777", "pincode": "560034", "lat": 12.9352, "lng": 77.6245, "cat": "Electronics", "max_price": 60000, "days": 1},

    # ── Clothing ─────────────────────────────────────────────────────────────
    {"name": "Swathi Gowda",       "email": "swathi.gowda@gmail.com",           "phone": "+91-9845778888", "pincode": "560010", "lat": 12.9850, "lng": 77.5533, "cat": "Clothing", "max_price": 5000,  "days": 0},
    {"name": "Harsha Menon",       "email": "harsha.menon@gmail.com",           "phone": "+91-9845889999", "pincode": "560076", "lat": 12.9121, "lng": 77.6446, "cat": "Clothing", "max_price": 3500,  "days": 0},
    {"name": "Riya Patel",         "email": "riya.patel.blr@gmail.com",         "phone": "+91-9886990000", "pincode": "560102", "lat": 12.9116, "lng": 77.6389, "cat": "Clothing", "max_price": 6000,  "days": 1},
    {"name": "Deepak Nair",        "email": "deepak.nair.blr@gmail.com",        "phone": "+91-9880101010", "pincode": "560003", "lat": 13.0031, "lng": 77.5718, "cat": "Clothing", "max_price": 8000,  "days": 0},
    {"name": "Ananya Krishnan",    "email": "ananya.krishnan@gmail.com",        "phone": "+91-9886202020", "pincode": "560029", "lat": 12.9165, "lng": 77.6101, "cat": "Clothing", "max_price": 4500,  "days": 2},

    # ── Computers ────────────────────────────────────────────────────────────
    {"name": "Rahul Verma",        "email": "rahul.verma.blr@gmail.com",        "phone": "+91-9880303030", "pincode": "560037", "lat": 13.0200, "lng": 77.6400, "cat": "Computers", "max_price": 60000, "days": 0},
    {"name": "Preethi Sharma",     "email": "preethi.sharma.blr@gmail.com",     "phone": "+91-9844404040", "pincode": "560095", "lat": 13.0400, "lng": 77.5900, "cat": "Computers", "max_price": 80000, "days": 0},
    {"name": "Sunil Rao",          "email": "sunil.rao.blr@gmail.com",          "phone": "+91-9848505050", "pincode": "560038", "lat": 12.9763, "lng": 77.6382, "cat": "Computers", "max_price": 45000, "days": 1},
    {"name": "Meghna Joshi",       "email": "meghna.joshi.blr@gmail.com",       "phone": "+91-9860606060", "pincode": "560066", "lat": 12.9698, "lng": 77.7499, "cat": "Computers", "max_price": 70000, "days": 0},
    {"name": "Aryan Kulkarni",     "email": "aryan.kulkarni.blr@gmail.com",     "phone": "+91-9886707070", "pincode": "560100", "lat": 12.8399, "lng": 77.6770, "cat": "Computers", "max_price": 35000, "days": 2},

    # ── Home & Kitchen ───────────────────────────────────────────────────────
    {"name": "Sunita Reddy",       "email": "sunita.reddy.blr@gmail.com",       "phone": "+91-9880808080", "pincode": "560034", "lat": 12.9312, "lng": 77.6278, "cat": "Home & Kitchen", "max_price": 15000, "days": 0},
    {"name": "Manoj Kumar",        "email": "manoj.kumar.blr@gmail.com",        "phone": "+91-9844909090", "pincode": "560078", "lat": 12.9041, "lng": 77.5879, "cat": "Home & Kitchen", "max_price": 25000, "days": 1},
    {"name": "Nisha Agarwal",      "email": "nisha.agarwal.blr@gmail.com",      "phone": "+91-9886010101", "pincode": "560043", "lat": 12.9580, "lng": 77.7190, "cat": "Home & Kitchen", "max_price": 10000, "days": 0},
    {"name": "Vijay Naik",         "email": "vijay.naik.blr@gmail.com",         "phone": "+91-9848121212", "pincode": "560003", "lat": 13.0014, "lng": 77.5736, "cat": "Home & Kitchen", "max_price": 30000, "days": 0},
    {"name": "Geetha Pillai",      "email": "geetha.pillai@gmail.com",          "phone": "+91-9880232323", "pincode": "560064", "lat": 13.1005, "lng": 77.5963, "cat": "Home & Kitchen", "max_price": 8000,  "days": 3},

    # ── Sports ───────────────────────────────────────────────────────────────
    {"name": "Akash Srinivas",     "email": "akash.srinivas@gmail.com",         "phone": "+91-9886343434", "pincode": "560102", "lat": 12.9082, "lng": 77.6411, "cat": "Sports", "max_price": 12000, "days": 0},
    {"name": "Pooja Hegde",        "email": "pooja.hegde.blr@gmail.com",        "phone": "+91-9844454545", "pincode": "560010", "lat": 12.9901, "lng": 77.5551, "cat": "Sports", "max_price": 8000,  "days": 0},
    {"name": "Rajan Bose",         "email": "rajan.bose.blr@gmail.com",         "phone": "+91-9880565656", "pincode": "560066", "lat": 12.9672, "lng": 77.7521, "cat": "Sports", "max_price": 20000, "days": 1},
    {"name": "Divya Pai",          "email": "divya.pai.blr@gmail.com",          "phone": "+91-9848676767", "pincode": "560029", "lat": 12.9180, "lng": 77.6120, "cat": "Sports", "max_price": 6000,  "days": 0},
    {"name": "Sanjay Gowda",       "email": "sanjay.gowda@gmail.com",           "phone": "+91-9860787878", "pincode": "560100", "lat": 12.8421, "lng": 77.6748, "cat": "Sports", "max_price": 15000, "days": 2},

    # ── Beauty ───────────────────────────────────────────────────────────────
    {"name": "Kaveri Nair",        "email": "kaveri.nair@gmail.com",            "phone": "+91-9886898989", "pincode": "560038", "lat": 12.9801, "lng": 77.6431, "cat": "Beauty", "max_price": 3000, "days": 0},
    {"name": "Ishita Das",         "email": "ishita.das.blr@gmail.com",         "phone": "+91-9880909090", "pincode": "560034", "lat": 12.9360, "lng": 77.6260, "cat": "Beauty", "max_price": 5000, "days": 0},
    {"name": "Rekha Menon",        "email": "rekha.menon.blr@gmail.com",        "phone": "+91-9844010203", "pincode": "560003", "lat": 13.0025, "lng": 77.5725, "cat": "Beauty", "max_price": 2500, "days": 1},
    {"name": "Aishwarya Bhat",     "email": "aishwarya.bhat@gmail.com",         "phone": "+91-9886040506", "pincode": "560078", "lat": 12.9055, "lng": 77.5865, "cat": "Beauty", "max_price": 4000, "days": 0},
    {"name": "Preeti Sharma",      "email": "preeti.sharma.blr@gmail.com",      "phone": "+91-9848070809", "pincode": "560064", "lat": 13.1010, "lng": 77.5970, "cat": "Beauty", "max_price": 6000, "days": 2},

    # ── Luggage ──────────────────────────────────────────────────────────────
    {"name": "Kartik Shenoy",      "email": "kartik.shenoy@gmail.com",          "phone": "+91-9880111213", "pincode": "560095", "lat": 13.0365, "lng": 77.5975, "cat": "Luggage", "max_price": 8000,  "days": 0},
    {"name": "Pallavi Rao",        "email": "pallavi.rao.blr@gmail.com",        "phone": "+91-9844141516", "pincode": "560043", "lat": 12.9600, "lng": 77.7215, "cat": "Luggage", "max_price": 12000, "days": 1},
    {"name": "Suresh Naik",        "email": "suresh.naik.blr@gmail.com",        "phone": "+91-9886171819", "pincode": "560066", "lat": 12.8950, "lng": 77.5980, "cat": "Luggage", "max_price": 5000,  "days": 0},
    {"name": "Nandita Iyer",       "email": "nandita.iyer@gmail.com",           "phone": "+91-9880202122", "pincode": "560102", "lat": 12.9090, "lng": 77.6420, "cat": "Luggage", "max_price": 9000,  "days": 0},

    # ── Toys ─────────────────────────────────────────────────────────────────
    {"name": "Smitha Reddy",       "email": "smitha.reddy.blr@gmail.com",       "phone": "+91-9844232425", "pincode": "560034", "lat": 12.9320, "lng": 77.6250, "cat": "Toys", "max_price": 3000, "days": 0},
    {"name": "Ajay Patil",         "email": "ajay.patil.blr@gmail.com",         "phone": "+91-9886262728", "pincode": "560078", "lat": 12.9070, "lng": 77.5870, "cat": "Toys", "max_price": 2000, "days": 1},
    {"name": "Kavita Nambiar",     "email": "kavita.nambiar@gmail.com",         "phone": "+91-9848293031", "pincode": "560064", "lat": 13.1000, "lng": 77.5960, "cat": "Toys", "max_price": 4000, "days": 0},
    {"name": "Ramesh Gowda",       "email": "ramesh.gowda.blr@gmail.com",       "phone": "+91-9880323334", "pincode": "560010", "lat": 12.9910, "lng": 77.5540, "cat": "Toys", "max_price": 1500, "days": 2},

    # ── Books ────────────────────────────────────────────────────────────────
    {"name": "Lakshmi Prasad",     "email": "lakshmi.prasad@gmail.com",         "phone": "+91-9844353637", "pincode": "560003", "lat": 13.0020, "lng": 77.5720, "cat": "Books", "max_price": 1000, "days": 0},
    {"name": "Venkat Krishnan",    "email": "venkat.krishnan.blr@gmail.com",    "phone": "+91-9886383940", "pincode": "560038", "lat": 12.9770, "lng": 77.6390, "cat": "Books", "max_price": 2000, "days": 0},
    {"name": "Bhavana Shetty",     "email": "bhavana.shetty@gmail.com",         "phone": "+91-9880414243", "pincode": "560095", "lat": 13.0370, "lng": 77.5980, "cat": "Books", "max_price": 1500, "days": 1},
    {"name": "Siddharth Iyer",     "email": "siddharth.iyer.blr@gmail.com",     "phone": "+91-9848444546", "pincode": "560100", "lat": 12.8410, "lng": 77.6760, "cat": "Books", "max_price": 3000, "days": 0},
]


def seed():
    print("\n🛒 Seeding Bangalore Buyers — All Categories")
    print("=" * 55)

    cat_counts = {}
    for b in BANGALORE_BUYERS:
        cat_counts[b["cat"]] = cat_counts.get(b["cat"], 0) + 1

    print(f"Total to seed: {len(BANGALORE_BUYERS)}")
    for cat, n in sorted(cat_counts.items()):
        print(f"  {cat:<20} {n} buyers")
    print()

    seeded = 0
    for b in BANGALORE_BUYERS:
        buyer_id = f"B-BLR-{str(uuid.uuid4())[:6].upper()}"

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
            "category_interest": b["cat"],
            "max_price": b["max_price"],
            "active": True,
            "last_active": past_iso(b["days"]),
            "created_at": past_iso(b["days"] + 14),
            "GSI9PK": f"BUYER_MATCH#Bangalore#{b['cat']}",
            "GSI9SK": f"PRICE#{b['max_price']:08d}",
        }))

        seeded += 1
        print(f"  ✓ {b['name']:<25} | {b['cat']:<16} | ₹{b['max_price']:>6,}")

    print(f"\n✅ Seeded {seeded} buyers across {len(cat_counts)} categories in Bangalore")


if __name__ == "__main__":
    seed()
