import os, sys
sys.path.insert(0, os.environ["CANDIDATE_DIR"])
from app import calculate

def test_arithmetic():
    assert calculate("2 + 3") == 5
    assert calculate("10 - 4") == 6
    assert calculate("3 * 4") == 12
