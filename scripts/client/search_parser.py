"""Search-card parser and public property URL validation."""

import re
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup, Tag

from scripts.domain.collections import RentalListingCollection, RentalSearchResult
from scripts.domain.entities import (
    ListingCore,
    ListingDetails,
    ListingIdentity,
    ListingMedia,
    ListingPublicLink,
    ListingValuation,
    RentalListing,
)
from scripts.domain.exceptions import InvalidPublicPropertyUrlException
from scripts.domain.value_objects import ListingPrice, PropertyCode

DEFAULT_PUBLIC_BASE_URL = "https://niltoncorretordeimoveis.com.br"


class SearchResultParser:
    """Parse ImobiBrasil rental search cards into adapter entities."""

    def __init__(self, public_base_url: str = DEFAULT_PUBLIC_BASE_URL) -> None:
        """Configure the public site origin for relative card links."""
        self._public_base_url = public_base_url.rstrip("/")
        _validate_public_base(self._public_base_url)

    def parse_search_response(self, html_text: str) -> RentalSearchResult:
        """Extract listings and total result count from search markup."""
        soup = BeautifulSoup(html_text, "html.parser")
        cards = soup.select(".imovelcard")
        items = [self._parse_card(card) for card in cards if _is_listing_card(card)]
        collection = RentalListingCollection(listings=tuple(items))
        total_count = self._extract_total_count(soup, len(items))
        return RentalSearchResult(collection=collection, total_listings_count=total_count)

    def _parse_card(self, card: Tag) -> RentalListing:
        """Convert one result card into a rental listing."""
        url_path = self._extract_card_link(card)
        property_code = _extract_property_code(url_path)
        public_link = resolve_public_property_link(url_path, self._public_base_url, property_code)
        title = self._extract_card_title(card)
        property_type = self._extract_property_type(card)
        price = self._extract_card_price(card)
        location = self._extract_card_location(card)
        media_url = self._extract_card_thumbnail(card)
        return _build_listing(property_code, title, property_type, price, location, media_url, public_link)

    def _extract_card_link(self, card: Tag) -> str:
        """Use the canonical card link or an actual detail anchor."""
        link = str(card.get("data-link", "")).strip()
        if link:
            return link
        anchor = card.select_one(".imovelcard__img")
        if anchor and anchor.get("href"):
            return str(anchor.get("href"))
        raise InvalidPublicPropertyUrlException("Listing card has no recoverable public URL.")

    def _extract_card_title(self, card: Tag) -> str:
        """Read a title from the image or local description."""
        image_link = card.select_one(".imovelcard__img")
        if image_link and image_link.get("title"):
            return str(image_link.get("title")).strip()
        location = card.select_one(".imovelcard__info__local")
        return location.get_text(strip=True) if location else "Imóvel para Locação"

    def _extract_property_type(self, card: Tag) -> str:
        """Read property type from the reference line."""
        reference = card.select_one(".imovelcard__info__ref")
        text = reference.get_text(strip=True) if reference else ""
        return text.split("-")[-1].strip() if "-" in text else "Imóvel"

    def _extract_card_price(self, card: Tag) -> float:
        """Parse a listing price from the result card."""
        node = card.select_one(".imovelcard__valor__valor")
        text = node.get_text(" ", strip=True) if node else ""
        digits = re.sub(r"[^\d]", "", text)
        return float(digits) if digits else 0.0

    def _extract_card_location(self, card: Tag) -> str:
        """Read the card's location label."""
        node = card.select_one(".imovelcard__info__local")
        return node.get_text(strip=True) if node else ""

    def _extract_card_thumbnail(self, card: Tag) -> str:
        """Read the thumbnail URL without changing its source."""
        image = card.select_one(".imovelcard__img img")
        return str(image.get("src", "")) if image else ""

    def _extract_total_count(self, soup: BeautifulSoup, page_count: int) -> int:
        """Infer total matches or fall back to the current page count."""
        match = re.search(r"(\d+)\s+im[óo]veis\s+encontrados", soup.get_text(" ", strip=True), re.IGNORECASE)
        return int(match.group(1)) if match else page_count


def _build_listing(
    property_code: str,
    title: str,
    property_type: str,
    price: float,
    location: str,
    media_url: str,
    public_link: ListingPublicLink,
) -> RentalListing:
    """Compose domain values for a parsed search listing."""
    identity = ListingIdentity(code=PropertyCode(property_code), title=title)
    valuation = ListingValuation(rental_price=ListingPrice(price), property_type=property_type)
    core = ListingCore(identity=identity, valuation=valuation)
    media = ListingMedia(media_url=media_url, public_link=public_link)
    details = ListingDetails(location_summary=location, media=media)
    return RentalListing(core=core, details=details)


def _is_listing_card(card: Tag) -> bool:
    """Ignore pagination wrappers but include malformed result cards."""
    return bool(card.get("data-link") or card.select_one(".imovelcard__info"))


def _extract_property_code(url_path: str) -> str:
    """Extract a numeric public property identifier from a card URL."""
    try:
        path = urlsplit(url_path).path
    except ValueError as error:
        raise InvalidPublicPropertyUrlException(
            f"Listing card has malformed public URL '{url_path}'."
        ) from error
    segments = [segment for segment in path.strip("/").split("/") if segment]
    if len(segments) > 1 and segments[0] == "imovel" and segments[1].isdigit():
        return segments[1]
    return ""


def resolve_public_property_link(
    url_path: str, public_base_url: str, property_code: str
) -> ListingPublicLink:
    """Resolve a card link and reject destinations outside public property pages."""
    if not url_path.strip():
        raise InvalidPublicPropertyUrlException(
            f"Property '{property_code}' has an empty public URL path."
        )
    try:
        return _resolve_public_property_link(url_path, public_base_url, property_code)
    except ValueError as error:
        if isinstance(error, InvalidPublicPropertyUrlException):
            raise
        raise InvalidPublicPropertyUrlException(
            f"Property '{property_code}' has malformed public URL '{url_path}'."
        ) from error


def _resolve_public_property_link(
    url_path: str, public_base_url: str, property_code: str
) -> ListingPublicLink:
    """Join a card path to the configured origin and validate its route."""
    base = urlsplit(public_base_url)
    _validate_public_parts(base, public_base_url, property_code)
    absolute_url = urljoin(f"{public_base_url.rstrip('/')}/", url_path)
    target = urlsplit(absolute_url)
    _validate_public_parts(target, url_path, property_code)
    _validate_property_target(base, target, url_path, property_code)
    return ListingPublicLink(url_path=url_path, url=absolute_url)


def _validate_public_base(public_base_url: str) -> None:
    """Fail fast when the configured public site origin is invalid."""
    base = urlsplit(public_base_url)
    _validate_public_parts(base, public_base_url, "configuration")


def _validate_public_parts(parsed_url, source: str, property_code: str) -> None:
    """Require an HTTP(S) URL with a hostname."""
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.hostname:
        raise InvalidPublicPropertyUrlException(
            f"Property '{property_code}' has invalid public URL '{source}'."
        )
    _ = parsed_url.port  # Accessing it validates the configured port range.


def _validate_property_target(base, target, url_path: str, property_code: str) -> None:
    """Require the configured portal host and a numeric property route."""
    base_host = _normalized_host(base.hostname)
    target_host = _normalized_host(target.hostname)
    segments = [segment for segment in target.path.split("/") if segment]
    is_property_path = len(segments) > 1 and segments[0] == "imovel" and segments[1].isdigit()
    if base_host != target_host or base.port != target.port or not is_property_path:
        raise InvalidPublicPropertyUrlException(
            f"Property '{property_code}' has invalid public URL '{url_path}'."
        )


def _normalized_host(hostname: str | None) -> str:
    """Normalize the portal's optional www subdomain."""
    return (hostname or "").lower().removeprefix("www.")
