import sqlite3

DB_NAME = "leaderboard.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS leaderboard (
                username TEXT PRIMARY KEY,
                count REAL DEFAULT 0
            )
        """)
        conn.commit()

def add_hotdogs(username, amount):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO leaderboard (username, count)
            VALUES (?, ?)
            ON CONFLICT(username) DO UPDATE SET count = count + ?
        """, (username, amount, amount))
        conn.commit()

def get_total(username):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT count FROM leaderboard WHERE username = ?", (username,))
        row = c.fetchone()
        return row[0] if row else 0

def get_leaderboard():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT username, count FROM leaderboard ORDER BY count DESC")
        return c.fetchall()
