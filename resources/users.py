 # resources/users.py
from flask_restx import Namespace, Resource, fields
from db import get_db  # Assuming db.py is in the parent directory or project root
import sqlite3

user_ns = Namespace('users', description='User administration ')

# --- Main User Models ---
user_model_input = user_ns.model('UserInput', {
    'username': fields.String(required=True, description='The username', example='john_doe', min_length=3,
                              max_length=50),
    'email': fields.String(required=True, description='The user email address', example='john.doe@example.com',
                           pattern=r"[^@]+@[^@]+\.[^@]+"),
    'profile_url': fields.String(description='URL to the user profile picture (optional)',
                                 example='http://example.com/profile.jpg', max_length=2048)
})

user_model_output = user_ns.model('UserOutput', {
    'user_id': fields.Integer(readonly=True, description='The user unique identifier'),
    'username': fields.String(required=True, description='The username'),
    'email': fields.String(required=True, description='The user email address'),
    'profile_url': fields.String(description='URL to the user profile picture'),
    'created_at': fields.String(readonly=True, description='Timestamp of user creation')
})

# --- Model for countries associated with a user (used by the nested route) ---
# This model is defined locally as country_ns is removed.
associated_country_model = user_ns.model('AssociatedCountryInfo', {  # New unique model name
    'country_id': fields.Integer(readonly=True, description='The unique identifier of the country'),
    'country_code3': fields.String(description='The 3-letter ISO code of the country'),
    'country': fields.String(description='The name of the country')
    # Add any other essential country fields you want to display here
    # e.g., 'flag_url': fields.String(description='URL of the country flag')
})


@user_ns.route('/')
class UserList(Resource):
    @user_ns.doc('list_users')
    @user_ns.marshal_list_with(user_model_output)
    @user_ns.doc('create_user')
    @user_ns.expect(user_model_input)
    @user_ns.marshal_with(user_model_output, code=201)
    def post(self):
        """Create a new user."""
        data = user_ns.payload
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        profile_url = data.get('profile_url', '').strip() if data.get('profile_url') is not None else None

        if not username or not email:  # Basic validation
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
                # This catches UNIQUE constraint violations for username or email
                user_ns.abort(409,
                              f"Could not create user. Username ('{username}') or email ('{email}') might already exist. Error: {e}")

        with get_db() as conn:  # Fetch the created user to return it
            new_user = conn.execute('SELECT * FROM Users WHERE user_id = ?', (user_id,)).fetchone()
        if not new_user:  # Should ideally not happen if insert was successful
            user_ns.abort(500, "Internal Server Error: Failed to retrieve user after creation.")
        return dict(new_user), 201


@user_ns.route('/<int:id>')
@user_ns.response(404, 'User not found')
@user_ns.param('id', 'The user identifier')
class UserResource(Resource):
    @user_ns.doc('get_user')
    @user_ns.marshal_with(user_model_output)
    def get(self, id):
        """Fetch a user given their identifier."""
        with get_db() as conn:
            user = conn.execute('SELECT * FROM Users WHERE user_id = ?', (id,)).fetchone()
        if user is None:
            user_ns.abort(404, f"User with ID {id} not found.")
        return dict(user)

    @user_ns.doc('update_user')
    @user_ns.expect(user_model_input)
    @user_ns.marshal_with(user_model_output)
    def put(self, id):
        """Update a user given their identifier."""
        data = user_ns.payload
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        profile_url = data.get('profile_url', '').strip() if data.get('profile_url') is not None else None

        if not username or not email:  # Basic validation
            user_ns.abort(400, "Username and email are required for update.")

        with get_db() as conn:
            # Check if user exists before attempting update
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
                              f"Could not update user. Username ('{username}') or email ('{email}') might conflict with another user. Error: {e}")

            updated_user = conn.execute('SELECT * FROM Users WHERE user_id = ?', (id,)).fetchone()
        if not updated_user:  # Should not happen if the initial check passed and no race condition
            user_ns.abort(404, f"User with ID {id} could not be retrieved after update attempt.")
        return dict(updated_user)

    @user_ns.doc('delete_user')
    @user_ns.response(204, 'User deleted successfully')
    def delete(self, id):
        """Delete a user by their identifier. Related data in other tables will be affected due to CASCADE rules."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM Users WHERE user_id = ?', (id,))
            conn.commit()
            if cursor.rowcount == 0:  # No rows were deleted
                user_ns.abort(404, f"User with ID {id} not found, cannot delete.")
        return '', 204


