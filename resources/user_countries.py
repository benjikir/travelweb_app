# resources/user_countries.py
from flask_restx import Namespace, Resource, fields
from db import get_db
import sqlite3
import pycountry
import re

user_country_ns = Namespace('user_countries',
                            description='Manage direct associations (links) between users and countries')

user_country_link_model = user_country_ns.model('UserCountryLink', {
    'user_id': fields.Integer(required=True, description='ID of the user', example=1),
    'country_id': fields.Integer(required=True, description='ID of the country', example=1)
})

# POST: Create a new link
@user_country_ns.route('')
class UserCountryLinkCreate(Resource):
    @user_country_ns.doc('link_user_country',
                         description="Create a new link associating a user with a country.")
    @user_country_ns.expect(user_country_link_model)
    @user_country_ns.marshal_with(user_country_link_model, code=201)
    @user_country_ns.response(400, 'Invalid input: Required fields missing, or User/Country ID does not exist.')
    @user_country_ns.response(409, 'Conflict: This user-country link already exists.')
    def post(self):
        """Link a user to a country."""
        data = user_country_ns.payload
        user_id = data.get('user_id')
        country_id = data.get('country_id')

        if user_id is None or country_id is None:
            user_country_ns.abort(400, "user_id and country_id are required.")

        with get_db() as conn:
            try:
                user_exists = conn.execute("SELECT 1 FROM Users WHERE user_id = ?", (user_id,)).fetchone()
                if not user_exists:
                    user_country_ns.abort(400, f"User with ID {user_id} does not exist.")

                country_exists = conn.execute("SELECT 1 FROM Countries WHERE country_id = ?", (country_id,)).fetchone()
                if not country_exists:
                    user_country_ns.abort(400, f"Country with ID {country_id} does not exist.")

                conn.execute('INSERT INTO User_countries (user_id, country_id) VALUES (?, ?)', (user_id, country_id))
                conn.commit()
            except sqlite3.IntegrityError:
                user_country_ns.abort(409,
                                        f"Link between user {user_id} and country {country_id} already exists.")
        return {'user_id': user_id, 'country_id': country_id}, 201

# GET: All countries for a specific user
@user_country_ns.route('/<int:user_id>')
@user_country_ns.param('user_id', 'The user identifier')
@user_country_ns.response(404, 'User not found.') # Changed message to reflect user not found
class UserCountriesByUser(Resource):
    @user_country_ns.marshal_list_with(user_country_link_model)
    def get(self, user_id):
        """List all countries associated with a specific user."""
        with get_db() as conn:
            # First check if user exists
            user = conn.execute('SELECT 1 FROM Users WHERE user_id = ?', (user_id,)).fetchone()
            if not user:
                user_country_ns.abort(404, f"User with ID {user_id} not found.")

            links = conn.execute(
                'SELECT user_id, country_id FROM User_countries WHERE user_id = ? ORDER BY country_id',
                (user_id,)
            ).fetchall()

            # Return empty list if no countries found for the user, as per typical REST list endpoints
            return [dict(row) for row in links]

# DELETE: Unlink a specific user from a specific country
@user_country_ns.route('/<int:user_id>/<int:country_id>')
@user_country_ns.param('user_id', 'The user identifier for the link')
@user_country_ns.param('country_id', 'The country identifier for the link')
@user_country_ns.response(404, 'Link not found for the specified user and country ID.')
class SpecificUserCountryLink(Resource):

    @user_country_ns.doc('unlink_user_country',
                         description='Unlink a specific user from a specific country.')
    @user_country_ns.response(204, 'User successfully unlinked from country.')
    def delete(self, user_id, country_id):
        """Unlink a specific user from a specific country."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM User_countries WHERE user_id = ? AND country_id = ?', (user_id, country_id))
            conn.commit()
            if cursor.rowcount == 0:
                user_country_ns.abort(404, f"No link found for user {user_id} and country {country_id} to delete.")
        return '', 204