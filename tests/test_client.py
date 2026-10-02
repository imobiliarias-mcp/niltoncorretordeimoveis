"""Unit tests for NiltonRentalClient using mocked network gateway."""

import pytest

from nilton_research.client import NiltonRentalClient
from nilton_research.collaborators import RentalNetworkGateway
from nilton_research.domain.criteria import SearchCriteria
from nilton_research.infrastructure.http_client import (
    HttpResponse,
    PropertyNotFoundError,
)
from tests.test_parsers import (
    SAMPLE_DETAIL_HTML,
    SAMPLE_METADATA_JS,
    SAMPLE_SEARCH_HTML,
)


class StubHttpClient:
    """Mock HTTP client returning canned responses."""

    def __init__(self, responses: dict[str, HttpResponse]) -> None:
        """Initialize with response map."""
        self._responses = responses

    def get(self, url: str, headers: dict[str, str] | None = None) -> HttpResponse:
        """Return mapped stub response."""
        for pattern, resp in self._responses.items():
            if pattern in url:
                return resp
        return HttpResponse(status_code=200, text="", final_url=url, headers={})


def test_client_search_with_stub():
    """Verify client search dispatches correctly and returns parsed collection."""
    stub_http = StubHttpClient({
        "imovel/locacao": HttpResponse(
            status_code=200,
            text=SAMPLE_SEARCH_HTML,
            final_url="https://niltoncorretordeimoveis.com.br/imovel/locacao/todos/timoteo",
            headers={},
        )
    })
    gateway = RentalNetworkGateway(http_client=stub_http)
    client = NiltonRentalClient(gateway=gateway)

    results = client.search(SearchCriteria.create_rental(city="timoteo"))
    assert len(results) == 1
    assert results[0].identity.property_id == "3561797"
    assert results[0].specs.bedrooms == 3


def test_client_details_with_stub():
    """Verify client detail retrieval dispatches and parses correctly."""
    stub_http = StubHttpClient({
        "imovel/3561797": HttpResponse(
            status_code=200,
            text=SAMPLE_DETAIL_HTML,
            final_url="https://niltoncorretordeimoveis.com.br/imovel/3561797",
            headers={},
        )
    })
    gateway = RentalNetworkGateway(http_client=stub_http)
    client = NiltonRentalClient(gateway=gateway)

    detail = client.get_details("3561797")
    assert detail.overview.property_id == "3561797"
    assert detail.pricing.amount == 1500.0
    assert detail.specs.bedrooms == 3


def test_client_photos_with_stub():
    """Verify client photo retrieval parses AJAX JSON."""
    ajax_json = '{"0": {"arquivo_imm": "pic1.jpg"}, "1": {"arquivo_imm": "pic2.jpg"}}'
    stub_http = StubHttpClient({
        "lista_imoveis_fotos.php": HttpResponse(
            status_code=200,
            text=ajax_json,
            final_url="https://niltoncorretordeimoveis.com.br/t27/lista_imoveis_fotos.php?imovel=3561797",
            headers={},
        )
    })
    gateway = RentalNetworkGateway(http_client=stub_http)
    client = NiltonRentalClient(gateway=gateway)

    photos = client.get_photos("3561797")
    assert len(photos) == 2
    assert "pic1.jpg" in photos[0]


def test_client_locations_with_stub():
    """Verify client location discovery parses catalog."""
    stub_http = StubHttpClient({
        "imovel": HttpResponse(
            status_code=200,
            text=SAMPLE_METADATA_JS,
            final_url="https://niltoncorretordeimoveis.com.br/imovel/locacao/todos/timoteo",
            headers={},
        )
    })
    gateway = RentalNetworkGateway(http_client=stub_http)
    client = NiltonRentalClient(gateway=gateway)

    catalog = client.get_locations()
    assert len(catalog) == 2
    assert catalog.find_city_by_slug("timoteo") is not None


def test_client_property_not_found_raises_exception():
    """Verify that redirecting to homepage triggers PropertyNotFoundError."""
    stub_http = StubHttpClient({
        "imovel/999999": HttpResponse(
            status_code=200,
            text="<html>Home</html>",
            final_url="https://niltoncorretordeimoveis.com.br",
            headers={},
        )
    })
    gateway = RentalNetworkGateway(http_client=stub_http)
    client = NiltonRentalClient(gateway=gateway)

    with pytest.raises(PropertyNotFoundError):
        client.get_details("999999")


def test_client_public_base_override_reaches_core_search_parser():
    """Keep search endpoint and public listing URL hosts independent."""
    from nilton_research.infrastructure.url_builder import UrlBuilder

    class RecordingHttpClient:
        def __init__(self):
            self.requested_urls = []

        def get(self, url, headers=None):
            self.requested_urls.append(url)
            return HttpResponse(200, SAMPLE_SEARCH_HTML, url, headers={})

    http_client = RecordingHttpClient()
    gateway = RentalNetworkGateway(
        http_client=http_client,
        url_builder=UrlBuilder(base_url="https://search.example"),
    )
    client = NiltonRentalClient(gateway=gateway, public_base_url="https://public.example")
    results = client.search(SearchCriteria.create_rental(city="timoteo"))

    assert len(http_client.requested_urls) == 1
    assert http_client.requested_urls[0].startswith("https://search.example/")
    assert results[0].url == (
        "https://public.example/imovel/3561797/"
        "apartamento-locacao-timoteo-mg-eldorado"
    )


def test_script_provider_public_base_override_reaches_parser():
    """Use the configured public host for serialized search links."""
    from scripts.client.configuration import NiltonConfiguration
    from scripts.client.query_builder import RentalQueryBuilder
    from scripts.domain.criteria import RentalFilter
    from scripts.providers.nilton import NiltonRentalProvider

    class RecordingTransport:
        def __init__(self):
            self.requested_urls = []

        def get_text(self, url):
            self.requested_urls.append(url)
            return SAMPLE_SEARCH_HTML

    transport = RecordingTransport()
    configuration = NiltonConfiguration(
        base_hostname="public.example",
        base_url="https://search.example",
    )
    provider = NiltonRentalProvider(
        transport=transport,
        query_builder=RentalQueryBuilder(configuration),
    )
    result = provider.search_rentals(RentalFilter())
    listing = result.to_dictionary()["listings"][0]

    assert len(transport.requested_urls) == 1
    assert transport.requested_urls[0].startswith("https://search.example/")
    assert listing["url"] == (
        "https://public.example/imovel/3561797/"
        "apartamento-locacao-timoteo-mg-eldorado"
    )
