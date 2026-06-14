"""Seed a test buyer for notification verification."""
import boto3
from decimal import Decimal
from datetime import datetime, timezone

dynamodb = boto3.resource("dynamodb", region_name="ap-south-1")
table = dynamodb.Table("ACIN_Main")

def seed_test_buyer():
    ts = datetime.now(timezone.utc).isoformat()
    table.put_item(Item={
        "PK": "BUYER#B-TEST-SHOCKWVE",
        "SK": "PROFILE",
        "entity_type": "BUYER_SIGNAL",
        "buyer_id": "B-TEST-SHOCKWVE",
        "name": "Shockwave Test Buyer",
        "email": "shockwve2@gmail.com",
        "phone": "+919356862180",
        "city": "Mumbai",
        "pincode": "400001",
        "lat": Decimal("19.0760"),
        "lng": Decimal("72.8777"),
        "category_interest": "Any",
        "max_price": 100000,
        "active": True,
        "last_active": ts,
        "created_at": ts,
        "GSI9PK": "BUYER_MATCH#Mumbai#Any",
        "GSI9SK": "PRICE#00100000",
    })
    print("✅ Seeded test buyer: shockwve2@gmail.com / 9356862180 in Mumbai")

if __name__ == "__main__":
    seed_test_buyer()
