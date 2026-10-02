"""Domain value objects wrapping primitives."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PriceRange:
    """Represents a price constraint range in BRL."""

    minimum: int | None = None
    maximum: int | None = None

    def __post_init__(self) -> None:
        """Validate price values."""
        if self.minimum is not None and self.minimum < 0:
            raise ValueError("Minimum price cannot be negative.")
        if self.maximum is not None and self.maximum < 0:
            raise ValueError("Maximum price cannot be negative.")
        if self.minimum and self.maximum and self.minimum > self.maximum:
            raise ValueError("Minimum price cannot exceed maximum price.")

    def query_parameters(self) -> dict[str, str]:
        """Convert to query parameters."""
        params: dict[str, str] = {}
        if self.minimum is not None:
            params["vmi"] = str(self.minimum)
        if self.maximum is not None:
            params["vma"] = str(self.maximum)
        return params


@dataclass(frozen=True)
class AreaRange:
    """Represents an area constraint range in square meters."""

    minimum: int | None = None
    maximum: int | None = None

    def __post_init__(self) -> None:
        """Validate area values."""
        if self.minimum is not None and self.minimum < 0:
            raise ValueError("Minimum area cannot be negative.")
        if self.maximum is not None and self.maximum < 0:
            raise ValueError("Maximum area cannot be negative.")
        if self.minimum and self.maximum and self.minimum > self.maximum:
            raise ValueError("Minimum area cannot exceed maximum area.")

    def query_parameters(self) -> dict[str, str]:
        """Convert to query parameters."""
        params: dict[str, str] = {}
        if self.minimum is not None:
            params["areaMinima"] = str(self.minimum)
        if self.maximum is not None:
            params["areaMaxima"] = str(self.maximum)
        return params


@dataclass(frozen=True)
class RoomCount:
    """Represents a room specification with exact or minimum semantics."""

    count: int
    is_minimum: bool = False

    def __post_init__(self) -> None:
        """Validate room bounds."""
        if self.count < 1 or self.count > 5:
            raise ValueError("Room count must be between 1 and 5.")

    def to_param_code(self) -> str:
        """Encode to portal format (20 + count for minimum)."""
        if self.is_minimum:
            return str(20 + self.count)
        return str(self.count)


@dataclass(frozen=True)
class PageNumber:
    """1-indexed pagination number."""

    value: int = 1

    def __post_init__(self) -> None:
        """Validate page number."""
        if self.value < 1:
            raise ValueError("Page number must be at least 1.")

    def to_param_code(self) -> str:
        """Return string representation."""
        return str(self.value)
