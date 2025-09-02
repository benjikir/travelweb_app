# resources/trips.py
from flask_restx import Namespace, Resource, fields, reqparse
from db import get_db
import sqlite3

trip_ns = Namespace('trips', description='Operations for managing trips')

# --- MODELLE ANGEPASST AN DIE DATENBANK-STRUKTUR ---
# Dieses Modell definiert, welche Daten wir von außen (Frontend) akzeptieren.
trip_model_input = trip_ns.model('TripInput', {
    'trip_name': fields.String(required=True, description='Name of the trip'),
    'user_id': fields.Integer(required=True, description='ID of the user'),
    'country_id': fields.Integer(required=True, description='ID of the country'),
    'location_id': fields.Integer(description='Optional ID of a specific location'),
    'startdate': fields.String(required=True, description='Start date (YYYY-MM-DD)'),
    'enddate': fields.String(required=True, description='End date (YYYY-MM-DD)'),
    'notes': fields.String(description='Optional notes for the trip')
})

# Dieses Modell definiert, wie die Daten an das Frontend zurückgeschickt werden.
trip_model_output = trip_ns.model('TripOutput', {
    'trip_id': fields.Integer(readonly=True),
    'trip_name': fields.String(),
    'user_id': fields.Integer(),
    'country_id': fields.Integer(),
    'location_id': fields.Integer(),
    'startdate': fields.String(),
    'enddate': fields.String(),
    'notes': fields.String()
})

# Parser für Query-Parameter (für GET-Anfragen)
trip_get_parser = reqparse.RequestParser()
trip_get_parser.add_argument('user_id', type=int, location='args', help='Filter trips by user ID')


@trip_ns.route('/')
class TripList(Resource):
    @trip_ns.doc('list_trips')
    @trip_ns.expect(trip_get_parser)
    @trip_ns.marshal_list_with(trip_model_output)
    def get(self):
        """List all trips (optionally filtered by user ID)."""
        args = trip_get_parser.parse_args()
        user_id = args.get('user_id')

        with get_db() as conn:
            if user_id is not None:
                trips = conn.execute(
                    'SELECT * FROM Trips WHERE user_id = ? ORDER BY startdate ASC',
                    (user_id,)
                ).fetchall()
            else:
                trips = conn.execute('SELECT * FROM Trips ORDER BY startdate ASC').fetchall()
        return [dict(trip) for trip in trips]

    @trip_ns.doc('create_trip')
    @trip_ns.expect(trip_model_input)
    @trip_ns.marshal_with(trip_model_output, code=201)
    def post(self):
        """Create a new trip"""
        data = trip_ns.payload

        trip_name = data.get('trip_name', '').strip()
        user_id = data.get('user_id')
        country_id = data.get('country_id')
        location_id = data.get('location_id')
        startdate = data.get('startdate')
        enddate = data.get('enddate')
        notes = data.get('notes')

        if not all([trip_name, user_id is not None, country_id is not None, startdate, enddate]):
            trip_ns.abort(400, "trip_name, user_id, country_id, startdate, and enddate are required.")

        with get_db() as conn:
            # Foreign-Key-Prüfungen
            user_exists = conn.execute("SELECT 1 FROM Users WHERE user_id = ?", (user_id,)).fetchone()
            if not user_exists:
                trip_ns.abort(400, f"User with ID {user_id} does not exist.")

            country_exists = conn.execute("SELECT 1 FROM Countries WHERE country_id = ?", (country_id,)).fetchone()
            if not country_exists:
                trip_ns.abort(400, f"Country with ID {country_id} does not exist.")

            if location_id is not None:
                location_exists = conn.execute("SELECT 1 FROM Locations WHERE location_id = ?",
                                               (location_id,)).fetchone()
                if not location_exists:
                    trip_ns.abort(400, f"Location with ID {location_id} does not exist.")

            cursor = conn.cursor()
            try:
                # --- INSERT-BEFEHL FINAL KORRIGIERT ---
                cursor.execute(
                    '''INSERT INTO Trips (trip_name, user_id, country_id, location_id, startdate, enddate, notes)
                       VALUES (?, ?, ?, ?, ?, ?, ?)''',
                    (trip_name, user_id, country_id, location_id, startdate, enddate, notes)
                )
                trip_id = cursor.lastrowid
                conn.commit()
            except sqlite3.IntegrityError as e:
                if "UNIQUE constraint failed" in str(e):
                    trip_ns.abort(409, f"User (ID: {user_id}) already has a trip named '{trip_name}'.")
                else:
                    trip_ns.abort(500, f"Database integrity error: {e}")
            except Exception as e:
                trip_ns.abort(500, f"An unexpected database error occurred: {e}")

        with get_db() as conn:
            new_trip = conn.execute('SELECT * FROM Trips WHERE trip_id = ?', (trip_id,)).fetchone()

        if new_trip is None:
            trip_ns.abort(500, "Failed to retrieve the trip after creation.")

        return dict(new_trip), 201


@trip_ns.route('/<int:trip_id>')
@trip_ns.response(404, 'Trip not found')
@trip_ns.param('trip_id', 'The unique identifier of the trip')
class TripResource(Resource):
    @trip_ns.doc('get_trip')
    @trip_ns.marshal_with(trip_model_output)
    def get(self, trip_id):
        """Fetch a specific trip by ID"""
        with get_db() as conn:
            trip = conn.execute('SELECT * FROM Trips WHERE trip_id = ?', (trip_id,)).fetchone()
        if not trip:
            trip_ns.abort(404, f"Trip with ID {trip_id} not found.")
        return dict(trip)

    @trip_ns.doc('update_trip')
    @trip_ns.expect(trip_model_input)
    @trip_ns.marshal_with(trip_model_output)
    def put(self, trip_id):
        """Update an existing trip"""
        data = trip_ns.payload
        trip_name = data.get('trip_name')
        user_id = data.get('user_id')
        country_id = data.get('country_id')
        location_id = data.get('location_id')
        startdate = data.get('startdate')
        enddate = data.get('enddate')
        notes = data.get('notes')

        with get_db() as conn:
            if not conn.execute('SELECT 1 FROM Trips WHERE trip_id = ?', (trip_id,)).fetchone():
                trip_ns.abort(404, f"Trip with ID {trip_id} not found.")

            try:
                conn.execute(
                    '''UPDATE Trips
                       SET trip_name   = ?,
                           user_id     = ?,
                           country_id  = ?,
                           location_id = ?,
                           startdate   = ?,
                           enddate     = ?,
                           notes       = ?
                       WHERE trip_id = ?''',
                    (trip_name, user_id, country_id, location_id, startdate, enddate, notes, trip_id)
                )
                conn.commit()
            except Exception as e:
                trip_ns.abort(500, f"Database error on update: {e}")

        with get_db() as conn:
            updated_trip = conn.execute('SELECT * FROM Trips WHERE trip_id = ?', (trip_id,)).fetchone()

        return dict(updated_trip)

    @trip_ns.doc('delete_trip')
    @trip_ns.response(204, 'Trip successfully deleted')
    def delete(self, trip_id):
        """Delete a trip by ID"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM Trips WHERE trip_id = ?', (trip_id,))
            conn.commit()
            if cursor.rowcount == 0:
                trip_ns.abort(404, f"Trip with ID {trip_id} not found.")
        return '', 204