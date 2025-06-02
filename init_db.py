# init_db.py
import sqlite3

DATABASE_NAME = 'travel_webapp.sqlite' # CHANGED

def create_tables():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Enable Foreign Keys enforcement for this connection
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Countries Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Countries (
        country_id INTEGER PRIMARY KEY AUTOINCREMENT,
        country_code3 TEXT NOT NULL UNIQUE, -- Assuming code3 should be unique
        country TEXT NOT NULL UNIQUE,       -- Assuming country name should be unique
        flag_url TEXT,
        currency TEXT,
        continent TEXT,
        capital TEXT
    )
    ''')

    # Users Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL UNIQUE,
        profile_url TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP -- Auto set creation time
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

    # User_countries Table (Linking Table for Many-to-Many)
    # Corrected PRIMARY KEY and added FOREIGN KEYS
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS User_countries (
        user_id INTEGER NOT NULL,
        country_id INTEGER NOT NULL,
        PRIMARY KEY (user_id, country_id),
        FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
        FOREIGN KEY (country_id) REFERENCES Countries(country_id) ON DELETE CASCADE
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

    conn.commit()
    conn.close()
    print(f"✅ Database schema initialized in {DATABASE_NAME}.")

if __name__ == '__main__':
    create_tables()
    # You can add some sample data insertion here if needed for testing
    # For example:
    # conn = sqlite3.connect(DATABASE_NAME)
    # cursor = conn.cursor()
    # try:
    #     cursor.execute("INSERT INTO Users (username, email) VALUES (?, ?)", ('testuser', 'test@example.com'))
    #     cursor.execute("INSERT INTO Countries (country_code3, country) VALUES (?, ?)", ('USA', 'United States'))
    #     conn.commit()
    #     print("Sample data inserted.")
    # except sqlite3.IntegrityError:
    #     print("Sample data might already exist.")
    # finally:
    #     conn.close()