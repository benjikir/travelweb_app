# resources/countries.py
from flask_restx import Namespace, Resource, fields
from db import get_db
import sqlite3

country_ns = Namespace('Countries', description='Country related operations - Create, Update, Delete')

country_model_input = country_ns.model('CountryInput', {
    'country_code3': fields.String(required=True, description='The 3-letter country code', example='USA'),
    'country': fields.String(required=True, description='The name of the country', example='United States'),
    'flag_url': fields.String(description='URL of the country flag'),
    'currency': fields.String(description='Currency used'),
    'continent': fields.String(description='Continent'),
    'capital': fields.String(description='Capital city')
})

country_model_output = country_ns.model('CountryOutput', {
    'country_id': fields.Integer(readonly=True),
    'country_code3': fields.String(required=True),
    'country': fields.String(required=True),
    'flag_url': fields.String(),
    'currency': fields.String(),
    'continent': fields.String(),
    'capital': fields.String()
})

# Removed: CountryAssociatedUsersList class and @country_ns.route('/<int:id>/users')
# as it depended on user_model_output from a non-existent users.py

@country_ns.route('/')
class CountryList(Resource):
    # NO GET for /countries
    @country_ns.doc('create_country')
    @country_ns.expect(country_model_input)
    @country_ns.marshal_with(country_model_output, code=201)
    def post(self):
        """Create a new country"""
        data = country_ns.payload
        with get_db() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    '''INSERT INTO Countries (country_code3, country, flag_url, currency, continent, capital) 
                       VALUES (?, ?, ?, ?, ?, ?)''',
                    (data['country_code3'], data['country'], data.get('flag_url'),
                     data.get('currency'), data.get('continent'), data.get('capital'))
                )
                country_id = cursor.lastrowid
                conn.commit()
            except sqlite3.IntegrityError as e:
                country_ns.abort(409, f"Error creating country: {e}. Country code or name might already exist.")
        with get_db() as conn:
            new_country = conn.execute('SELECT * FROM Countries WHERE country_id = ?', (country_id,)).fetchone()
        if not new_country:
            country_ns.abort(500, "Failed to retrieve country after insertion.")
        return dict(new_country), 201

@country_ns.route('/<int:id>')
@country_ns.response(404, 'Country not found')
@country_ns.param('id', 'The country identifier')
class CountryResource(Resource):
    # NO GET for /countries/{id}
    @country_ns.doc('update_country')
    @country_ns.expect(country_model_input)
    @country_ns.marshal_with(country_model_output)
    def put(self, id):
        """Update a country given its identifier"""
        data = country_ns.payload
        with get_db() as conn:
            try:
                conn.execute(
                    '''UPDATE Countries SET country_code3 = ?, country = ?, flag_url = ?, 
                       currency = ?, continent = ?, capital = ? WHERE country_id = ?''',
                    (data['country_code3'], data['country'], data.get('flag_url'),
                     data.get('currency'), data.get('continent'), data.get('capital'), id)
                )
                conn.commit()
                if conn.changes() == 0:
                    country_ns.abort(404, f"Country {id} not found, cannot update.")
            except sqlite3.IntegrityError as e:
                 country_ns.abort(409, f"Error updating: {e}. Name or code conflict.")
            updated_country = conn.execute('SELECT * FROM Countries WHERE country_id = ?', (id,)).fetchone()
        if not updated_country:
            country_ns.abort(404, "Country not found after update attempt.")
        return dict(updated_country)

    @country_ns.doc('delete_country')
    @country_ns.response(204, 'Country deleted')
    def delete(self, id):
        """Delete a country and its related data via CASCADE"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM Countries WHERE country_id = ?', (id,))
            conn.commit()
            if cursor.rowcount == 0:
                country_ns.abort(404, f"Country {id} not found, cannot delete.")
        return '', 204