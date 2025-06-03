# resources/trips.py
from flask_restx import Namespace, Resource, fields
from db import get_db
import sqlite3

# You might want a date validation helper here if you get more specific with date formats
# from datetime import datetime

trip_ns = Namespace('Trips', description='Trip-Routes')


# Basic date format check (YYYY-MM-DD)
# For more robust validation, use datetime.strptime or a library
def is_valid_iso_date(date_string):
    if not date_string:  # Allow empty if optional
        return True
    try:
        # datetime.strptime(date_string, '%Y-%m-%d') # Stricter check
        parts = date_string.split('-')
        if len(parts) == 3 and len(parts[0]) == 4 and len(parts[1]) == 2 and len(parts[2]) == 2:
            return True
    except ValueError:
        return False
    return False


trip_model_input = trip_ns.model('TripInput', {
    'trip_name': fields.String(required=True, description='Name of the trip', example='Summer Vacation', min_length=2,
                               max_length=255),
    'user_id': fields.Integer(required=True, description='ID of the user who owns the trip', example=1),
    'country_id': fields.Integer(required=True, description='ID of the country for the trip', example=1),
    'startdate': fields.String(description='Start date (YYYY-MM-DD optional)', example='2024-07-01'),
    'enddate': fields.String(description='End date (YYYY-MM-DD optional)', example='2024-07-15')
})

trip_model_output = trip_ns.model('TripOutput', {
    'trip_id': fields.Integer(readonly=True, description='The trip unique identifier'),
    'trip_name': fields.String(required=True),
    'user_id': fields.Integer(required=True),
    'country_id': fields.Integer(required=True),
    'startdate': fields.String(),
    'enddate': fields.String()
})


@trip_ns.route('/')
class TripList(Resource):
    @trip_ns.doc('list_trips')
    @trip_ns.marshal_list_with(trip_model_output)
    def get(self):
        """Retrieve all trips"""
        with get_db() as conn:
            trips = conn.execute('SELECT * FROM Trips ORDER BY trip_name ASC').fetchall()
        return [dict(row) for row in trips]

    @trip_ns.doc('create_trip')
    @trip_ns.expect(trip_model_input)
    @trip_ns.marshal_with(trip_model_output, code=201)
    def post(self):
        """Create a new trip"""
        data = trip_ns.payload
        trip_name = data.get('trip_name', '').strip()
        user_id = data.get('user_id')
        country_id = data.get('country_id')
        startdate = data.get('startdate', '').strip() if data.get('startdate') is not None else None
        enddate = data.get('enddate', '').strip() if data.get('enddate') is not None else None

        if not trip_name:
            trip_ns.abort(400, "Trip name is required.")
        if user_id is None:
            trip_ns.abort(400, "user_id is required.")
        if country_id is None:
            trip_ns.abort(400, "country_id is required.")

        if startdate and not is_valid_iso_date(startdate):
            trip_ns.abort(400, "Invalid startdate format. Use YYYY-MM-DD.")
        if enddate and not is_valid_iso_date(enddate):
            trip_ns.abort(400, "Invalid enddate format. Use YYYY-MM-DD.")

        # Optional: Validate if enddate is after startdate if both are provided
        # if startdate and enddate and enddate < startdate:
        #     trip_ns.abort(400, "End date cannot be before start date.")

        with get_db() as conn:
            user_exists = conn.execute('SELECT 1 FROM Users WHERE user_id = ?', (user_id,)).fetchone()
            if not user_exists:
                trip_ns.abort(400, f"User with ID {user_id} does not exist.")
            country_exists = conn.execute('SELECT 1 FROM Countries WHERE country_id = ?', (country_id,)).fetchone()
            if not country_exists:
                trip_ns.abort(400, f"Country with ID {country_id} does not exist.")

            cursor = conn.cursor()
            try:
                cursor.execute(
                    'INSERT INTO Trips (trip_name, user_id, country_id, startdate, enddate) VALUES (?, ?, ?, ?, ?)',
                    (trip_name, user_id, country_id, startdate, enddate)
                )
                trip_id = cursor.lastrowid
                conn.commit()
            except sqlite3.IntegrityError as e:
                trip_ns.abort(400, f"Database error creating trip: {e}.")

        with get_db() as conn:
            new_trip = conn.execute('SELECT * FROM Trips WHERE trip_id = ?', (trip_id,)).fetchone()
        if not new_trip:
            trip_ns.abort(500, "Internal Server Error: Failed to retrieve trip after insertion.")
        return dict(new_trip), 201


@trip_ns.route('/<int:id>')
@trip_ns.response(404, 'Trip not found')
@trip_ns.param('id', 'The trip identifier')
class TripResource(Resource):
    @trip_ns.doc('get_trip')
    @trip_ns.marshal_with(trip_model_output)
    def get(self, id):
        """Fetch a trip given its identifier"""
        with get_db() as conn:
            trip = conn.execute('SELECT * FROM Trips WHERE trip_id = ?', (id,)).fetchone()
        if trip is None:
            trip_ns.abort(404, f"Trip with ID {id} not found.")
        return dict(trip)

    @trip_ns.doc('update_trip')
    @trip_ns.expect(trip_model_input)
    @trip_ns.marshal_with(trip_model_output)
    def put(self, id):
        """Update a trip given its identifier"""
        data = trip_ns.payload
        trip_name = data.get('trip_name', '').strip()
        user_id = data.get('user_id')
        country_id = data.get('country_id')
        startdate = data.get('startdate', '').strip() if data.get('startdate') is not None else None
        enddate = data.get('enddate', '').strip() if data.get('enddate') is not None else None

        if not trip_name:
            trip_ns.abort(400, "Trip name is required for update.")
        if user_id is None:
            trip_ns.abort(400, "user_id is required for update.")
        if country_id is None:
            trip_ns.abort(400, "country_id is required for update.")

        if startdate and not is_valid_iso_date(startdate):
            trip_ns.abort(400, "Invalid startdate format. Use YYYY-MM-DD.")
        if enddate and not is_valid_iso_date(enddate):
            trip_ns.abort(400, "Invalid enddate format. Use YYYY-MM-DD.")

        with get_db() as conn:
            current_trip = conn.execute('SELECT trip_id FROM Trips WHERE trip_id = ?', (id,)).fetchone()
            if not current_trip:
                trip_ns.abort(404, f"Trip with ID {id} not found, cannot update.")

            user_exists = conn.execute('SELECT 1 FROM Users WHERE user_id = ?', (user_id,)).fetchone()
            if not user_exists:
                trip_ns.abort(400, f"User with ID {user_id} does not exist for update.")
            country_exists = conn.execute('SELECT 1 FROM Countries WHERE country_id = ?', (country_id,)).fetchone()
            if not country_exists:
                trip_ns.abort(400, f"Country with ID {country_id} does not exist for update.")

            try:
                conn.execute(
                    '''UPDATE Trips SET trip_name = ?, user_id = ?, country_id = ?, startdate = ?, enddate = ?
                       WHERE trip_id = ?''',
                    (trip_name, user_id, country_id, startdate, enddate, id)
                )
                conn.commit()
            except sqlite3.IntegrityError as e:
                trip_ns.abort(400, f"Database error updating trip: {e}.")

            updated_trip = conn.execute('SELECT * FROM Trips WHERE trip_id = ?', (id,)).fetchone()
        if not updated_trip:
            trip_ns.abort(404, f"Trip with ID {id} could not be retrieved after update.")
        return dict(updated_trip)

    @trip_ns.doc('delete_trip')
    @trip_ns.response(204, 'Trip deleted successfully')
    def delete(self, id):
        """Delete a trip given its identifier"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM Trips WHERE trip_id = ?', (id,))
            conn.commit()
            if cursor.rowcount == 0:
                trip_ns.abort(404, f"Trip with ID {id} not found, cannot delete.")
        return '', 204