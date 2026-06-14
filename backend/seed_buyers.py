"""Seed realistic buyer data across Indian cities into DynamoDB.

Run: python seed_buyers.py

Buyers have:
- Location (city, pincode, coordinates)
- Category interests (Electronics, Footwear, Clothing, etc.)
- Budget range
- Activity signal (active/inactive, last_active)
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


# ─── Buyer Data by City ──────────────────────────────────────────────────────

BUYERS = [
    # ── Mumbai (400xxx) ──────────────────────────────────────────────────────
    {"name": "Aarav Mehta",    "email": "aarav.mehta@gmail.com",    "phone": "+91-9820112233", "city": "Mumbai", "pincode": "400001", "lat": 18.9388, "lng": 72.8354, "category": "Electronics",   "max_price": 15000, "active_days_ago": 1},
    {"name": "Priya Sharma",   "email": "priya.sharma@gmail.com",   "phone": "+91-9821223344", "city": "Mumbai", "pincode": "400050", "lat": 19.0596, "lng": 72.8295, "category": "Electronics",   "max_price": 25000, "active_days_ago": 0},
    {"name": "Kabir Patel",    "email": "kabir.patel@yahoo.com",    "phone": "+91-9833445566", "city": "Mumbai", "pincode": "400070", "lat": 19.0760, "lng": 72.8777, "category": "Electronics",   "max_price": 60000, "active_days_ago": 2},
    {"name": "Diya Shah",      "email": "diya.shah@gmail.com",      "phone": "+91-9867890123", "city": "Mumbai", "pincode": "400016", "lat": 19.0454, "lng": 72.8280, "category": "Footwear",      "max_price": 12000, "active_days_ago": 0},
    {"name": "Rohan Desai",    "email": "rohan.desai@outlook.com",  "phone": "+91-9876543210", "city": "Mumbai", "pincode": "400086", "lat": 19.1136, "lng": 72.8697, "category": "Footwear",      "max_price": 8000,  "active_days_ago": 1},
    {"name": "Sneha Joshi",    "email": "sneha.joshi@gmail.com",    "phone": "+91-9823344556", "city": "Mumbai", "pincode": "400019", "lat": 19.0178, "lng": 72.8478, "category": "Clothing",      "max_price": 5000,  "active_days_ago": 0},
    {"name": "Arjun Kapoor",   "email": "arjun.kapoor@gmail.com",   "phone": "+91-9845678901", "city": "Mumbai", "pincode": "400093", "lat": 19.1543, "lng": 72.9892, "category": "Clothing",      "max_price": 7000,  "active_days_ago": 3},
    {"name": "Meera Iyer",     "email": "meera.iyer@gmail.com",     "phone": "+91-9812345678", "city": "Mumbai", "pincode": "400022", "lat": 19.0222, "lng": 72.8561, "category": "Home & Kitchen","max_price": 20000, "active_days_ago": 1},
    {"name": "Vikram Singh",   "email": "vikram.singh@hotmail.com", "phone": "+91-9856789012", "city": "Mumbai", "pincode": "400053", "lat": 19.0728, "lng": 72.8826, "category": "Computers",     "max_price": 45000, "active_days_ago": 0},
    {"name": "Anjali Nair",    "email": "anjali.nair@gmail.com",    "phone": "+91-9819012345", "city": "Mumbai", "pincode": "400101", "lat": 19.2183, "lng": 72.9781, "category": "Beauty",        "max_price": 3000,  "active_days_ago": 2},
    {"name": "Siddharth Rao",  "email": "siddharth.rao@gmail.com",  "phone": "+91-9834567890", "city": "Mumbai", "pincode": "400064", "lat": 19.0948, "lng": 72.8556, "category": "Sports",        "max_price": 10000, "active_days_ago": 1},
    {"name": "Tanya Gupta",    "email": "tanya.gupta@gmail.com",    "phone": "+91-9878901234", "city": "Mumbai", "pincode": "400012", "lat": 18.9667, "lng": 72.8311, "category": "Electronics",   "max_price": 35000, "active_days_ago": 0},

    # ── Delhi (110xxx) ────────────────────────────────────────────────────────
    {"name": "Ananya Reddy",   "email": "ananya.reddy@gmail.com",   "phone": "+91-9711223344", "city": "Delhi", "pincode": "110001", "lat": 28.6139, "lng": 77.2090, "category": "Computers",     "max_price": 50000, "active_days_ago": 0},
    {"name": "Vivaan Kumar",   "email": "vivaan.kumar@gmail.com",   "phone": "+91-9723334455", "city": "Delhi", "pincode": "110017", "lat": 28.5245, "lng": 77.1855, "category": "Electronics",   "max_price": 20000, "active_days_ago": 1},
    {"name": "Riya Malhotra",  "email": "riya.malhotra@yahoo.com",  "phone": "+91-9745556677", "city": "Delhi", "pincode": "110092", "lat": 28.6517, "lng": 77.3219, "category": "Footwear",      "max_price": 9000,  "active_days_ago": 0},
    {"name": "Aditya Sharma",  "email": "aditya.sharma@gmail.com",  "phone": "+91-9767778899", "city": "Delhi", "pincode": "110044", "lat": 28.5355, "lng": 77.2507, "category": "Clothing",      "max_price": 6000,  "active_days_ago": 2},
    {"name": "Pooja Verma",    "email": "pooja.verma@gmail.com",    "phone": "+91-9789990011", "city": "Delhi", "pincode": "110085", "lat": 28.6731, "lng": 77.3108, "category": "Beauty",        "max_price": 5000,  "active_days_ago": 0},
    {"name": "Harsh Aggarwal", "email": "harsh.aggarwal@gmail.com", "phone": "+91-9701122334", "city": "Delhi", "pincode": "110059", "lat": 28.5706, "lng": 77.0870, "category": "Electronics",   "max_price": 80000, "active_days_ago": 3},
    {"name": "Sakshi Tyagi",   "email": "sakshi.tyagi@outlook.com", "phone": "+91-9713344556", "city": "Delhi", "pincode": "110034", "lat": 28.6989, "lng": 77.1534, "category": "Home & Kitchen","max_price": 15000, "active_days_ago": 1},
    {"name": "Rahul Bhatia",   "email": "rahul.bhatia@gmail.com",   "phone": "+91-9735566778", "city": "Delhi", "pincode": "110018", "lat": 28.5535, "lng": 77.1065, "category": "Sports",        "max_price": 12000, "active_days_ago": 0},

    # ── Bangalore (560xxx) ────────────────────────────────────────────────────
    {"name": "Ishaan Nair",       "email": "ishaan.nair@gmail.com",       "phone": "+91-9880112233", "city": "Bangalore", "pincode": "560001", "lat": 12.9716, "lng": 77.5946, "category": "Footwear",      "max_price": 10000,  "active_days_ago": 0},
    {"name": "Saanvi Rao",        "email": "saanvi.rao@gmail.com",        "phone": "+91-9892223344", "city": "Bangalore", "pincode": "560038", "lat": 12.9352, "lng": 77.6245, "category": "Electronics",   "max_price": 100000, "active_days_ago": 1},
    {"name": "Dev Krishnamurthy", "email": "dev.krishnamurthy@gmail.com", "phone": "+91-9844334455", "city": "Bangalore", "pincode": "560095", "lat": 13.0358, "lng": 77.5970, "category": "Computers",     "max_price": 75000,  "active_days_ago": 0},
    {"name": "Kavya Suresh",      "email": "kavya.suresh@yahoo.com",      "phone": "+91-9886445566", "city": "Bangalore", "pincode": "560076", "lat": 12.9121, "lng": 77.6446, "category": "Clothing",      "max_price": 8000,   "active_days_ago": 2},
    {"name": "Neel Hegde",        "email": "neel.hegde@gmail.com",        "phone": "+91-9848556677", "city": "Bangalore", "pincode": "560043", "lat": 12.9592, "lng": 77.7209, "category": "Sports",        "max_price": 18000,  "active_days_ago": 0},
    {"name": "Aisha Patel",       "email": "aisha.patel@gmail.com",       "phone": "+91-9860667788", "city": "Bangalore", "pincode": "560010", "lat": 12.9850, "lng": 77.5533, "category": "Beauty",        "max_price": 4000,   "active_days_ago": 1},
    {"name": "Roshan Menon",      "email": "roshan.menon@gmail.com",      "phone": "+91-9872778899", "city": "Bangalore", "pincode": "560066", "lat": 12.8941, "lng": 77.5973, "category": "Electronics",   "max_price": 30000,  "active_days_ago": 0},
    {"name": "Preethi Gowda",     "email": "preethi.gowda@gmail.com",     "phone": "+91-9884889900", "city": "Bangalore", "pincode": "560100", "lat": 12.8456, "lng": 77.6603, "category": "Home & Kitchen","max_price": 25000,  "active_days_ago": 3},

    # ── Chennai (600xxx) ──────────────────────────────────────────────────────
    {"name": "Lakshmi Iyer",    "email": "lakshmi.iyer@gmail.com",    "phone": "+91-9444112233", "city": "Chennai", "pincode": "600001", "lat": 13.0827, "lng": 80.2707, "category": "Home & Kitchen","max_price": 20000, "active_days_ago": 0},
    {"name": "Karthik Venkat",  "email": "karthik.venkat@gmail.com",  "phone": "+91-9876223344", "city": "Chennai", "pincode": "600028", "lat": 13.0418, "lng": 80.2341, "category": "Electronics",   "max_price": 40000, "active_days_ago": 1},
    {"name": "Nithya Sundaram", "email": "nithya.sundaram@yahoo.com", "phone": "+91-9445334455", "city": "Chennai", "pincode": "600041", "lat": 12.9279, "lng": 80.1445, "category": "Footwear",      "max_price": 7000,  "active_days_ago": 0},
    {"name": "Gopal Krishnan",  "email": "gopal.krishnan@gmail.com",  "phone": "+91-9444445566", "city": "Chennai", "pincode": "600097", "lat": 13.0569, "lng": 80.2425, "category": "Computers",     "max_price": 55000, "active_days_ago": 2},
    {"name": "Divya Rajan",     "email": "divya.rajan@gmail.com",     "phone": "+91-9841556677", "city": "Chennai", "pincode": "600020", "lat": 13.0080, "lng": 80.2630, "category": "Beauty",        "max_price": 3500,  "active_days_ago": 0},

    # ── Hyderabad (500xxx) ────────────────────────────────────────────────────
    {"name": "Amir Khan",    "email": "amir.khan@gmail.com",    "phone": "+91-9849112233", "city": "Hyderabad", "pincode": "500001", "lat": 17.3850, "lng": 78.4867, "category": "Electronics",   "max_price": 45000, "active_days_ago": 1},
    {"name": "Fatima Begum", "email": "fatima.begum@gmail.com", "phone": "+91-9848223344", "city": "Hyderabad", "pincode": "500081", "lat": 17.4400, "lng": 78.3489, "category": "Clothing",      "max_price": 6000,  "active_days_ago": 0},
    {"name": "Suresh Reddy", "email": "suresh.reddy@yahoo.com", "phone": "+91-9866334455", "city": "Hyderabad", "pincode": "500072", "lat": 17.3616, "lng": 78.4747, "category": "Computers",     "max_price": 60000, "active_days_ago": 2},
    {"name": "Manisha Rao",  "email": "manisha.rao@gmail.com",  "phone": "+91-9849445566", "city": "Hyderabad", "pincode": "500034", "lat": 17.4123, "lng": 78.4471, "category": "Home & Kitchen","max_price": 30000, "active_days_ago": 0},

    # ── Pune (411xxx) ─────────────────────────────────────────────────────────
    {"name": "Shubham Joshi",    "email": "shubham.joshi@gmail.com",    "phone": "+91-9890112233", "city": "Pune", "pincode": "411001", "lat": 18.5204, "lng": 73.8567, "category": "Electronics","max_price": 25000, "active_days_ago": 0},
    {"name": "Neha Kulkarni",    "email": "neha.kulkarni@gmail.com",    "phone": "+91-9823223344", "city": "Pune", "pincode": "411037", "lat": 18.5679, "lng": 73.9143, "category": "Footwear",   "max_price": 9000,  "active_days_ago": 1},
    {"name": "Omkar Patil",      "email": "omkar.patil@gmail.com",      "phone": "+91-9876334455", "city": "Pune", "pincode": "411048", "lat": 18.5074, "lng": 73.7898, "category": "Sports",     "max_price": 15000, "active_days_ago": 0},
    {"name": "Shruti Deshpande", "email": "shruti.deshpande@yahoo.com", "phone": "+91-9870445566", "city": "Pune", "pincode": "411004", "lat": 18.5314, "lng": 73.8446, "category": "Clothing",   "max_price": 7000,  "active_days_ago": 2},

    # ── Kolkata (700xxx) ──────────────────────────────────────────────────────
    {"name": "Amit Das",      "email": "amit.das@gmail.com",      "phone": "+91-9831112233", "city": "Kolkata", "pincode": "700001", "lat": 22.5726, "lng": 88.3639, "category": "Electronics",   "max_price": 30000, "active_days_ago": 1},
    {"name": "Sunita Banerjee","email": "sunita.banerjee@gmail.com","phone": "+91-9830223344", "city": "Kolkata", "pincode": "700019", "lat": 22.5355, "lng": 88.3642, "category": "Clothing",     "max_price": 5000,  "active_days_ago": 0},
    {"name": "Rajesh Ghosh",  "email": "rajesh.ghosh@yahoo.com",  "phone": "+91-9836334455", "city": "Kolkata", "pincode": "700091", "lat": 22.5958, "lng": 88.4267, "category": "Home & Kitchen","max_price": 18000, "active_days_ago": 3},
    {"name": "Mohua Sen",     "email": "mohua.sen@gmail.com",      "phone": "+91-9831445566", "city": "Kolkata", "pincode": "700064", "lat": 22.6186, "lng": 88.4111, "category": "Beauty",        "max_price": 4000,  "active_days_ago": 0},

    # ── Jaipur (302xxx) ───────────────────────────────────────────────────────
    {"name": "Vikram Singh",   "email": "vikram.singh.jpr@gmail.com", "phone": "+91-9414112233", "city": "Jaipur", "pincode": "302001", "lat": 26.9124, "lng": 75.7873, "category": "Luggage",    "max_price": 8000,  "active_days_ago": 1},
    {"name": "Kavita Sharma",  "email": "kavita.sharma@gmail.com",   "phone": "+91-9829223344", "city": "Jaipur", "pincode": "302017", "lat": 26.9260, "lng": 75.8235, "category": "Clothing",   "max_price": 4000,  "active_days_ago": 0},
    {"name": "Rajendra Meena", "email": "rajendra.meena@yahoo.com",  "phone": "+91-9414334455", "city": "Jaipur", "pincode": "302003", "lat": 26.9200, "lng": 75.7800, "category": "Electronics","max_price": 20000, "active_days_ago": 2},
]


def seed_all_buyers():
    print("\n🛒 Seeding Buyer Registry")
    print("=" * 50)
    cities = {}
    for b in BUYERS:
        cities[b["city"]] = cities.get(b["city"], 0) + 1

    print(f"Total buyers: {len(BUYERS)}")
    for city, count in sorted(cities.items()):
        print(f"  {city}: {count} buyers")
    print()

    seeded = 0
    for b in BUYERS:
        buyer_id = f"B-{b['city'][:3].upper()}-{str(uuid.uuid4())[:6].upper()}"
        ts = past_iso(b["active_days_ago"])

        table.put_item(Item=to_decimal({
            "PK": f"BUYER#{buyer_id}",
            "SK": "PROFILE",
            "entity_type": "BUYER_SIGNAL",
            "buyer_id": buyer_id,
            "name": b["name"],
            "email": b.get("email", ""),
            "phone": b.get("phone", ""),
            "city": b["city"],
            "pincode": b["pincode"],
            "lat": b["lat"],
            "lng": b["lng"],
            "category_interest": b["category"],
            "max_price": b["max_price"],
            "active": True,
            "last_active": ts,
            "created_at": past_iso(b["active_days_ago"] + 30),
            # GSI9 — match by city + category
            "GSI9PK": f"BUYER_MATCH#{b['city']}#{b['category']}",
            "GSI9SK": f"PRICE#{b['max_price']:08d}",
        }))
        seeded += 1

    print(f"✅ Seeded {seeded} buyers across {len(cities)} cities")
    print("\nNow the Market Intelligence Agent will count REAL buyers from DynamoDB!")
    print("Buyers per city/category:")
    for city in sorted(cities.keys()):
        city_buyers = [b for b in BUYERS if b["city"] == city]
        cats = {}
        for b in city_buyers:
            cats[b["category"]] = cats.get(b["category"], 0) + 1
        cat_str = ", ".join(f"{c}:{n}" for c, n in sorted(cats.items()))
        print(f"  {city}: [{cat_str}]")


if __name__ == "__main__":
    seed_all_buyers()
