"""Domain models for portal geographic taxonomy and metadata."""

from collections.abc import Iterator
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Neighborhood:
    """Neighborhood entity."""

    name: str
    slug: str
    numeric_id: str | None = None


@dataclass(frozen=True)
class City:
    """Municipality entity with nested neighborhoods."""

    name: str
    slug: str
    neighborhoods: tuple[Neighborhood, ...] = field(default_factory=tuple)

    def find_neighborhood_by_slug(self, slug: str) -> Neighborhood | None:
        """Find neighborhood matching given slug."""
        for neighborhood in self.neighborhoods:
            if neighborhood.slug == slug:
                return neighborhood
        return None


class LocationCatalog:
    """First-class collection representing the complete portal location taxonomy."""

    def __init__(self, cities: tuple[City, ...]) -> None:
        """Initialize location catalog."""
        self._cities = cities

    def find_city_by_slug(self, slug: str) -> City | None:
        """Find city matching slug."""
        for city in self._cities:
            if city.slug == slug:
                return city
        return None

    def __len__(self) -> int:
        """Return total cities."""
        return len(self._cities)

    def __iter__(self) -> Iterator[City]:
        """Iterate over cities."""
        return iter(self._cities)

    def __getitem__(self, index: int) -> City:
        """Access city by index."""
        return self._cities[index]
