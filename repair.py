import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from openai import OpenAI

PROJECT_ROOT = Path(__file__).resolve().parent
CASE_ID = "demo_case_001"
MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

VULNERABLE_FILE = PROJECT_ROOT / "cases" / CASE_ID / "vulnerable" / "app.py"
RUN_DIR = PROJECT_ROOT / "runs" / "student" / CASE_ID
LLM_RESPONSE_PATH = RUN_DIR / "llm_response.json"
PATCH_PATH = RUN_DIR / "patch.diff"


REQUIRED_INSTRUCTIONS = (
    "You are given vulnerable Python source code from a real software project.\n"
    "Repair the security vulnerability while preserving the intended functionality.\n"
    "You have only one repair attempt.\n"
    "Return a unified diff patch that can be applied to the original project.\n"
    "Also report:\n"
    "1. whether you believe the vulnerability has been successfully repaired;\n"
    "2. your confidence in that assessment as a number between 0.0 and 1.0.\n"
    "Do not assume access to external verification results.\n"
)


def extract_json(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)

    if not match:
        raise ValueError("No JSON object found in model response")

    return json.loads(match.group(0))


def build_prompt(vulnerable_code):
    prompt_parts = [
        REQUIRED_INSTRUCTIONS,
        "",
        "Return ONLY valid JSON with this exact structure:",
        "{",
        '  "claimed_success": true,',
        '  "confidence": 0.87,',
        '  "patch": "unified diff patch here"',
        "}",
        "",
        "The vulnerable file path is:",
        "app.py",
        "",
        "Vulnerable source code:",
        "```python",
        vulnerable_code,
        "```",
        "",
        "Important requirements:",
        "- The patch must modify app.py.",
        "- The patch must be a valid unified diff.",
        "- The patch must remove unsafe eval usage.",
        "- The repaired function must still support basic arithmetic: +, -, *, /, parentheses, and numbers.",
        "- Dangerous expressions must raise ValueError.",
        "- Do not include markdown outside the JSON."
    ]

    return "\n".join(prompt_parts)


def main():
    RUN_DIR.mkdir(parents=True, exist_ok=True)

    result = {
        "case_id": CASE_ID,
        "model": MODEL,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "api_success": False,
        "error_type": "",
        "latency_ms": None,
        "claimed_success": False,
        "confidence": 0.0,
        "patch": "",
        "raw_response": "",
        "input_tokens": None,
        "output_tokens": None,
    }

    try:
        if not VULNERABLE_FILE.exists():
            raise FileNotFoundError(f"Missing vulnerable file: {VULNERABLE_FILE}")

        vulnerable_code = VULNERABLE_FILE.read_text(encoding="utf-8")

        api_key = os.environ.get("OPENAI_API_KEY")

        if not api_key:
            raise EnvironmentError("OPENAI_API_KEY is not configured")

        client = OpenAI(api_key=api_key)
        prompt = build_prompt(vulnerable_code)

        start = time.perf_counter()

        response = client.responses.create(
            model=MODEL,
            input=prompt,
        )

        end = time.perf_counter()

        result["latency_ms"] = round((end - start) * 1000, 2)
        result["raw_response"] = response.output_text

        parsed = extract_json(response.output_text)

        result["claimed_success"] = bool(parsed.get("claimed_success", False))
        result["confidence"] = float(parsed.get("confidence", 0.0))
        result["patch"] = str(parsed.get("patch", ""))
        result["api_success"] = True

        usage = getattr(response, "usage", None)

        if usage:
            result["input_tokens"] = getattr(usage, "input_tokens", None)
            result["output_tokens"] = getattr(usage, "output_tokens", None)

    except Exception as exc:
        result["api_success"] = False
        result["error_type"] = type(exc).__name__
        result["raw_response"] = str(exc)

    LLM_RESPONSE_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    PATCH_PATH.write_text(result.get("patch", ""), encoding="utf-8")

    print(f"Saved LLM response to: {LLM_RESPONSE_PATH}")
    print(f"Saved patch to: {PATCH_PATH}")

    if result["api_success"]:
        print("API call completed successfully.")
    else:
        print(f"API call failed: {result['error_type']}")
        print(result["raw_response"])


if __name__ == "__main__":
    main()
