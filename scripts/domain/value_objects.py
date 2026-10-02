"""Value objects wrapping domain primitives for Nilton Corretor de Imóveis."""

from dataclasses import dataclass
from scripts.domain.exceptions import (
    InvalidPriceException,
    InvalidPropertyCodeException,
)


@dataclass(frozen=True)
class ListingPrice:
    """Represents a validated monetary price in Brazilian Reais."""

    amount: float

    def __post_init__(self) -> None:
        """Validate non-negative monetary amount."""
        if self.amount < 0.0:
            raise InvalidPriceException(f"Price cannot be negative: {self.amount}")

    def format_brl(self) -> str:
        """Format the monetary amount into Brazilian currency string."""
        formatted_number = f"{self.amount:,.2f}"
        localized = formatted_number.replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {localized}"

    def is_zero(self) -> bool:
        """Check if price is zero."""
        return self.amount == 0.0

    def value(self) -> float:
        """Return raw numeric value."""
        return self.amount


@dataclass(frozen=True)
class PropertyCode:
    """Represents a unique real estate listing business code."""

    identifier: str

    def __post_init__(self) -> None:
        """Validate non-empty code identifier."""
        cleaned = self.identifier.strip()
        if not cleaned:
            raise InvalidPropertyCodeException("Property code cannot be empty.")

    def value(self) -> str:
        """Return clean identifier string."""
        return self.identifier.strip()

    def __str__(self) -> str:
        """String representation."""
        return self.value()


@dataclass(frozen=True)
class GeoCoordinate:
    """Represents geographical latitude and longitude coordinates."""

    latitude: float
    longitude: float

    def is_valid(self) -> bool:
        """Check if coordinates fall within real geospatial bounds."""
        if self.latitude == 0.0 and self.longitude == 0.0:
            return False
        is_lat_valid = -90.0 <= self.latitude <= 90.0
        is_lng_valid = -180.0 <= self.longitude <= 180.0
        return is_lat_valid and is_lng_valid

    def format_coordinates(self) -> str:
        """Return coordinates formatted as string."""
        return f"({self.latitude:.6f}, {self.longitude:.6f})"
