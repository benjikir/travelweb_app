from flask_restx import Namespace, Resource, fields
from db import get_db
import sqlite3

trip_ns = Namespace('Trips', description='Trip-Routes')

trip_model_input = trip_ns.model('TripInput', {
    'trip_name': fields.String(required=True, description='Name of the trip', example='Summer Vacation'),
    'user_id': fields.Integer(required=True, description='ID of the user who owns the trip', example=1),
    'country_id': fields.Integer(required=True, description='ID of the country for the trip', example=1),
    'startdate': fields.String(description='Start date of the trip (e.g., YYYY-MM-DD)', example='2024-07-01'),
    'enddate': fields.String(description='End date of the trip (e.g., YYYY-MM-DD)', example='2024-07-15')
})

trip_model_output = trip_ns.model('TripOutput', {
    'trip_id': fields.Integer(readonly=True, description='The trip unique identifier'),
    'trip_name': fields.String(required=True, description='Name of the trip'),
    'user_id': fields.Integer(required=True, description='ID of the user who owns the trip'),
    'country_id': fields.Integer(required=True, description='ID of the country for the trip'),
    'startdate': fields.String(description='Start date of the trip (e.g., YYYY-MM-DD)'),
    'enddate': fields.String(description='End date of the trip (e.g., YYYY-MM-DD)')
})


@trip_ns.route('/')
class TripList(Resource):
    @trip_ns.doc('list_trips')
    @trip_ns.marshal_list_with(trip_model_output)
    def get(self):
        """List all trips"""
        with get_db() as conn:
            trips = conn.execute('SELECT * FROM Trips').fetchall()
        return [dict(row) for row in trips]

    @trip_ns.doc('create_trip')
    @trip_ns.expect(trip_model_input)
    @trip_ns.marshal_with(trip_model_output, code=201)
    def post(self):
        """Create a new trip"""
        data = trip_ns.payload
        with get_db() as conn:
            cursor = conn.cursor()
            try:
                # Ensure user_id and country_id exist before inserting
                user_exists = conn.execute('SELECT 1 FROM Users WHERE user_id = ?', (data['user_id'],)).fetchone()
                country_exists = conn.execute('SELECT 1 FROM Countries WHERE country_id = ?',
                                              (data['country_id'],)).fetchone()

                if not user_exists:
                    trip_ns.abort(400, f"User with ID {data['user_id']} does not exist.")
                if not country_exists:
                    trip_ns.abort(400, f"Country with ID {data['country_id']} does not exist.")

                cursor.execute(
                    'INSERT INTO Trips (trip_name, user_id, country_id, startdate, enddate) VALUES (?, ?, ?, ?, ?)',
                    (data['trip_name'], data['user_id'], data['country_id'], data.get('startdate'), data.get('enddate'))
                )
                trip_id = cursor.lastrowid
                conn.commit()
            except sqlite3.IntegrityError as e:
                trip_ns.abort(400, f"Error creating trip: {e}. Foreign key constraint failed.")

        with get_db() as conn:
            new_trip = conn.execute('SELECT * FROM Trips WHERE trip_id = ?', (trip_id,)).fetchone()
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
            trip_ns.abort(404, f"Trip {id} doesn't exist")
        return dict(trip)

    @trip_ns.doc('update_trip')
    @trip_ns.expect(trip_model_input)
    @trip_ns.marshal_with(trip_model_output)
    def put(self, id):
        """Update a trip given its identifier"""
        data = trip_ns.payload
        with get_db() as conn:
            try:
                user_exists = conn.execute('SELECT 1 FROM Users WHERE user_id = ?', (data['user_id'],)).fetchone()
                country_exists = conn.execute('SELECT 1 FROM Countries WHERE country_id = ?',
                                              (data['country_id'],)).fetchone()

                if not user_exists:
                    trip_ns.abort(400, f"User with ID {data['user_id']} does not exist.")
                if not country_exists:
                    trip_ns.abort(400, f"Country with ID {data['country_id']} does not exist.")

                conn.execute(
                    '''UPDATE Trips 
                       SET trip_name = ?, user_id = ?, country_id = ?, startdate = ?, enddate = ?
                       WHERE trip_id = ?''',
                    (data['trip_name'], data['user_id'], data['country_id'],
                     data.get('startdate'), data.get('enddate'), id)
                )
                conn.commit()
                if conn.changes() == 0:
                    trip_ns.abort(404, f"Trip {id} doesn't exist, cannot update.")
            except sqlite3.IntegrityError as e:
                trip_ns.abort(400, f"Error updating trip: {e}. Foreign key constraint failed.")

            updated_trip = conn.execute('SELECT * FROM Trips WHERE trip_id = ?', (id,)).fetchone()
        return dict(updated_trip)

    @trip_ns.doc('delete_trip')
    @trip_ns.response(204, 'Trip deleted')
    def delete(self, id):
        """Delete a trip given its identifier"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM Trips WHERE trip_id = ?', (id,))
            conn.commit()
            if cursor.rowcount == 0:
                trip_ns.abort(404, f"Trip {id} doesn't exist, cannot delete.")
        return '', 204