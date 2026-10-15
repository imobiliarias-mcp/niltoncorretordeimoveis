"""Nilton Corretor de Imóveis rental search provider implementation."""

import httpx

from scripts.client.configuration import NiltonConfiguration
from scripts.client.http_transport import NiltonHttpTransport
from scripts.client.parsers import (
    FacetParser,
    PropertyDetailParser,
    SearchResultParser,
)
from scripts.client.query_builder import RentalQueryBuilder
from scripts.domain.collections import FacetCollection, RentalSearchResult
from scripts.domain.criteria import RentalFilter
from scripts.domain.entities import RentalPropertyDetail
from scripts.domain.exceptions import PropertyNotFoundException
from scripts.domain.value_objects import PropertyCode
from scripts.interfaces.provider import RentalProviderProtocol


class NiltonRentalProvider(RentalProviderProtocol):
    """Adapter implementing RentalProviderProtocol for Nilton Corretor de Imóveis portal."""

    def __init__(
        self,
        transport: NiltonHttpTransport,
        query_builder: RentalQueryBuilder,
    ) -> None:
        """Initialize provider with transport and query builder."""
        self._transport = transport
        self._builder = query_builder

    @classmethod
    def create_default(cls) -> "NiltonRentalProvider":
        """Factory method constructing provider with default configurations."""
        config = NiltonConfiguration()
        client = httpx.Client(timeout=20.0, follow_redirects=True)
        transport = NiltonHttpTransport(configuration=config, http_client=client)
        builder = RentalQueryBuilder(configuration=config)
        return cls(transport=transport, query_builder=builder)

    def provider_name(self) -> str:
        """Return unique provider identifier for central MCP registry."""
        return "nilton"

    def search_rentals(self, search_filter: RentalFilter) -> RentalSearchResult:
        """Search rental listings using criteria."""
        search_url = self._builder.build_search_url(search_filter)
        html_content = self._transport.get_text(search_url)
        parser = SearchResultParser(public_base_url=self._builder.public_base_url())
        return parser.parse_search_response(html_content)

    def get_property_detail(self, code: PropertyCode) -> RentalPropertyDetail:
        """Retrieve full details for a single property by code."""
        code_str = code.value()
        url = f"https://niltoncorretordeimoveis.com.br/imovel/{code_str}"
        resp = self._transport.get_response(url)
        final_url = str(resp.url).rstrip("/")
        if final_url.endswith("niltoncorretordeimoveis.com.br"):
            raise PropertyNotFoundException(f"Property '{code_str}' was not found.")
        parser = PropertyDetailParser(public_base_url=self._builder.public_base_url())
        return parser.parse_detail_response(resp.text, requested_code=code_str)

    def get_facets(self) -> FacetCollection:
        """Retrieve available cities, neighborhoods, and filter options."""
        url = "https://niltoncorretordeimoveis.com.br/imovel/locacao"
        html_content = self._transport.get_text(url)
        parser = FacetParser()
        return parser.parse_facets_response(html_content)
