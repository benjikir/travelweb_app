# resources/locations.py
from flask_restx import Namespace, Resource, fields
from db import get_db
import sqlite3

# --- Models (location_model_input, location_model_output) remain the same ---
location_ns = Namespace('Locations', description='Location management')

location_model_input = location_ns.model('LocationInput', {
    'loc_name': fields.String(required=True, description='Name of the location', example='Eiffel Tower', min_length=1,
                              max_length=255),
    'user_id': fields.Integer(required=True, description='ID of the user adding the location', example=1),
    'country_id': fields.Integer(required=True, description='ID of the country for the location', example=1),
    'image_url': fields.String(description='Image URL (optional)', max_length=2048)
})

location_model_output = location_ns.model('LocationOutput', {
    'location_id': fields.Integer(readonly=True),
    'loc_name': fields.String(),
    'user_id': fields.Integer(),
    'country_id': fields.Integer(),
    'image_url': fields.String()
})


@location_ns.route('/')
class LocationList(Resource):
    @location_ns.doc('list_locations', params={'user_id': 'Filter locations by user ID (optional)',
                                               'country_id': 'Filter locations by country ID (optional)'})
    @location_ns.marshal_list_with(location_model_output)
    def get(self):
        """List all locations, or filter by user_id and/or country_id."""
        parser = location_ns.parser()
        parser.add_argument('user_id', type=int, location='args')
        parser.add_argument('country_id', type=int, location='args')
        args = parser.parse_args()

        query = "SELECT * FROM Locations"
        conditions = []
        params = []

        if args.get('user_id') is not None:
            conditions.append("user_id = ?")
            params.append(args['user_id'])
        if args.get('country_id') is not None:
            conditions.append("country_id = ?")
            params.append(args['country_id'])

        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY loc_name ASC"

        with get_db() as conn:
            locations = conn.execute(query, tuple(params)).fetchall()
        return [dict(row) for row in locations]

    @location_ns.doc('create_location')
    @location_ns.expect(location_model_input)
    @location_ns.marshal_with(location_model_output, code=201)
    def post(self):
        """Create a new location. A user cannot add two locations with the same name."""
        data = location_ns.payload
        loc_name = data.get('loc_name', '').strip()
        user_id_input = data.get('user_id')
        country_id_input = data.get('country_id')
        image_url = data.get('image_url', '').strip() if data.get('image_url') is not None else None

        if not all([loc_name, user_id_input is not None, country_id_input is not None]):
            location_ns.abort(400, "loc_name, user_id, and country_id are required.")

        with get_db() as conn:
            user_exists = conn.execute("SELECT 1 FROM Users WHERE user_id = ?", (user_id_input,)).fetchone()
            if not user_exists:
                location_ns.abort(400, f"User with ID {user_id_input} does not exist.")

            country_exists = conn.execute("SELECT 1 FROM Countries WHERE country_id = ?",
                                          (country_id_input,)).fetchone()
            if not country_exists:
                location_ns.abort(400, f"Country with ID {country_id_input} does not exist.")

            cursor = conn.cursor()
            try:
                cursor.execute(
                    'INSERT INTO Locations (loc_name, user_id, country_id, image_url) VALUES (?, ?, ?, ?)',
                    (loc_name, user_id_input, country_id_input, image_url)
                )
                location_id = cursor.lastrowid
                conn.commit()
            except sqlite3.IntegrityError as e:
                if "UNIQUE constraint failed: Locations.user_id, Locations.loc_name" in str(e):
                    location_ns.abort(409,
                                      f"User (ID: {user_id_input}) already has a location named '{loc_name}'. Please choose a different name.")
                else:
                    location_ns.abort(500, f"Database error: {e}")

        with get_db() as conn:
            new_location = conn.execute('SELECT * FROM Locations WHERE location_id = ?', (location_id,)).fetchone()
        if not new_location:
            location_ns.abort(500, "Failed to retrieve location after creation.")
        return dict(new_location), 201


@location_ns.route('/<int:id>')
@location_ns.response(404, 'Location not found')
@location_ns.param('id', 'The location identifier')
class LocationResource(Resource):
    @location_ns.doc('get_location')
    @location_ns.marshal_with(location_model_output)
    def get(self, id):
        """Fetch a specific location by its ID."""
        with get_db() as conn:
            location = conn.execute('SELECT * FROM Locations WHERE location_id = ?', (id,)).fetchone()
        if location is None:
            location_ns.abort(404, f"Location with ID {id} not found.")
        return dict(location)

    @location_ns.doc('update_location')
    @location_ns.expect(location_model_input)
    @location_ns.marshal_with(location_model_output)
    def put(self, id):
        """Update an existing location. A user cannot have two locations with the same name."""
        data = location_ns.payload
        loc_name = data.get('loc_name', '').strip()
        user_id_input = data.get('user_id')
        country_id_input = data.get('country_id')
        image_url = data.get('image_url', '').strip() if data.get('image_url') is not None else None

        if not all([loc_name, user_id_input is not None, country_id_input is not None]):
            location_ns.abort(400, "loc_name, user_id, and country_id are required for update.")

        with get_db() as conn:
            current_location = conn.execute('SELECT user_id FROM Locations WHERE location_id = ?', (id,)).fetchone()
            if not current_location:
                location_ns.abort(404, f"Location with ID {id} not found.")

            user_exists = conn.execute("SELECT 1 FROM Users WHERE user_id = ?", (user_id_input,)).fetchone()
            if not user_exists:
                location_ns.abort(400, f"User with ID {user_id_input} (for update) does not exist.")

            country_exists = conn.execute("SELECT 1 FROM Countries WHERE country_id = ?",
                                          (country_id_input,)).fetchone()
            if not country_exists:
                location_ns.abort(400, f"Country with ID {country_id_input} (for update) does not exist.")

            try:
                conn.execute(
                    '''UPDATE Locations SET loc_name = ?, user_id = ?, country_id = ?, image_url = ?
                       WHERE location_id = ?''',
                    (loc_name, user_id_input, country_id_input, image_url, id)
                )
                conn.commit()
            except sqlite3.IntegrityError as e:
                if "UNIQUE constraint failed: Locations.user_id, Locations.loc_name" in str(e):
                    location_ns.abort(409,
                                      f"User (ID: {user_id_input}) already has another location named '{loc_name}'. Please choose a different name.")
                else:
                    location_ns.abort(500, f"Database error during update: {e}")

            updated_location = conn.execute('SELECT * FROM Locations WHERE location_id = ?', (id,)).fetchone()
        if not updated_location:
            location_ns.abort(404, "Failed to retrieve location after update.")
        return dict(updated_location)

    @location_ns.doc('delete_location')
    @location_ns.response(204, 'Location deleted successfully')
    def delete(self, id):
        """Delete a location by its ID."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM Locations WHERE location_id = ?', (id,))
            conn.commit()
            if cursor.rowcount == 0:
                location_ns.abort(404, f"Location with ID {id} not found, cannot delete.")
        return '', 204