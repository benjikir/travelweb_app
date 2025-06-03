# resources/users.py
from flask_restx import Namespace, Resource, fields
from db import get_db
import sqlite3

# Import country model if you plan to implement the nested /users/{id}/countries route
# from .countries import country_model_output # Assuming country_model_output is defined in countries.py

user_ns = Namespace('Users', description='User administration')

user_model_input = user_ns.model('UserInput', {
    'username': fields.String(required=True, description='The username', example='john_doe'),
    'email': fields.String(required=True, description='The user email address', example='john.doe@example.com'),
    'profile_url': fields.String(description='URL to the user profile picture (optional)',
                                 example='http://example.com/profile.jpg')
})

user_model_output = user_ns.model('UserOutput', {
    'user_id': fields.Integer(readonly=True, description='The user unique identifier'),
    'username': fields.String(required=True, description='The username'),
    'email': fields.String(required=True, description='The user email address'),
    'profile_url': fields.String(description='URL to the user profile picture'),
    'created_at': fields.String(readonly=True, description='Timestamp of user creation')
})


@user_ns.route('/')
class UserList(Resource):
    @user_ns.doc('list_users')
    @user_ns.marshal_list_with(user_model_output)
    def get(self):
        """List all users"""
        with get_db() as conn:
            users = conn.execute(
                'SELECT user_id, username, email, profile_url, created_at FROM Users ORDER BY username ASC').fetchall()
        return [dict(row) for row in users]

    @user_ns.doc('create_user')
    @user_ns.expect(user_model_input)
    @user_ns.marshal_with(user_model_output, code=201)
    def post(self):
        """Create a new user"""
        data = user_ns.payload
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        profile_url = data.get('profile_url', '').strip() if data.get('profile_url') is not None else None

        if not username or not email:
            user_ns.abort(400, "Username and email are required.")

        with get_db() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    'INSERT INTO Users (username, email, profile_url) VALUES (?, ?, ?)',
                    (username, email, profile_url)
                )
                user_id = cursor.lastrowid
                conn.commit()
            except sqlite3.IntegrityError as e:
                user_ns.abort(409, f"Could not create user. Username or email might already exist. Error: {e}")

        with get_db() as conn:
            new_user = conn.execute('SELECT * FROM Users WHERE user_id = ?', (user_id,)).fetchone()
        if not new_user:
            user_ns.abort(500, "Internal Server Error: Failed to retrieve user after creation.")
        return dict(new_user), 201


@user_ns.route('/<int:id>')
@user_ns.response(404, 'User not found')
@user_ns.param('id', 'The user identifier')
class UserResource(Resource):
    @user_ns.doc('get_user')
    @user_ns.marshal_with(user_model_output)
    def get(self, id):
        """Fetch a user given their identifier"""
        with get_db() as conn:
            user = conn.execute('SELECT * FROM Users WHERE user_id = ?', (id,)).fetchone()
        if user is None:
            user_ns.abort(404, f"User with ID {id} not found.")
        return dict(user)

    @user_ns.doc('update_user')
    @user_ns.expect(user_model_input)
    @user_ns.marshal_with(user_model_output)
    def put(self, id):
        """Update a user given their identifier"""
        data = user_ns.payload
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        profile_url = data.get('profile_url', '').strip() if data.get('profile_url') is not None else None

        if not username or not email:
            user_ns.abort(400, "Username and email are required for update.")

        with get_db() as conn:
            # Check if user exists
            existing_user = conn.execute('SELECT user_id FROM Users WHERE user_id = ?', (id,)).fetchone()
            if not existing_user:
                user_ns.abort(404, f"User with ID {id} not found, cannot update.")
            try:
                conn.execute(
                    'UPDATE Users SET username = ?, email = ?, profile_url = ? WHERE user_id = ?',
                    (username, email, profile_url, id)
                )
                conn.commit()
            except sqlite3.IntegrityError as e:
                user_ns.abort(409,
                              f"Could not update user. Username or email might conflict with another user. Error: {e}")

            updated_user = conn.execute('SELECT * FROM Users WHERE user_id = ?', (id,)).fetchone()
        if not updated_user:  # Should not happen if the initial check passed
            user_ns.abort(404, f"User with ID {id} could not be retrieved after update attempt.")
        return dict(updated_user)

    @user_ns.doc('delete_user')
    @user_ns.response(204, 'User deleted successfully')
    def delete(self, id):
        """Delete a user by their identifier. Related data (trips, locations, user_countries) will also be deleted due to CASCADE."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM Users WHERE user_id = ?', (id,))
            conn.commit()
            if cursor.rowcount == 0:
                user_ns.abort(404, f"User with ID {id} not found, cannot delete.")
        return '', 204


# --- Nested route for /users/{id}/countries ---
# You'll need to import country_model_output from .countries
from .countries import country_model_output  # Make sure this path is correct and model exists


@user_ns.route('/<int:id>/countries')
@user_ns.param('id', 'The user identifier')
@user_ns.response(404, 'User not found')
class UserAssociatedCountriesList(Resource):
    @user_ns.doc('get_countries_for_user')
    @user_ns.marshal_list_with(country_model_output)
    def get(self, id):
        """Get all countries associated with a specific user via the User_countries table."""
        with get_db() as conn:
            user = conn.execute('SELECT 1 FROM Users WHERE user_id = ?', (id,)).fetchone()
            if not user:
                user_ns.abort(404, f"User with ID {id} not found.")

            countries = conn.execute('''
                SELECT c.* FROM Countries c
                JOIN User_countries uc ON c.country_id = uc.country_id
                WHERE uc.user_id = ?
                ORDER BY c.country ASC
            ''', (id,)).fetchall()
        return [dict(row) for row in countries]  # Returns empty list if no associations