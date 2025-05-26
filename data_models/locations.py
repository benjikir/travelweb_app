from flask_restx import Namespace, Resource, fields
import sqlite3

location_ns = Namespace('locations', description='Manage locations added by users')

# 🔧 API model for Swagger UI
location_model = location_ns.model('Location', {
    'location_id': fields.Integer(readonly=True),
    'loc_name': fields.String(required=True, description='Name of the location'),
    'user_id': fields.Integer(required=True, description='ID of the user who added the location'),
    'country_id': fields.Integer(required=True, description='ID of the related country'),
    'image_url': fields.String(description='URL of the location image')
})

# 📦 SQLite database connection helper
def get_db_connection():
    conn = sqlite3.connect('travel_webapp.sqlite')
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn

# 🔍 GET /locations — list all locations
@location_ns.route('/')
class LocationList(Resource):
    @location_ns.marshal_list_with(location_model)
    def get(self):
        """Retrieve all saved locations"""
        conn = get_db_connection()
        rows = conn.execute('SELECT * FROM Locations').fetchall()
        conn.close()
        return [dict(row) for row in rows]

    @location_ns.expect(location_model)
    def post(self):
        """Add a new location"""
        data = location_ns.payload
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO Locations (loc_name, user_id, country_id, image_url) VALUES (?, ?, ?, ?)',
            (data['loc_name'], data['user_id'], data['country_id'], data.get('image_url', ''))
        )
        conn.commit()
        conn.close()
        return {'message': 'Location added'}, 201
