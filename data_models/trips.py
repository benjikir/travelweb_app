from flask_restx import Namespace, Resource, fields
import sqlite3

trip_ns = Namespace('trips', description='Trip-Routes')

trip_model = trip_ns.model('Trip', {
    'trip_id': fields.Integer(readonly=True),
    'trip_name': fields.String(required=True),
    'user_id': fields.Integer(required=True),
    'country_id': fields.Integer(required=True),
    'startdate': fields.String,
    'enddate': fields.String
})

def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@trip_ns.route('/')
class TripList(Resource):
    @trip_ns.marshal_list_with(trip_model)
    def get(self):
        """Alle Trips abrufen"""
        conn = get_db()
        trips = conn.execute('SELECT * FROM Trips').fetchall()
        return [dict(row) for row in trips]

    @trip_ns.expect(trip_model)
    def post(self):
        """Neuen Trip erstellen"""
        data = trip_ns.payload
        conn = get_db()
        conn.execute(
            'INSERT INTO Trips (trip_name, user_id, country_id, startdate, enddate) VALUES (?, ?, ?, ?, ?)',
            (data['trip_name'], data['user_id'], data['country_id'], data['startdate'], data['enddate'])
        )
        conn.commit()
        return {'message': 'Trip was added'}, 201
