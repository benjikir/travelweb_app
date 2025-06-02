from flask_restx import Namespace, Resource, fields
from db import get_db
import sqlite3

location_ns = Namespace('Locations', description='Manage locations')

location_model_input = location_ns.model('LocationInput', {
    'loc_name': fields.String(required=True, description='Name of the location', example='Eiffel Tower'),
    'user_id': fields.Integer(required=True, description='ID of the user who added the location', example=1),
    'country_id': fields.Integer(required=True, description='ID of the related country', example=1),
    'image_url': fields.String(description='URL of the location image', example='http://example.com/eiffel.jpg')
})

location_model_output = location_ns.model('LocationOutput', {
    'location_id': fields.Integer(readonly=True, description='The location unique identifier'),
    'loc_name': fields.String(required=True, description='Name of the location'),
    'user_id': fields.Integer(required=True, description='ID of the user who added the location'),
    'country_id': fields.Integer(required=True, description='ID of the related country'),
    'image_url': fields.String(description='URL of the location image')
})


@location_ns.route('/')
class LocationList(Resource):
    @location_ns.doc('list_locations')
    @location_ns.marshal_list_with(location_model_output)
    def get(self):
        """Retrieve all saved locations"""
        with get_db() as conn:
            locations = conn.execute('SELECT * FROM Locations').fetchall()
        return [dict(row) for row in locations]

    @location_ns.doc('create_location')
    @location_ns.expect(location_model_input)
    @location_ns.marshal_with(location_model_output, code=201)
    def post(self):
        """Add a new location"""
        data = location_ns.payload
        with get_db() as conn:
            cursor = conn.cursor()
            try:
                # Ensure user_id and country_id exist before inserting
                user_exists = conn.execute('SELECT 1 FROM Users WHERE user_id = ?', (data['user_id'],)).fetchone()
                country_exists = conn.execute('SELECT 1 FROM Countries WHERE country_id = ?',
                                              (data['country_id'],)).fetchone()

                if not user_exists:
                    location_ns.abort(400, f"User with ID {data['user_id']} does not exist.")
                if not country_exists:
                    location_ns.abort(400, f"Country with ID {data['country_id']} does not exist.")

                cursor.execute(
                    'INSERT INTO Locations (loc_name, user_id, country_id, image_url) VALUES (?, ?, ?, ?)',
                    (data['loc_name'], data['user_id'], data['country_id'], data.get('image_url'))
                )
                location_id = cursor.lastrowid
                conn.commit()
            except sqlite3.IntegrityError as e:  # Should be caught by manual checks above, but good fallback
                location_ns.abort(400,
                                  f"Error creating location: {e}. Foreign key constraint failed (User or Country ID invalid).")

        with get_db() as conn:  # Fetch the created location to return it
            new_location = conn.execute('SELECT * FROM Locations WHERE location_id = ?', (location_id,)).fetchone()
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
            location_ns.abort(404, f"Location {id} doesn't exist")
        return dict(location)

    @location_ns.doc('update_location')
    @location_ns.expect(location_model_input)
    @location_ns.marshal_with(location_model_output)
    def put(self, id):
        """Update a location given its identifier"""
        data = location_ns.payload
        with get_db() as conn:
            try:
                user_exists = conn.execute('SELECT 1 FROM Users WHERE user_id = ?', (data['user_id'],)).fetchone()
                country_exists = conn.execute('SELECT 1 FROM Countries WHERE country_id = ?',
                                              (data['country_id'],)).fetchone()

                if not user_exists:
                    location_ns.abort(400, f"User with ID {data['user_id']} does not exist.")
                if not country_exists:
                    location_ns.abort(400, f"Country with ID {data['country_id']} does not exist.")

                conn.execute(
                    '''UPDATE Locations 
                       SET loc_name = ?, user_id = ?, country_id = ?, image_url = ? 
                       WHERE location_id = ?''',
                    (data['loc_name'], data['user_id'], data['country_id'], data.get('image_url'), id)
                )
                conn.commit()
                if conn.changes() == 0:
                    location_ns.abort(404, f"Location {id} doesn't exist, cannot update.")
            except sqlite3.IntegrityError as e:
                location_ns.abort(400, f"Error updating location: {e}. Foreign key constraint failed.")

            updated_location = conn.execute('SELECT * FROM Locations WHERE location_id = ?', (id,)).fetchone()
        return dict(updated_location)

    @location_ns.doc('delete_location')
    @location_ns.response(204, 'Location deleted')
    def delete(self, id):
        """Delete a location given its identifier"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM Locations WHERE location_id = ?', (id,))
            conn.commit()
            if cursor.rowcount == 0:
                location_ns.abort(404, f"Location {id} doesn't exist, cannot delete.")
        return '', 204