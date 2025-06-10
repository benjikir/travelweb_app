#resources/countries.py
from flask_restx import Namespace, Resource, fields
from db import get_db
import sqlite3
import pycountry
import re



country_ns = Namespace('Countries', description='Country related operations')

# --- Define some constants for validation ---
MAX_STRING_LENGTH = 255
MAX_URL_LENGTH = 2048
ALLOWED_CONTINENTS = [
    "Africa", "Antarctica", "Asia", "Europe",
    "North America", "Oceania", "South America"
]


def is_valid_url(url_string: str) -> bool:
    if not url_string:
        return True
    regex = re.compile(
        r'^(?:http|ftp)s?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url_string) is not None


country_model_input = country_ns.model('CountryInput', {
    'country_code3': fields.String(required=True, description='The 3-letter country code (ISO 3166-1 alpha-3)',
                                   example='USA', pattern=r'^[A-Za-z]{3}$', min_length=3, max_length=3),
    'country': fields.String(required=True, description='The name of the country', example='United States',
                             min_length=2, max_length=MAX_STRING_LENGTH),
    'flag_url': fields.String(description='URL of the country flag (optional)', example='http://example.com/flag.png',
                              max_length=MAX_URL_LENGTH),
    'currency': fields.String(description='Currency used (optional)', example='USD', min_length=3, max_length=10),
    'continent': fields.String(description='Continent (optional)', example='North America', enum=ALLOWED_CONTINENTS,
                               max_length=MAX_STRING_LENGTH),
    'capital': fields.String(description='Capital city (optional)', example='Washington D.C.',
                             max_length=MAX_STRING_LENGTH)
})

country_model_output = country_ns.model('CountryOutput', {
    'country_id': fields.Integer(readonly=True, description='The country unique identifier'),
    'country_code3': fields.String(required=True),
    'country': fields.String(required=True),
    'flag_url': fields.String(),
    'currency': fields.String(),
    'continent': fields.String(),
    'capital': fields.String()
})


@country_ns.route('/')
class CountryList(Resource):
    # GET for listing all countries (if you want it, otherwise keep commented)
    # @country_ns.doc('list_countries')
    # @country_ns.marshal_list_with(country_model_output)
    # def get(self):
    #     """List all countries"""
    #     with get_db() as conn:
    #         countries = conn.execute('SELECT * FROM Countries ORDER BY country ASC').fetchall()
    #     return [dict(row) for row in countries]

    @country_ns.doc('create_country')
    @country_ns.expect(country_model_input)
    @country_ns.marshal_with(country_model_output, code=201)
    def post(self):
        """Create a new country (with ISO code and other validations)"""
        data = country_ns.payload
        country_code3_input = data.get('country_code3', '').strip().upper()
        country_name_input = data.get('country', '').strip()
        flag_url_input = data.get('flag_url', '').strip() if data.get('flag_url') is not None else None
        currency_input = data.get('currency', '').strip().upper() if data.get('currency') is not None else None
        continent_input = data.get('continent', '').strip() if data.get('continent') is not None else None
        capital_input = data.get('capital', '').strip() if data.get('capital') is not None else None

        if not country_code3_input:
            country_ns.abort(400, "country_code3 is required.")
        country_info = pycountry.countries.get(alpha_3=country_code3_input)
        if country_info is None:
            country_ns.abort(400, f"Invalid ISO 3166-1 alpha-3 country code: '{data.get('country_code3')}'.")

        if not country_name_input:
            country_ns.abort(400, "country name is required.")

        if flag_url_input and not is_valid_url(flag_url_input):
            country_ns.abort(400, f"Invalid flag_url format: '{flag_url_input}'.")

        with get_db() as conn:
            existing_by_code = conn.execute("SELECT country_id FROM Countries WHERE country_code3 = ?",
                                            (country_code3_input,)).fetchone()
            if existing_by_code:
                country_ns.abort(409,
                                 f"Conflict: Country with code '{country_code3_input}' already exists (ID: {existing_by_code['country_id']}).")
            existing_by_name = conn.execute("SELECT country_id FROM Countries WHERE LOWER(country) = ?",
                                            (country_name_input.lower(),)).fetchone()
            if existing_by_name:
                country_ns.abort(409,
                                 f"Conflict: Country with name '{country_name_input}' already exists (ID: {existing_by_name['country_id']}).")

            cursor = conn.cursor()
            try:
                cursor.execute(
                    '''INSERT INTO Countries (country_code3, country, flag_url, currency, continent, capital) 
                       VALUES (?, ?, ?, ?, ?, ?)''',
                    (country_code3_input, country_name_input, flag_url_input, currency_input, continent_input,
                     capital_input)
                )
                country_id = cursor.lastrowid
                conn.commit()
            except sqlite3.IntegrityError as e:
                country_ns.abort(409, f"Database integrity error: {e}.")

        with get_db() as conn:
            new_country = conn.execute('SELECT * FROM Countries WHERE country_id = ?', (country_id,)).fetchone()
        if not new_country:
            country_ns.abort(500, "Internal Server Error: Failed to retrieve country after insertion.")
        return dict(new_country), 201


@country_ns.route('/<int:id>')
@country_ns.response(404, 'Country not found')
@country_ns.param('id', 'The country identifier')
class CountryResource(Resource):
    # GET for a single country (if you want it, otherwise keep commented)
    # @country_ns.doc('get_country')
    # @country_ns.marshal_with(country_model_output)
    # def get(self, id):
    #     """Fetch a specific country by its ID"""
    #     with get_db() as conn:
    #         country = conn.execute('SELECT * FROM Countries WHERE country_id = ?', (id,)).fetchone()
    #     if country is None:
    #         country_ns.abort(404, f"Country with ID {id} not found.")
    #     return dict(country)

    @country_ns.doc('update_country')
    @country_ns.expect(country_model_input)
    @country_ns.marshal_with(country_model_output)
    def put(self, id):
        """Update an existing country"""
        data = country_ns.payload
        country_code3_input = data.get('country_code3', '').strip().upper()
        country_name_input = data.get('country', '').strip()
        flag_url_input = data.get('flag_url', '').strip() if data.get('flag_url') is not None else None
        currency_input = data.get('currency', '').strip().upper() if data.get('currency') is not None else None
        continent_input = data.get('continent', '').strip() if data.get('continent') is not None else None
        capital_input = data.get('capital', '').strip() if data.get('capital') is not None else None

        with get_db() as conn:
            current_country = conn.execute('SELECT * FROM Countries WHERE country_id = ?', (id,)).fetchone()
            if not current_country:
                country_ns.abort(404, f"Country with ID {id} not found, cannot update.")

        if not country_code3_input:
            country_ns.abort(400, "country_code3 is required for update.")
        country_info = pycountry.countries.get(alpha_3=country_code3_input)
        if country_info is None:
            country_ns.abort(400, f"Invalid ISO 3166-1 alpha-3 country code for update: '{data.get('country_code3')}'.")

        if not country_name_input:
            country_ns.abort(400, "country name is required for update.")

        if flag_url_input and not is_valid_url(flag_url_input):
            country_ns.abort(400, f"Invalid flag_url format for update: '{flag_url_input}'.")

        with get_db() as conn:
            existing_by_code = conn.execute(
                "SELECT country_id FROM Countries WHERE country_code3 = ? AND country_id != ?",
                (country_code3_input, id)).fetchone()
            if existing_by_code:
                country_ns.abort(409,
                                 f"Conflict: Another country (ID: {existing_by_code['country_id']}) already has the code '{country_code3_input}'.")
            existing_by_name = conn.execute(
                "SELECT country_id FROM Countries WHERE LOWER(country) = ? AND country_id != ?",
                (country_name_input.lower(), id)).fetchone()
            if existing_by_name:
                country_ns.abort(409,
                                 f"Conflict: Another country (ID: {existing_by_name['country_id']}) already has the name '{country_name_input}'.")

            try:
                conn.execute(
                    '''UPDATE Countries SET country_code3 = ?, country = ?, flag_url = ?, currency = ?, continent = ?, capital = ? 
                       WHERE country_id = ?''',
                    (country_code3_input, country_name_input, flag_url_input, currency_input, continent_input,
                     capital_input, id)
                )
                conn.commit()
            except sqlite3.IntegrityError as e:
                country_ns.abort(409, f"Database integrity error during update: {e}.")

            updated_country = conn.execute('SELECT * FROM Countries WHERE country_id = ?', (id,)).fetchone()
        if not updated_country:
            country_ns.abort(404, f"Country with ID {id} could not be retrieved after update attempt.")
        return dict(updated_country)

    @country_ns.doc('delete_country')
    @country_ns.response(204, 'Country deleted successfully')
    def delete(self, id):
        """Delete a country by its ID."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM Countries WHERE country_id = ?', (id,))
            conn.commit()
            if cursor.rowcount == 0:
                country_ns.abort(404, f"Country with ID {id} not found, cannot delete.")
        return '', 204


# Nested route for /countries/{id}/users
@country_ns.route('/<int:id>/users')
@country_ns.param('id', 'The country identifier')
@country_ns.response(404, 'Country not found')
class CountryAssociatedUsersList(Resource):
    @country_ns.doc('get_users_for_country')
    @country_ns.marshal_list_with(user_model_output)  # Uses user_model_output from users.py
    def get(self, id):
        """Get all users associated with a specific country via the User_countries table."""
        with get_db() as conn:
            country = conn.execute('SELECT 1 FROM Countries WHERE country_id = ?', (id,)).fetchone()
            if not country:
                country_ns.abort(404, f"Country with ID {id} not found.")

            users = conn.execute('''
                SELECT u.user_id, u.username, u.email, u.profile_url, u.created_at 
                FROM Users u
                JOIN User_countries uc ON u.user_id = uc.user_id
                WHERE uc.country_id = ?
                ORDER BY u.username ASC
            ''', (id,)).fetchall()
        return [dict(row) for row in users]

