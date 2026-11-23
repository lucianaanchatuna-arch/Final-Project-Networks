import os, sys, pytest
from pathlib import Path
sys.path.insert(0, os.environ["CANDIDATE_DIR"])
from app import list_directory

def test_rejects_shell_metacharacters(tmp_path):
    with pytest.raises(ValueError):
        list_directory(f"{tmp_path}; #")
    assert "shell=True" not in Path(os.environ["CANDIDATE_DIR"], "app.py").read_text()
