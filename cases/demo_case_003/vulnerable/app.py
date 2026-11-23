def find_user(connection, username):
    query = f"SELECT name FROM users WHERE username = '{username}'"
    return [row[0] for row in connection.execute(query)]
