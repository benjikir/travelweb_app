from flask_restx import Namespace, Resource, fields
from db import get_db
import sqlite3

trip_ns = Namespace('trips', description='Operations for managing user trips')

# ✅ Match input keys to Postman JSON
trip_model_input = trip_ns.model('TripInput', {
    'trip_name': fields.String(required=True, description='Name of the trip', example='Summer Vacation in Italy', min_length=1, max_length=255),
    'user_id': fields.Integer(required=True, description='ID of the user who owns the trip', example=1),
    'country_id': fields.Integer(required=True, description='ID of the country for the trip', example=1),
    'start_date': fields.String(description='Start date of the trip (YYYY-MM-DD)', example='2024-07-01'),
    'end_date': fields.String(description='End date of the trip (YYYY-MM-DD)', example='2024-07-15')
})

trip_model_output = trip_ns.model('TripOutput', {
    'trip_id': fields.Integer(readonly=True, description='The unique identifier of the trip'),
    'trip_name': fields.String(description='Name of the trip'),
    'user_id': fields.Integer(description='ID of the user who owns the trip'),
    'country_id': fields.Integer(description='ID of the country for the trip'),
    'start_date': fields.String(description='Start date of the trip'),
    'end_date': fields.String(description='End date of the trip')
})


@trip_ns.route('/')
class TripList(Resource):
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
                    'INSERT INTO Trips (trip_name, user_id, country_id, startdate, enddate) VALUES (?, ?, ?, ?, ?)',
                    (trip_name, user_id_input, country_id_input, start_date, end_date)
                )
                trip_id = cursor.lastrowid
                conn.commit()
            except sqlite3.IntegrityError as e:
                if "UNIQUE constraint failed: Trips.user_id, Trips.trip_name" in str(e):
                    trip_ns.abort(409, f"User (ID: {user_id_input}) already has a trip named '{trip_name}'. Please choose a different name.")
                else:
                    trip_ns.abort(500, f"Database error during trip creation: {e}")

        with get_db() as conn:
            new_trip = conn.execute('SELECT * FROM Trips WHERE trip_id = ?', (trip_id,)).fetchone()
        if not new_trip:
            trip_ns.abort(500, "Internal Server Error: Failed to retrieve trip after creation.")

        # Convert DB column names to match API output
        return {
            'trip_id': new_trip['trip_id'],
            'trip_name': new_trip['trip_name'],
            'user_id': new_trip['user_id'],
            'country_id': new_trip['country_id'],
            'start_date': new_trip['startdate'],
            'end_date': new_trip['enddate']
        }, 201
