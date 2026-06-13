"""S3 presigned URL helper for image uploads."""

import boto3
import botocore
from config import AWS_REGION, S3_BUCKET

# Virtual-hosted addressing with explicit regional endpoint generates
# https://<bucket>.s3.<region>.amazonaws.com/<key> natively — no rewrite needed,
# so the SigV4 signature matches the host the browser actually calls.
s3_client = boto3.client(
    "s3",
    region_name=AWS_REGION,
    endpoint_url=f"https://s3.{AWS_REGION}.amazonaws.com",
    config=botocore.config.Config(
        signature_version="s3v4",
        s3={"addressing_style": "virtual"},
    ),
)


def get_presigned_url(return_id: str, filename: str, expiration: int = 3600) -> dict:
    """Generate a presigned URL for uploading an image to S3.

    ContentType is intentionally NOT pinned so the browser can upload any
    image type (jpeg/png/webp) without a signature mismatch.
    """
    key = f"returns/{return_id}/{filename}"

    url = s3_client.generate_presigned_url(
        "put_object",
        Params={"Bucket": S3_BUCKET, "Key": key},
        ExpiresIn=expiration,
    )

    return {
        "upload_url": url,
        "s3_url": f"s3://{S3_BUCKET}/{key}",
        "expires_in": expiration,
    }


def get_download_url(s3_url: str, expiration: int = 3600) -> str:
    """Generate a presigned download URL for an S3 object."""
    if s3_url.startswith("s3://"):
        path = s3_url[5:]
        parts = path.split("/", 1)
        bucket, key = parts[0], parts[1]
    else:
        bucket, key = S3_BUCKET, s3_url

    return s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=expiration,
    )
