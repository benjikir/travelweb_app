# init_db.py
import sqlite3

DATABASE_NAME = 'travel_webapp.sqlite'

def create_tables():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Users Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL UNIQUE,
        profile_url TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Countries Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Countries (
        country_id INTEGER PRIMARY KEY AUTOINCREMENT,
        country_code3 TEXT NOT NULL UNIQUE,
        country TEXT NOT NULL UNIQUE,
        flag_url TEXT,
        currency TEXT,
        continent TEXT,
        capital TEXT
    )
    ''')

    # Locations Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Locations (
        location_id INTEGER PRIMARY KEY AUTOINCREMENT,
        loc_name TEXT NOT NULL,
        user_id INTEGER NOT NULL,
        country_id INTEGER NOT NULL,
        image_url TEXT,
        FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
        FOREIGN KEY (country_id) REFERENCES Countries(country_id) ON DELETE CASCADE
    )
    ''')

    # Trips Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Trips (
        trip_id INTEGER PRIMARY KEY AUTOINCREMENT,
        trip_name TEXT NOT NULL,
        user_id INTEGER NOT NULL,
        country_id INTEGER NOT NULL,
        startdate TEXT,
        enddate TEXT,
        FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
        FOREIGN KEY (country_id) REFERENCES Countries(country_id) ON DELETE CASCADE
    )
    ''')

    # User_countries Table (Linking Table for Many-to-Many between Users and Countries)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS User_countries (
        user_id INTEGER NOT NULL,
        country_id INTEGER NOT NULL,
        PRIMARY KEY (user_id, country_id),
        FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
        FOREIGN KEY (country_id) REFERENCES Countries(country_id) ON DELETE CASCADE
    )
    ''')

    conn.commit()
    conn.close()
    print(f"✅ Full database schema initialized in {DATABASE_NAME}.")

if __name__ == '__main__':
    create_tables()
    # Optional: Add a default user if needed for immediate testing
    # conn = sqlite3.connect(DATABASE_NAME)
    # cursor = conn.cursor()
    # try:
    #     cursor.execute("INSERT OR IGNORE INTO Users (user_id, username, email) VALUES (?, ?, ?)", (1, 'sampleuser', 'sample@example.com'))
    #     conn.commit()
    #     print("Sample user ensured.")
    # except sqlite3.Error as e:
    #     print(f"Error with sample user: {e}")
    # finally:
    #     if conn: conn.close()