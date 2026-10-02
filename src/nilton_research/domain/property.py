"""Domain models for full property details and media."""

from collections.abc import Iterator
from dataclasses import dataclass, field


@dataclass(frozen=True)
class PropertyPricing:
    """Pricing representation for property."""

    amount: float
    currency: str = "BRL"
    formatted: str = ""


@dataclass(frozen=True)
class PropertyOverview:
    """Core descriptive attributes of a property."""

    property_id: str
    reference_code: str
    title: str
    canonical_url: str
    description: str = ""


@dataclass(frozen=True)
class PropertyLocation:
    """Geographic information for a property."""

    street: str
    neighborhood: str
    city: str
    state: str
    postal_code: str = ""


@dataclass(frozen=True)
class PropertySpecs:
    """Physical specifications and features of a property."""

    bedrooms: int | None = None
    suites: int | None = None
    bathrooms: int | None = None
    parking_spaces: int | None = None
    total_area: float | None = None
    features: tuple[str, ...] = field(default_factory=tuple)


class PhotoGallery:
    """First-class collection representing property photo gallery."""

    def __init__(self, photo_urls: tuple[str, ...]) -> None:
        """Initialize photo gallery with photo URLs."""
        self._urls = photo_urls

    def first_photo(self) -> str:
        """Return the first photo or empty string."""
        if not self._urls:
            return ""
        return self._urls[0]

    def is_empty(self) -> bool:
        """Check if gallery has no photos."""
        return len(self._urls) == 0

    def __len__(self) -> int:
        """Return count of photos in gallery."""
        return len(self._urls)

    def __iter__(self) -> Iterator[str]:
        """Iterate over photo URLs."""
        return iter(self._urls)

    def __getitem__(self, index: int | slice) -> str | tuple[str, ...]:
        """Access photo by index."""
        return self._urls[index]


@dataclass(frozen=True)
class PropertyIdentityBundle:
    """Bundle containing overview and pricing."""

    overview: PropertyOverview
    pricing: PropertyPricing


@dataclass(frozen=True)
class PropertyContentBundle:
    """Bundle containing location, specs, and photos."""

    location: PropertyLocation
    specs: PropertySpecs
    gallery: PhotoGallery = field(default_factory=lambda: PhotoGallery(()))


class PropertyDetail:
    """Aggregate root representing comprehensive property details."""

    def __init__(
        self,
        identity: PropertyIdentityBundle,
        content: PropertyContentBundle,
    ) -> None:
        """Initialize detail aggregate."""
        self._identity = identity
        self._content = content

    @property
    def overview(self) -> PropertyOverview:
        """Return overview information."""
        return self._identity.overview

    @property
    def pricing(self) -> PropertyPricing:
        """Return pricing details."""
        return self._identity.pricing

    @property
    def location(self) -> PropertyLocation:
        """Return location details."""
        return self._content.location

    @property
    def specs(self) -> PropertySpecs:
        """Return physical specs."""
        return self._content.specs

    @property
    def gallery(self) -> PhotoGallery:
        """Return photo gallery."""
        return self._content.gallery
