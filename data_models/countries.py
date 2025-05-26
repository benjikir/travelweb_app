from flask_restx import Namespace, Resource, fields
import sqlite3

country_ns = Namespace('countries', description='Manage countries in the system')

# Database helper


def get_db_connection():
    conn = sqlite3.connect('travel_webapp.db')
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn



# Swagger API model
country_model = country_ns.model('Country', {
    'country_id': fields.Integer(readonly=True),
    'country_code3': fields.String(required=True, description='Three-letter ISO code'),
    'country': fields.String(required=True, description='Country name'),
    'flag_url': fields.String(description='URL of the country flag image'),
    'currency': fields.String(required=True, description='Currency of the country'),
    'continent': fields.String(description='Continent'),
    'capital': fields.String(description='Capital city')
})



# GET all countries / POST new country
@country_ns.route('/')
class CountryList(Resource):

    @country_ns.marshal_list_with(country_model)
    def get(self):
        """Retrieve all countries"""
        conn = get_db_connection()
        countries = conn.execute('SELECT * FROM Countries').fetchall()
        conn.close()
        return [dict(row) for row in countries]



    @country_ns.expect(country_model)
    def post(self):
        """Add a new country with validation"""
        data = country_ns.payload

        # Manual validation
        if not data.get('country_code3') or len(data['country_code3']) != 3:
            country_ns.abort(400, 'country_code3 must be exactly 3 characters.')

        if not data.get('currency'):
            country_ns.abort(400, 'currency is required.')

        conn = get_db_connection()
        conn.execute(
            '''
            INSERT INTO Countries (country_code3, country, flag_url, currency, continent, capital)
            VALUES (?, ?, ?, ?, ?, ?)
            ''',
            (
                data['country_code3'],
                data['country'],
                data.get('flag_url', ''),
                data['currency'],
                data.get('continent', ''),
                data.get('capital', '')
            )
        )
        conn.commit()
        conn.close()

        return {'message': 'Country was added'}, 201




# GET/PUT/DELETE a specific country by ID
@country_ns.route('/<int:country_id>')
@country_ns.param('country_id', 'The country identifier')
class CountryDetail(Resource):

    @country_ns.marshal_with(country_model)
    def get(self, country_id):
        """Retrieve a single country by its ID"""
        conn = get_db_connection()
        row = conn.execute('SELECT * FROM Countries WHERE country_id = ?', (country_id,)).fetchone()
        conn.close()
        if row is None:
            country_ns.abort(404, 'Country not found')
        return dict(row)





    def delete(self, country_id):
        """Delete a country by its ID"""
        conn = get_db_connection()
        cursor = conn.execute('DELETE FROM Countries WHERE country_id = ?', (country_id,))
        conn.commit()
        rows_deleted = cursor.rowcount
        conn.close()

        if rows_deleted == 0:
            country_ns.abort(404, f'No country with ID {country_id} found.')

        return {'message': f'Country with ID {country_id} was deleted'}, 200





    @country_ns.expect(country_model)
    def put(self, country_id):
        """Update an existing country with validation"""
        data = country_ns.payload

        # Manual validation
        if not data.get('country_code3') or len(data['country_code3']) != 3:
            country_ns.abort(400, 'country_code3 must be exactly 3 characters.')
        if not data.get('country') or not data['country'].isalpha():
            country_ns.abort(400, 'country must contain only letters.')
        if not data.get('currency'):
            country_ns.abort(400, 'currency is required.')

        conn = get_db_connection()
        conn.execute(
            '''
            UPDATE Countries
            SET country_code3 = ?, country = ?, flag_url = ?, currency = ?, continent = ?, capital = ?
            WHERE country_id = ?
            ''',
            (
                data['country_code3'],
                data['country'],
                data.get('flag_url', ''),
                data['currency'],
                data.get('continent', ''),
                data.get('capital', ''),
                country_id
            )
        )
        conn.commit()
        conn.close()

        return {'message': f'Country with ID {country_id} updated'}, 200
