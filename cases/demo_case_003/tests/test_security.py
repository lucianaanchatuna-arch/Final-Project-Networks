import os, sqlite3, sys
sys.path.insert(0, os.environ["CANDIDATE_DIR"])
from app import find_user

def test_does_not_allow_sql_injection():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE users (username TEXT, name TEXT)")
    conn.executemany("INSERT INTO users VALUES (?, ?)", [("alice", "Alice"), ("bob", "Bob")])
    assert find_user(conn, "' OR '1'='1") == []
