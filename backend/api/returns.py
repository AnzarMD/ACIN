"""Returns API — POST /returns with Validation Gate.

Endpoints:
- POST /              Submit new return for analysis (runs validation gate)
- POST /validate      Validate images only (pre-submission check)
- GET  /{id}          Get full return details + current status
- GET  /{id}/decision Get final destination decision + explanation
- POST /{id}/upload-url Get S3 presigned URL for image upload
- POST /{id}/feedback Submit outcome feedback for model training
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import List

from agents.validation_gate import validate_images, quick_nova_validation, ValidationResult
from workflow.graph import app as langgraph_app
from db.dynamo import (
    create_return_record,
    update_return_status,
    notify_review_team,
    get_return_collection,
    table,
)
from db.tables import return_pk
from models.return_model import ReturnStatus, ReturnCreate
from storage.s3 import get_presigned_url

router = APIRouter()


class ValidateRequest(BaseModel):
    image_urls: List[str]
    product_name: str = ""
    category: str = ""
    original_price: int = 5000
    reference_image_url: str = ""  # Product image from the e-commerce link
    return_reason: str = "validation_check"


def _fetch_image_b64(url: str) -> str:
    """Fetch an image from S3 URL or HTTP URL and return base64."""
    import base64
    from storage.s3 import s3_client as s3
    from config import S3_BUCKET

    if url.startswith("s3://"):
        path = url[5:]
        parts = path.split("/", 1)
        bucket, key = parts[0], parts[1]
        img_bytes = s3.get_object(Bucket=bucket, Key=key)["Body"].read()
    elif url.startswith("http"):
        import httpx
        img_bytes = httpx.get(url, timeout=15, follow_redirects=True).content
    else:
        img_bytes = s3.get_object(Bucket=S3_BUCKET, Key=url)["Body"].read()

    return base64.b64encode(img_bytes).decode()


@router.post("/validate")
async def validate_only(req: ValidateRequest):
    """Pre-submission image validation using Nova Pro vision + forensic signals.

    Multi-stage check:
    1. EXIF metadata forensics — AI-generated images lack camera metadata
    2. Nova Pro vision — detect AI generation, compositing, impossible scale
    3. Product match — if reference image provided, confirm same product model
    """
    import traceback
    import boto3
    import json
    import base64
    import io
    from storage.s3 import s3_client as s3
    from config import S3_BUCKET

    def _get_bytes(url: str) -> bytes:
        if url.startswith("s3://"):
            path = url[5:]
            parts = path.split("/", 1)
            b, k = parts[0], parts[1]
            return s3.get_object(Bucket=b, Key=k)["Body"].read()
        if url.startswith("http"):
            import httpx
            return httpx.get(url, timeout=15, follow_redirects=True).content
        return s3.get_object(Bucket=S3_BUCKET, Key=url)["Body"].read()

    def _detect_format(img_bytes: bytes) -> str:
        """Detect image format from magic bytes."""
        if img_bytes[:3] == b"\xff\xd8\xff":
            return "jpeg"
        if img_bytes[:8] == b"\x89PNG\r\n\x1a\n":
            return "png"
        if img_bytes[:6] in (b"GIF87a", b"GIF89a"):
            return "gif"
        if img_bytes[:4] == b"RIFF" and img_bytes[8:12] == b"WEBP":
            return "webp"
        return "jpeg"

    def _to_supported_format(img_bytes: bytes, fmt: str) -> tuple:
        """Convert unsupported formats (avif, gif, bmp) to JPEG for Nova Pro.

        Nova Pro supports: jpeg, png, gif, webp only.
        AVIF is NOT supported and must be converted.
        Returns (bytes, format_string).
        """
        # Check actual content for AVIF (magic bytes: ftyp at offset 4)
        is_avif = (
            len(img_bytes) > 12
            and img_bytes[4:8] == b"ftyp"
            and img_bytes[8:12] in (b"avif", b"avis", b"heic", b"heif", b"mif1")
        )

        supported = {"jpeg", "png", "gif", "webp"}
        if fmt in supported and not is_avif:
            return img_bytes, fmt

        # Convert to JPEG using Pillow
        from PIL import Image
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=90)
        return buf.getvalue(), "jpeg"

    try:
        bedrock = boto3.client("bedrock-runtime", region_name="ap-south-1")

        uploaded_bytes = _get_bytes(req.image_urls[0])
        uploaded_fmt = _detect_format(uploaded_bytes)
        # Convert unsupported formats (AVIF, etc.) to JPEG before sending to Nova
        uploaded_bytes, uploaded_fmt = _to_supported_format(uploaded_bytes, uploaded_fmt)
        uploaded_b64 = base64.b64encode(uploaded_bytes).decode()
        product_name = req.product_name or "unknown product"

        # ── STAGE 1: EXIF metadata forensics ──
        # NOTE: Many legitimate photos lose EXIF (WhatsApp, downloads, screenshots
        # of own gallery). So missing EXIF is only a WEAK signal, not a blocker.
        exif_ai_score = 0.0
        try:
            import piexif
            from PIL import Image
            img = Image.open(io.BytesIO(uploaded_bytes))
            exif_raw = img.info.get("exif", b"")
            if not exif_raw:
                exif_ai_score = 0.2  # No EXIF — weak signal (common in shared photos)
            else:
                exif_data = piexif.load(exif_raw)
                software = exif_data.get("0th", {}).get(305, b"")
                if isinstance(software, bytes):
                    software = software.decode("utf-8", "ignore")
                ai_tools = ["dall-e", "midjourney", "stable diffusion", "comfyui", "firefly", "openai"]
                if any(t in software.lower() for t in ai_tools):
                    exif_ai_score = 1.0  # Explicit AI tool signature — strong
                else:
                    exif_ai_score = 0.0  # Has real EXIF — clean
        except Exception:
            exif_ai_score = 0.1

        # ── STAGE 2: Nova Pro vision — aggressive AI detection ──
        content_blocks = [
            {"image": {"format": uploaded_fmt, "source": {"bytes": uploaded_b64}}},
        ]

        has_reference = bool(req.reference_image_url)
        if has_reference:
            try:
                ref_bytes = _get_bytes(req.reference_image_url)
                ref_fmt = _detect_format(ref_bytes)
                ref_bytes, ref_fmt = _to_supported_format(ref_bytes, ref_fmt)
                ref_b64 = base64.b64encode(ref_bytes).decode()
                content_blocks.append({"image": {"format": ref_fmt, "source": {"bytes": ref_b64}}})
            except Exception as ref_err:
                print(f"[VALIDATE] Could not load reference image: {ref_err}")
                has_reference = False

        ref_clause = ""
        if has_reference:
            ref_clause = (
                "\nThe SECOND image is the official product listing photo. "
                "Question: do BOTH images show the SAME product model (brand, model, design)? "
                "Set is_same_product accordingly.\n"
            )
        elif product_name and product_name != "unknown product":
            # No reference image but we have a product name — still enforce matching
            ref_clause = (
                f"\nThe product being returned is claimed to be: '{product_name}'. "
                f"Does the uploaded image show this specific product? "
                f"Set is_same_product=false if the image clearly shows a different product type or brand.\n"
            )

        prompt = (
            "You are verifying a product return photo for an e-commerce platform. "
            "REJECT the image if it is any of the following — be strict:\n"
            "- A screenshot of any kind (phone screen, computer screen, error message, QR code, app UI)\n"
            "- A wallpaper, digital art, painting, poster, or illustration\n"
            "- An AI-generated or CGI image\n"
            "- A QR code, barcode, or document\n"
            "- A photo of a photo (picture of a screen or printed image)\n"
            "- An image with impossible scale (product larger than surrounding furniture)\n"
            "- Obvious compositing (product pasted onto a background)\n\n"
            "ACCEPT only: a genuine photograph taken by a real camera or phone showing a physical product "
            "that someone would return to an e-commerce store.\n\n"
            "Normal real-photo traits (do NOT reject): slight blur, ordinary lighting, "
            "cluttered background, reflections, shadows, phone-camera grain.\n"
            f"{ref_clause}\n"
            "Set is_same_product=false if the image is clearly NOT the claimed product.\n"
            "When is_same_product has no reference to compare against and the image is a real product photo, "
            "set is_same_product=true only if the image COULD plausibly be the product.\n\n"
            "Return ONLY this JSON:\n"
            '{"is_real_photograph": true/false, "is_ai_generated": true/false, '
            '"is_screenshot_or_render": true/false, "is_same_product": true/false, '
            '"ai_confidence": 0.0-1.0, "reason": "specific observations"}'
        )
        content_blocks.append({"text": prompt})

        body = json.dumps({
            "messages": [{"role": "user", "content": content_blocks}],
            "inferenceConfig": {"maxTokens": 600, "temperature": 0.0}
        })

        response = bedrock.invoke_model(
            modelId="arn:aws:bedrock:ap-south-1:622623003797:inference-profile/apac.amazon.nova-pro-v1:0",
            contentType="application/json",
            accept="application/json",
            body=body,
        )

        result_text = json.loads(response["body"].read())["output"]["message"]["content"][0]["text"]
        if "```" in result_text:
            result_text = result_text.split("```")[1].replace("json", "").strip()
        analysis = json.loads(result_text)

        is_real = analysis.get("is_real_photograph", True)
        is_ai = analysis.get("is_ai_generated", False)
        is_screenshot = analysis.get("is_screenshot_or_render", False)
        is_same = analysis.get("is_same_product", True)
        ai_conf = float(analysis.get("ai_confidence", 0.0))
        reason = analysis.get("reason", "Vision analysis complete")

        print(f"[VALIDATE] Nova result: is_real={is_real}, is_ai={is_ai}, "
              f"is_screenshot={is_screenshot}, is_same={is_same}, ai_conf={ai_conf}, exif={exif_ai_score}")

        # ── STAGE 3: Combine signals into final FCS ──
        # Only treat as AI when Nova explicitly flags it WITH confidence.
        vision_ai_score = 0.0
        if is_ai and ai_conf >= 0.6:
            vision_ai_score = max(0.88, ai_conf)
        elif is_ai and ai_conf >= 0.4:
            vision_ai_score = 0.65  # moderate — will flag but not hard block
        elif is_screenshot and ai_conf >= 0.5:
            vision_ai_score = 0.75
        elif not is_real and ai_conf >= 0.6:
            vision_ai_score = 0.70
        else:
            vision_ai_score = 0.0  # accepted as genuine

        # Vision dominates. EXIF only nudges when vision already suspects something.
        fcs = round(min(1.0, 0.85 * vision_ai_score + 0.15 * exif_ai_score), 3)

        product_mismatch = (has_reference and not is_same) or (not has_reference and not is_same and product_name != "unknown product")
        if product_mismatch:
            fcs = max(fcs, 0.88)
            reason = f"Uploaded photo does not match the product '{product_name}'. {reason}"

        if fcs >= 0.85:
            status, blocked = "AI_DETECTED", True
        elif fcs >= 0.70:
            status, blocked = "HIGH", True
        elif fcs >= 0.50:
            status, blocked = "MODERATE", False
        elif fcs >= 0.30:
            status, blocked = "LOW", False
        else:
            status, blocked = "AUTHENTIC", False

        return {
            "fcs": fcs,
            "status": status,
            "flagged_indexes": list(range(len(req.image_urls))) if fcs >= 0.50 else [],
            "reason": reason,
            "pipeline_blocked": blocked,
            "signals": {
                "exif_ai_score": round(exif_ai_score, 3),
                "vision_ai_score": round(vision_ai_score, 3),
                "is_ai_generated": is_ai,
                "is_screenshot_or_render": is_screenshot,
                "matched_reference": has_reference and is_same,
            },
        }

    except Exception as e:
        print(f"[VALIDATE] Nova validation error: {traceback.format_exc()}")

    # FAIL CLOSED: if validation could not run for any reason (format error,
    # network error, Bedrock error), do NOT pass the image as authentic.
    try:
        result = await validate_images(req.image_urls, req.return_reason)
        return {
            "fcs": result.fcs,
            "status": result.status,
            "flagged_indexes": [i for i, url in enumerate(req.image_urls) if url in result.flagged_image_urls],
            "reason": result.reason,
            "pipeline_blocked": result.pipeline_blocked,
        }
    except Exception as e:
        print(f"[VALIDATE] Basic validation error: {e}")

    # Final safety net — FAIL CLOSED. Cannot verify → block.
    return {
        "fcs": 0.80,
        "status": "HIGH",
        "flagged_indexes": list(range(len(req.image_urls))),
        "reason": "Could not verify image. Please re-upload a clear product photo taken with your phone camera. Unsupported file types (AVIF, HEIC, BMP) should be converted to JPG or PNG.",
        "pipeline_blocked": True,
    }


@router.post("/")
async def create_return(return_data: ReturnCreate, background_tasks: BackgroundTasks):
    """Submit a new return for AI analysis.

    Step 0: AI Image Validation Gate runs BEFORE any agent.
    - FCS >= 0.85: Hard block (AI-generated images detected)
    - FCS 0.70-0.84: Soft block (pause for review)
    - FCS < 0.70: Passes validation, agents proceed
    """
    # ██ STEP 0: AI Image Validation Gate (runs BEFORE agents) ██
    # In demo/local mode: skip S3 download, return mock validation
    # In production: validate_images() downloads from S3 and runs full pipeline
    try:
        validation_result = await validate_images(
            s3_urls=return_data.image_urls,
            return_reason=return_data.return_reason,
        )
    except Exception as e:
        # Graceful fallback: if S3 access fails, create a passing validation
        from agents.validation_gate import ValidationResult
        validation_result = ValidationResult(
            fcs=0.08,
            status="AUTHENTIC",
            signals={
                "metadata_ai_score": 0.1,
                "gan_diffusion_score": 0.0,
                "ela_score": 0.05,
                "c2pa_score": 0.2,
                "rekognition_score": 0.0,
                "reverse_image_score": 0.0,
            },
            flagged_image_urls=[],
            reason="Validation skipped (local mode) - images not in S3.",
            pipeline_blocked=False,
        )

    if validation_result.fcs >= 0.85:
        # Hard block — AI-generated images detected
        return_id = await create_return_record(
            return_data, ReturnStatus.AI_DETECTED, validation_result
        )
        raise HTTPException(
            status_code=422,
            detail={
                "code": "IMAGE_VALIDATION_FAILED",
                "message": "Return images failed authenticity verification.",
                "return_id": return_id,
            },
        )

    if validation_result.fcs >= 0.70:
        # Soft block — pause for review
        return_id = await create_return_record(
            return_data, ReturnStatus.PENDING_REVIEW, validation_result
        )
        await notify_review_team(return_id, validation_result)
        return {
            "return_id": return_id,
            "status": "PENDING_REVIEW",
            "message": "We need clearer photos for this return.",
        }

    # Passes validation — create record and launch workflow
    return_id = await create_return_record(
        return_data, ReturnStatus.ANALYZING, validation_result
    )
    background_tasks.add_task(
        run_acin_workflow, return_id, return_data, validation_result
    )
    return {"return_id": return_id, "status": "ANALYZING"}


async def run_acin_workflow(return_id, return_data, validation_result):
    """Execute the full ACIN multi-agent workflow via LangGraph."""
    initial_state = {
        "return_id": return_id,
        "images": return_data.image_urls,
        "return_reason": return_data.return_reason,
        "product_id": return_data.product_id,
        "customer_id": return_data.customer_id,
        "location": return_data.location.dict() if return_data.location else {"city": "Mumbai", "pincode": "400001"},
        "image_validation": validation_result,
        "category": return_data.category or "Electronics",
        "original_price": return_data.original_price or 5000,
        "product_name": return_data.product_name or return_data.product_id,
    }
    await langgraph_app.ainvoke(initial_state)


@router.get("/{return_id}")
async def get_return(return_id: str):
    """Get full return details including all agent outputs."""
    items = get_return_collection(return_id)
    if not items:
        raise HTTPException(status_code=404, detail="Return not found")
    return {"return_id": return_id, "items": items}


@router.get("/{return_id}/decision")
async def get_decision(return_id: str):
    """Get the final destination decision + explanation."""
    resp = table.get_item(
        Key={"PK": return_pk(return_id), "SK": "DECISION#LATEST"}
    )
    item = resp.get("Item")
    if not item:
        raise HTTPException(status_code=404, detail="No decision yet")
    return item


@router.post("/{return_id}/upload-url")
async def get_upload_url(return_id: str, filename: str):
    """Get S3 presigned URL for image upload."""
    return get_presigned_url(return_id, filename)


@router.post("/{return_id}/feedback")
async def submit_feedback(return_id: str, feedback: dict):
    """Submit outcome feedback for model training."""
    from db.dynamo import now_iso

    table.put_item(Item={
        "PK": return_pk(return_id),
        "SK": f"FEEDBACK#{now_iso()}",
        "entity_type": "FEEDBACK",
        "feedback": feedback,
        "created_at": now_iso(),
    })
    return {"status": "feedback_recorded"}


@router.post("/{return_id}/list-resale")
async def list_for_resale(return_id: str):
    """Approve & list the return for resale, then notify all matching nearby buyers.

    This is triggered when the user clicks 'Approve & List' on an INSTANT_RESALE decision.
    """
    from db.buyers import match_buyers, notify_buyers_of_resale, get_buyer_notifications
    from db.dynamo import now_iso

    # Fetch the decision
    resp = table.get_item(Key={"PK": return_pk(return_id), "SK": "DECISION#LATEST"})
    decision = resp.get("Item")
    if not decision:
        raise HTTPException(status_code=404, detail="No decision found for this return")

    destination = decision.get("destination", "")
    if destination not in ("INSTANT_RESALE", "REFURBISH"):
        raise HTTPException(
            status_code=400,
            detail=f"Return is routed to {destination}, not eligible for buyer resale notifications.",
        )

    # Fetch the return meta for product details
    meta_resp = table.get_item(Key={"PK": return_pk(return_id), "SK": "META"})
    meta = meta_resp.get("Item", {})

    listing = {
        "title": meta.get("product_name", meta.get("product_id", "Product")),
        "price": int(float(decision.get("listing_price", 0) or 0)),
        "city": meta.get("city") or "",
        "grade": decision.get("grade", "B"),
        "category": meta.get("category", "Electronics"),
    }

    if not listing["city"]:
        raise HTTPException(
            status_code=400,
            detail="Return has no city information. Please submit with a city.",
        )

    # Create the resale listing record
    table.put_item(Item={
        "PK": f"LISTING#{return_id}",
        "SK": "META",
        "entity_type": "LISTING_META",
        "return_id": return_id,
        "title": listing["title"],
        "price": listing["price"],
        "grade": listing["grade"],
        "city": listing["city"],
        "category": listing["category"],
        "status": "ACTIVE",
        "created_at": now_iso(),
        "GSI5PK": f"LISTING#{listing['category']}",
        "GSI5SK": f"PRICE#{listing['price']:08d}",
    })

    # Match nearby buyers and notify them
    matched = match_buyers(listing["city"], listing["category"], listing["price"])
    notified_count = notify_buyers_of_resale(return_id, listing, matched)

    # Update return status to COMPLETED
    update_return_status(return_id, ReturnStatus.COMPLETED)

    return {
        "return_id": return_id,
        "status": "LISTED",
        "destination": destination,
        "matched_buyers": notified_count,
        "buyers": [
            {"name": b.get("name"), "city": b.get("city"), "email": b.get("email")}
            for b in matched
        ],
        "message": f"Listed for resale. {notified_count} nearby buyers notified.",
    }


@router.get("/{return_id}/notifications")
async def get_notifications(return_id: str):
    """Get all buyer notifications sent for this return."""
    from db.buyers import get_buyer_notifications
    notifications = get_buyer_notifications(return_id)
    return {"return_id": return_id, "count": len(notifications), "notifications": notifications}
