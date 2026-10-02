"""Unit tests for domain value objects, criteria, and first-class collections."""

import pytest

from nilton_research.domain.criteria import (
    SearchCriteria,
)
from nilton_research.domain.enums import PropertyType, TransactionType
from nilton_research.domain.listing import (
    ListingCollection,
    ListingIdentity,
    ListingLocation,
    ListingPagination,
    ListingPresentation,
    ListingSpecs,
    ListingSummary,
)
from nilton_research.domain.metadata import City, LocationCatalog, Neighborhood
from nilton_research.domain.property import PhotoGallery
from nilton_research.domain.values import AreaRange, PageNumber, PriceRange, RoomCount


def test_price_range_query_parameters():
    """Verify price range generates vmi and vma query parameters."""
    rng = PriceRange(minimum=1000, maximum=2500)
    params = rng.query_parameters()
    assert params == {"vmi": "1000", "vma": "2500"}


def test_price_range_invalid():
    """Verify price range rejects inverted or negative amounts."""
    with pytest.raises(ValueError):
        PriceRange(minimum=-10)
    with pytest.raises(ValueError):
        PriceRange(minimum=5000, maximum=1000)


def test_area_range_query_parameters():
    """Verify area range generates areaMinima and areaMaxima."""
    area = AreaRange(minimum=50, maximum=300)
    params = area.query_parameters()
    assert params == {"areaMinima": "50", "areaMaxima": "300"}


def test_room_count_exact_and_minimum():
    """Verify room count converts to exact count or ImobiBrasil minimum 20+N."""
    exact = RoomCount(count=2, is_minimum=False)
    assert exact.to_param_code() == "2"

    minimum = RoomCount(count=2, is_minimum=True)
    assert minimum.to_param_code() == "22"


def test_room_count_validation():
    """Verify room count rejects numbers outside 1..5."""
    with pytest.raises(ValueError):
        RoomCount(0)
    with pytest.raises(ValueError):
        RoomCount(6)


def test_page_number_validation():
    """Verify page number rejects invalid non-positive integers."""
    valid = PageNumber(1)
    assert valid.to_param_code() == "1"

    with pytest.raises(ValueError):
        PageNumber(0)


def test_search_criteria_rental_factory():
    """Verify convenience factory builds complete rental criteria."""
    criteria = SearchCriteria.create_rental(
        city="timoteo",
        property_type=PropertyType.APARTAMENTO,
        bedrooms=2,
        min_bedrooms=False,
        max_price=2000,
        page=1,
    )
    assert criteria.scope.transaction == TransactionType.LOCACAO
    assert criteria.scope.property_type == PropertyType.APARTAMENTO
    assert criteria.location.city_slug == "timoteo"
    assert criteria.filters.price_range.maximum == 2000


def test_listing_collection_iteration_and_indexing():
    """Verify first-class collection behavior for listings."""
    item = ListingSummary(
        identity=ListingIdentity(property_id="3561797", url_path="/imovel/3561797", reference_code="IM0670", property_type="Apartamento"),
        location=ListingLocation(neighborhood="Eldorado", city="Timóteo", state="MG"),
        specs=ListingSpecs(bedrooms=3, suites=1, bathrooms=1, parking_spaces=1),
        presentation=ListingPresentation(title="Apartamento Teste", price_text="R$ 1.500", thumbnail_url="https://img.jpg"),
    )
    col = ListingCollection(items=(item,), pagination=ListingPagination(current_page=1, has_next_page=False))
    assert len(col) == 1
    assert not col.is_empty()
    assert col[0].identity.property_id == "3561797"
    assert next(iter(col)).title == "Apartamento Teste"
    assert col.pagination.current_page == 1
    assert not col.pagination.has_next_page


def test_listing_collection_serializes_public_url_and_pagination():
    """Serialize each public URL with the original pagination metadata."""
    from nilton_research.parsers.search_parser import SearchPageParser
    from tests.test_parsers import SAMPLE_SEARCH_HTML

    collection = SearchPageParser().parse(SAMPLE_SEARCH_HTML, page_number=2)
    serialized = collection.to_dictionary()

    assert serialized["items"][0]["url"].startswith(
        "https://niltoncorretordeimoveis.com.br/imovel/3561797/"
    )
    assert serialized["items"][0]["url_path"].startswith("/imovel/3561797/")
    assert serialized["pagination"]["current_page"] == 2
    assert serialized["pagination"]["has_next_page"] is True


def test_listing_collection_serializes_zero_and_multiple_results():
    """Preserve pagination metadata for empty and multi-listing pages."""
    from nilton_research.parsers.search_parser import SearchPageParser
    from tests.test_parsers import SAMPLE_SEARCH_HTML

    empty = SearchPageParser().parse("<html></html>", page_number=2).to_dictionary()
    second_card = (
        '<div class="imovelcard" data-link="/imovel/3561798/apartamento">'
        '<div class="imovelcard__info"><h2 class="imovelcard__info__local">Centro, Timóteo / MG</h2></div>'
        "</div>"
    )
    multi_html = SAMPLE_SEARCH_HTML.replace("</body>", f"{second_card}</body>")
    multiple = SearchPageParser().parse(multi_html, page_number=2).to_dictionary()

    assert empty["items"] == []
    assert empty["pagination"]["current_page"] == 2
    assert len(multiple["items"]) == 2
    assert multiple["pagination"]["current_page"] == 2
    assert multiple["pagination"]["has_next_page"] is True


def test_core_listing_serializer_rejects_missing_and_relative_public_urls():
    """Reject manually constructed listings that cannot serialize a public URL."""
    from dataclasses import replace

    from nilton_research.domain.listing import InvalidPublicPropertyUrlError
    from nilton_research.parsers.search_parser import SearchPageParser
    from tests.test_parsers import SAMPLE_SEARCH_HTML

    listing = SearchPageParser().parse(SAMPLE_SEARCH_HTML)[0]
    for url in ("", "/imovel/3561797"):
        with pytest.raises(InvalidPublicPropertyUrlError, match="3561797"):
            replace(listing, url=url).to_dictionary()


def test_photo_gallery_behavior():
    """Verify PhotoGallery methods and indexing."""
    gallery = PhotoGallery(photo_urls=("https://example.com/1.jpg", "https://example.com/2.jpg"))
    assert len(gallery) == 2
    assert gallery[0] == "https://example.com/1.jpg"
    assert gallery.first_photo() == "https://example.com/1.jpg"
    assert not gallery.is_empty()

    empty = PhotoGallery(())
    assert len(empty) == 0
    assert empty.first_photo() == ""
    assert empty.is_empty()


def test_location_catalog_lookup():
    """Verify finding city and neighborhood inside catalog."""
    nb = Neighborhood(name="Eldorado", slug="eldorado-498991", numeric_id="498991")
    city = City(name="Timóteo", slug="timoteo", neighborhoods=(nb,))
    catalog = LocationCatalog(cities=(city,))

    found_city = catalog.find_city_by_slug("timoteo")
    assert found_city is not None
    assert found_city.name == "Timóteo"
    assert len(found_city.neighborhoods) == 1

    found_nb = found_city.find_neighborhood_by_slug("eldorado-498991")
    assert found_nb is not None
    assert found_nb.numeric_id == "498991"
