"""Unit tests for UrlBuilder canonical routing and parameter assembly."""

from nilton_research.domain.criteria import (
    FeatureBundle,
    FilterBundle,
    LocationCriteria,
    PriceRange,
    RoomCount,
    RoomCriteria,
    SearchCriteria,
    SearchScope,
)
from nilton_research.domain.enums import PropertyType, SortOrder, TransactionType
from nilton_research.domain.values import PageNumber
from nilton_research.infrastructure.url_builder import UrlBuilder


def test_default_rental_search_url():
    """Verify default criteria builds canonical rental search URL."""
    builder = UrlBuilder(base_url="https://niltoncorretordeimoveis.com.br")
    criteria = SearchCriteria.create_rental(city="timoteo")
    url = builder.build_search_url(criteria)
    assert url == "https://niltoncorretordeimoveis.com.br/imovel/locacao/todos/timoteo"


def test_url_with_single_neighborhood_path():
    """Verify single neighborhood is appended to path."""
    builder = UrlBuilder(base_url="https://niltoncorretordeimoveis.com.br")
    loc = LocationCriteria(city_slug="timoteo", neighborhood_slug="eldorado-498991")
    criteria = SearchCriteria(
        scope=SearchScope(transaction=TransactionType.LOCACAO, property_type=PropertyType.TODOS),
        location=loc,
    )
    url = builder.build_search_url(criteria)
    assert url == "https://niltoncorretordeimoveis.com.br/imovel/locacao/todos/timoteo/eldorado-498991"


def test_url_with_multi_neighborhoods_query():
    """Verify multiple neighborhood IDs are passed as query parameter."""
    builder = UrlBuilder(base_url="https://niltoncorretordeimoveis.com.br")
    loc = LocationCriteria(city_slug="timoteo", neighborhood_ids=("498991", "498264"))
    criteria = SearchCriteria(
        scope=SearchScope(transaction=TransactionType.LOCACAO, property_type=PropertyType.APARTAMENTO),
        location=loc,
    )
    url = builder.build_search_url(criteria)
    assert "bairros=498991%2C498264" in url or "bairros=498991,498264" in url
    assert "/imovel/locacao/apartamento/timoteo/?" in url


def test_url_with_room_counts_and_price():
    """Verify encoding of room counts (exact vs minimum) and maximum price."""
    builder = UrlBuilder(base_url="https://niltoncorretordeimoveis.com.br")
    criteria = SearchCriteria(
        scope=SearchScope(transaction=TransactionType.LOCACAO, property_type=PropertyType.TODOS),
        location=LocationCriteria(city_slug="timoteo"),
        filters=FilterBundle(price_range=PriceRange(maximum=2000)),
        features=FeatureBundle(
            room_criteria=RoomCriteria(
                bedrooms=RoomCount(3, is_minimum=False),
                suites=RoomCount(1, is_minimum=True),
            )
        ),
    )
    url = builder.build_search_url(criteria)
    assert "vma=2000" in url
    assert "dormitorios=3" in url
    assert "suites=21" in url


def test_url_with_sorting_and_pagination():
    """Verify sort order and page query parameter."""
    builder = UrlBuilder(base_url="https://niltoncorretordeimoveis.com.br")
    criteria = SearchCriteria(
        scope=SearchScope(transaction=TransactionType.LOCACAO, property_type=PropertyType.TODOS),
        location=LocationCriteria(city_slug="timoteo"),
        sort_order=SortOrder.MENOR_VALOR,
        page=PageNumber(2),
    )
    url = builder.build_search_url(criteria)
    assert "ord=menor_valor" in url
    assert "pag=2" in url


def test_url_with_reference_code():
    """Verify reference code search appends ref and reftipo=exata."""
    builder = UrlBuilder(base_url="https://niltoncorretordeimoveis.com.br")
    criteria = SearchCriteria(
        scope=SearchScope(transaction=TransactionType.LOCACAO, property_type=PropertyType.TODOS),
        location=LocationCriteria(city_slug="timoteo"),
        reference_code="IM0670",
    )
    url = builder.build_search_url(criteria)
    assert "ref=IM0670" in url
    assert "reftipo=exata" in url


def test_detail_and_photos_urls():
    """Verify detail page URL and AJAX photos URL construction."""
    builder = UrlBuilder(base_url="https://niltoncorretordeimoveis.com.br")
    detail_url = builder.build_detail_url("3561797")
    photos_url = builder.build_photos_url("3561797")
    assert detail_url == "https://niltoncorretordeimoveis.com.br/imovel/3561797"
    assert photos_url == "https://niltoncorretordeimoveis.com.br/t27/lista_imoveis_fotos.php?imovel=3561797"
