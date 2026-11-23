import os, sys
sys.path.insert(0, os.environ["CANDIDATE_DIR"])
from app import read_note

def test_reads_public_note():
    assert read_note("public.txt") == "public study note\n"
