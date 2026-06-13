"""FEATURES#LATEST read/write helpers for the feature store."""

from .dynamo import update_features_latest, get_features_latest


def write_features(return_id: str, features: dict):
    """Write aggregated feature scores to FEATURES#LATEST."""
    update_features_latest(return_id, features)


def read_features(return_id: str) -> dict:
    """Read the latest feature snapshot for a return."""
    result = get_features_latest(return_id)
    return result if result else {}
