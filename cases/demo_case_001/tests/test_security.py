import os, sys, pytest
sys.path.insert(0, os.environ["CANDIDATE_DIR"])
from app import calculate

def test_rejects_code_execution():
    with pytest.raises(ValueError):
        calculate("__import__('os').system('echo hacked')")
