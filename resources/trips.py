# resources/trips.py
from flask_restx import Namespace, Resource, fields, reqparse
from db import get_db
import sqlite3

trip_ns = Namespace('trips', description='Operations for managing trips')

trip_model_input = trip_ns.model('TripInput', {
    'trip_name': fields.String(required=True, description='Name of the trip', example='Paris Vacation', min_length=1, max_length=255),
    'user_id': fields.Integer(required=True, description='ID of the user who owns the trip', example=1),
    'country_id': fields.Integer(required=True, description='ID of the country for the trip', example=1),
    'start_date': fields.String(description='Start date of the trip (YYYY-MM-DD)', example='2025-09-15'),
    'end_date': fields.String(description='End date of the trip (YYYY-MM-DD)', example='2025-09-20')
})

trip_model_output = trip_ns.model('TripOutput', {
    'trip_id': fields.Integer(readonly=True, description='The unique identifier of the trip'),
    'trip_name': fields.String(description='Name of the trip'),
    'user_id': fields.Integer(description='ID of the user who owns the trip'),
    'country_id': fields.Integer(description='ID of the country for the trip'),
    'start_date': fields.String(description='Start date of the trip'),
    'end_date': fields.String(description='End date of the trip')
})

# Parser for query parameters
trip_get_parser = reqparse.RequestParser()
trip_get_parser.add_argument('userId', type=int, location='args', help='Filter trips by user ID')


@trip_ns.route('/')
class TripList(Resource):
    @trip_ns.doc('list_trips')
    @trip_ns.expect(trip_get_parser)
    @trip_ns.marshal_list_with(trip_model_output)
    def get(self): # This method now lists ALL trips or filters by userId
        """List all trips (optionally filtered by user ID)."""
        args = trip_get_parser.parse_args()
        user_id = args.get('userId')

        with get_db() as conn:
            if user_id is not None: # Check for None to allow 0 or valid IDs
                user_exists = conn.execute("SELECT 1 FROM Users WHERE user_id = ?", (user_id,)).fetchone()
                if not user_exists:
                    trip_ns.abort(404, f"User with ID {user_id} does not exist for trip filtering.")

                trips = conn.execute(
                    'SELECT * FROM Trips WHERE user_id = ? ORDER BY startdate ASC',
                    (user_id,)
                ).fetchall()
            else:
                trips = conn.execute('SELECT * FROM Trips ORDER BY startdate ASC').fetchall()

        # Return empty list if no trips found (for listing all or filtering)
        return [dict(trip) for trip in trips]

    @trip_ns.doc('create_trip', description="Add a new trip. A user cannot add two trips with the same name.")
    @trip_ns.expect(trip_model_input)
    @trip_ns.marshal_with(trip_model_output, code=201)
    @trip_ns.response(400, 'Validation Error: Required fields missing or invalid foreign keys.')
    @trip_ns.response(409, 'Conflict: A trip with this name already exists for this user.')
    def post(self):
        """Create a new trip"""
        data = trip_ns.payload
        trip_name = data.get('trip_name', '').strip()
        user_id_input = data.get('user_id')
        country_id_input = data.get('country_id')
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if not all([trip_name, user_id_input is not None, country_id_input is not None]):
            trip_ns.abort(400, "trip_name, user_id, and country_id are required.")

        with get_db() as conn:
            user_exists = conn.execute("SELECT 1 FROM Users WHERE user_id = ?", (user_id_input,)).fetchone()
            if not user_exists:
                trip_ns.abort(400, f"User with ID {user_id_input} does not exist.")

            country_exists = conn.execute("SELECT 1 FROM Countries WHERE country_id = ?", (country_id_input,)).fetchone()
            if not country_exists:
                trip_ns.abort(400, f"Country with ID {country_id_input} does not exist.")

            cursor = conn.cursor()
            try:
                cursor.execute(
                    'INSERT INTO Trips (trip_name, user_id, country_id, start_date, end_date) VALUES (?, ?, ?, ?, ?)',
                    # Spaltennamen mit Unterstrich
                    (trip_name, user_id_input, country_id_input, start_date, end_date)
                )
                trip_id = cursor.lastrowid
                conn.commit()
            except sqlite3.IntegrityError as e:
                if "UNIQUE constraint failed: Trips.user_id, Trips.trip_name" in str(e):
                    trip_ns.abort(409, f"User (ID: {user_id_input}) already has a trip named '{trip_name}'.")
                else:
                    trip_ns.abort(500, f"Database error: {e}")

        with get_db() as conn:
            new_trip = conn.execute('SELECT * FROM Trips WHERE trip_id = ?', (trip_id,)).fetchone()
        return dict(new_trip), 201


@trip_ns.route('/<int:trip_id>')
@trip_ns.response(404, 'Trip not found for the given ID.')
@trip_ns.param('trip_id', 'The unique identifier of the trip')
class TripResource(Resource):
    @trip_ns.marshal_with(trip_model_output)
    def get(self, trip_id):
        """Fetch a specific trip by ID"""
        with get_db() as conn:
            trip = conn.execute('SELECT * FROM Trips WHERE trip_id = ?', (trip_id,)).fetchone()
        if not trip:
            trip_ns.abort(404, f"Trip with ID {trip_id} not found.")
        return dict(trip)

    @trip_ns.expect(trip_model_input)
    @trip_ns.marshal_with(trip_model_output)
    @trip_ns.response(400, 'Validation Error: Required fields missing or invalid foreign keys.')
    @trip_ns.response(404, 'Trip not found.')
    @trip_ns.response(409, 'Conflict: Trip name already exists for this user.')
    def put(self, trip_id):
        """Update an existing trip"""
        data = trip_ns.payload
        trip_name = data.get('trip_name', '').strip()
        user_id_input = data.get('user_id')
        country_id_input = data.get('country_id')
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if not all([trip_name, user_id_input is not None, country_id_input is not None]):
            trip_ns.abort(400, "trip_name, user_id, and country_id are required for update.")

        with get_db() as conn:
            current_trip = conn.execute('SELECT user_id FROM Trips WHERE trip_id = ?', (trip_id,)).fetchone()
            if not current_trip:
                trip_ns.abort(404, f"Trip with ID {trip_id} not found, cannot update.")

            try:
                conn.execute(
                    '''UPDATE Trips SET trip_name = ?, user_id = ?, country_id = ?, startdate = ?, enddate = ?
                       WHERE trip_id = ?''',
                    (trip_name, user_id_input, country_id_input, start_date, end_date, trip_id)
                )
                conn.commit()
            except sqlite3.IntegrityError as e:
                if "UNIQUE constraint failed: Trips.user_id, Trips.trip_name" in str(e):
                    trip_ns.abort(409, f"User (ID: {user_id_input}) already has another trip named '{trip_name}'.")
                else:
                    trip_ns.abort(500, f"Database error: {e}")

            updated_trip = conn.execute('SELECT * FROM Trips WHERE trip_id = ?', (trip_id,)).fetchone()
        if not updated_trip:
            trip_ns.abort(404, f"Trip with ID {trip_id} could not be retrieved after update.")
        return dict(updated_trip)

    @trip_ns.doc('delete_trip')
    @trip_ns.response(204, 'Trip deleted successfully')
    @trip_ns.response(404, 'Trip not found.')
    def delete(self, trip_id):
        """Delete a trip by ID"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM Trips WHERE trip_id = ?', (trip_id,))
            conn.commit()
            if cursor.rowcount == 0:
                trip_ns.abort(404, f"Trip with ID {trip_id} not found, cannot delete.")
        return '', 204

# Removed the UserTrips class and its route /user/<int:user_id>
# This endpoint is no longer supported directly.