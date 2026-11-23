import os, sys, pytest
sys.path.insert(0, os.environ["CANDIDATE_DIR"])
from app import read_note

def test_rejects_path_traversal():
    with pytest.raises(ValueError):
        read_note("../app.py")
