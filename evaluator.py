"""Run the official Vul4Py evaluator and normalize its actual output."""
import argparse
import json
import subprocess
import sys
from pathlib import Path

from vul4py_adapter import eligible_cases, normalize_eval

ROOT = Path(__file__).resolve().parent
VUL4PY = ROOT / "vul4py"

def evaluate(case_id):
    ok_cases = {case.case_id for case in eligible_cases(VUL4PY)}
    if case_id not in ok_cases:
        raise SystemExit(f"Refusing to evaluate {case_id}: it is not marked OK by Vul4Py scan")
    run_dir = VUL4PY / "runs" / "student" / case_id
    if not (run_dir / "llm_response.json").exists() or not (run_dir / "patch.diff").exists():
        raise SystemExit("Frozen llm_response.json and patch.diff are required before evaluation")
    frozen = json.loads((run_dir / "llm_response.json").read_text(encoding="utf-8"))
    if not frozen.get("api_success") or not frozen.get("patch"):
        raise SystemExit("Frozen response has no successful API repair patch; refusing to evaluate")
    command = [sys.executable, "scripts/evaluate.py", "--agent", "student", "--vuln-id", case_id]
    completed = subprocess.run(command, cwd=VUL4PY, text=True, capture_output=True, timeout=3600)
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "adapter.log").write_text(completed.stdout + completed.stderr, encoding="utf-8")
    eval_path = run_dir / "eval.json"
    if eval_path.exists():
        # Preserve the official eval.json; save our normalized mapping separately.
        normalized = normalize_eval(eval_path)
        (run_dir / "normalized_eval.json").write_text(json.dumps(normalized, indent=2), encoding="utf-8")
    if completed.returncode:
        raise SystemExit(f"Vul4Py evaluator exited {completed.returncode}; inspect {run_dir / 'adapter.log'}")
    print((run_dir / "eval.json").read_text(encoding="utf-8"))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-id", required=True)
    args = parser.parse_args()
    evaluate(args.case_id)

if __name__ == "__main__":
    main()
