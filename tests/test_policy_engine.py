
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from policy_engine import evaluate_policy


POLICY = {
    "policy_id": "POL-ENC-01",
    "name": "PII Data Encryption at Rest",
    "scope": {
        "classification_tag": {
            "key": "data-classification",
            "value": "PII",
        }
    },
    "evaluation": {
        "encryption_observation_field": "encryption_observation.status",
        "pass_when": ["EXPLICIT_HEADER_PRESENT"],
        "fail_when": ["EXPLICIT_ENCRYPTION_DISABLED"],
        "error_when": [
            "NOT_DETERMINED",
            "EVIDENCE_MISSING",
            "INVALID_EVIDENCE",
        ],
    },
}


def make_evidence(classification, encryption_status):
    return {
        "evidence_id": "TEST-001",
        "resource_id": "customer-raw/test.csv",
        "tags": {
            "data-classification": classification
        },
        "encryption_observation": {
            "status": encryption_status
        },
    }


def test_encryption_enabled():
    evidence = make_evidence("PII", "EXPLICIT_HEADER_PRESENT")
    assert evaluate_policy(POLICY, evidence)["status"] == "PASS"


def test_encryption_disabled():
    evidence = make_evidence("PII", "EXPLICIT_ENCRYPTION_DISABLED")
    assert evaluate_policy(POLICY, evidence)["status"] == "FAIL"


def test_encryption_unknown():
    evidence = make_evidence("PII", "NOT_DETERMINED")
    assert evaluate_policy(POLICY, evidence)["status"] == "ERROR"


def test_not_applicable():
    evidence = make_evidence("PUBLIC", "NOT_DETERMINED")
    assert evaluate_policy(POLICY, evidence)["status"] == "NOT_APPLICABLE"
