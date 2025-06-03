# init_db.py
import sqlite3

DATABASE_NAME = 'travel_webapp.sqlite'

def create_tables():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Users Table (remains the same)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL UNIQUE,
        profile_url TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Countries Table (remains the same)
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
        country_id INTEGER NOT NULL, -- Country still relevant for the location itself
        image_url TEXT,
        FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
        FOREIGN KEY (country_id) REFERENCES Countries(country_id) ON DELETE CASCADE,
        UNIQUE (user_id, loc_name) -- Ensures a user cannot have two locations with the same name
    )
    ''')

    # Trips Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Trips (
        trip_id INTEGER PRIMARY KEY AUTOINCREMENT,
        trip_name TEXT NOT NULL,
        user_id INTEGER NOT NULL,
        country_id INTEGER NOT NULL, -- Country still relevant for the trip itself
        startdate TEXT,
        enddate TEXT,
        FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
        FOREIGN KEY (country_id) REFERENCES Countries(country_id) ON DELETE CASCADE,
        UNIQUE (user_id, trip_name) -- Ensures a user cannot have two trips with the same name
    )
    ''')

    # User_countries Table (remains the same)
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
    print(f"✅ Full database schema initialized in {DATABASE_NAME} with updated UNIQUE constraints.")

if __name__ == '__main__':
    create_tables()