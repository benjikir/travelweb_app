# resources/locations.py
from flask_restx import Namespace, Resource, fields
from db import get_db
import sqlite3
import re  # For URL validation if needed, or use a library

location_ns = Namespace('Locations', description='Manage locations added by users')


def is_valid_url(url_string: str) -> bool:  # You can centralize this helper
    if not url_string:
        return True
    regex = re.compile(
        r'^(?:http|ftp)s?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url_string) is not None


location_model_input = location_ns.model('LocationInput', {
    'loc_name': fields.String(required=True, description='Name of the location', example='Eiffel Tower', min_length=2,
                              max_length=255),
    'user_id': fields.Integer(required=True, description='ID of the user who added the location', example=1),
    'country_id': fields.Integer(required=True, description='ID of the related country', example=1),
    'image_url': fields.String(description='URL of the location image (optional)',
                               example='http://example.com/eiffel.jpg', max_length=2048)
})

location_model_output = location_ns.model('LocationOutput', {
    'location_id': fields.Integer(readonly=True, description='The location unique identifier'),
    'loc_name': fields.String(required=True),
    'user_id': fields.Integer(required=True),
    'country_id': fields.Integer(required=True),
    'image_url': fields.String()
})


@location_ns.route('/')
class LocationList(Resource):
    @location_ns.doc('list_locations')
    @location_ns.marshal_list_with(location_model_output)
    def get(self):
        """Retrieve all saved locations"""
        with get_db() as conn:
            locations = conn.execute('SELECT * FROM Locations ORDER BY loc_name ASC').fetchall()
        return [dict(row) for row in locations]

    @location_ns.doc('create_location')
    @location_ns.expect(location_model_input)
    @location_ns.marshal_with(location_model_output, code=201)
    def post(self):
        """Add a new location"""
        data = location_ns.payload
        loc_name = data.get('loc_name', '').strip()
        user_id = data.get('user_id')  # Should be validated as integer by model
        country_id = data.get('country_id')  # Should be validated as integer by model
        image_url = data.get('image_url', '').strip() if data.get('image_url') is not None else None

        if not loc_name:
            location_ns.abort(400, "Location name (loc_name) is required.")
        if user_id is None:  # Model should catch if not int, but check for presence if not strictly required by model
            location_ns.abort(400, "user_id is required.")
        if country_id is None:
            location_ns.abort(400, "country_id is required.")

        if image_url and not is_valid_url(image_url):
            location_ns.abort(400, f"Invalid image_url format: '{image_url}'.")

        with get_db() as conn:
            # Validate foreign keys
            user_exists = conn.execute('SELECT 1 FROM Users WHERE user_id = ?', (user_id,)).fetchone()
            if not user_exists:
                location_ns.abort(400, f"User with ID {user_id} does not exist.")
            country_exists = conn.execute('SELECT 1 FROM Countries WHERE country_id = ?', (country_id,)).fetchone()
            if not country_exists:
                location_ns.abort(400, f"Country with ID {country_id} does not exist.")

            # Optional: Check for duplicate location name for the same user/country (if desired)
            # existing_loc = conn.execute("SELECT location_id FROM Locations WHERE LOWER(loc_name) = ? AND user_id = ? AND country_id = ?",
            #                             (loc_name.lower(), user_id, country_id)).fetchone()
            # if existing_loc:
            #     location_ns.abort(409, f"Location '{loc_name}' already exists for this user and country.")

            cursor = conn.cursor()
            try:
                cursor.execute(
                    'INSERT INTO Locations (loc_name, user_id, country_id, image_url) VALUES (?, ?, ?, ?)',
                    (loc_name, user_id, country_id, image_url)
                )
                location_id = cursor.lastrowid
                conn.commit()
            except sqlite3.IntegrityError as e:  # Fallback, FK checks above should catch most
                location_ns.abort(400, f"Database error creating location: {e}. Check foreign keys.")

        with get_db() as conn:
            new_location = conn.execute('SELECT * FROM Locations WHERE location_id = ?', (location_id,)).fetchone()
        if not new_location:
            location_ns.abort(500, "Internal Server Error: Failed to retrieve location after insertion.")
        return dict(new_location), 201


@location_ns.route('/<int:id>')
@location_ns.response(404, 'Location not found')
@location_ns.param('id', 'The location identifier')
class LocationResource(Resource):
    @location_ns.doc('get_location')
    @location_ns.marshal_with(location_model_output)
    def get(self, id):
        """Fetch a location given its identifier"""
        with get_db() as conn:
            location = conn.execute('SELECT * FROM Locations WHERE location_id = ?', (id,)).fetchone()
        if location is None:
            location_ns.abort(404, f"Location with ID {id} not found.")
        return dict(location)

    @location_ns.doc('update_location')
    @location_ns.expect(location_model_input)
    @location_ns.marshal_with(location_model_output)
    def put(self, id):
        """Update a location given its identifier"""
        data = location_ns.payload
        loc_name = data.get('loc_name', '').strip()
        user_id = data.get('user_id')
        country_id = data.get('country_id')
        image_url = data.get('image_url', '').strip() if data.get('image_url') is not None else None

        if not loc_name:
            location_ns.abort(400, "Location name (loc_name) is required for update.")
        if user_id is None:
            location_ns.abort(400, "user_id is required for update.")
        if country_id is None:
            location_ns.abort(400, "country_id is required for update.")

        if image_url and not is_valid_url(image_url):
            location_ns.abort(400, f"Invalid image_url format: '{image_url}'.")

        with get_db() as conn:
            current_loc = conn.execute('SELECT location_id FROM Locations WHERE location_id = ?', (id,)).fetchone()
            if not current_loc:
                location_ns.abort(404, f"Location with ID {id} not found, cannot update.")

            user_exists = conn.execute('SELECT 1 FROM Users WHERE user_id = ?', (user_id,)).fetchone()
            if not user_exists:
                location_ns.abort(400, f"User with ID {user_id} does not exist for update.")
            country_exists = conn.execute('SELECT 1 FROM Countries WHERE country_id = ?', (country_id,)).fetchone()
            if not country_exists:
                location_ns.abort(400, f"Country with ID {country_id} does not exist for update.")

            # Optional: Duplicate check excluding self
            # existing_loc = conn.execute("SELECT location_id FROM Locations WHERE LOWER(loc_name) = ? AND user_id = ? AND country_id = ? AND location_id != ?",
            #                             (loc_name.lower(), user_id, country_id, id)).fetchone()
            # if existing_loc:
            #     location_ns.abort(409, f"Another location '{loc_name}' already exists for this user and country.")

            try:
                conn.execute(
                    '''UPDATE Locations SET loc_name = ?, user_id = ?, country_id = ?, image_url = ? 
                       WHERE location_id = ?''',
                    (loc_name, user_id, country_id, image_url, id)
                )
                conn.commit()
            except sqlite3.IntegrityError as e:
                location_ns.abort(400, f"Database error updating location: {e}.")

            updated_location = conn.execute('SELECT * FROM Locations WHERE location_id = ?', (id,)).fetchone()
        if not updated_location:
            location_ns.abort(404, f"Location with ID {id} could not be retrieved after update.")
        return dict(updated_location)

    @location_ns.doc('delete_location')
    @location_ns.response(204, 'Location deleted successfully')
    def delete(self, id):
        """Delete a location given its identifier"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM Locations WHERE location_id = ?', (id,))
            conn.commit()
            if cursor.rowcount == 0:
                location_ns.abort(404, f"Location with ID {id} not found, cannot delete.")
        return '', 204