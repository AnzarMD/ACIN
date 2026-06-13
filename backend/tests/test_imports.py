"""Test that all modules import successfully."""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_config_imports():
    from config import AWS_REGION, S3_BUCKET, DYNAMODB_TABLE
    assert AWS_REGION == "ap-south-1"
    assert "acin" in S3_BUCKET
    assert DYNAMODB_TABLE == "ACIN_Main"


def test_models_import():
    from models.return_model import ReturnStatus, ReturnCreate
    assert ReturnStatus.ANALYZING == "ANALYZING"
    assert ReturnStatus.DECIDED == "DECIDED"


def test_tables_import():
    from db.tables import return_pk, output_sk, features_latest_sk
    assert return_pk("RET-001") == "RETURN#RET-001"
    assert output_sk("PRODUCT", "abc") == "OUTPUT#PRODUCT#abc"
    assert features_latest_sk() == "FEATURES#LATEST"


def test_main_app_import():
    from main import app
    assert app.title == "ACIN API"
