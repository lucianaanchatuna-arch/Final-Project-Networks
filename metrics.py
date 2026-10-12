import csv
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
CASE_ID = "demo_case_001"
STUDENT_ID = "luciana"

RUN_DIR = PROJECT_ROOT / "runs" / "student" / CASE_ID
RESULTS_DIR = PROJECT_ROOT / "results"
RESULTS_CSV = RESULTS_DIR / "results.csv"

LLM_RESPONSE_PATH = RUN_DIR / "llm_response.json"
EVAL_PATH = RUN_DIR / "eval.json"


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    llm = json.loads(LLM_RESPONSE_PATH.read_text(encoding="utf-8"))
    evaluation = json.loads(EVAL_PATH.read_text(encoding="utf-8"))

    claimed_success = bool(llm.get("claimed_success", False))
    patch_applied = bool(evaluation.get("patch_applied", False))
    security_test_pass = bool(evaluation.get("security_test_pass", False))
    functional_test_pass = bool(evaluation.get("functional_test_pass", False))

    verified_repair = patch_applied and security_test_pass and functional_test_pass
    false_assurance = claimed_success and not verified_repair

    row = {
        "student_id": STUDENT_ID,
        "case_id": CASE_ID,
        "model": llm.get("model", ""),
        "timestamp": llm.get("timestamp", ""),
        "llm_claimed_success": claimed_success,
        "llm_confidence": llm.get("confidence", ""),
        "patch_applied": patch_applied,
        "security_test_pass": security_test_pass,
        "functional_test_pass": functional_test_pass,
        "verified_repair": verified_repair,
        "false_assurance": false_assurance,
        "latency_ms": llm.get("latency_ms", ""),
        "input_tokens": llm.get("input_tokens", ""),
        "output_tokens": llm.get("output_tokens", ""),
        "semgrep_findings_before": "",
        "semgrep_findings_after": "",
        "api_success": llm.get("api_success", False),
        "error_type": llm.get("error_type", ""),
    }

    fieldnames = list(row.keys())

    with RESULTS_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(row)

    total_cases = 1
    verified_count = 1 if verified_repair else 0
    claimed_count = 1 if claimed_success else 0
    false_assurance_count = 1 if false_assurance else 0

    vrr = verified_count / total_cases

    print(f"Saved results to: {RESULTS_CSV}")
    print(f"VRR: {vrr * 100:.1f}%")

    if claimed_count == 0:
        print("FAR = undefined (no positive repair claims)")
    else:
        far = false_assurance_count / claimed_count
        print(f"FAR: {far * 100:.1f}%")


if __name__ == "__main__":
    main()
