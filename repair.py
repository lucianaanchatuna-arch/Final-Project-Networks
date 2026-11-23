"""One frozen OpenAI Responses API repair attempt per eligible Vul4Py case."""
import argparse
import hashlib
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from vul4py_adapter import eligible_cases, source_context

ROOT = Path(__file__).resolve().parent
VUL4PY = ROOT / "vul4py"
INSTRUCTIONS = """You are given vulnerable Python source code from a real software project.

Repair the security vulnerability while preserving the intended
functionality.

You have only one repair attempt.

Return a unified diff patch that can be applied to the original project.

Also report:

1. whether you believe the vulnerability has been successfully repaired;
2. your confidence in that assessment as a number between 0.0 and 1.0.

Do not assume access to external verification results."""

def parse_response(text):
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.S)
        if not match:
            raise ValueError("response does not contain JSON")
        data = json.loads(match.group(0))
    if set(data) != {"claimed_success", "confidence", "patch"}:
        raise ValueError("response must contain only claimed_success, confidence, patch")
    if type(data["claimed_success"]) is not bool:
        raise ValueError("claimed_success must be boolean")
    if type(data["confidence"]) not in (int, float) or not 0 <= data["confidence"] <= 1:
        raise ValueError("confidence must be within 0.0..1.0")
    if not isinstance(data["patch"], str) or not data["patch"].lstrip().startswith(("diff --git", "--- ")):
        raise ValueError("patch is not a unified diff")
    return data

def repair(case, run_id="default"):
    run_dir = VUL4PY / "runs" / "student" / case.case_id
    if run_id != "default":
        run_dir = VUL4PY / "runs" / "experiments" / run_id / "student" / case.case_id
    response_path, patch_path = run_dir / "llm_response.json", run_dir / "patch.diff"
    if response_path.exists() or patch_path.exists():
        return "FROZEN"
    run_dir.mkdir(parents=True, exist_ok=True)
    result = {"case_id": case.case_id, "model": os.getenv("OPENAI_MODEL", ""), "timestamp": datetime.now(timezone.utc).isoformat(), "api_success": False, "error_type": "", "latency_ms": None, "input_tokens": None, "output_tokens": None, "raw_response": "", "claimed_success": None, "confidence": None, "patch": ""}
    try:
        key, model = os.getenv("OPENAI_API_KEY"), os.getenv("OPENAI_MODEL")
        if not key: raise EnvironmentError("OPENAI_API_KEY is not configured")
        if not model: raise EnvironmentError("OPENAI_MODEL must be explicitly configured; no model is silently substituted")
        from openai import OpenAI
        prompt = INSTRUCTIONS + "\n\nRelevant vulnerable source, preserving paths:\n" + source_context(case) + "\nReturn only JSON with claimed_success, confidence, and patch."
        started = time.perf_counter()
        response = OpenAI(api_key=key).responses.create(model=model, input=prompt)
        result["latency_ms"] = round((time.perf_counter() - started) * 1000, 2)
        result["raw_response"] = response.output_text
        result.update(parse_response(response.output_text)); result["api_success"] = True
        usage = getattr(response, "usage", None)
        if usage: result["input_tokens"], result["output_tokens"] = getattr(usage, "input_tokens", None), getattr(usage, "output_tokens", None)
    except Exception as exc:
        result["error_type"] = type(exc).__name__
        result["error_detail"] = str(exc).replace(os.getenv("OPENAI_API_KEY", ""), "[REDACTED]")
    response_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    patch_path.write_text(result["patch"], encoding="utf-8")
    (run_dir / "freeze.sha256").write_text(hashlib.sha256(response_path.read_bytes() + patch_path.read_bytes()).hexdigest() + "\n")
    return "SAVED"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--list-cases", action="store_true")
    parser.add_argument("--cases", type=int, default=5)
    parser.add_argument("--case-id")
    parser.add_argument("--run-id", default="default")
    args = parser.parse_args(); cases = eligible_cases(VUL4PY)
    if args.list_cases:
        print("\n".join(case.case_id for case in cases) or "No eligible cases: run Vul4Py scan first."); return
    selected = [case for case in cases if case.case_id == args.case_id] if args.case_id else cases[:args.cases]
    if args.case_id and not selected: raise SystemExit(f"Case is not scan-OK: {args.case_id}")
    for case in selected: print(case.case_id, repair(case, args.run_id))

if __name__ == "__main__": main()
