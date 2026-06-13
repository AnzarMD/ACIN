"""ACIN Configuration — loads from environment variables."""

import os
from dotenv import load_dotenv

load_dotenv()

# AWS
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
S3_BUCKET = os.getenv("S3_BUCKET", "acin-uploads-622623003797")
DYNAMODB_TABLE = os.getenv("DYNAMODB_TABLE", "ACIN_Main")

# Bedrock
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "arn:aws:bedrock:ap-south-1:622623003797:inference-profile/apac.amazon.nova-pro-v1:0")

# Hive API
HIVE_API_KEY = os.getenv("HIVE_API_KEY", "")

# Cognito
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID", "")
COGNITO_CLIENT_ID = os.getenv("COGNITO_CLIENT_ID", "")

# CORS
ALLOWED_ORIGINS = [
    "https://acin.vercel.app",
    "http://localhost:3000",
]
