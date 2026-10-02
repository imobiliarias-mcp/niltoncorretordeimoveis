"""Query builder translating RentalFilter to canonical portal routes and parameters."""

from urllib.parse import urlencode

from scripts.client.configuration import NiltonConfiguration
from scripts.domain.criteria import RentalFilter


class RentalQueryBuilder:
    """Builds search request URLs and parameter dictionaries from RentalFilter."""

    def __init__(self, configuration: NiltonConfiguration | None = None) -> None:
        """Initialize query builder with portal configuration."""
        self._config = configuration or NiltonConfiguration()

    def public_base_url(self) -> str:
        """Return the public listing origin independent from search endpoints."""
        configuration = self._config
        return configuration.public_site_base_url()

    def build_search_url(self, search_filter: RentalFilter) -> str:
        """Construct canonical search URL with path components and query string."""
        city_slug = self._resolve_city_slug(search_filter)
        type_slug = self._resolve_property_type(search_filter)
        nb_slug = self._resolve_neighborhood_slug(search_filter)
        if nb_slug:
            path = f"/imovel/locacao/{type_slug}/{city_slug}/{nb_slug}"
        else:
            path = f"/imovel/locacao/{type_slug}/{city_slug}"

        query_dict = self.build_parameters(search_filter)
        if not query_dict:
            return f"{self._config.base_url}{path}"
        query_string = urlencode(query_dict)
        return f"{self._config.base_url}{path}/?&{query_string}"

    def build_parameters(self, search_filter: RentalFilter) -> dict[str, str]:
        """Convert domain filter into ImobiBrasil query parameter dictionary."""
        params: dict[str, str] = {}
        self._apply_bedrooms(params, search_filter)
        self._apply_price(params, search_filter)
        self._apply_page(params, search_filter)
        return params

    def _resolve_city_slug(self, search_filter: RentalFilter) -> str:
        """Map filter city to URL slug identifier."""
        raw_city = search_filter.criteria.location.city.strip().lower()
        if not raw_city:
            return "todos"
        cleaned = raw_city.replace("ó", "o").replace("é", "e").replace("á", "a")
        return cleaned.replace(" ", "-")

    def _resolve_property_type(self, search_filter: RentalFilter) -> str:
        """Map filter property type to URL slug."""
        raw_type = search_filter.criteria.specifications.property_type.strip().lower()
        if not raw_type:
            return "todos"
        return raw_type.replace(" ", "-")

    def _resolve_neighborhood_slug(self, search_filter: RentalFilter) -> str | None:
        """Map filter neighborhood to URL slug if provided."""
        nb = search_filter.criteria.location.neighborhood.strip().lower()
        if not nb:
            return None
        cleaned = nb.replace("ó", "o").replace("é", "e").replace("á", "a")
        return cleaned.replace(" ", "-")

    def _apply_bedrooms(self, params: dict[str, str], search_filter: RentalFilter) -> None:
        """Encode bedroom count (minimum 20+N format)."""
        count = search_filter.criteria.specifications.minimum_bedrooms
        if count <= 0:
            return
        code = str(20 + count)
        params["dormitorios"] = code

    def _apply_price(self, params: dict[str, str], search_filter: RentalFilter) -> None:
        """Encode maximum price ceiling."""
        max_price = search_filter.constraints.price_range.maximum_price.value()
        if max_price <= 0.0:
            return
        params["vma"] = str(int(max_price))

    def _apply_page(self, params: dict[str, str], search_filter: RentalFilter) -> None:
        """Encode page index parameter."""
        page_num = search_filter.constraints.pagination.page_number
        if page_num <= 1:
            return
        params["pag"] = str(page_num)
