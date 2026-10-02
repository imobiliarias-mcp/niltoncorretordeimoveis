"""Parser for search results listing pages."""

import re
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup, Tag

from nilton_research.domain.listing import (
    InvalidPublicPropertyUrlError,
    ListingCollection,
    ListingIdentity,
    ListingLocation,
    ListingPagination,
    ListingPresentation,
    ListingSummary,
)
from nilton_research.parsers.feature_extractor import FeatureExtractor


class SearchPageParser:
    """Parses server-side rendered HTML into ListingCollection."""

    def __init__(
        self,
        extractor: FeatureExtractor | None = None,
        public_base_url: str = "https://niltoncorretordeimoveis.com.br",
    ) -> None:
        """Initialize parser with feature and public-page collaborators."""
        self._extractor = extractor or FeatureExtractor()
        self._public_base_url = public_base_url.rstrip("/")
        self._validate_public_base()

    def parse(self, html: str, page_number: int = 1) -> ListingCollection:
        """Parse HTML string into listing collection."""
        soup = BeautifulSoup(html, "html.parser")
        card_tags = soup.select(".imovelcard")
        items = [self._parse_card(card) for card in card_tags if self._is_listing_card(card)]
        has_next = self._check_next_page(soup)
        pagination = ListingPagination(current_page=page_number, has_next_page=has_next)
        return ListingCollection(items=tuple(items), pagination=pagination)

    def _parse_card(self, card: Tag) -> ListingSummary:
        """Parse individual card."""
        link = self._extract_card_link(card)
        identity = self._extract_identity(card, link)
        public_url = self._resolve_public_url(link, identity.property_id)
        location = self._extract_location(card)
        specs = self._extractor.extract(card)
        presentation = self._extract_presentation(card)
        return ListingSummary(
            identity=identity,
            location=location,
            specs=specs,
            presentation=presentation,
            url=public_url,
        )

    def _extract_identity(self, card: Tag, link: str) -> ListingIdentity:
        """Extract identifier and native URL path with card attributes."""
        try:
            path = urlsplit(link).path
        except ValueError as error:
            raise InvalidPublicPropertyUrlError(
                f"Listing card has malformed public URL '{link}'."
            ) from error
        parts = path.strip("/").split("/")
        property_id = parts[1] if len(parts) > 1 and parts[0] == "imovel" else ""
        ref_tag = card.select_one(".imovelcard__info__ref")
        ref_text = ref_tag.get_text(strip=True) if ref_tag else ""
        ref_code = self._extract_reference_code(ref_text)
        prop_type = ref_text.split("-")[-1].strip() if "-" in ref_text else ""
        return ListingIdentity(
            property_id=property_id,
            url_path=link,
            reference_code=ref_code,
            property_type=prop_type,
        )

    def _extract_card_link(self, card: Tag) -> str:
        """Return the card path or its actual public detail anchor."""
        link = str(card.get("data-link", "")).strip()
        if link:
            return link
        anchor = card.select_one(".imovelcard__img")
        if anchor and anchor.get("href"):
            return str(anchor.get("href"))
        raise InvalidPublicPropertyUrlError("Listing card has no recoverable public URL.")

    def _is_listing_card(self, card: Tag) -> bool:
        """Include result cards and ignore pagination-only wrappers."""
        return bool(card.get("data-link") or card.select_one(".imovelcard__info"))

    def _validate_public_base(self) -> None:
        """Reject invalid public URL configuration before parsing."""
        base = urlsplit(self._public_base_url)
        if base.scheme not in {"http", "https"} or not base.hostname:
            raise InvalidPublicPropertyUrlError(
                f"Invalid public property URL base '{self._public_base_url}'."
            )

    def _resolve_public_url(self, link: str, property_id: str) -> str:
        """Resolve and validate one public property destination."""
        target = urljoin(f"{self._public_base_url}/", link)
        parsed_target = urlsplit(target)
        self._validate_public_target(parsed_target, property_id, link)
        return target

    def _validate_public_target(self, target, property_id: str, link: str) -> None:
        """Reject non-web, cross-site, or non-property destinations."""
        host_matches = self._same_host(target.hostname)
        segments = [part for part in target.path.split("/") if part]
        is_property = len(segments) > 1 and segments[0] == "imovel" and segments[1].isdigit()
        if target.scheme not in {"http", "https"} or not target.hostname or not host_matches or not is_property:
            raise InvalidPublicPropertyUrlError(
                f"Property '{property_id}' has invalid public URL '{link}'."
            )

    def _same_host(self, hostname: str | None) -> bool:
        """Compare configured and destination portal hostnames."""
        base_hostname = urlsplit(self._public_base_url).hostname or ""
        target_hostname = hostname or ""
        return base_hostname.lower().removeprefix("www.") == target_hostname.lower().removeprefix("www.")

    def _extract_location(self, card: Tag) -> ListingLocation:
        """Extract neighborhood, city, and state."""
        local_tag = card.select_one(".imovelcard__info__local")
        if not local_tag:
            return ListingLocation(neighborhood="", city="", state="")
        text = local_tag.get_text(strip=True)
        neighborhood = text.split(",")[0].strip() if "," in text else ""
        rest = text.split(",")[1].strip() if "," in text else text
        city = rest.split("/")[0].strip() if "/" in rest else rest
        state = rest.split("/")[1].strip() if "/" in rest else ""
        return ListingLocation(neighborhood=neighborhood, city=city, state=state)

    def _extract_presentation(self, card: Tag) -> ListingPresentation:
        """Extract title, price, and thumbnail image."""
        img_link = card.select_one(".imovelcard__img")
        title = img_link.get("title", "") if img_link else ""
        img_tag = card.select_one(".imovelcard__img img")
        thumb = img_tag.get("src", "") if img_tag else ""
        val_tag = card.select_one(".imovelcard__valor__valor")
        price = val_tag.get_text(separator=" ", strip=True) if val_tag else ""
        return ListingPresentation(title=title, price_text=price, thumbnail_url=thumb)

    def _extract_reference_code(self, ref_text: str) -> str:
        """Extract reference code via regex."""
        match = re.search(r"Ref:\s*([A-Za-z0-9_]+)", ref_text)
        if match:
            return match.group(1).strip()
        return ""

    def _check_next_page(self, soup: BeautifulSoup) -> bool:
        """Determine if next page exists."""
        next_btn = soup.select_one('.lista_imoveis_paginacao a[title="Próxima Página"]')
        if next_btn:
            return True
        for a in soup.select(".lista_imoveis_paginacao a"):
            if ">" in a.get_text():
                return True
        return False
