"""Products API — demand, pricing, and product link extraction.

Endpoints:
- GET  /products/{asin}/demand          Get demand forecast
- GET  /products/{asin}/price-suggestion Get dynamic pricing
- POST /products/extract                Extract product info from URL
"""

import os
import json
import re
from fastapi import APIRouter
import httpx
import boto3

router = APIRouter()

bedrock = boto3.client("bedrock-runtime", region_name=os.getenv("AWS_REGION", "ap-south-1"))
MODEL_ID = "arn:aws:bedrock:ap-south-1:622623003797:inference-profile/apac.amazon.nova-pro-v1:0"


@router.post("/extract")
async def extract_product_from_url(data: dict):
    """Extract product details from an e-commerce URL (Amazon, Flipkart, etc.)."""
    url = data.get("url", "")
    if not url:
        return {"error": "No URL provided"}

    # Fetch the page HTML
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "en-IN,en;q=0.9",
            }
            response = await client.get(url, headers=headers)
            html = response.text
    except Exception as e:
        return {"error": f"Could not fetch URL: {str(e)[:100]}"}

    # ── Step 1: Extract image URL directly from HTML using regex patterns ──
    image_url = ""

    # Try Open Graph image first (most reliable across all sites)
    og_match = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.IGNORECASE)
    if not og_match:
        og_match = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', html, re.IGNORECASE)
    if og_match:
        image_url = og_match.group(1)

    # Amazon: look for main product image
    if not image_url and "amazon" in url:
        amz = re.search(r'"hiRes":"(https://m\.media-amazon\.com/images/I/[^"]+)"', html)
        if not amz:
            amz = re.search(r'"large":"(https://m\.media-amazon\.com/images/I/[^"]+)"', html)
        if amz:
            image_url = amz.group(1)

    # Flipkart: look for main image
    if not image_url and "flipkart" in url:
        flip = re.search(r'https://rukminim[12]\.flixcart\.com/image/[^"\'\\s]+\.(?:jpg|jpeg|png|webp)', html)
        if flip:
            image_url = flip.group(0)

    # Nykaa: look for product image CDN
    if not image_url and "nykaa" in url:
        nykaa = re.search(r'https://adn-static\d*\.nykaa\.com/[^"\'\\s]+\.(?:jpg|jpeg|png|webp)', html)
        if nykaa:
            image_url = nykaa.group(0)

    # Generic: try JSON-LD structured data
    if not image_url:
        jsonld = re.search(r'"image"\s*:\s*"(https?://[^"]+\.(?:jpg|jpeg|png|webp))"', html, re.IGNORECASE)
        if jsonld:
            image_url = jsonld.group(1)

    # Generic: first large product image
    if not image_url:
        imgs = re.findall(r'https?://[^\s"\'<>]+\.(?:jpg|jpeg|png|webp)', html)
        # Filter out icons, logos, tracking pixels
        candidates = [i for i in imgs if not any(x in i.lower() for x in ["logo", "icon", "1x1", "pixel", "banner", "sprite", "flag"])]
        if candidates:
            image_url = candidates[0]

    # ── Step 2: Use Nova Pro to extract text info from HTML ──
    info = {
        "product_name": "",
        "brand": "",
        "category": "Other",
        "original_price": 5000,
        "product_id": "",
        "description": "",
        "image_url": image_url,
        "source_url": url,
        "extracted": False,
    }

    try:
        prompt = f"""Extract product information from this e-commerce page HTML. Return ONLY valid JSON.

URL: {url}

HTML (first 8000 chars):
{html[:8000]}

Return ONLY this JSON:
{{
    "product_name": "<full product name>",
    "brand": "<brand name>",
    "category": "<one of: Electronics, Footwear, Clothing, Computers, Home & Kitchen, Beauty, Sports, Toys, Books, Luggage, Other>",
    "original_price": <price in INR as integer, no commas>,
    "product_id": "<ASIN or product ID if found, else empty string>",
    "description": "<one line description>"
}}"""

        body = json.dumps({
            "messages": [{"role": "user", "content": [{"text": prompt}]}],
            "inferenceConfig": {"maxTokens": 400, "temperature": 0.1},
        })

        resp = bedrock.invoke_model(
            modelId=MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=body,
        )

        result_text = json.loads(resp["body"].read())["output"]["message"]["content"][0]["text"]
        if "```" in result_text:
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]
            result_text = result_text.strip()

        extracted = json.loads(result_text)
        info.update({
            "product_name": extracted.get("product_name", ""),
            "brand": extracted.get("brand", ""),
            "category": extracted.get("category", "Other"),
            "original_price": extracted.get("original_price", 5000),
            "product_id": extracted.get("product_id", ""),
            "description": extracted.get("description", ""),
            "extracted": True,
        })

    except Exception as e:
        # Fallback to basic regex extraction
        info.update(extract_basic(url, html))

    return info


def extract_basic(url: str, html: str) -> dict:
    """Basic regex fallback for when LLM extraction fails."""
    info = {
        "product_name": "",
        "brand": "",
        "category": "Other",
        "original_price": 0,
        "product_id": "",
        "description": "",
        "image_url": "",
        "source_url": url,
        "extracted": False,
    }

    # Extract title
    title_match = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE)
    if title_match:
        info["product_name"] = title_match.group(1).split(" - ")[0].split(" | ")[0].strip()

    # Extract price (Indian format)
    price_match = re.search(r'[₹][\s]*([\d,]+)', html)
    if price_match:
        info["original_price"] = int(price_match.group(1).replace(",", ""))

    # Extract ASIN from Amazon URL
    asin_match = re.search(r'/dp/([A-Z0-9]{10})', url)
    if asin_match:
        info["product_id"] = asin_match.group(1)

    # Extract Flipkart product ID
    flip_match = re.search(r'pid=([^&]+)', url)
    if flip_match:
        info["product_id"] = flip_match.group(1)

    return info


@router.get("/{asin}/demand")
async def get_demand(asin: str, city: str = "Mumbai", pincode: str = "400001"):
    """Get demand forecast for a product in a given location."""
    return {
        "asin": asin,
        "city": city,
        "demand_score": 75,
        "buyer_count": 15,
        "expected_sale_days": 4,
        "seasonality_factor": 1.1,
        "demand_trend": "stable",
    }


@router.get("/{asin}/price-suggestion")
async def get_price_suggestion(
    asin: str,
    condition_score: int = 80,
    original_price: int = 5000,
):
    """Get dynamic pricing suggestion for a product."""
    condition_factor = condition_score / 100
    fast_sale = int(original_price * condition_factor * 0.72)
    balanced = int(original_price * condition_factor * 0.78)
    max_profit = int(original_price * condition_factor * 0.85)

    return {
        "asin": asin,
        "original_price": original_price,
        "condition_score": condition_score,
        "fast_sale_price": fast_sale,
        "balanced_price": balanced,
        "max_profit_price": max_profit,
        "recommended_strategy": "balanced",
    }
