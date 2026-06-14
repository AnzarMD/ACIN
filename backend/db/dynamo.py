"""DynamoDB CRUD helpers for ACIN_Main single-table design."""

import boto3
import time
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from .tables import (
    TABLE_NAME,
    return_pk,
    output_sk,
    agent_run_sk,
    validation_sk,
    decision_sk,
    features_latest_sk,
    carbon_txn_sk,
    media_sk,
    trust_badge_sk,
)

import os

dynamodb = boto3.resource("dynamodb", region_name=os.getenv("AWS_REGION", "ap-south-1"))
table = dynamodb.Table(TABLE_NAME)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def to_decimal(value):
    """Convert float values to Decimal for DynamoDB."""
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, dict):
        return {k: to_decimal(v) for k, v in value.items()}
    if isinstance(value, list):
        return [to_decimal(v) for v in value]
    return value


# ─── Return Collection ───────────────────────────────────────────────────────


def get_return_collection(return_id: str) -> list:
    """Single query — retrieves ALL items for a return."""
    resp = table.query(
        KeyConditionExpression=Key("PK").eq(return_pk(return_id))
    )
    return resp["Items"]


def get_customer_id(return_id: str) -> str:
    """Retrieve customer_id from RETURN_META."""
    resp = table.get_item(
        Key={"PK": return_pk(return_id), "SK": "META"}
    )
    item = resp.get("Item", {})
    return item.get("customer_id", "UNKNOWN")


# ─── Return Record ───────────────────────────────────────────────────────────


async def create_return_record(return_data, status, validation_result) -> str:
    """Create a new return record in ACIN_Main."""
    import uuid

    return_id = f"RET-{datetime.now().strftime('%Y-%m-%d')}-{str(uuid.uuid4())[:8]}"
    ts = now_iso()

    # Extract location fields
    location = return_data.location.dict() if return_data.location else {}
    city = location.get("city", "")
    pincode = location.get("pincode", "")
    lat = location.get("lat")
    lng = location.get("lng")

    table.put_item(Item=to_decimal({
        "PK": return_pk(return_id),
        "SK": "META",
        "entity_type": "RETURN_META",
        "return_id": return_id,
        "customer_id": return_data.customer_id,
        "product_id": return_data.product_id,
        "product_name": getattr(return_data, "product_name", "") or return_data.product_id,
        "category": getattr(return_data, "category", "") or "Other",
        "original_price": getattr(return_data, "original_price", 0) or 0,
        "return_reason": return_data.return_reason,
        "status": status.value,
        "stage": "VALIDATION",
        "city": city,
        "pincode": pincode,
        "lat": lat,       # ← exact returner latitude
        "lng": lng,       # ← exact returner longitude
        "validation_status": validation_result.status if validation_result else "PENDING",
        "image_fcs": validation_result.fcs if validation_result else 0,
        "fraud_score": 0,
        "requires_manual_review": validation_result.fcs >= 0.50 if validation_result else False,
        "created_at": ts,
        "updated_at": ts,
        # GSI1 — customer return history
        "GSI1PK": f"CUSTOMER#{return_data.customer_id}",
        "GSI1SK": f"RETURN#{ts}",
        # GSI2 — status queue
        "GSI2PK": f"STATUS#{status.value}",
        "GSI2SK": f"UPDATED#{ts}",
        # GSI3 — product return history
        "GSI3PK": f"PRODUCT#{return_data.product_id}",
        "GSI3SK": f"RETURN#{ts}",
    }))

    # Store media references
    for i, url in enumerate(return_data.image_urls):
        table.put_item(Item={
            "PK": return_pk(return_id),
            "SK": media_sk(f"{i:04d}"),
            "entity_type": "RETURN_MEDIA",
            "s3_url": url,
            "scan_status": "SCANNED" if validation_result else "PENDING",
            "created_at": ts,
        })

    return return_id


# ─── Agent Outputs ───────────────────────────────────────────────────────────


def put_agent_output(
    return_id: str,
    agent: str,
    run_id: str,
    payload: dict,
    model_id: str,
    prompt_version: str,
    agent_version: str,
    confidence: float,
):
    ts = now_iso()
    table.put_item(Item=to_decimal({
        "PK": return_pk(return_id),
        "SK": output_sk(agent, run_id),
        "entity_type": "AGENT_OUTPUT",
        "agent": agent,
        "payload": payload,
        "model_id": model_id,
        "prompt_version": prompt_version,
        "agent_version": agent_version,
        "confidence": str(confidence),
        "created_at": ts,
        # GSI8
        "GSI8PK": f"AGENT#{agent}#COMPLETED",
        "GSI8SK": f"STARTED#{ts}",
    }))


def put_agent_run(
    return_id: str,
    agent: str,
    run_id: str,
    status: str = "RUNNING",
    retry_count: int = 0,
):
    ts = now_iso()
    table.put_item(Item={
        "PK": return_pk(return_id),
        "SK": agent_run_sk(agent, run_id),
        "entity_type": "AGENT_RUN",
        "agent_name": agent,
        "status": status,
        "retry_count": retry_count,
        "started_at": ts,
        # GSI8
        "GSI8PK": f"AGENT#{agent}#{status}",
        "GSI8SK": f"STARTED#{ts}",
    })


# ─── Validation ──────────────────────────────────────────────────────────────


def put_validation_result(return_id: str, result):
    from dataclasses import asdict

    ts = now_iso()
    result_dict = asdict(result)
    item = {
        "PK": return_pk(return_id),
        "SK": validation_sk(ts),
        "entity_type": "IMAGE_VALIDATION",
        # GSI10
        "GSI10PK": f"CUSTOMER#{get_customer_id(return_id)}",
        "GSI10SK": f"VALIDATION#{result.fcs:.3f}#{ts}",
    }
    for k, v in result_dict.items():
        if isinstance(v, (float, bool)):
            item[k] = str(v)
        else:
            item[k] = v

    table.put_item(Item=to_decimal(item))


def get_validation_result(return_id: str):
    """Retrieve existing validation result if already computed."""
    resp = table.query(
        KeyConditionExpression=Key("PK").eq(return_pk(return_id))
        & Key("SK").begins_with("VALIDATION#"),
        ScanIndexForward=False,
        Limit=1,
    )
    items = resp.get("Items", [])
    return items[0] if items else None


# ─── Status Updates ──────────────────────────────────────────────────────────


def update_return_status(return_id: str, status):
    ts = now_iso()
    table.update_item(
        Key={"PK": return_pk(return_id), "SK": "META"},
        UpdateExpression="SET #s=:s, GSI2PK=:gp, GSI2SK=:gs, updated_at=:ts",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={
            ":s": status.value,
            ":gp": f"STATUS#{status.value}",
            ":gs": f"UPDATED#{ts}",
            ":ts": ts,
        },
    )


# ─── Idempotency ─────────────────────────────────────────────────────────────


def try_acquire_validation_lock(return_id: str, version: str = "v1") -> bool:
    """Prevent duplicate Rekognition calls from S3 retries."""
    try:
        table.put_item(
            Item={
                "PK": return_pk(return_id),
                "SK": f"IDEMPOTENCY#VALIDATION#{version}",
                "entity_type": "IDEMPOTENCY_RECORD",
                "status": "IN_PROGRESS",
                "ttl_epoch": int(time.time()) + 3600,
            },
            ConditionExpression="attribute_not_exists(PK)",
        )
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return False
        raise


# ─── Features Latest ─────────────────────────────────────────────────────────


def update_features_latest(return_id: str, features: dict):
    table.put_item(Item=to_decimal({
        "PK": return_pk(return_id),
        "SK": features_latest_sk(),
        "entity_type": "FEATURES_LATEST",
        **features,
        "updated_at": now_iso(),
    }))


def get_features_latest(return_id: str) -> Optional[dict]:
    resp = table.get_item(
        Key={"PK": return_pk(return_id), "SK": features_latest_sk()}
    )
    return resp.get("Item")


# ─── Decisions ───────────────────────────────────────────────────────────────


def put_decision(return_id: str, decision: dict, decision_number: int = 1):
    ts = now_iso()
    item = to_decimal({
        "PK": return_pk(return_id),
        "SK": decision_sk(decision_number),
        "entity_type": "DECISION",
        **decision,
        "created_at": ts,
        # GSI4 — items by destination
        "GSI4PK": f"DESTINATION#{decision.get('destination', 'UNKNOWN')}",
        "GSI4SK": f"GRADE#{decision.get('grade', 'X')}#{ts}",
    })
    table.put_item(Item=item)

    # DECISION#LATEST — copy ALL decision fields (not just pointer)
    table.put_item(Item=to_decimal({
        "PK": return_pk(return_id),
        "SK": "DECISION#LATEST",
        "entity_type": "DECISION_LATEST",
        "decision_sk": decision_sk(decision_number),
        **decision,
        "status": "DECIDED",
        "created_at": ts,
        "updated_at": ts,
    }))


# ─── Carbon Ledger ───────────────────────────────────────────────────────────


def record_carbon_txn(return_id: str, co2_saved_kg: float, source: str):
    """Immutable carbon ledger — independent of Green Points."""
    import uuid

    ts = now_iso()
    txn_id = str(uuid.uuid4())[:8]
    table.put_item(Item=to_decimal({
        "PK": return_pk(return_id),
        "SK": carbon_txn_sk(ts, txn_id),
        "entity_type": "CARBON_TXN",
        "co2_saved_kg": co2_saved_kg,
        "source": source,  # RESALE | REFURB | RECYCLE | DONATE
        "status": "POSTED",
        "created_at": ts,
    }))


# ─── Trust Badges ────────────────────────────────────────────────────────────


def put_trust_badge(return_id: str, badge_type: str, reason: str):
    import uuid

    badge_id = str(uuid.uuid4())[:8]
    table.put_item(Item={
        "PK": return_pk(return_id),
        "SK": trust_badge_sk(badge_id),
        "entity_type": "TRUST_BADGE",
        "badge_type": badge_type,
        "reason": reason,
        "created_at": now_iso(),
    })


# ─── Review Team Notification ────────────────────────────────────────────────


async def notify_review_team(return_id: str, validation_result):
    """Queue a manual review case for the risk operations team."""
    table.put_item(Item=to_decimal({
        "PK": return_pk(return_id),
        "SK": f"REVIEW#{now_iso()}",
        "entity_type": "RISK_REVIEW",
        "fcs": validation_result.fcs,
        "status": validation_result.status,
        "reason": validation_result.reason,
        "flagged_urls": validation_result.flagged_image_urls,
        "review_status": "PENDING",
        "created_at": now_iso(),
    }))
