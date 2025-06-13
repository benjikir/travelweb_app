# resources/trips.py
from flask_restx import Namespace, Resource, fields
from db import get_db
import sqlite3

trip_ns = Namespace('trips', description='Operations for managing user trips')

trip_model_input = trip_ns.model('TripInput', {
    'trip_name': fields.String(required=True, description='Name of the trip', example='Summer Vacation in Italy',
                               min_length=1, max_length=255),
    'user_id': fields.Integer(required=True, description='ID of the user who owns the trip', example=1),
    'country_id': fields.Integer(required=True, description='ID of the country for the trip', example=1),
    # Assuming country is still relevant
    'startdate': fields.String(description='Start date of the trip (YYYY-MM-DD)', example='2024-07-01'),
    'enddate': fields.String(description='End date of the trip (YYYY-MM-DD)', example='2024-07-15')
})

trip_model_output = trip_ns.model('TripOutput', {
    'trip_id': fields.Integer(readonly=True, description='The unique identifier of the trip'),
    'trip_name': fields.String(description='Name of the trip'),
    'user_id': fields.Integer(description='ID of the user who owns the trip'),
    'country_id': fields.Integer(description='ID of the country for the trip'),
    'startdate': fields.String(description='Start date of the trip'),
    'enddate': fields.String(description='End date of the trip')
})


@trip_ns.route('/')
class TripList(Resource):
    # GET method for listing ALL trips has been REMOVED
    # @trip_ns.doc('list_all_trips', description="Retrieve a list of all trips.")
    # @trip_ns.marshal_list_with(trip_model_output)
    # def get(self):
    #     """List all trips."""
    #     with get_db() as conn:
    #         trips = conn.execute('SELECT * FROM Trips ORDER BY trip_name ASC').fetchall()
    #     return [dict(row) for row in trips]

    @trip_ns.doc('create_trip', description="Create a new trip. A user cannot have two trips with the same name.")
    @trip_ns.expect(trip_model_input)
    @trip_ns.marshal_with(trip_model_output, code=201)
    @trip_ns.response(400, 'Validation Error: Required fields missing or invalid foreign keys.')
    @trip_ns.response(409, 'Conflict: A trip with this name already exists for this user.')
    def post(self):
        """Create a new trip."""
        data = trip_ns.payload
        trip_name = data.get('trip_name', '').strip()
        user_id_input = data.get('user_id')
        country_id_input = data.get('country_id')  # Still present as per your schema
        startdate = data.get('startdate')
        enddate = data.get('enddate')

        if not all([trip_name, user_id_input is not None, country_id_input is not None]):
            trip_ns.abort(400, "trip_name, user_id, and country_id are required.")

        with get_db() as conn:
            # Validate foreign keys
            user_exists = conn.execute("SELECT 1 FROM Users WHERE user_id = ?", (user_id_input,)).fetchone()
            if not user_exists:
                trip_ns.abort(400, f"User with ID {user_id_input} does not exist.")

            country_exists = conn.execute("SELECT 1 FROM Countries WHERE country_id = ?",
                                          (country_id_input,)).fetchone()
            if not country_exists:
                trip_ns.abort(400, f"Country with ID {country_id_input} does not exist.")

            cursor = conn.cursor()
            try:
                cursor.execute(
                    'INSERT INTO Trips (trip_name, user_id, country_id, startdate, enddate) VALUES (?, ?, ?, ?, ?)',
                    (trip_name, user_id_input, country_id_input, startdate, enddate)
                )
                trip_id = cursor.lastrowid
                conn.commit()
            except sqlite3.IntegrityError as e:
                # This catches the UNIQUE (user_id, trip_name) constraint from init_db.py
                if "UNIQUE constraint failed: Trips.user_id, Trips.trip_name" in str(e):
                    trip_ns.abort(409,
                                  f"User (ID: {user_id_input}) already has a trip named '{trip_name}'. Please choose a different name.")
                else:
                    trip_ns.abort(500, f"Database error during trip creation: {e}")

        with get_db() as conn:
            new_trip = conn.execute('SELECT * FROM Trips WHERE trip_id = ?', (trip_id,)).fetchone()
        if not new_trip:
            trip_ns.abort(500, "Internal Server Error: Failed to retrieve trip after creation.")
        return dict(new_trip), 201


@trip_ns.route('/<int:trip_id>')  # Using trip_id for clarity in path parameter
@trip_ns.response(404, 'Trip not found for the given ID.')
@trip_ns.param('trip_id', 'The unique identifier of the trip')
class TripResource(Resource):
    @trip_ns.doc('get_trip_by_id', description="Fetch a specific trip by its unique ID.")
    @trip_ns.marshal_with(trip_model_output)
    def get(self, trip_id):
        """Fetch a specific trip by its ID."""
        with get_db() as conn:
            trip = conn.execute('SELECT * FROM Trips WHERE trip_id = ?', (trip_id,)).fetchone()
        if trip is None:
            trip_ns.abort(404, f"Trip with ID {trip_id} not found.")
        return dict(trip)

    @trip_ns.doc('update_trip_by_id',
                 description="Update an existing trip. A user cannot have two trips with the same name.")
    @trip_ns.expect(trip_model_input)
    @trip_ns.marshal_with(trip_model_output)
    @trip_ns.response(400, 'Validation Error: Required fields missing or invalid foreign keys.')
    @trip_ns.response(409, 'Conflict: An updated trip name would conflict with an existing trip for this user.')
    def put(self, trip_id):
        """Update an existing trip."""
        data = trip_ns.payload
        trip_name = data.get('trip_name', '').strip()
        user_id_input = data.get('user_id')
        country_id_input = data.get('country_id')
        startdate = data.get('startdate')
        enddate = data.get('enddate')

        if not all([trip_name, user_id_input is not None, country_id_input is not None]):
            trip_ns.abort(400, "trip_name, user_id, and country_id are required for update.")

        with get_db() as conn:
            current_trip = conn.execute('SELECT user_id FROM Trips WHERE trip_id = ?', (trip_id,)).fetchone()
            if not current_trip:
                trip_ns.abort(404, f"Trip with ID {trip_id} not found, cannot update.")

            # Validate foreign keys for update
            user_exists = conn.execute("SELECT 1 FROM Users WHERE user_id = ?", (user_id_input,)).fetchone()
            if not user_exists:
                trip_ns.abort(400, f"User with ID {user_id_input} (for update) does not exist.")
            country_exists = conn.execute("SELECT 1 FROM Countries WHERE country_id = ?",
                                          (country_id_input,)).fetchone()
            if not country_exists:
                trip_ns.abort(400, f"Country with ID {country_id_input} (for update) does not exist.")

            try:
                conn.execute(
                    '''UPDATE Trips SET trip_name = ?, user_id = ?, country_id = ?, 
                       startdate = ?, enddate = ? WHERE trip_id = ?''',
                    (trip_name, user_id_input, country_id_input, startdate, enddate, trip_id)
                )
                conn.commit()
            except sqlite3.IntegrityError as e:
                if "UNIQUE constraint failed: Trips.user_id, Trips.trip_name" in str(e):
                    trip_ns.abort(409,
                                  f"User (ID: {user_id_input}) already has another trip named '{trip_name}'. Please choose a different name.")
                else:
                    trip_ns.abort(500, f"Database error during trip update: {e}")

            updated_trip = conn.execute('SELECT * FROM Trips WHERE trip_id = ?', (trip_id,)).fetchone()
        if not updated_trip:  # Should be caught if trip didn't exist
            trip_ns.abort(404, f"Trip with ID {trip_id} could not be retrieved after update attempt.")
        return dict(updated_trip)

    @trip_ns.doc('delete_trip_by_id', description="Delete a trip by its unique ID.")
    @trip_ns.response(204, 'Trip deleted successfully.')
    def delete(self, trip_id):
        """Delete a trip by its ID."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM Trips WHERE trip_id = ?', (trip_id,))
            conn.commit()
            if cursor.rowcount == 0:
                trip_ns.abort(404, f"Trip with ID {trip_id} not found, cannot delete.")
        return '', 204