# test_db.py
import sqlite3
import os

DATABASE_NAME = 'travel_webapp.sqlite'  # Make sure this matches your actual database name


def test_database():
    if not os.path.exists(DATABASE_NAME):
        print(f"Database {DATABASE_NAME} does not exist!")
        return

    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()

        # Check Users table
        cursor.execute("SELECT * FROM Users")
        users = cursor.fetchall()
        print(f"Users: {users}")

        # Check Countries table
        cursor.execute("SELECT * FROM Countries")
        countries = cursor.fetchall()
        print(f"Countries: {countries[:5]}...")  # Print first 5 countries

        # Check User_countries table
        cursor.execute("SELECT * FROM User_countries")
        user_countries = cursor.fetchall()
        print(f"User-Country links: {user_countries}")

        # Check specifically for user 1
        cursor.execute("SELECT * FROM User_countries WHERE user_id = 1")
        user1_links = cursor.fetchall()
        print(f"User 1 links: {user1_links}")


if __name__ == '__main__':
    test_database()