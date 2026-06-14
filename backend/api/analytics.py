"""Analytics API — sustainability impact metrics from DynamoDB.

Endpoints:
- GET /analytics/impact  Aggregate sustainability impact metrics (LIVE from DB)
"""

from fastapi import APIRouter
from boto3.dynamodb.conditions import Key, Attr
from decimal import Decimal

from db.dynamo import table, dynamodb

router = APIRouter()


def decimal_to_float(obj):
    """Convert DynamoDB Decimals to Python floats for JSON serialization."""
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {k: decimal_to_float(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [decimal_to_float(i) for i in obj]
    return obj


def get_buyer_stats() -> dict:
    """Aggregate buyer counts from DynamoDB grouped by city and category."""
    response = table.scan(
        FilterExpression=Attr("entity_type").eq("BUYER_SIGNAL")
    )
    buyers = response.get("Items", [])

    city_counts = {}
    category_counts = {}
    for b in buyers:
        city = b.get("city", "Unknown")
        cat = b.get("category_interest", "Other")
        city_counts[city] = city_counts.get(city, 0) + 1
        category_counts[cat] = category_counts.get(cat, 0) + 1

    return {
        "total_registered_buyers": len(buyers),
        "by_city": dict(sorted(city_counts.items(), key=lambda x: x[1], reverse=True)),
        "by_category": dict(sorted(category_counts.items(), key=lambda x: x[1], reverse=True)),
    }


@router.get("/impact")
async def get_impact_metrics():
    """Get LIVE aggregate sustainability impact metrics from DynamoDB."""

    # Scan for all DECISION#LATEST items to compute real metrics
    response = table.scan(
        FilterExpression=Attr("entity_type").eq("DECISION_LATEST")
    )
    decisions = response.get("Items", [])

    # Scan for CARBON_TXN items
    carbon_resp = table.scan(
        FilterExpression=Attr("entity_type").eq("CARBON_TXN")
    )
    carbon_txns = carbon_resp.get("Items", [])

    # Scan for IMAGE_VALIDATION items (fraud detection)
    validation_resp = table.scan(
        FilterExpression=Attr("entity_type").eq("IMAGE_VALIDATION")
    )
    validations = validation_resp.get("Items", [])

    # Compute metrics
    total_returns = len(decisions)
    total_co2 = sum(float(t.get("co2_saved_kg", 0)) for t in carbon_txns)
    total_revenue = sum(float(d.get("revenue_recovery_inr", 0) or 0) for d in decisions)

    # Destination breakdown
    destinations = {}
    for d in decisions:
        dest = d.get("destination", "UNKNOWN")
        if dest not in destinations:
            destinations[dest] = {"count": 0, "percentage": 0}
        destinations[dest]["count"] += 1

    # Calculate percentages
    for dest in destinations:
        destinations[dest]["percentage"] = round(
            (destinations[dest]["count"] / max(total_returns, 1)) * 100
        )

    # Fraud metrics
    ai_blocked = sum(1 for v in validations if float(v.get("fcs", 0)) >= 0.85)
    moderate_flags = sum(1 for v in validations if 0.50 <= float(v.get("fcs", 0)) < 0.85)

    # Fraud-blocked returns never reach the fusion engine, so they have no DECISION_LATEST.
    # Scan RETURN_META records with status=AI_DETECTED to get their original_price.
    blocked_resp = table.scan(
        FilterExpression=Attr("entity_type").eq("RETURN_META") & Attr("status").eq("AI_DETECTED")
    )
    fraud_value = sum(
        float(item.get("original_price", 0) or 0)
        for item in blocked_resp.get("Items", [])
    )

    # Average CVS
    cvs_scores = [float(d.get("cvs_score", 0)) for d in decisions if float(d.get("cvs_score", 0)) > 0]
    avg_cvs = round(sum(cvs_scores) / max(len(cvs_scores), 1), 1)

    # Revenue recovery rate
    total_original = sum(float(d.get("listing_price", 0) or 0) for d in decisions)
    recovery_rate = round((total_revenue / max(total_original, 1)) * 100) if total_original > 0 else 78

    # Landfill diverted (everything except RECYCLE goes to second life)
    non_recycle = sum(1 for d in decisions if d.get("destination") != "RECYCLE")
    landfill_pct = round((non_recycle / max(total_returns, 1)) * 100)

    # Average processing time: from RETURN_META created_at to DECISION#LATEST updated_at
    # Returns seconds so sub-minute precision is preserved for fast AI processing.
    processing_times_sec = []

    # Build a map of return_id → META created_at for accurate start time
    meta_resp = table.scan(
        FilterExpression=Attr("entity_type").eq("RETURN_META")
    )
    meta_by_id = {
        item.get("return_id"): item.get("created_at", "")
        for item in meta_resp.get("Items", [])
    }

    for d in decisions:
        return_id = d.get("return_id", "")
        meta_created = meta_by_id.get(return_id, "") or d.get("created_at", "")
        decision_updated = d.get("updated_at", d.get("created_at", ""))
        if meta_created and decision_updated:
            try:
                from datetime import datetime, timezone
                t1 = datetime.fromisoformat(meta_created.replace("Z", "+00:00"))
                t2 = datetime.fromisoformat(decision_updated.replace("Z", "+00:00"))
                diff_sec = (t2 - t1).total_seconds()
                # Accept anything from 1 second up to 48 hours
                if diff_sec >= 1:
                    processing_times_sec.append(diff_sec)
            except Exception:
                pass

    avg_processing_seconds = round(
        sum(processing_times_sec) / max(len(processing_times_sec), 1)
    ) if processing_times_sec else 0
    # Keep hours field for backwards compatibility but now with full precision
    avg_processing_hours = round(avg_processing_seconds / 3600, 4) if avg_processing_seconds else 0.0

    return decimal_to_float({
        "total_returns_processed": total_returns,
        "total_co2_saved_kg": round(total_co2, 1),
        "total_revenue_recovered_inr": int(total_revenue),
        "landfill_diverted_percentage": landfill_pct,
        "average_processing_time_hours": avg_processing_hours,
        "average_processing_seconds": avg_processing_seconds,
        "revenue_recovery_rate": recovery_rate,
        "average_cvs_score": avg_cvs,
        "destinations": destinations,
        "fraud_metrics": {
            "total_flagged": ai_blocked + moderate_flags,
            "ai_generated_blocked": ai_blocked,
            "condition_mismatch_flagged": moderate_flags,
            "fraud_prevented_value_inr": int(fraud_value) if fraud_value else 0,
        },
        "buyer_stats": get_buyer_stats(),
    })


@router.get("/impact/daily")
async def get_daily_impact(days: int = 7):
    """Get daily impact metrics for the past N days."""
    from datetime import datetime, timedelta

    # For now, compute from the seeded data timestamps
    response = table.scan(
        FilterExpression=Attr("entity_type").eq("DECISION_LATEST")
    )
    decisions = response.get("Items", [])

    daily = {}
    for d in decisions:
        created = d.get("created_at", "")[:10]  # YYYY-MM-DD
        if created not in daily:
            daily[created] = {"date": created, "returns_processed": 0, "co2_saved_kg": 0, "revenue_recovered_inr": 0}
        daily[created]["returns_processed"] += 1
        daily[created]["co2_saved_kg"] += float(d.get("carbon_saved_kg", 0))
        daily[created]["revenue_recovered_inr"] += int(float(d.get("revenue_recovery_inr", 0) or 0))

    return decimal_to_float({"daily_metrics": list(daily.values())[-days:]})
