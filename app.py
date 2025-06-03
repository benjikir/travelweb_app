# app.py
from flask import Flask
from flask_restx import Api
from resources import user_ns, country_ns, location_ns, trip_ns, user_country_ns
from init_db import create_tables, DATABASE_NAME
import os

app = Flask(__name__)


api = Api(app,
          title="Travel WebApp BACKEND",
          version="0.2",
          description="Showing my API Endpoints with Swagger UI",
          )

# Add endpoints
api.add_namespace(country_ns, path='/Countries')
api.add_namespace(location_ns, path='/Locations')
api.add_namespace(trip_ns, path='/Trips')
api.add_namespace(user_country_ns, path='/User-countries-')
api.add_namespace(user_ns, path='/Users')

if __name__ == '__main__':
    if not os.path.exists(DATABASE_NAME):
        print(f"WARNING: Database {DATABASE_NAME} not found. Running create_tables().")
        create_tables()
        # Consider adding the default user here too if init_db.py might not be run separately
        # conn = sqlite3.connect(DATABASE_NAME)
        # cursor = conn.cursor()
        # try:
        #     cursor.execute("INSERT OR IGNORE INTO Users (user_id, username, email) VALUES (?, ?, ?)", (1, 'default_user', 'default@example.com'))
        #     conn.commit()
        #     print("Default user ensured in Users table from app.py.")
        # finally:
        #     if conn: conn.close()

    app.run(debug=True, port=5001)