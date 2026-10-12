import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

STEPS = [
    ("Repair step", "repair.py"),
    ("Evaluation step", "evaluator.py"),
    ("Metrics step", "metrics.py"),
]


def run_step(name, script):
    script_path = PROJECT_ROOT / script

    if not script_path.exists():
        print(f"[ERROR] Missing file: {script}")
        return False

    print(f"\n=== {name} ===")

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=PROJECT_ROOT,
        text=True,
    )

    if result.returncode != 0:
        print(f"[ERROR] {script} failed with exit code {result.returncode}")
        return False

    print(f"[OK] {script} completed")
    return True


def main():
    print("Starting one-case vulnerability repair MVP pipeline...")

    for name, script in STEPS:
        ok = run_step(name, script)
        if not ok:
            print("Pipeline stopped.")
            return

    print("\nPipeline completed.")
    print("Generated files:")
    print("  runs/student/demo_case_001/llm_response.json")
    print("  runs/student/demo_case_001/patch.diff")
    print("  runs/student/demo_case_001/eval.json")
    print("  results/results.csv")


if __name__ == "__main__":
    main()
