"""ACIN_Main single-table key builders.

All entities use RETURN#<return_id> as PK (never analysis_id).
One Query(PK=RETURN#<id>) retrieves the entire case.
"""

TABLE_NAME = "ACIN_Main"


def return_pk(return_id: str) -> str:
    return f"RETURN#{return_id}"


def output_sk(agent: str, run_id: str) -> str:
    return f"OUTPUT#{agent}#{run_id}"


def agent_run_sk(agent: str, run_id: str) -> str:
    return f"AGENT_RUN#{agent}#{run_id}"


def validation_sk(ts: str) -> str:
    return f"VALIDATION#{ts}"


def decision_sk(n: int) -> str:
    return f"DECISION#{n}"


def features_latest_sk() -> str:
    return "FEATURES#LATEST"


def carbon_txn_sk(ts: str, txn_id: str) -> str:
    return f"CARBON_TXN#{ts}#{txn_id}"


def media_sk(media_id: str) -> str:
    return f"MEDIA#{media_id}"


def event_sk(ts: str, event_id: str) -> str:
    return f"EVENT#{ts}#{event_id}"


def dlq_sk(ts: str, dlq_id: str) -> str:
    return f"DLQ#{ts}#{dlq_id}"


def trust_badge_sk(badge_id: str) -> str:
    return f"TRUST_BADGE#{badge_id}"


def outbox_sk(version: str) -> str:
    return f"OUTBOX#{version}"


def idempotency_sk(key: str) -> str:
    return f"IDEMPOTENCY#{key}"
