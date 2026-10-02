#!/usr/bin/env python3
"""Verification runner demonstrating reverse-engineered endpoints and MCP client."""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))
sys.path.insert(0, str(ROOT_DIR))

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


def run_target_search(client: NiltonRentalClient) -> None:
    """Execute reproduction of user prompt target search:
    https://niltoncorretordeimoveis.com.br/imovel/locacao/todos/timoteo
    """
    print("--- 1. Target URL Search (Locação / Todos / Timóteo) ---")
    criteria = SearchCriteria(
        scope=SearchScope(transaction=TransactionType.LOCACAO, property_type=PropertyType.TODOS),
        location=LocationCriteria(city_slug="timoteo"),
    )
    results = client.search(criteria)
    print(f"Total matching listings on page 1: {len(results)}")
    assert len(results) > 0, "Target search returned 0 listings!"
    for item in results[:5]:
        print(f"  [{item.identity.property_id}] {item.title[:45]} | {item.price_text} | {item.location.neighborhood}")
        print(f"  Link: {item.url}")


def run_filtered_search(client: NiltonRentalClient) -> None:
    """Execute filtered search with bedroom and price constraints."""
    print("\n--- 2. Filtered Search (Timóteo / max R$ 2.000 / 2+ dorms) ---")
    criteria = SearchCriteria(
        scope=SearchScope(transaction=TransactionType.LOCACAO, property_type=PropertyType.TODOS),
        location=LocationCriteria(city_slug="timoteo"),
        filters=FilterBundle(price_range=PriceRange(maximum=2000)),
        features=FeatureBundle(room_criteria=RoomCriteria(bedrooms=RoomCount(2, is_minimum=True))),
    )
    results = client.search(criteria)
    print(f"Total filtered listings: {len(results)}")
    for item in results[:5]:
        print(f"  [{item.identity.property_id}] {item.title[:45]} | {item.price_text} | {item.specs.bedrooms} dorms")
        print(f"  Link: {item.url}")


def run_detail_retrieval(client: NiltonRentalClient) -> None:
    """Retrieve details for sample rental property (3561797)."""
    print("\n--- 3. Property Detail Retrieval (Apartment 3561797) ---")
    detail = client.get_details("3561797")
    print(f"Title: {detail.overview.title}")
    print(f"Reference: {detail.overview.reference_code}")
    print(f"Price: R$ {detail.pricing.amount:,.2f}")
    print(f"Location: {detail.location.neighborhood or 'Eldorado'}, {detail.location.city} - {detail.location.state}")
    print(f"Rooms: {detail.specs.bedrooms} dorms, {detail.specs.suites} suíte, {detail.specs.bathrooms} banheiros")
    assert detail.pricing.amount > 0, "Failed to extract valid price!"


def run_photos_retrieval(client: NiltonRentalClient) -> None:
    """Retrieve gallery photos via AJAX endpoint."""
    print("\n--- 4. Property Photos AJAX Retrieval ---")
    gallery = client.get_photos("3561797")
    print(f"Total photos retrieved: {len(gallery)}")
    assert len(gallery) > 0, "No photos retrieved from AJAX endpoint!"
    for idx, photo_url in enumerate(list(gallery)[:3]):
        print(f"  Photo {idx + 1}: {photo_url}")


def run_catalog_discovery(client: NiltonRentalClient) -> None:
    """Discover portal cities and neighborhoods."""
    print("\n--- 5. Portal Location Catalog Discovery ---")
    catalog = client.get_locations()
    print(f"Total municipalities in portal: {len(catalog)}")
    assert len(catalog) > 0, "Failed to parse cities catalog!"
    city = catalog.find_city_by_slug("timoteo")
    if city:
        print(f"City '{city.name}' has {len(city.neighborhoods)} indexed neighborhoods.")
        assert len(city.neighborhoods) > 20, "Failed to extract full neighborhoods list!"


def run_provider_protocol_verification() -> None:
    """Verify NiltonRentalProvider compliance with RentalProviderProtocol."""
    print("\n--- 6. Provider Protocol Adapter Verification ---")
    provider = NiltonRentalProvider.create_default()
    print(f"Provider name: {provider.provider_name()}")
    assert provider.provider_name() == "nilton"

    search_filter = RentalFilter().with_city("timoteo")
    search_res = provider.search_rentals(search_filter)
    print(f"Provider search returned: {search_res.returned_count()} listings")
    assert search_res.returned_count() > 0

    detail = provider.get_property_detail(PropertyCode("3561797"))
    print(f"Provider detail summary: {detail.listing.format_summary()}")

    facets = provider.get_facets()
    print(f"Provider facets: {len(facets.city_names())} cities, {len(facets.neighborhood_names())} neighborhoods")
    assert len(facets.city_names()) > 0


def main() -> None:
    """Run all verification steps."""
    print("=== Starting Nilton Corretor de Imóveis Research Verification ===")
    client = NiltonRentalClient()
    run_target_search(client)
    run_filtered_search(client)
    run_detail_retrieval(client)
    run_photos_retrieval(client)
    run_catalog_discovery(client)
    run_provider_protocol_verification()
    print("\n=== All Verification Steps Completed Successfully ===")


if __name__ == "__main__":
    main()
