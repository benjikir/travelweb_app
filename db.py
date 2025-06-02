import sqlite3

DATABASE_NAME = 'travel_webapp.sqlite' # CHANGED

def get_db():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn