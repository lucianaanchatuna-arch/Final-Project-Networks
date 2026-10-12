import json
import shutil
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
CASE_ID = "demo_case_001"

SOURCE_DIR = PROJECT_ROOT / "cases" / CASE_ID / "vulnerable"
RUN_DIR = PROJECT_ROOT / "runs" / "student" / CASE_ID
CANDIDATE_DIR = RUN_DIR / "candidate"
PATCH_PATH = RUN_DIR / "patch.diff"
EVAL_PATH = RUN_DIR / "eval.json"


def copy_candidate():
    if CANDIDATE_DIR.exists():
        shutil.rmtree(CANDIDATE_DIR)

    shutil.copytree(SOURCE_DIR, CANDIDATE_DIR)


def apply_patch():
    if not PATCH_PATH.exists() or PATCH_PATH.stat().st_size == 0:
        return False, "patch.diff is missing or empty"

    attempts = [
        ["patch", "-p0", "-i", str(PATCH_PATH)],
        ["patch", "-p1", "-i", str(PATCH_PATH)],
    ]

    outputs = []

    for command in attempts:
        copy_candidate()

        result = subprocess.run(
            command,
            cwd=CANDIDATE_DIR,
            text=True,
            capture_output=True,
        )

        outputs.append("Command: " + " ".join(command))
        outputs.append(result.stdout)
        outputs.append(result.stderr)

        if result.returncode == 0:
            return True, "\n".join(outputs)

    return False, "\n".join(outputs)


def run_pytest(test_file):
    result = subprocess.run(
        ["python", "-m", "pytest", str(test_file), "-q"],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
    )

    return result.returncode == 0, result.stdout + result.stderr


def main():
    RUN_DIR.mkdir(parents=True, exist_ok=True)

    evaluation = {
        "case_id": CASE_ID,
        "patch_applied": False,
        "functional_test_pass": False,
        "security_test_pass": False,
        "patch_output": "",
        "functional_output": "",
        "security_output": "",
    }

    copy_candidate()

    patch_applied, patch_output = apply_patch()
    evaluation["patch_applied"] = patch_applied
    evaluation["patch_output"] = patch_output

    if patch_applied:
        functional_pass, functional_output = run_pytest(
            PROJECT_ROOT / "tests" / "test_functional.py"
        )
        security_pass, security_output = run_pytest(
            PROJECT_ROOT / "tests" / "test_security.py"
        )

        evaluation["functional_test_pass"] = functional_pass
        evaluation["security_test_pass"] = security_pass
        evaluation["functional_output"] = functional_output
        evaluation["security_output"] = security_output

    EVAL_PATH.write_text(json.dumps(evaluation, indent=2), encoding="utf-8")

    print(f"Saved evaluation to: {EVAL_PATH}")
    print(f"patch_applied: {evaluation['patch_applied']}")
    print(f"functional_test_pass: {evaluation['functional_test_pass']}")
    print(f"security_test_pass: {evaluation['security_test_pass']}")


if __name__ == "__main__":
    main()
