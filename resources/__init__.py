from .countries import country_ns
from .locations import location_ns
from .trips import trip_ns
from .admin_user_countries import admin_user_country_ns # Corrected import from new filename

__all__ = [
    'country_ns',
    'location_ns',
    'trip_ns',
    'admin_user_country_ns' # Corrected variable name
]