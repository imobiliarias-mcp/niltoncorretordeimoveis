"""Live integration tests hitting niltoncorretordeimoveis.com.br endpoints."""

import pytest
from nilton_research import (
    FeatureBundle,
    FilterBundle,
    LocationCriteria,
    NiltonRentalClient,
    PriceRange,
    PropertyType,
    RoomCount,
    RoomCriteria,
    SearchCriteria,
    SearchScope,
    TransactionType,
)
from scripts.domain.criteria import RentalFilter
from scripts.domain.value_objects import PropertyCode
from scripts.providers.nilton import NiltonRentalProvider


@pytest.fixture
def client() -> NiltonRentalClient:
    """Fixture providing live NiltonRentalClient."""
    return NiltonRentalClient()


@pytest.fixture
def live_property_id(client: NiltonRentalClient) -> str:
    """Return the id of a rental currently listed, so detail tests never depend on a fixed listing."""
    criteria = SearchCriteria(
        scope=SearchScope(transaction=TransactionType.LOCACAO, property_type=PropertyType.TODOS),
        location=LocationCriteria(city_slug="timoteo"),
    )
    results = client.search(criteria)
    assert len(results) > 0
    return results[0].identity.property_id


def test_live_target_prompt_url_search(client: NiltonRentalClient):
    """Verify live search with exact target URL from prompt:
    https://niltoncorretordeimoveis.com.br/imovel/locacao/todos/timoteo
    """
    criteria = SearchCriteria(
        scope=SearchScope(transaction=TransactionType.LOCACAO, property_type=PropertyType.TODOS),
        location=LocationCriteria(city_slug="timoteo"),
    )
    results = client.search(criteria)
    assert len(results) > 0
    first = results[0]
    assert first.identity.property_id != ""
    assert "Timóteo" in first.location.city
    assert first.price_text != ""


def test_live_filtered_rental_search(client: NiltonRentalClient):
    """Verify live rental search with maximum price and bedroom filters."""
    criteria = SearchCriteria(
        scope=SearchScope(transaction=TransactionType.LOCACAO, property_type=PropertyType.TODOS),
        location=LocationCriteria(city_slug="timoteo"),
        filters=FilterBundle(price_range=PriceRange(maximum=2000)),
        features=FeatureBundle(room_criteria=RoomCriteria(bedrooms=RoomCount(2, is_minimum=True))),
    )
    results = client.search(criteria)
    assert len(results) > 0
    for item in results:
        assert item.identity.property_id != ""


def test_live_property_details(client: NiltonRentalClient, live_property_id: str):
    """Verify live detail retrieval for a rental currently listed in Timóteo."""
    detail = client.get_details(live_property_id)
    assert detail.overview.property_id == live_property_id
    assert detail.overview.title != ""
    assert detail.overview.reference_code != ""
    assert "Timóteo" in detail.location.city
    assert detail.pricing.amount > 0


def test_live_photo_gallery_endpoint(client: NiltonRentalClient, live_property_id: str):
    """Verify live retrieval of photos from /t27/lista_imoveis_fotos.php."""
    gallery = client.get_photos(live_property_id)
    assert len(gallery) > 0
    assert gallery.first_photo().startswith("https://niltoncorretordeimoveis.com.br/imagens/imoveis/")


def test_live_provider_protocol():
    """Verify NiltonRentalProvider behavior against live endpoints."""
    provider = NiltonRentalProvider.create_default()
    assert provider.provider_name() == "nilton"

    search_res = provider.search_rentals(RentalFilter().with_city("timoteo"))
    assert search_res.returned_count() > 0

    listed_code = next(iter(search_res.listings())).code()
    detail = provider.get_property_detail(PropertyCode(listed_code))
    assert detail.listing.code() == listed_code
    assert detail.listing.core.valuation.rental_price.value() > 0.0
