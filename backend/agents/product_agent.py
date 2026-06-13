"""Agent 1 — Product Intelligence Agent.

Analyses physical condition of returned item from images, video, and return reason.
Detects defects and flags potential return fraud.
Also detects non-product images (wallpapers, screenshots, AI art).
"""

import os
import json
import uuid
import base64

from langchain_aws import ChatBedrock
from langchain_core.messages import SystemMessage, HumanMessage

from db.dynamo import put_agent_output, put_agent_run
from db.tables import output_sk, agent_run_sk
from storage.s3 import s3_client, S3_BUCKET

PRODUCT_VISION_PROMPT = """You are an expert product condition assessor for an e-commerce returns platform. Analyse the provided product images and return ONLY valid JSON.

CRITICAL RULES:
- If the image is NOT a physical product (e.g., it's a wallpaper, screenshot, AI art, landscape, meme, or unrelated image), set condition_score to 0, grade to "D", and fraud_probability to 0.95 with fraud_signal "NON_PRODUCT_IMAGE".
- Only assess condition if the image shows an actual physical product (electronics, clothing, shoes, accessories, appliances, etc.)

Assess:
1. Overall condition (0-100 scale) — 0 if not a product image
2. Detected defects with location and severity
3. Packaging assessment (intact/damaged/missing)
4. Usage level estimate (new/light/moderate/heavy)
5. Missing components (if any)
6. Safety concerns (if any)
7. Return fraud signals (mismatch with customer claim, non-product image)

Grading:
Grade A: 85-100 | Grade B: 70-84 | Grade C: 50-69 | Grade D: <50

Return ONLY this JSON:
{
    "condition_score": <int>,
    "grade": "<A|B|C|D>",
    "defects": [{"type": "<str>", "location": "<str>", "severity": "<low|medium|high|critical>"}],
    "packaging_status": "<intact|damaged|missing|not_applicable>",
    "usage_level": "<new|light|moderate|heavy|not_applicable>",
    "missing_parts": ["<str>"],
    "safety_risk": <bool>,
    "fraud_probability": <float 0-1>,
    "fraud_signals": ["<str>"],
    "repair_recommendation": "<str>",
    "estimated_repair_cost_inr": <int>,
    "is_product_image": <bool>
}"""


def get_image_bytes_from_s3(s3_url: str) -> bytes:
    """Download image from S3 URL."""
    if s3_url.startswith("s3://"):
        path = s3_url[5:]
        parts = path.split("/", 1)
        bucket, key = parts[0], parts[1]
    else:
        bucket, key = S3_BUCKET, s3_url

    response = s3_client.get_object(Bucket=bucket, Key=key)
    return response["Body"].read()


class ProductIntelligenceAgent:
    """Analyse physical condition and detect fraud signals."""

    def __init__(self):
        self.llm = ChatBedrock(
            model_id="arn:aws:bedrock:ap-south-1:622623003797:inference-profile/apac.amazon.nova-pro-v1:0",
            provider="amazon",
            region_name=os.getenv("AWS_REGION", "ap-south-1"),
            model_kwargs={"max_tokens": 2048, "temperature": 0.1},
        )

    async def analyse(self, state: dict) -> dict:
        run_id = str(uuid.uuid4())[:8]
        put_agent_run(state["return_id"], "PRODUCT", run_id, "RUNNING")

        validation = state.get("image_validation")

        # Build text context
        extra_text = f"Return reason: {state['return_reason']}"
        if validation:
            extra_text += (
                f"\nImage validation FCS: {validation.fcs:.2f}"
                f"\nValidation signals: {json.dumps(validation.signals)}"
                "\nFactor validation findings into your fraud_probability score."
            )

        # Build image content — fetch from S3 and encode as base64
        image_content = []
        for url in state["images"]:
            try:
                img_bytes = get_image_bytes_from_s3(url)
                img_b64 = base64.b64encode(img_bytes).decode()
                # Detect MIME type from magic bytes
                if img_bytes[:8] == b"\x89PNG\r\n\x1a\n":
                    mime = "image/png"
                elif img_bytes[:4] == b"RIFF" and img_bytes[8:12] == b"WEBP":
                    mime = "image/webp"
                elif img_bytes[:6] in (b"GIF87a", b"GIF89a"):
                    mime = "image/gif"
                else:
                    mime = "image/jpeg"
                image_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime};base64,{img_b64}"},
                })
            except Exception as e:
                extra_text += f"\n[Could not load image: {url} - {str(e)[:50]}]"

        image_content.append({"type": "text", "text": extra_text})

        response = await self.llm.ainvoke([
            SystemMessage(content=PRODUCT_VISION_PROMPT),
            HumanMessage(content=image_content),
        ])

        # Parse JSON response
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0]
        result = json.loads(content)

        # Boost fraud_probability if validation gate flagged moderate
        if validation and validation.fcs >= 0.50:
            result["fraud_probability"] = max(
                result.get("fraud_probability", 0),
                validation.fcs * 0.85,
            )
            result.setdefault("fraud_signals", []).append(
                f"Image validation FCS={validation.fcs:.2f}: {validation.reason}"
            )

        put_agent_output(
            state["return_id"],
            "PRODUCT",
            run_id,
            result,
            "nova-pro-v1",
            "v1",
            "1.0",
            result.get("condition_score", 0) / 100,
        )

        return {"product_analysis": result}


async def product_intelligence_agent(state: dict) -> dict:
    """LangGraph node entry point."""
    try:
        return await ProductIntelligenceAgent().analyse(state)
    except Exception as e:
        # Fallback when Bedrock/S3 unavailable (local demo mode)
        return {"product_analysis": {
            "condition_score": 82,
            "grade": "B",
            "defects": [],
            "packaging_status": "intact",
            "usage_level": "light",
            "missing_parts": [],
            "safety_risk": False,
            "fraud_probability": 0.05,
            "fraud_signals": [],
            "repair_recommendation": "No repair needed",
            "estimated_repair_cost_inr": 0,
            "is_product_image": True,
        }}
