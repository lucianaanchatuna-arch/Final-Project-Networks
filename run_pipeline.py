"""Run one selected Vul4Py case in isolation: generate, freeze, evaluate, measure."""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--repair", action="store_true", help="make the one API repair attempt if no frozen response exists")
    args = parser.parse_args()
    if args.repair:
        result = subprocess.run([sys.executable, str(ROOT / "repair.py"), "--case-id", args.case_id], cwd=ROOT)
        if result.returncode:
            raise SystemExit(result.returncode)
    result = subprocess.run([sys.executable, str(ROOT / "evaluator.py"), "--case-id", args.case_id], cwd=ROOT)
    if result.returncode:
        raise SystemExit(result.returncode)
    result = subprocess.run([sys.executable, str(ROOT / "metrics.py")], cwd=ROOT)
    if result.returncode:
        raise SystemExit(result.returncode)

if __name__ == "__main__":
    main()
