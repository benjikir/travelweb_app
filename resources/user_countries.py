# resources/user_countries.py
from flask_restx import Namespace, Resource, fields
from db import get_db
import sqlite3

user_country_ns = Namespace('User_countries',
                            description='Manage direct associations (links) between users and countries')

user_country_link_model = user_country_ns.model('UserCountryLink', {
    'user_id': fields.Integer(required=True, description='ID of the user', example=1),
    'country_id': fields.Integer(required=True, description='ID of the country', example=1)
})

@user_country_ns.route('/')
class UserCountryLinkList(Resource):
    @user_country_ns.doc('list_all_user_country_links')
    @user_country_ns.marshal_list_with(user_country_link_model)
    def get(self):
        """List all user-country associations."""
        with get_db() as conn:
            links = conn.execute('SELECT user_id, country_id FROM User_countries').fetchall()
        return [dict(row) for row in links]

    @user_country_ns.doc('link_user_country')
    @user_country_ns.expect(user_country_link_model)
    @user_country_ns.marshal_with(user_country_link_model, code=201)
    @user_country_ns.response(400, 'Invalid input or User/Country ID does not exist.')
    @user_country_ns.response(409, 'Link already exists.')
    def post(self):
        """Link a user to a country."""
        data = user_country_ns.payload
        user_id = data['user_id']
        country_id = data['country_id']

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
                                        f"Link between user {user_id} and country {country_id} might already exist.")
        return {'user_id': user_id, 'country_id': country_id}, 201


@user_country_ns.route('/users/<int:user_id>/countries/<int:country_id>')
@user_country_ns.param('user_id', 'The user identifier')
@user_country_ns.param('country_id', 'The country identifier')
@user_country_ns.response(404, 'Link not found.')
class SpecificUserCountryLink(Resource):
    @user_country_ns.doc('get_specific_user_country_link')
    @user_country_ns.marshal_with(user_country_link_model)
    def get(self, user_id, country_id):
        """Check if a specific link exists between a user and a country."""
        with get_db() as conn:
            link = conn.execute(
                'SELECT user_id, country_id FROM User_countries WHERE user_id = ? AND country_id = ?',
                (user_id, country_id)
            ).fetchone()
        if not link:
            user_country_ns.abort(404, f"No link found between user {user_id} and country {country_id}.")
        return dict(link)

    @user_country_ns.doc('unlink_user_country')
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