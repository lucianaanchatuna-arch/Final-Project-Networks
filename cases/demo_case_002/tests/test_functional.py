import os, sys
sys.path.insert(0, os.environ["CANDIDATE_DIR"])
from app import list_directory

def test_lists_directory(tmp_path):
    (tmp_path / "visible.txt").write_text("ok")
    assert "visible.txt" in list_directory(str(tmp_path))
