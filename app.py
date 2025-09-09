from flask import Flask, send_from_directory
from flask_restx import Api
from resources import user_ns
from resources import location_ns
from resources import trip_ns
from resources import user_country_ns
from resources import country_ns
from init_db import create_tables
from flask_cors import CORS
import os
import sqlite3

# Use absolute path for database
DATABASE_NAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'travel_webapp.sqlite')

app = Flask(__name__)
CORS(app, resources={r'/*': {'origins': '*'}})

api = Api(app,
          title="Travel WebApp BACKEND",
          version="0.1.1",
          description="API for managing travel data including users, locations, trips, and country associations",
          ui_params={
              'defaultModelsExpandDepth': -1,
          }
          )

# Add namespaces with their paths
api.add_namespace(user_ns, path='/users')
api.add_namespace(user_country_ns, path='/user-countries')
api.add_namespace(location_ns, path='/locations')
api.add_namespace(trip_ns, path='/trips')
api.add_namespace(country_ns, path='/countries')


# ✅ NEUE ROUTE: GeoJSON für Country-Highlighting bereitstellen
@app.route('/countries.geojson')
def serve_countries_geojson():
    """Serve the countries GeoJSON file for map highlighting"""
    try:
        return send_from_directory(
            'static',
            'countries.geojson',
            mimetype='application/json'
        )
    except FileNotFoundError:
        return {"error": "countries.geojson not found. Please add the file to the static folder."}, 404


# ✅ NEUE ROUTE: Generelle statische Dateien (optional, für bessere Flexibilität)
@app.route('/static/<path:filename>')
def serve_static_files(filename):
    """Serve static files from the static directory"""
    try:
        return send_from_directory('static', filename)
    except FileNotFoundError:
        return {"error": f"File {filename} not found"}, 404


# ✅ NEUE ROUTE: Root-Route für API-Info (optional)
@app.route('/')
def api_info():
    """Basic API information"""
    return {
        "message": "Travel WebApp API",
        "version": "0.1.1",
        "status": "running",
        "endpoints": {
            "swagger_ui": "/",
            "countries_geojson": "/countries.geojson",
            "static_files": "/static/<filename>",
            "api_endpoints": [
                "/users",
                "/locations",
                "/trips",
                "/countries",
                "/user-countries"
            ]
        }
    }


def ensure_default_data():
    """Ensure default user, country, and their relationship exist"""
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()

        # Check if default user exists
        cursor.execute("SELECT user_id FROM Users WHERE user_id = 1")
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO Users (user_id, username, email) VALUES (?, ?, ?)",
                (1, 'default_user', 'default@example.com')
            )
            print("Created default user with ID 1")

        # Check if default country exists
        cursor.execute("SELECT country_id FROM Countries WHERE country_id = 1")
        if not cursor.fetchone():
            cursor.execute(
                "INSERT OR IGNORE INTO Countries (country_id, country_code3, country) VALUES (?, ?, ?)",
                (1, 'USA', 'United States')
            )
            print("Created default country with ID 1")

        # Check if relationship exists
        cursor.execute("SELECT 1 FROM User_countries WHERE user_id = 1 AND country_id = 1")
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO User_countries (user_id, country_id) VALUES (?, ?)",
                (1, 1)
            )
            print("Created relationship between user 1 and country 1")

        conn.commit()


def verify_database_state():
    """Verify the current state of the database and print useful information"""
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()

        # Check Users table
        cursor.execute("SELECT COUNT(*) FROM Users")
        user_count = cursor.fetchone()[0]
        print(f"Users table has {user_count} records")

        # Check Countries table
        cursor.execute("SELECT COUNT(*) FROM Countries")
        country_count = cursor.fetchone()[0]
        print(f"Countries table has {country_count} records")

        # Check User_countries table
        cursor.execute("SELECT COUNT(*) FROM User_countries")
        link_count = cursor.fetchone()[0]
        print(f"User_countries table has {link_count} records")

        # Check specifically for user 1
        cursor.execute("SELECT COUNT(*) FROM User_countries WHERE user_id = 1")
        user1_links = cursor.fetchone()[0]
        print(f"User 1 has {user1_links} country links")

        if user1_links == 0:
            print("WARNING: User 1 has no country links!")
            # Try to create one
            cursor.execute(
                "INSERT OR IGNORE INTO User_countries (user_id, country_id) VALUES (?, ?)",
                (1, 1)
            )
            conn.commit()
            print("Created a link between user 1 and country 1")


def check_static_folder():
    """Check if static folder exists and contains countries.geojson"""
    static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    geojson_file = os.path.join(static_folder, 'countries.geojson')

    if not os.path.exists(static_folder):
        os.makedirs(static_folder)
        print(f"Created static folder: {static_folder}")

    if not os.path.exists(geojson_file):
        print(f"WARNING: countries.geojson not found in {static_folder}")
        print("Please download a GeoJSON file with country boundaries and place it there.")
        print(
            "Example: curl -o static/countries.geojson https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson")
    else:
        print(f"✅ countries.geojson found in static folder")


if __name__ == '__main__':
    # Initialize database if it doesn't exist
    port = int(os.environ.get("PORT", 5001))

    if not os.path.exists(DATABASE_NAME):
        print(f"Database {DATABASE_NAME} not found. Running create_tables().")
        create_tables()
        ensure_default_data()
    else:
        # Always ensure default data exists
        ensure_default_data()

    # Verify database state
    verify_database_state()

    # Check static folder and GeoJSON file
    check_static_folder()

    print(f"Starting Flask app on port {port}")
    print(f"API Documentation available at: http://localhost:{port}/")
    print(f"Countries GeoJSON available at: http://localhost:{port}/countries.geojson")

    # Run the application
    app.run(debug=True, port=port, host='0.0.0.0')
