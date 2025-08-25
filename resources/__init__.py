from .users import user_ns
from .locations import location_ns
from .trips import trip_ns
from .countries import country_ns
from .user_countries import user_country_ns

# This part was already correct and needs no changes
__all__ = [
    'user_ns',
    'location_ns',
    'trip_ns',
    'user_country_ns',
    'country_ns'
]