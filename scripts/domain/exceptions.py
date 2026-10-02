"""Domain exceptions for Nilton Corretor de Imóveis rental research."""


class RentalSearchException(Exception):
    """Base exception for rental search domain errors."""


class InvalidPublicPropertyUrlException(RentalSearchException, ValueError):
    """Raised when a listing link is missing or not a public property route."""


class InvalidPriceException(RentalSearchException):
    """Raised when price amount violates non-negative validation."""


class InvalidPropertyCodeException(RentalSearchException):
    """Raised when property code is empty or invalid."""


class InvalidFilterException(RentalSearchException):
    """Raised when filter constraints are inconsistent."""


class PropertyNotFoundException(RentalSearchException):
    """Raised when requested property cannot be found or redirects."""
