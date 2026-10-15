"""Unit tests for NiltonMcpAdapter."""

from scripts.client.configuration import NiltonConfiguration
from scripts.client.query_builder import RentalQueryBuilder
from scripts.mcp.tools import NiltonMcpAdapter
from scripts.providers.nilton import NiltonRentalProvider


class StubHttpTransport:
    """Stub HTTP transport for testing without network requests."""

    def get_text(self, url: str) -> str:
        return '<html><body><div class="card-imovel"><a href="/imovel/101">Casa</a><span class="preco">R$ 1.200</span></div></body></html>'

    def get_response(self, url: str):
        class DummyResponse:
            url = "https://niltoncorretordeimoveis.com.br/imovel/101"
            text = '<html><body><h1 class="titulo">Casa no Centro</h1><span class="preco">R$ 1.200</span></body></html>'
        return DummyResponse()


def test_mcp_adapter_provider_info() -> None:
    """Test MCP provider metadata."""
    transport = StubHttpTransport()
    config = NiltonConfiguration()
    builder = RentalQueryBuilder(configuration=config)
    provider = NiltonRentalProvider(transport=transport, query_builder=builder)
    adapter = NiltonMcpAdapter(provider=provider)

    info = adapter.get_provider_info()
    assert info["provider_name"] == "nilton"
    assert "search_rentals" in info["supported_operations"]


def test_mcp_adapter_search_rentals() -> None:
    """Test MCP search tool execution."""
    transport = StubHttpTransport()
    config = NiltonConfiguration()
    builder = RentalQueryBuilder(configuration=config)
    provider = NiltonRentalProvider(transport=transport, query_builder=builder)
    adapter = NiltonMcpAdapter(provider=provider)

    result_dict = adapter.search_rentals(city="Timóteo", bedrooms=2, max_price=1500.0)
    assert isinstance(result_dict, dict)
    assert "listings" in result_dict


def test_detail_parser_uses_requested_numeric_code_when_page_lacks_json_ld():
    """Pages without JSON-LD expose only the non-numeric reference; the requested id must still resolve."""
    from scripts.client.parsers import PropertyDetailParser

    html = '<html><body><h1>Apartamento para Locação</h1><div class="info__col">Ref: IMO836</div></body></html>'
    detail = PropertyDetailParser().parse_detail_response(html, requested_code="3980012")

    assert detail.listing.code() == "3980012"
    assert detail.listing.details.media.public_link.url_path == "/imovel/3980012"
