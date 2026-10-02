"""Central rental research MCP interface and client."""

from nilton_research.collaborators import RentalNetworkGateway, RentalParserSuite
from nilton_research.domain.criteria import SearchCriteria
from nilton_research.domain.enums import PropertyType
from nilton_research.domain.listing import ListingCollection
from nilton_research.domain.metadata import LocationCatalog
from nilton_research.domain.property import PhotoGallery, PropertyDetail


class NiltonRentalClient:
    """Central rental research client serving as the project's MCP interface."""

    def __init__(
        self,
        gateway: RentalNetworkGateway | None = None,
        parsers: RentalParserSuite | None = None,
        public_base_url: str | None = None,
    ) -> None:
        """Initialize client with gateway and parser suite collaborators."""
        self._gateway = gateway or RentalNetworkGateway()
        self._parsers = parsers or RentalParserSuite(public_base_url=public_base_url)

    def search(self, criteria: SearchCriteria) -> ListingCollection:
        """Execute search query and return parsed collection of listings."""
        resp = self._gateway.fetch_search(criteria)
        parser = self._parsers.search_parser
        return parser.parse(resp.text, page_number=criteria.page.value)

    def search_rentals(
        self,
        city: str = "timoteo",
        property_type: PropertyType = PropertyType.TODOS,
        bedrooms: int | None = None,
        min_bedrooms: bool = False,
        max_price: int | None = None,
        page: int = 1,
    ) -> ListingCollection:
        """Convenience method for executing rental searches with standard filters."""
        criteria = SearchCriteria.create_rental(
            city=city,
            property_type=property_type,
            bedrooms=bedrooms,
            min_bedrooms=min_bedrooms,
            max_price=max_price,
            page=page,
        )
        return self.search(criteria)

    def get_details(self, property_id: str) -> PropertyDetail:
        """Retrieve full details for a specific property by ID."""
        resp = self._gateway.fetch_detail(property_id)
        parser = self._parsers.detail_parser
        return parser.parse(resp.text, property_id=property_id, canonical_url=resp.final_url)

    def get_photos(self, property_id: str) -> PhotoGallery:
        """Retrieve photo gallery for a specific property via AJAX endpoint."""
        resp = self._gateway.fetch_photos(property_id)
        parser = self._parsers.photo_parser
        return parser.parse_ajax_json(resp.text)

    def get_locations(self) -> LocationCatalog:
        """Retrieve catalog of cities and neighborhoods supported by the portal."""
        resp = self._gateway.fetch_search(SearchCriteria())
        parser = self._parsers.metadata_parser
        return parser.parse(resp.text)
