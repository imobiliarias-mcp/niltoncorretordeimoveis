"""Domain models for search listing cards and collections."""

from collections.abc import Iterator
from dataclasses import asdict, dataclass
from urllib.parse import urlsplit


class InvalidPublicPropertyUrlError(ValueError):
    """Raised when a listing has no valid public property URL."""


@dataclass(frozen=True)
class ListingIdentity:
    """Identifiers and categorization for a property."""

    property_id: str
    url_path: str
    reference_code: str
    property_type: str


@dataclass(frozen=True)
class ListingLocation:
    """Location information for a listing."""

    neighborhood: str
    city: str
    state: str


@dataclass(frozen=True)
class ListingSpecs:
    """Feature specifications for a listing."""

    bedrooms: int | None = None
    suites: int | None = None
    bathrooms: int | None = None
    parking_spaces: int | None = None
    area_description: str | None = None


@dataclass(frozen=True)
class ListingPresentation:
    """Display attributes for a listing card."""

    title: str
    price_text: str
    thumbnail_url: str


@dataclass(frozen=True)
class ListingSummary:
    """Summary of a property listing card."""

    identity: ListingIdentity
    location: ListingLocation
    specs: ListingSpecs
    presentation: ListingPresentation
    url: str = ""

    def to_dictionary(self) -> dict:
        """Serialize listing attributes and its original relative path."""
        property_id = self.identity.property_id
        if not _is_public_property_url(self.url, property_id):
            raise InvalidPublicPropertyUrlError(
                f"Property '{property_id}' has invalid public URL '{self.url}'."
            )
        listing_data = asdict(self)
        listing_data["url_path"] = self.identity.url_path
        return listing_data

    @property
    def title(self) -> str:
        """Shortcut to title."""
        return self.presentation.title

    @property
    def price_text(self) -> str:
        """Shortcut to price text."""
        return self.presentation.price_text

    @property
    def thumbnail_url(self) -> str:
        """Shortcut to thumbnail URL."""
        return self.presentation.thumbnail_url


@dataclass(frozen=True)
class ListingPagination:
    """Pagination metadata for a listing collection."""

    current_page: int
    has_next_page: bool


def _is_public_property_url(url: str, property_id: str) -> bool:
    """Check that the serialized URL is absolute and identifies this property."""
    if not url or url != url.strip():
        return False
    try:
        parsed_url = urlsplit(url)
        port = parsed_url.port
    except ValueError:
        return False
    path_segments = [segment for segment in parsed_url.path.split("/") if segment]
    return (
        parsed_url.scheme in {"http", "https"}
        and bool(parsed_url.hostname)
        and (port is None or 0 <= port <= 65535)
        and len(path_segments) > 1
        and path_segments[0] == "imovel"
        and path_segments[1] == property_id
    )


class ListingCollection:
    """First-class collection wrapping listing results."""

    def __init__(
        self,
        items: tuple[ListingSummary, ...],
        pagination: ListingPagination | None = None,
    ) -> None:
        """Initialize collection."""
        self._items = items
        self._pagination = pagination or ListingPagination(current_page=1, has_next_page=False)

    @property
    def pagination(self) -> ListingPagination:
        """Return pagination metadata."""
        return self._pagination

    def __len__(self) -> int:
        """Return number of listings in collection."""
        return len(self._items)

    def __iter__(self) -> Iterator[ListingSummary]:
        """Iterate over listings."""
        return iter(self._items)

    def __getitem__(self, index: int | slice) -> ListingSummary | tuple[ListingSummary, ...]:
        """Access listing by index or slice."""
        return self._items[index]

    def is_empty(self) -> bool:
        """Check if collection has zero items."""
        return len(self._items) == 0

    def to_dictionary(self) -> dict:
        """Serialize listings without losing pagination metadata."""
        serialized_items = [item.to_dictionary() for item in self._items]
        return {
            "items": serialized_items,
            "pagination": asdict(self._pagination),
        }
