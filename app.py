# init_db.py
import sqlite3
import os
import json

# Database configuration - absolute path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_NAME = os.path.join(BASE_DIR, 'travel_webapp.sqlite')
COUNTRIES_JSON = os.path.join(BASE_DIR, 'countries_data.json')


def create_tables():
    """Create all necessary tables for the travel application"""
    print(f"Creating database tables in {DATABASE_NAME}...")

    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()

        # Create Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                profile_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create Countries table
        # Erweiterung: country_code2 (ISO2, UNIQUE, NOT NULL) für zuverlässiges Mapping/Highlighting
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Countries (
                country_id INTEGER PRIMARY KEY AUTOINCREMENT,
                country_code2 TEXT NOT NULL UNIQUE,  -- ISO2 (A2), z. B. "DE"
                country_code3 TEXT,                  -- ISO3 (A3), optional
                country TEXT NOT NULL UNIQUE,        -- Ländername (Englisch)
                flag_url TEXT,
                currency TEXT,
                continent TEXT,
                capital TEXT
            )
        ''')
        cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_countries_code2 ON Countries(country_code2)')
        cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_countries_name ON Countries(country)')

        # Create Locations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Locations (
                location_id INTEGER PRIMARY KEY AUTOINCREMENT,
                loc_name TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                country_id INTEGER NOT NULL,
                image_url TEXT,
                UNIQUE(user_id, loc_name),
                FOREIGN KEY (user_id) REFERENCES Users(user_id),
                FOREIGN KEY (country_id) REFERENCES Countries(country_id)
            )
        ''')

        # Create Trips table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Trips (
                trip_id INTEGER PRIMARY KEY AUTOINCREMENT,
                trip_name TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                country_id INTEGER NOT NULL,
                location_id INTEGER,
                startdate TEXT NOT NULL,
                enddate TEXT NOT NULL,
                notes TEXT,
                UNIQUE(user_id, trip_name),
                FOREIGN KEY (user_id) REFERENCES Users(user_id),
                FOREIGN KEY (country_id) REFERENCES Countries(country_id),
                FOREIGN KEY (location_id) REFERENCES Locations(location_id)
            )
        ''')

        # Create User_countries table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS User_countries (
                user_id INTEGER NOT NULL,
                country_id INTEGER NOT NULL,
                PRIMARY KEY (user_id, country_id),
                FOREIGN KEY (user_id) REFERENCES Users(user_id),
                FOREIGN KEY (country_id) REFERENCES Countries(country_id)
            )
        ''')

        conn.commit()
        print("All database tables created successfully.")


def populate_countries_from_json(cursor):
    """Populate Countries from countries_data.json (expects ISO2 codes)"""
    try:
        with open(COUNTRIES_JSON, 'r', encoding='utf-8') as f:
            data = json.load(f)
        countries = data.get('countries', {}).get('country', [])
        print(f"Found {len(countries)} countries in JSON.")
    except Exception as e:
        print("Failed to read countries_data.json:", e)
        countries = []

    inserted = 0
    for c in countries:
        code2 = (c.get('countryCode') or '').strip().upper()
        name = (c.get('countryName') or '').strip()
        currency = (c.get('currencyCode') or None)
        capital = (c.get('capital') or None)
        continent = (c.get('continentName') or None)

        if not code2 or not name:
            continue

        # ISO3 liegt in der JSON nicht zuverlässig vor; ggf. NULL lassen oder später anreichern
        cursor.execute('''
            INSERT OR IGNORE INTO Countries (country_code2, country_code3, country, currency, continent, capital)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (code2, None, name, currency, continent, capital))
        inserted += cursor.rowcount

    print(f"Inserted/ignored {inserted} country rows from JSON.")


def populate_sample_data():
    """Populate the database with sample data for testing"""
    print("Populating database with sample data...")

    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()

        # Sample user
        cursor.execute(
            "INSERT OR IGNORE INTO Users (user_id, username, email) VALUES (?, ?, ?)",
            (1, 'default_user', 'default@example.com')
        )

        # Full countries list from JSON
        populate_countries_from_json(cursor)

        # Ensure a couple of rows exist for safety if JSON missing
        cursor.execute("INSERT OR IGNORE INTO Countries (country_code2, country) VALUES (?, ?)", ('FR', 'France'))
        cursor.execute("INSERT OR IGNORE INTO Countries (country_code2, country) VALUES (?, ?)", ('US', 'United States'))

        # Link user to a known country (France) if present
        cursor.execute("SELECT country_id FROM Countries WHERE country_code2 = 'FR'")
        row = cursor.fetchone()
        if row:
            cursor.execute(
                "INSERT OR IGNORE INTO User_countries (user_id, country_id) VALUES (?, ?)",
                (1, row)
            )

        conn.commit()
        print("Sample data populated successfully.")


def initialize_database():
    """Initialize the database with tables and sample data"""
    # Remove existing database file if it exists
    if os.path.exists(DATABASE_NAME):
        os.remove(DATABASE_NAME)
        print(f"Removed existing database: {DATABASE_NAME}")

    # Create tables
    create_tables()

    # Populate sample data
    populate_sample_data()

    print(f"Database initialized successfully: {DATABASE_NAME}")


if __name__ == '__main__':
    initialize_database()
