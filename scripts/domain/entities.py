"""Domain entities for rental property listings."""

from dataclasses import dataclass
from urllib.parse import urlsplit

from scripts.domain.exceptions import InvalidPublicPropertyUrlException
from scripts.domain.value_objects import ListingPrice, PropertyCode


@dataclass(frozen=True)
class ListingIdentity:
    """Core identification fields for a listing."""

    code: PropertyCode
    title: str


@dataclass(frozen=True)
class ListingValuation:
    """Monetary and typology valuation for a listing."""

    rental_price: ListingPrice
    property_type: str


@dataclass(frozen=True)
class ListingCore:
    """Combines identification and valuation attributes."""

    identity: ListingIdentity
    valuation: ListingValuation


@dataclass(frozen=True)
class ListingPublicLink:
    """Public property link and its native card path."""

    url_path: str
    url: str


@dataclass(frozen=True)
class ListingMedia:
    """Media metadata composed with the listing's navigation link."""

    media_url: str
    public_link: ListingPublicLink


@dataclass(frozen=True)
class ListingDetails:
    """Supplementary display metadata for a listing."""

    location_summary: str
    media: ListingMedia

    @property
    def media_url(self) -> str:
        """Retain the legacy media URL attribute."""
        media = self.media
        return media.media_url


@dataclass(frozen=True)
class RentalListing:
    """Lightweight rental listing model for search results."""

    core: ListingCore
    details: ListingDetails

    def code(self) -> str:
        """Return business listing code."""
        return self.core.identity.code.value()

    def title(self) -> str:
        """Return public display title."""
        return self.core.identity.title

    def format_summary(self) -> str:
        """Format listing into a readable single-line summary."""
        code_str = self.core.identity.code.value()
        price_str = self.core.valuation.rental_price.format_brl()
        type_str = self.core.valuation.property_type
        loc_str = self.details.location_summary
        return f"[{code_str}] {type_str} em {loc_str} - {price_str}/mês"

    def to_dictionary(self) -> dict:
        """Export entity with public navigation and legacy display fields."""
        details = self.details
        media = details.media
        public_link = media.public_link
        property_code = self.core.identity.code.value()
        if not _is_public_property_url(public_link.url, property_code):
            raise InvalidPublicPropertyUrlException(
                f"Property '{property_code}' has invalid public URL '{public_link.url}'."
            )
        return {
            "code": property_code,
            "title": self.core.identity.title,
            "property_type": self.core.valuation.property_type,
            "rental_price": self.core.valuation.rental_price.value(),
            "rental_price_formatted": self.core.valuation.rental_price.format_brl(),
            "location": details.location_summary,
            "media_url": media.media_url,
            "url_path": public_link.url_path,
            "url": public_link.url,
        }


def _is_public_property_url(url: str, property_code: str) -> bool:
    """Check that a serialized URL is absolute and identifies a property page."""
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
        and path_segments[1] == property_code
    )


@dataclass(frozen=True)
class DetailedProfile:
    """Extended description and attributes for a listing."""

    description: str
    amenities_summary: str


@dataclass(frozen=True)
class RentalPropertyDetail:
    """Detailed rental property view."""

    listing: RentalListing
    profile: DetailedProfile

    def format_detailed_view(self) -> str:
        """Format full property information into structured text."""
        summary = self.listing.format_summary()
        amenities = self.profile.amenities_summary
        description = self.profile.description
        return f"{summary}\nComodidades: {amenities}\n\nDescrição:\n{description}"

    def to_dictionary(self) -> dict:
        """Export detailed property into dictionary representation."""
        base_dict = self.listing.to_dictionary()
        base_dict["amenities"] = self.profile.amenities_summary
        base_dict["description"] = self.profile.description
        return base_dict
