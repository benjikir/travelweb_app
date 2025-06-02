from flask_restx import Namespace, Resource, fields
from db import get_db
import sqlite3

# STEP 1: Rename the Namespace variable
admin_user_country_ns = Namespace('Admin_user_countries', # This string is the prefix for Swagger UI
                                   description='Admin: Manage direct associations (links) between users and countries')

# STEP 2: Use the new Namespace variable for model definition
admin_user_country_link_model = admin_user_country_ns.model('AdminUserCountryLink', { # Optionally rename model
    'user_id': fields.Integer(required=True, description='ID of the user', example=1),
    'country_id': fields.Integer(required=True, description='ID of the country', example=1)
})

# STEP 3: Use the new Namespace variable for routes and decorators
@admin_user_country_ns.route('/')
class AdminUserCountryLinkList(Resource): # Optionally rename class for clarity
    @admin_user_country_ns.doc('list_all_admin_user_country_links') # Update doc name
    @admin_user_country_ns.marshal_list_with(admin_user_country_link_model) # Use updated model name
    def get(self):
        """List all user-country associations."""
        with get_db() as conn:
            links = conn.execute('SELECT user_id, country_id FROM User_countries').fetchall()
        return [dict(row) for row in links]

    @admin_user_country_ns.doc('link_admin_user_country') # Update doc name
    @admin_user_country_ns.expect(admin_user_country_link_model) # Use updated model name
    @admin_user_country_ns.marshal_with(admin_user_country_link_model, code=201) # Use updated model name
    @admin_user_country_ns.response(400, 'Invalid input or User/Country ID does not exist.')
    @admin_user_country_ns.response(409, 'Link already exists.')
    def post(self):
        """Link a user to a country."""
        data = admin_user_country_ns.payload # Use new ns variable
        user_id = data['user_id']
        country_id = data['country_id']

        with get_db() as conn:
            try:
                user_exists = conn.execute("SELECT 1 FROM Users WHERE user_id = ?", (user_id,)).fetchone()
                if not user_exists:
                    admin_user_country_ns.abort(400, f"User with ID {user_id} does not exist.") # Use new ns variable

                country_exists = conn.execute("SELECT 1 FROM Countries WHERE country_id = ?", (country_id,)).fetchone()
                if not country_exists:
                    admin_user_country_ns.abort(400, f"Country with ID {country_id} does not exist.") # Use new ns variable

                conn.execute('INSERT INTO User_countries (user_id, country_id) VALUES (?, ?)', (user_id, country_id))
                conn.commit()
            except sqlite3.IntegrityError:
                admin_user_country_ns.abort(409, # Use new ns variable
                                        f"Link between user {user_id} and country {country_id} might already exist.")
        return {'user_id': user_id, 'country_id': country_id}, 201


@admin_user_country_ns.route('/users/<int:user_id>/countries/<int:country_id>') # Use new ns variable
@admin_user_country_ns.param('user_id', 'The user identifier') # Use new ns variable
@admin_user_country_ns.param('country_id', 'The country identifier') # Use new ns variable
@admin_user_country_ns.response(404, 'Link not found.') # Use new ns variable
class SpecificAdminUserCountryLink(Resource): # Optionally rename class
    @admin_user_country_ns.doc('get_specific_admin_link') # Update doc name
    @admin_user_country_ns.marshal_with(admin_user_country_link_model) # Use updated model name
    def get(self, user_id, country_id):
        """Check if a specific link exists between a user and a country."""
        with get_db() as conn:
            link = conn.execute(
                'SELECT user_id, country_id FROM User_countries WHERE user_id = ? AND country_id = ?',
                (user_id, country_id)
            ).fetchone()
        if not link:
            admin_user_country_ns.abort(404, f"No link found between user {user_id} and country {country_id}.") # Use new ns variable
        return dict(link)

    @admin_user_country_ns.doc('unlink_admin_user_country') # Update doc name
    @admin_user_country_ns.response(204, 'User successfully unlinked from country.') # Use new ns variable
    def delete(self, user_id, country_id):
        """Unlink a specific user from a specific country."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM User_countries WHERE user_id = ? AND country_id = ?', (user_id, country_id))
            conn.commit()
            if cursor.rowcount == 0:
                admin_user_country_ns.abort(404, f"No link found for user {user_id} and country {country_id} to delete.") # Use new ns variable
        return '', 204