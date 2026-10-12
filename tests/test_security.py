import sys
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_DIR = PROJECT_ROOT / "runs" / "student" / "demo_case_001" / "candidate"

sys.path.insert(0, str(CANDIDATE_DIR))

from app import calculate


def test_rejects_dangerous_expression():
    dangerous_expression = "__import__('os').system('echo hacked')"

    with pytest.raises(ValueError):
        calculate(dangerous_expression)
