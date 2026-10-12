import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_DIR = PROJECT_ROOT / "runs" / "student" / "demo_case_001" / "candidate"

sys.path.insert(0, str(CANDIDATE_DIR))

from app import calculate


def test_addition():
    assert calculate("2 + 3") == 5


def test_subtraction():
    assert calculate("10 - 4") == 6


def test_multiplication():
    assert calculate("3 * 4") == 12
