import sqlite3

schema = """
CREATE TABLE IF NOT EXISTS Countries (
    country_id INTEGER PRIMARY KEY NOT NULL,
    country_code3 INTEGER NOT NULL,
    country TEXT NOT NULL,
    flag_url TEXT NOT NULL,
    currency TEXT NOT NULL,
    continent TEXT,
    capital TEXT
);

CREATE TABLE IF NOT EXISTS Users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    email TEXT UNIQUE,
    profile_url TEXT,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS Trips (
    trip_id INTEGER PRIMARY KEY NOT NULL,
    trip_name TEXT,
    user_id INTEGER,
    country_id INTEGER,
    startdate TEXT,
    enddate TEXT
);

CREATE TABLE IF NOT EXISTS User_countries (
    user_id INTEGER PRIMARY KEY NOT NULL,
    country_id INTEGER
);

CREATE TABLE IF NOT EXISTS Locations (
    location_id INTEGER PRIMARY KEY,
    loc_name TEXT,
    user_id INTEGER,
    country_id INTEGER,
    image_url TEXT
);

PRAGMA foreign_keys = ON;
"""

conn = sqlite3.connect('travel_webapp.sqlite')
conn.executescript(schema)
conn.commit()
conn.close()

print("✅ Database schema initialized.")
