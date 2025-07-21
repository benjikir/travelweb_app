from flask_restx import Namespace, Resource, fields
from db import get_db
import sqlite3

location_ns = Namespace('locations', description='Operations for managing locations')

location_model_input = location_ns.model('LocationInput', {
    'loc_name': fields.String(required=True, description='Name of the location', example='Eiffel Tower', min_length=1,
                              max_length=255),
    'user_id': fields.Integer(required=True, description='ID of the user adding the location', example=1),
    'country_id': fields.Integer(required=True, description='ID of the country where the location is', example=1),
    'image_url': fields.String(description='Image URL of the location (optional)', max_length=2048),
    # Add latitude and longitude to the input model
    'latitude': fields.Float(required=True, description='Latitude of the location', example=48.8584),
    'longitude': fields.Float(required=True, description='Longitude of the location', example=2.2945)
})

location_model_output = location_ns.model('LocationOutput', {
    'location_id': fields.Integer(readonly=True, description='The unique identifier of the location'),
    'loc_name': fields.String(description='Name of the location'),
    'user_id': fields.Integer(description='ID of the user who added the location'),
    'country_id': fields.Integer(description='ID of the country where the location is'),
    'image_url': fields.String(description='Image URL of the location'),
    # Add latitude and longitude to the output model
    'latitude': fields.Float(description='Latitude of the location'),
    'longitude': fields.Float(description='Longitude of the location')
})


@location_ns.route('/')
class LocationList(Resource):
    @location_ns.doc('create_location',
                     description="Add a new location. A user cannot add two locations with the same name.")
    @location_ns.expect(location_model_input)
    @location_ns.marshal_with(location_model_output, code=201)
    @location_ns.response(400, 'Validation Error: Required fields missing or invalid foreign keys.')
    @location_ns.response(409, 'Conflict: A location with this name already exists for this user.')
    def post(self):
        """Create a new location."""
        data = location_ns.payload
        loc_name = data.get('loc_name', '').strip()
        user_id_input = data.get('user_id')
        country_id_input = data.get('country_id')
        image_url = data.get('image_url', '').strip() if data.get('image_url') is not None else None
        # Get latitude and longitude from the payload
        latitude = data.get('latitude')
        longitude = data.get('longitude')

        if not all([loc_name, user_id_input is not None, country_id_input is not None, latitude is not None, longitude is not None]):
            location_ns.abort(400, "loc_name, user_id, country_id, latitude, and longitude are required.")

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
                # Update the INSERT statement to include latitude and longitude
                cursor.execute(
                    'INSERT INTO Locations (loc_name, user_id, country_id, image_url, latitude, longitude) VALUES (?, ?, ?, ?, ?, ?)',
                    (loc_name, user_id_input, country_id_input, image_url, latitude, longitude)
                )
                location_id = cursor.lastrowid
                conn.commit()
            except sqlite3.IntegrityError as e:
                if "UNIQUE constraint failed: Locations.user_id, Locations.loc_name" in str(e):
                    location_ns.abort(409,
                                      f"User (ID: {user_id_input}) already has a location named '{loc_name}'. Please choose a different name.")
                else:
                    location_ns.abort(500, f"Database error during location creation: {e}")

        with get_db() as conn:
            # Update the SELECT statement to retrieve latitude and longitude
            new_location = conn.execute('SELECT * FROM Locations WHERE location_id = ?', (location_id,)).fetchone()
        if not new_location:
            location_ns.abort(500, "Internal Server Error: Failed to retrieve location after creation.")
        return dict(new_location), 201


@location_ns.route('/<int:location_id>')
@location_ns.response(404, 'Location not found for the given ID.')
@location_ns.param('location_id', 'The unique identifier of the location')
class LocationResource(Resource):
    @location_ns.doc('get_location_by_id', description="Fetch a specific location by its unique ID.")
    @location_ns.marshal_with(location_model_output)
    def get(self, location_id):
        """Fetch a specific location by its ID."""
        with get_db() as conn:
            # Update the SELECT statement to retrieve latitude and longitude
            location = conn.execute('SELECT * FROM Locations WHERE location_id = ?', (location_id,)).fetchone()
        if location is None:
            location_ns.abort(404, f"Location with ID {location_id} not found.")
        return dict(location)

    @location_ns.doc('update_location_by_id',
                     description="Update an existing location. A user cannot have two locations with the same name.")
    @location_ns.expect(location_model_input)
    @location_ns.marshal_with(location_model_output)
    @location_ns.response(400, 'Validation Error: Required fields missing or invalid foreign keys.')
    @location_ns.response(409,
                          'Conflict: An updated location name would conflict with an existing location for this user.')
    def put(self, location_id):
        """Update an existing location."""
        data = location_ns.payload
        loc_name = data.get('loc_name', '').strip()
        user_id_input = data.get('user_id')
        country_id_input = data.get('country_id')
        image_url = data.get('image_url', '').strip() if data.get('image_url') is not None else None
        # Get latitude and longitude from the payload for update
        latitude = data.get('latitude')
        longitude = data.get('longitude')

        # Update the validation for required fields
        if not all([loc_name, user_id_input is not None, country_id_input is not None, latitude is not None, longitude is not None]):
            location_ns.abort(400, "loc_name, user_id, country_id, latitude, and longitude are required for update.")

        with get_db() as conn:
            current_location = conn.execute('SELECT user_id FROM Locations WHERE location_id = ?',
                                            (location_id,)).fetchone()
            if not current_location:
                location_ns.abort(404, f"Location with ID {location_id} not found, cannot update.")

            user_exists = conn.execute("SELECT 1 FROM Users WHERE user_id = ?", (user_id_input,)).fetchone()
            if not user_exists:
                location_ns.abort(400, f"User with ID {user_id_input} (for update) does not exist.")
            country_exists = conn.execute("SELECT 1 FROM Countries WHERE country_id = ?",
                                          (country_id_input,)).fetchone()
            if not country_exists:
                location_ns.abort(400, f"Country with ID {country_id_input} (for update) does not exist.")

            try:
                # Update the UPDATE statement to include latitude and longitude
                conn.execute(
                    '''UPDATE Locations SET loc_name = ?, user_id = ?, country_id = ?, image_url = ?, latitude = ?, longitude = ?
                       WHERE location_id = ?''',
                    (loc_name, user_id_input, country_id_input, image_url, latitude, longitude, location_id)
                )
                conn.commit()
            except sqlite3.IntegrityError as e:
                if "UNIQUE constraint failed: Locations.user_id, Locations.loc_name" in str(e):
                    location_ns.abort(409,
                                      f"User (ID: {user_id_input}) already has another location named '{loc_name}'. Please choose a different name.")
                else:
                    location_ns.abort(500, f"Database error during location update: {e}")

            # Update the SELECT statement to retrieve latitude and longitude
            updated_location = conn.execute('SELECT * FROM Locations WHERE location_id = ?', (location_id,)).fetchone()
        if not updated_location:
            location_ns.abort(404, f"Location with ID {location_id} could not be retrieved after update attempt.")
        return dict(updated_location)

    @location_ns.doc('delete_location_by_id', description="Delete a location by its unique ID.")
    @location_ns.response(204, 'Location deleted successfully.')
    def delete(self, location_id):
        """Delete a location by its ID."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM Locations WHERE location_id = ?', (location_id,))
            conn.commit()
            if cursor.rowcount == 0:
                location_ns.abort(404, f"Location with ID {location_id} not found, cannot delete.")
        return '', 204


@location_ns.route('/user/<int:user_id>')
@location_ns.param('user_id', 'The unique identifier of the user')
@location_ns.response(404, 'No locations found for the given user ID.')
class UserLocations(Resource):
    @location_ns.doc('get_locations_by_user_id', description="Retrieve all locations added by a specific user.")
    @location_ns.marshal_list_with(location_model_output)
    def get(self, user_id):
        """Fetch all locations for a specific user by their user ID."""
        with get_db() as conn:
            user_exists = conn.execute("SELECT 1 FROM Users WHERE user_id = ?", (user_id,)).fetchone()
            if not user_exists:
                location_ns.abort(404, f"User with ID {user_id} does not exist.")

            # Update the SELECT statement to retrieve latitude and longitude
            locations = conn.execute(
                'SELECT * FROM Locations WHERE user_id = ? ORDER BY loc_name ASC',
                (user_id,)
            ).fetchall()

        if not locations:
            location_ns.abort(404, f"No locations found for user ID {user_id}.")

        return [dict(loc) for loc in locations]