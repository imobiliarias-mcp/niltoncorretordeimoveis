"""Network gateway and parser suite collaborators for rental research client."""

from nilton_research.domain.criteria import SearchCriteria
from nilton_research.infrastructure.http_client import (
    HttpClientProtocol,
    HttpResponse,
    HttpxHttpClient,
    PropertyNotFoundError,
)
from nilton_research.infrastructure.url_builder import UrlBuilder
from nilton_research.parsers.detail_parser import PropertyDetailParser
from nilton_research.parsers.metadata_parser import MetadataParser
from nilton_research.parsers.photo_parser import PhotoGalleryParser
from nilton_research.parsers.search_parser import SearchPageParser


class RentalNetworkGateway:
    """Dispatches HTTP requests for rental searches, details, and photos."""

    def __init__(
        self,
        http_client: HttpClientProtocol | None = None,
        url_builder: UrlBuilder | None = None,
    ) -> None:
        """Initialize gateway with network client and URL builder."""
        self._http = http_client or HttpxHttpClient()
        self._builder = url_builder or UrlBuilder()

    def fetch_search(self, criteria: SearchCriteria) -> HttpResponse:
        """Fetch search results page for given criteria."""
        url = self._builder.build_search_url(criteria)
        return self._http.get(url)

    def fetch_detail(self, property_id: str) -> HttpResponse:
        """Fetch detail page for a given property ID."""
        url = self._builder.build_detail_url(property_id)
        resp = self._http.get(url)
        self._validate_property_response(resp, property_id)
        return resp

    def fetch_photos(self, property_id: str) -> HttpResponse:
        """Fetch photos JSON payload for a given property ID."""
        url = self._builder.build_photos_url(property_id)
        return self._http.get(url)

    def _validate_property_response(self, resp: HttpResponse, property_id: str) -> None:
        """Validate that response did not redirect to root landing page."""
        final_url = resp.final_url.rstrip("/")
        if final_url.endswith("niltoncorretordeimoveis.com.br"):
            raise PropertyNotFoundError(f"Property with ID '{property_id}' was not found.")


class ListingParserBundle:
    """Aggregates search and metadata parsers."""

    def __init__(
        self,
        search_parser: SearchPageParser | None = None,
        public_base_url: str | None = None,
    ) -> None:
        """Initialize search and metadata parsers."""
        self._search = search_parser or SearchPageParser(
            public_base_url=public_base_url or "https://niltoncorretordeimoveis.com.br"
        )
        self._metadata = MetadataParser()

    @property
    def search_parser(self) -> SearchPageParser:
        """Return search parser."""
        return self._search

    @property
    def metadata_parser(self) -> MetadataParser:
        """Return metadata parser."""
        return self._metadata


class DetailParserBundle:
    """Aggregates detail view and photo gallery parsers."""

    def __init__(self, detail_parser: PropertyDetailParser | None = None) -> None:
        """Initialize detail and photo parsers."""
        self._detail = detail_parser or PropertyDetailParser()
        self._photo = PhotoGalleryParser()

    @property
    def detail_parser(self) -> PropertyDetailParser:
        """Return detail parser."""
        return self._detail

    @property
    def photo_parser(self) -> PhotoGalleryParser:
        """Return photo parser."""
        return self._photo


class RentalParserSuite:
    """Composite suite containing listing and detail parser bundles."""

    def __init__(
        self,
        listing_bundle: ListingParserBundle | None = None,
        detail_bundle: DetailParserBundle | None = None,
        public_base_url: str | None = None,
    ) -> None:
        """Initialize suite with listing and detail bundles."""
        self._listing = listing_bundle or ListingParserBundle(public_base_url=public_base_url)
        self._detail = detail_bundle or DetailParserBundle()

    @property
    def search_parser(self) -> SearchPageParser:
        """Return search parser."""
        return self._listing.search_parser

    @property
    def metadata_parser(self) -> MetadataParser:
        """Return metadata parser."""
        return self._listing.metadata_parser

    @property
    def detail_parser(self) -> PropertyDetailParser:
        """Return detail parser."""
        return self._detail.detail_parser

    @property
    def photo_parser(self) -> PhotoGalleryParser:
        """Return photo parser."""
        return self._detail.photo_parser
