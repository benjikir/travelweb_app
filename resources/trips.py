# resources/trips.py
from flask_restx import Namespace, Resource, fields
from db import get_db
import sqlite3

# --- Models (trip_model_input, trip_model_output) remain the same ---
trip_ns = Namespace('Trips', description='Trip-Routes')

trip_model_input = trip_ns.model('TripInput', {
    'trip_name': fields.String(required=True, description='Name of the trip', example='Summer Vacation', min_length=1,
                               max_length=255),
    'user_id': fields.Integer(required=True, description='ID of the user who owns the trip', example=1),
    'country_id': fields.Integer(required=True, description='ID of the country for the trip', example=1),
    'startdate': fields.String(description='Start date (YYYY-MM-DD)', example='2024-07-01'),
    'enddate': fields.String(description='End date (YYYY-MM-DD)', example='2024-07-15')
})

trip_model_output = trip_ns.model('TripOutput', {
    'trip_id': fields.Integer(readonly=True),
    'trip_name': fields.String(),
    'user_id': fields.Integer(),
    'country_id': fields.Integer(),
    'startdate': fields.String(),
    'enddate': fields.String()
})


@trip_ns.route('/')
class TripList(Resource):
    @trip_ns.doc('list_trips_for_user', params={'user_id': 'Filter trips by user ID (optional)'})
    @trip_ns.marshal_list_with(trip_model_output)
    def get(self):
        """List all trips, or filter by user_id if provided as a query parameter."""
        parser = trip_ns.parser()
        parser.add_argument('user_id', type=int, help='User ID to filter trips for', location='args')
        args = parser.parse_args()
        user_id_filter = args.get('user_id')

        with get_db() as conn:
            if user_id_filter is not None:
                trips = conn.execute('SELECT * FROM Trips WHERE user_id = ? ORDER BY trip_name ASC',
                                     (user_id_filter,)).fetchall()
            else:
                trips = conn.execute('SELECT * FROM Trips ORDER BY trip_name ASC').fetchall()
        return [dict(row) for row in trips]

    @trip_ns.doc('create_trip')
    @trip_ns.expect(trip_model_input)
    @trip_ns.marshal_with(trip_model_output, code=201)
    def post(self):
        """Create a new trip. A user cannot have two trips with the same name."""
        data = trip_ns.payload
        trip_name = data.get('trip_name', '').strip()
        user_id_input = data.get('user_id')
        country_id_input = data.get('country_id')
        startdate = data.get('startdate')
        enddate = data.get('enddate')

        if not all([trip_name, user_id_input is not None, country_id_input is not None]):
            trip_ns.abort(400, "trip_name, user_id, and country_id are required.")

        with get_db() as conn:
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
                if "UNIQUE constraint failed: Trips.user_id, Trips.trip_name" in str(
                        e):  # Check for specific constraint
                    trip_ns.abort(409,
                                  f"User (ID: {user_id_input}) already has a trip named '{trip_name}'. Please choose a different name.")
                else:
                    trip_ns.abort(500, f"Database error: {e}")

        with get_db() as conn:
            new_trip = conn.execute('SELECT * FROM Trips WHERE trip_id = ?', (trip_id,)).fetchone()
        if not new_trip:
            trip_ns.abort(500, "Failed to retrieve trip after creation.")
        return dict(new_trip), 201


@trip_ns.route('/<int:id>')
@trip_ns.response(404, 'Trip not found')
@trip_ns.param('id', 'The trip identifier')
class TripResource(Resource):
    @trip_ns.doc('get_trip')
    @trip_ns.marshal_with(trip_model_output)
    def get(self, id):
        """Fetch a specific trip by its ID."""
        with get_db() as conn:
            trip = conn.execute('SELECT * FROM Trips WHERE trip_id = ?', (id,)).fetchone()
        if trip is None:
            trip_ns.abort(404, f"Trip with ID {id} not found.")
        return dict(trip)

    @trip_ns.doc('update_trip')
    @trip_ns.expect(trip_model_input)  # Note: user_id in payload for PUT is debatable for ownership
    @trip_ns.marshal_with(trip_model_output)
    def put(self, id):
        """Update an existing trip. A user cannot have two trips with the same name."""
        data = trip_ns.payload
        trip_name = data.get('trip_name', '').strip()
        # For PUT, typically user_id and country_id might not be updatable or require special permission.
        # Here, we assume they can be updated, but the user_id in the payload must match the trip's owner for the unique check.
        user_id_input = data.get('user_id')
        country_id_input = data.get('country_id')
        startdate = data.get('startdate')
        enddate = data.get('enddate')

        if not all([trip_name, user_id_input is not None, country_id_input is not None]):
            trip_ns.abort(400, "trip_name, user_id, and country_id are required for update.")

        with get_db() as conn:
            # Verify trip exists
            current_trip = conn.execute('SELECT user_id FROM Trips WHERE trip_id = ?', (id,)).fetchone()
            if not current_trip:
                trip_ns.abort(404, f"Trip with ID {id} not found.")

            # Important: If user_id can be changed, this logic might need adjustment.
            # For this unique check, we are assuming the user_id submitted in the payload
            # is the one against which the uniqueness of trip_name should be checked.
            # If user_id in payload is different from current_trip['user_id'], it implies reassigning ownership.
            # The UNIQUE constraint (user_id, trip_name) will apply to the NEW user_id if it's changed.
            # Here we assume the data['user_id'] is the intended owner.

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
                    (trip_name, user_id_input, country_id_input, startdate, enddate, id)
                )
                conn.commit()
            except sqlite3.IntegrityError as e:
                if "UNIQUE constraint failed: Trips.user_id, Trips.trip_name" in str(e):
                    trip_ns.abort(409,
                                  f"User (ID: {user_id_input}) already has another trip named '{trip_name}'. Please choose a different name.")
                else:
                    trip_ns.abort(500, f"Database error during update: {e}")

            updated_trip = conn.execute('SELECT * FROM Trips WHERE trip_id = ?', (id,)).fetchone()
        if not updated_trip:
            trip_ns.abort(404, "Failed to retrieve trip after update.")  # Should be caught if trip didn't exist
        return dict(updated_trip)

    @trip_ns.doc('delete_trip')
    @trip_ns.response(204, 'Trip deleted successfully')
    def delete(self, id):
        """Delete a trip by its ID."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM Trips WHERE trip_id = ?', (id,))
            conn.commit()
            if cursor.rowcount == 0:
                trip_ns.abort(404, f"Trip with ID {id} not found, cannot delete.")
        return '', 204