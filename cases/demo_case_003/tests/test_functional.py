import os, sqlite3, sys
sys.path.insert(0, os.environ["CANDIDATE_DIR"])
from app import find_user

def test_finds_requested_user():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE users (username TEXT, name TEXT)")
    conn.execute("INSERT INTO users VALUES ('alice', 'Alice')")
    assert find_user(conn, "alice") == ["Alice"]
