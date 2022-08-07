"""Init script."""

from .database import Database
from .versions import AMBRE_PACKAGE_INTERNAL_DATABASE_SCHEMA_VERSION, AMBRE_PACKAGE_VERSION

__version__ = AMBRE_PACKAGE_VERSION

__all__ = [
    "AMBRE_PACKAGE_VERSION",
    "AMBRE_PACKAGE_INTERNAL_DATABASE_SCHEMA_VERSION",
    "Database",
]
