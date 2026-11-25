
import json
import sys
from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parent.parent

POLICY_PATH = PROJECT_ROOT / "policies" / "POL-ENC-01.yaml"
EVIDENCE_PATH = PROJECT_ROOT / "results" / "latest_evidence.json"
RESULT_PATH = PROJECT_ROOT / "results" / "latest_policy_result.json"


def load_json(path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_policy(path):
    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def get_nested_value(data, field_path):
    value = data

    for key in field_path.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(key)

    return value


def evaluate_policy(policy, evidence):
    scope = policy["scope"]
    evaluation = policy["evaluation"]

    tags = evidence.get("tags", {})
    classification = scope["classification_tag"]

    # 1. Kiểm tra phạm vi áp dụng
    if tags.get(classification["key"]) != classification["value"]:
        status = "NOT_APPLICABLE"
        reason = "Object is outside the policy scope."

    else:
        # 2. Lấy trạng thái encryption
        field = evaluation["encryption_observation_field"]
        observation = get_nested_value(evidence, field)

        if observation in evaluation["pass_when"]:
            status = "PASS"
            reason = "Explicit encryption evidence was found."

        elif observation in evaluation["fail_when"]:
            status = "FAIL"
            reason = "Explicit evidence confirms encryption is disabled."

        else:
            status = "ERROR"
            reason = "Encryption status cannot be determined."

    return {
        "policy_id": policy["policy_id"],
        "policy_name": policy["name"],
        "resource_id": evidence.get("resource_id"),
        "evidence_id": evidence.get("evidence_id"),
        "status": status,
        "reason": reason,
    }


def main():
    try:
        policy = load_policy(POLICY_PATH)
        evidence = load_json(EVIDENCE_PATH)

        result = evaluate_policy(policy, evidence)

        RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)

        with RESULT_PATH.open("w", encoding="utf-8") as file:
            json.dump(result, file, indent=2, ensure_ascii=False)

        print("Policy evaluation completed")
        print("Policy:", result["policy_id"])
        print("Resource:", result["resource_id"])
        print("Status:", result["status"])
        print("Reason:", result["reason"])
        print("Result file:", RESULT_PATH)

    except FileNotFoundError as error:
        print("ERROR: Required file not found:", error)
        sys.exit(1)

    except (KeyError, TypeError, ValueError, yaml.YAMLError) as error:
        print("ERROR: Invalid policy or evidence:", error)
        sys.exit(1)


if __name__ == "__main__":
    main()
