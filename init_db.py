# init_db.py
import sqlite3
import os

# Database configuration - absolute path
DATABASE_NAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'travel_webapp.sqlite')


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

        # ✅ Create Trips table with country_id
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

        # Sample countries
        cursor.execute(
            "INSERT OR IGNORE INTO Countries (country_id, country_code3, country) VALUES (?, ?, ?)",
            (1, 'FRA', 'France')
        )
        cursor.execute(
            "INSERT OR IGNORE INTO Countries (country_id, country_code3, country) VALUES (?, ?, ?)",
            (2, 'USA', 'United States')
        )

        # Link user to a country
        cursor.execute(
            "INSERT OR IGNORE INTO User_countries (user_id, country_id) VALUES (?, ?)",
            (1, 1)
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
