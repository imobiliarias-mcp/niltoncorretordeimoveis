"""URL builder for niltoncorretordeimoveis.com.br search and detail routes."""

from urllib.parse import urlencode
from nilton_research.domain.criteria import SearchCriteria
from nilton_research.domain.enums import SortOrder


class UrlBuilder:
    """Builds canonical URLs for property search, detail, and media endpoints."""

    def __init__(self, base_url: str = "https://niltoncorretordeimoveis.com.br") -> None:
        """Initialize with target portal base URL."""
        self.base_url = base_url.rstrip("/")

    def build_search_url(self, criteria: SearchCriteria) -> str:
        """Construct the full search URL from domain criteria."""
        path = self._build_path(criteria)
        query = self._build_query_string(criteria)
        if not query:
            return f"{self.base_url}{path}"
        return f"{self.base_url}{path}/?&{query}"

    def build_detail_url(self, property_id: str) -> str:
        """Construct direct property detail URL by numeric identifier."""
        return f"{self.base_url}/imovel/{property_id}"

    def build_photos_url(self, property_id: str) -> str:
        """Construct AJAX photo gallery endpoint URL."""
        return f"{self.base_url}/t27/lista_imoveis_fotos.php?imovel={property_id}"

    def _build_path(self, criteria: SearchCriteria) -> str:
        """Assemble SEO-friendly path components."""
        trans = criteria.scope.transaction.value
        ptype = criteria.scope.property_type.value
        city = criteria.location.city_slug
        bairro = criteria.location.neighborhood_slug
        if bairro:
            return f"/imovel/{trans}/{ptype}/{city}/{bairro}"
        return f"/imovel/{trans}/{ptype}/{city}"

    def _build_query_string(self, criteria: SearchCriteria) -> str:
        """Assemble query string parameters from bundles."""
        params: dict[str, str] = {}
        params.update(criteria.filters.query_parameters())
        params.update(criteria.features.query_parameters())
        params.update(criteria.location.query_parameters())
        self._append_options(params, criteria)
        return urlencode(params)

    def _append_options(self, params: dict[str, str], criteria: SearchCriteria) -> None:
        """Append sorting, pagination, and reference code."""
        if criteria.sort_order != SortOrder.DEFAULT:
            params["ord"] = criteria.sort_order.value
        if criteria.page.value > 1:
            params["pag"] = criteria.page.to_param_code()
        if criteria.reference_code is not None:
            params["ref"] = criteria.reference_code
            params["reftipo"] = "exata"
