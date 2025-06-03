# resources/__init__.py
from .users import user_ns
from .countries import country_ns
from .locations import location_ns
from .trips import trip_ns
from .user_countries import user_country_ns # Assuming you reverted to this name

__all__ = [
    'user_ns',
    'country_ns',
    'location_ns',
    'trip_ns',
    'user_country_ns'
]