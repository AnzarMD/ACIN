"""
ACIN Database Seeder — Populates DynamoDB with demo data for testing.

Run: python seed.py

This creates realistic demo returns with full agent outputs, decisions,
and impact metrics so the frontend has data to display immediately.
"""

import boto3
import uuid
import random
from datetime import datetime, timezone, timedelta
from decimal import Decimal

# ─── Config ──────────────────────────────────────────────────────────────────

REGION = "ap-south-1"
TABLE_NAME = "ACIN_Main"

dynamodb = boto3.resource("dynamodb", region_name=REGION)
table = dynamodb.Table(TABLE_NAME)


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def past_iso(hours_ago):
    return (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat()


def to_decimal(obj):
    """Convert floats to Decimal for DynamoDB."""
    if isinstance(obj, float):
        return Decimal(str(round(obj, 4)))
    if isinstance(obj, dict):
        return {k: to_decimal(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [to_decimal(i) for i in obj]
    return obj


# ─── Demo Products ───────────────────────────────────────────────────────────

DEMO_RETURNS = [
    {
        "return_id": "RET-2025-06-0001",
        "product_id": "B09XS7JWHH",
        "customer_id": "C-28374-MH",
        "product_name": "Philips Baby Monitor HD",
        "category": "Electronics",
        "original_price": 4999,
        "return_reason": "changed_mind",
        "city": "Mumbai",
        "pincode": "400001",
        "condition_score": 92,
        "grade": "A",
        "demand_score": 87,
        "buyer_count": 21,
        "expected_sale_days": 3,
        "destination": "INSTANT_RESALE",
        "cvs_score": 88.3,
        "confidence": 94,
        "listing_price": 4199,
        "carbon_saved_kg": 2.4,
        "image_fcs": 0.12,
        "fraud_probability": 0.04,
        "explanation": "Excellent condition (92/100). 21 active buyers nearby. No refurbishment needed. Same-day delivery to buyer saves Rs 140.",
    },
    {
        "return_id": "RET-2025-06-0002",
        "product_id": "B08N5WRWNW",
        "customer_id": "C-19482-DL",
        "product_name": "Dell Inspiron 15 Laptop",
        "category": "Computers",
        "original_price": 52999,
        "return_reason": "defective",
        "city": "Delhi",
        "pincode": "110001",
        "condition_score": 62,
        "grade": "C",
        "demand_score": 79,
        "buyer_count": 12,
        "expected_sale_days": 7,
        "destination": "REFURBISH",
        "cvs_score": 73.1,
        "confidence": 89,
        "listing_price": 38999,
        "carbon_saved_kg": 3.2,
        "image_fcs": 0.08,
        "fraud_probability": 0.12,
        "explanation": "Cracked hinge detected but otherwise functional. Repair cost Rs 2,000 with 750% ROI. 12 buyers waiting in Delhi region. Saves 3.2 kg CO2 vs manufacturing new.",
    },
    {
        "return_id": "RET-2025-06-0003",
        "product_id": "B07WR4SH1X",
        "customer_id": "C-55901-KA",
        "product_name": "Nike Air Max 270 (Size 10)",
        "category": "Footwear",
        "original_price": 8999,
        "return_reason": "size_mismatch",
        "city": "Bangalore",
        "pincode": "560001",
        "condition_score": 98,
        "grade": "A",
        "demand_score": 92,
        "buyer_count": 8,
        "expected_sale_days": 1,
        "destination": "EXCHANGE",
        "cvs_score": 91.5,
        "confidence": 97,
        "listing_price": 8499,
        "carbon_saved_kg": 1.8,
        "image_fcs": 0.05,
        "fraud_probability": 0.02,
        "explanation": "Perfect condition, wrong size. Matched with 3 nearby customers who returned Size 8. Direct exchange — zero logistics cost, zero warehouse time.",
    },
    {
        "return_id": "RET-2025-06-0004",
        "product_id": "B09GY3456X",
        "customer_id": "C-77234-TN",
        "product_name": "Prestige Induction Cooktop",
        "category": "Home & Kitchen",
        "original_price": 2499,
        "return_reason": "defective",
        "city": "Chennai",
        "pincode": "600001",
        "condition_score": 35,
        "grade": "D",
        "demand_score": 25,
        "buyer_count": 2,
        "expected_sale_days": 30,
        "destination": "RECYCLE",
        "cvs_score": 32.4,
        "confidence": 91,
        "listing_price": 0,
        "carbon_saved_kg": 0.9,
        "image_fcs": 0.15,
        "fraud_probability": 0.08,
        "explanation": "Severe burn damage on heating element. Repair cost exceeds product value. Routed to certified e-waste recycler — recovers copper and saves 0.9 kg CO2.",
    },
    {
        "return_id": "RET-2025-06-0005",
        "product_id": "B08KHN3SY2",
        "customer_id": "C-43210-WB",
        "product_name": "JBL Tune 760NC Headphones",
        "category": "Electronics",
        "original_price": 4999,
        "return_reason": "not_as_described",
        "city": "Kolkata",
        "pincode": "700001",
        "condition_score": 75,
        "grade": "B",
        "demand_score": 68,
        "buyer_count": 9,
        "expected_sale_days": 5,
        "destination": "INSTANT_RESALE",
        "cvs_score": 76.2,
        "confidence": 86,
        "listing_price": 3499,
        "carbon_saved_kg": 1.5,
        "image_fcs": 0.22,
        "fraud_probability": 0.15,
        "explanation": "Light wear on ear cushions, fully functional. 9 buyers in Kolkata area. Priced competitively at Rs 3,499 — 70% recovery. Saves 1.5 kg CO2.",
    },
    {
        "return_id": "RET-2025-06-0006",
        "product_id": "B09FRAUD01",
        "customer_id": "C-99999-MH",
        "product_name": "Sony WH-1000XM5 (FRAUD ATTEMPT)",
        "category": "Electronics",
        "original_price": 11499,
        "return_reason": "defective",
        "city": "Mumbai",
        "pincode": "400050",
        "condition_score": 95,
        "grade": "A",
        "demand_score": 0,
        "buyer_count": 0,
        "expected_sale_days": 0,
        "destination": "AI_DETECTED",
        "cvs_score": 0,
        "confidence": 98,
        "listing_price": 0,
        "carbon_saved_kg": 0,
        "image_fcs": 0.94,
        "fraud_probability": 0.91,
        "explanation": "BLOCKED: Return images failed authenticity verification. AI-generated image detected (FCS=0.94). Account flagged for manual review.",
    },
    {
        "return_id": "RET-2025-06-0007",
        "product_id": "B07PVCVBN7",
        "customer_id": "C-61234-RJ",
        "product_name": "Wildcraft Backpack 45L",
        "category": "Luggage",
        "original_price": 2999,
        "return_reason": "changed_mind",
        "city": "Jaipur",
        "pincode": "302001",
        "condition_score": 88,
        "grade": "A",
        "demand_score": 45,
        "buyer_count": 4,
        "expected_sale_days": 8,
        "destination": "DONATE",
        "cvs_score": 48.7,
        "confidence": 82,
        "listing_price": 0,
        "carbon_saved_kg": 1.1,
        "image_fcs": 0.10,
        "fraud_probability": 0.03,
        "explanation": "Good condition but low local demand (off-season). Resale profit negative after logistics. Routed to partner NGO — serves underprivileged students. Saves 1.1 kg CO2.",
    },
]


# ─── Seed Functions ──────────────────────────────────────────────────────────


def seed_return(r: dict, hours_ago: int):
    """Seed a complete return with all entity types."""
    rid = r["return_id"]
    ts = past_iso(hours_ago)
    pk = f"RETURN#{rid}"

    status = "COMPLETED" if r["destination"] != "AI_DETECTED" else "AI_DETECTED"

    # 1. RETURN_META
    table.put_item(Item=to_decimal({
        "PK": pk,
        "SK": "META",
        "entity_type": "RETURN_META",
        "return_id": rid,
        "customer_id": r["customer_id"],
        "product_id": r["product_id"],
        "product_name": r["product_name"],
        "category": r["category"],
        "original_price": r["original_price"],
        "return_reason": r["return_reason"],
        "status": status,
        "stage": "COMPLETED",
        "validation_status": "AI_DETECTED" if r["image_fcs"] >= 0.85 else "AUTHENTIC",
        "image_fcs": r["image_fcs"],
        "fraud_score": r["fraud_probability"],
        "requires_manual_review": r["fraud_probability"] >= 0.60,
        "created_at": ts,
        "updated_at": now_iso(),
        "GSI1PK": f"CUSTOMER#{r['customer_id']}",
        "GSI1SK": f"RETURN#{ts}",
        "GSI2PK": f"STATUS#{status}",
        "GSI2SK": f"UPDATED#{ts}",
        "GSI3PK": f"PRODUCT#{r['product_id']}",
        "GSI3SK": f"RETURN#{ts}",
    }))

    # 2. IMAGE_VALIDATION
    table.put_item(Item=to_decimal({
        "PK": pk,
        "SK": f"VALIDATION#{ts}",
        "entity_type": "IMAGE_VALIDATION",
        "fcs": r["image_fcs"],
        "status": "AI_DETECTED" if r["image_fcs"] >= 0.85 else "AUTHENTIC",
        "metadata_ai_score": r["image_fcs"] * 0.5,
        "gan_diffusion_score": r["image_fcs"] * 0.8,
        "ela_score": r["image_fcs"] * 0.3,
        "c2pa_score": 0.2,
        "rekognition_score": r["image_fcs"] * 0.6,
        "pipeline_blocked": str(r["image_fcs"] >= 0.85),
        "created_at": ts,
    }))

    # Skip agent outputs for blocked returns
    if r["destination"] == "AI_DETECTED":
        print(f"  ⛔ {rid} — FRAUD BLOCKED (FCS={r['image_fcs']})")
        return

    # 3. AGENT_OUTPUT — Product
    run_id = str(uuid.uuid4())[:8]
    table.put_item(Item=to_decimal({
        "PK": pk,
        "SK": f"OUTPUT#PRODUCT#{run_id}",
        "entity_type": "AGENT_OUTPUT",
        "agent": "PRODUCT",
        "payload": {
            "condition_score": r["condition_score"],
            "grade": r["grade"],
            "defects": [],
            "fraud_probability": r["fraud_probability"],
            "estimated_repair_cost_inr": 0 if r["grade"] == "A" else 2000,
        },
        "model_id": "claude-sonnet-4-6",
        "confidence": str(r["condition_score"] / 100),
        "created_at": ts,
        "GSI8PK": "AGENT#PRODUCT#COMPLETED",
        "GSI8SK": f"STARTED#{ts}",
    }))

    # 4. AGENT_OUTPUT — Market
    run_id = str(uuid.uuid4())[:8]
    table.put_item(Item=to_decimal({
        "PK": pk,
        "SK": f"OUTPUT#MARKET#{run_id}",
        "entity_type": "AGENT_OUTPUT",
        "agent": "MARKET",
        "payload": {
            "demand_score": r["demand_score"],
            "buyer_count": r["buyer_count"],
            "expected_sale_days": r["expected_sale_days"],
            "region": r["city"],
        },
        "model_id": "claude-sonnet-4-6",
        "confidence": str(r["demand_score"] / 100),
        "created_at": ts,
        "GSI8PK": "AGENT#MARKET#COMPLETED",
        "GSI8SK": f"STARTED#{ts}",
    }))

    # 5. AGENT_OUTPUT — Pricing
    run_id = str(uuid.uuid4())[:8]
    table.put_item(Item=to_decimal({
        "PK": pk,
        "SK": f"OUTPUT#PRICING#{run_id}",
        "entity_type": "AGENT_OUTPUT",
        "agent": "PRICING",
        "payload": {
            "fast_sale_price": int(r["listing_price"] * 0.9),
            "balanced_price": r["listing_price"],
            "max_profit_price": int(r["listing_price"] * 1.1),
            "original_price": r["original_price"],
            "recommended_strategy": "balanced",
        },
        "model_id": "claude-sonnet-4-6",
        "confidence": "0.85",
        "created_at": ts,
        "GSI8PK": "AGENT#PRICING#COMPLETED",
        "GSI8SK": f"STARTED#{ts}",
    }))

    # 6. AGENT_OUTPUT — Fraud
    run_id = str(uuid.uuid4())[:8]
    table.put_item(Item=to_decimal({
        "PK": pk,
        "SK": f"OUTPUT#FRAUD#{run_id}",
        "entity_type": "AGENT_OUTPUT",
        "agent": "FRAUD",
        "payload": {
            "fraud_score": r["fraud_probability"],
            "fraud_type": None,
            "image_fcs": r["image_fcs"],
            "vision_fraud_prob": r["fraud_probability"],
            "recommendation": "PROCEED",
        },
        "model_id": "claude-sonnet-4-6",
        "confidence": "0.90",
        "created_at": ts,
        "GSI8PK": "AGENT#FRAUD#COMPLETED",
        "GSI8SK": f"STARTED#{ts}",
    }))

    # 7. DECISION#LATEST
    table.put_item(Item=to_decimal({
        "PK": pk,
        "SK": "DECISION#LATEST",
        "entity_type": "DECISION_LATEST",
        "destination": r["destination"],
        "cvs_score": r["cvs_score"],
        "confidence": r["confidence"],
        "fraud_check": "CLEAR" if r["fraud_probability"] < 0.30 else "FLAGGED",
        "image_fcs": r["image_fcs"],
        "fraud_probability": r["fraud_probability"],
        "listing_price": r["listing_price"],
        "carbon_saved_kg": r["carbon_saved_kg"],
        "revenue_recovery_inr": r["listing_price"],
        "trust_badges": ["AI_VERIFIED", "LOW_FRAUD_RISK"] if r["image_fcs"] < 0.30 else [],
        "explanation": r["explanation"],
        "grade": r["grade"],
        "status": "DECIDED",
        "created_at": ts,
        "GSI4PK": f"DESTINATION#{r['destination']}",
        "GSI4SK": f"GRADE#{r['grade']}#{ts}",
    }))

    # 8. FEATURES#LATEST
    table.put_item(Item=to_decimal({
        "PK": pk,
        "SK": "FEATURES#LATEST",
        "entity_type": "FEATURES_LATEST",
        "condition_score": r["condition_score"],
        "demand_score": r["demand_score"],
        "pricing_score": r["listing_price"] / max(r["original_price"], 1),
        "carbon_score": r["carbon_saved_kg"],
        "fraud_score": r["fraud_probability"],
        "image_fcs": r["image_fcs"],
        "updated_at": ts,
    }))

    # 9. CARBON_TXN
    table.put_item(Item=to_decimal({
        "PK": pk,
        "SK": f"CARBON_TXN#{ts}#{str(uuid.uuid4())[:8]}",
        "entity_type": "CARBON_TXN",
        "co2_saved_kg": r["carbon_saved_kg"],
        "source": r["destination"].split("_")[0] if "_" in r["destination"] else r["destination"],
        "status": "POSTED",
        "created_at": ts,
    }))

    # 10. TRUST_BADGE (for good returns)
    if r["image_fcs"] < 0.30:
        table.put_item(Item=to_decimal({
            "PK": pk,
            "SK": f"TRUST_BADGE#{str(uuid.uuid4())[:8]}",
            "entity_type": "TRUST_BADGE",
            "badge_type": "AI_VERIFIED",
            "reason": "Image authenticity verified (FCS < 0.30)",
            "created_at": ts,
        }))

    print(f"  ✅ {rid} — {r['product_name']} → {r['destination']} (CVS: {r['cvs_score']})")


def seed_customers():
    """Seed customer profiles."""
    customers = [
        {"id": "C-28374-MH", "name": "Rahul Sharma", "city": "Mumbai", "tier": "Prime"},
        {"id": "C-19482-DL", "name": "Priya Gupta", "city": "Delhi", "tier": "Prime"},
        {"id": "C-55901-KA", "name": "Arjun Reddy", "city": "Bangalore", "tier": "Standard"},
        {"id": "C-77234-TN", "name": "Lakshmi Iyer", "city": "Chennai", "tier": "Standard"},
        {"id": "C-43210-WB", "name": "Amit Das", "city": "Kolkata", "tier": "Prime"},
        {"id": "C-99999-MH", "name": "Suspicious Account", "city": "Mumbai", "tier": "Standard"},
        {"id": "C-61234-RJ", "name": "Vikram Singh", "city": "Jaipur", "tier": "Standard"},
    ]

    for c in customers:
        table.put_item(Item={
            "PK": f"CUSTOMER#{c['id']}",
            "SK": "PROFILE",
            "entity_type": "CUSTOMER_PROFILE",
            "customer_id": c["id"],
            "name": c["name"],
            "city": c["city"],
            "tier": c["tier"],
            "created_at": past_iso(720),
        })
    print(f"  👤 Seeded {len(customers)} customer profiles")


def seed_partners():
    """Seed partner organizations."""
    partners = [
        {"id": "P-REFURB-01", "name": "QuickFix Mumbai", "type": "REFURBISH", "city": "Mumbai", "capacity": 50},
        {"id": "P-REFURB-02", "name": "TechRevive Delhi", "type": "REFURBISH", "city": "Delhi", "capacity": 30},
        {"id": "P-DONATE-01", "name": "Goonj Foundation", "type": "DONATE", "city": "Delhi", "capacity": 200},
        {"id": "P-DONATE-02", "name": "Robin Hood Army", "type": "DONATE", "city": "Mumbai", "capacity": 150},
        {"id": "P-RECYCLE-01", "name": "E-Parisaraa", "type": "RECYCLE", "city": "Bangalore", "capacity": 100},
        {"id": "P-RECYCLE-02", "name": "Attero Recycling", "type": "RECYCLE", "city": "Delhi", "capacity": 80},
    ]

    for p in partners:
        table.put_item(Item=to_decimal({
            "PK": f"PARTNER#{p['id']}",
            "SK": "META",
            "entity_type": "PARTNER_META",
            "partner_id": p["id"],
            "name": p["name"],
            "partner_type": p["type"],
            "city": p["city"],
            "capacity": p["capacity"],
            "rating": Decimal("4.5"),
            "created_at": past_iso(1000),
            "GSI7PK": f"PARTNER#{p['id']}",
            "GSI7SK": f"RATING#4.5",
        }))
    print(f"  🏭 Seeded {len(partners)} partner organizations")


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    print("\n🌱 ACIN Database Seeder")
    print("=" * 50)
    print(f"Table: {TABLE_NAME}")
    print(f"Region: {REGION}")
    print(f"Returns to seed: {len(DEMO_RETURNS)}")
    print("=" * 50)

    print("\n📦 Seeding customers...")
    seed_customers()

    print("\n🏭 Seeding partners...")
    seed_partners()

    print("\n📋 Seeding returns with full agent outputs...")
    for i, r in enumerate(DEMO_RETURNS):
        seed_return(r, hours_ago=(len(DEMO_RETURNS) - i) * 4)

    print("\n" + "=" * 50)
    print("✅ Seeding complete!")
    print(f"   - {len(DEMO_RETURNS)} returns (with validation, agents, decisions)")
    print(f"   - 7 customer profiles")
    print(f"   - 6 partner organizations")
    print("\n🚀 Demo return IDs:")
    for r in DEMO_RETURNS:
        icon = "⛔" if r["destination"] == "AI_DETECTED" else "✅"
        print(f"   {icon} {r['return_id']} — {r['destination']}")

    print("\n💡 Test with:")
    print(f"   curl http://localhost:8000/v1/returns/RET-2025-06-0001")
    print(f"   curl http://localhost:8000/v1/returns/RET-2025-06-0001/decision")
    print(f"   curl http://localhost:8000/v1/analytics/impact")
    print()


if __name__ == "__main__":
    main()


# ─── Buyer Registry Seed ─────────────────────────────────────────────────────

def seed_buyers():
    """Seed buyers interested in receiving resale notifications."""
    buyers = [
        {"id": "B-MUM001", "name": "Aarav Mehta", "email": "aarav@example.com", "phone": "+91-9820011111", "city": "Mumbai", "category": "Electronics", "max_price": 15000},
        {"id": "B-MUM002", "name": "Diya Shah", "email": "diya@example.com", "phone": "+91-9820022222", "city": "Mumbai", "category": "Footwear", "max_price": 12000},
        {"id": "B-MUM003", "name": "Kabir Patel", "email": "kabir@example.com", "phone": "+91-9820033333", "city": "Mumbai", "category": "Electronics", "max_price": 60000},
        {"id": "B-DEL001", "name": "Ananya Reddy", "email": "ananya@example.com", "phone": "+91-9810044444", "city": "Delhi", "category": "Computers", "max_price": 50000},
        {"id": "B-DEL002", "name": "Vivaan Kumar", "email": "vivaan@example.com", "phone": "+91-9810055555", "city": "Delhi", "category": "Electronics", "max_price": 20000},
        {"id": "B-BLR001", "name": "Ishaan Nair", "email": "ishaan@example.com", "phone": "+91-9880066666", "city": "Bangalore", "category": "Footwear", "max_price": 10000},
        {"id": "B-BLR002", "name": "Saanvi Rao", "email": "saanvi@example.com", "phone": "+91-9880077777", "city": "Bangalore", "category": "Any", "max_price": 100000},
    ]

    for b in buyers:
        table.put_item(Item=to_decimal({
            "PK": f"BUYER#{b['id']}",
            "SK": "PROFILE",
            "entity_type": "BUYER_SIGNAL",
            "buyer_id": b["id"],
            "name": b["name"],
            "email": b["email"],
            "phone": b["phone"],
            "city": b["city"],
            "category_interest": b["category"],
            "max_price": b["max_price"],
            "created_at": past_iso(500),
            "GSI9PK": f"BUYER_MATCH#{b['city']}#{b['category']}",
            "GSI9SK": f"PRICE#{b['max_price']:08d}",
        }))
    print(f"  🛒 Seeded {len(buyers)} buyers for resale matching")


if __name__ == "__main__":
    seed_buyers()
