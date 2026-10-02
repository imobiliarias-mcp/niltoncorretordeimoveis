"""Domain layer exports."""

from nilton_research.domain.criteria import (
    FeatureBundle,
    FilterBundle,
    LocationCriteria,
    RoomCriteria,
    SearchCriteria,
    SearchScope,
)
from nilton_research.domain.enums import PropertyType, SortOrder, TransactionType
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
from nilton_research.domain.property import (
    PhotoGallery,
    PropertyContentBundle,
    PropertyDetail,
    PropertyIdentityBundle,
    PropertyLocation,
    PropertyOverview,
    PropertyPricing,
    PropertySpecs,
)
from nilton_research.domain.values import AreaRange, PageNumber, PriceRange, RoomCount

__all__ = [
    "AreaRange",
    "City",
    "FeatureBundle",
    "FilterBundle",
    "ListingCollection",
    "ListingIdentity",
    "ListingLocation",
    "ListingPagination",
    "ListingPresentation",
    "ListingSpecs",
    "ListingSummary",
    "LocationCatalog",
    "LocationCriteria",
    "Neighborhood",
    "PageNumber",
    "PhotoGallery",
    "PriceRange",
    "PropertyContentBundle",
    "PropertyDetail",
    "PropertyIdentityBundle",
    "PropertyLocation",
    "PropertyOverview",
    "PropertyPricing",
    "PropertySpecs",
    "PropertyType",
    "RoomCount",
    "RoomCriteria",
    "SearchCriteria",
    "SearchScope",
    "SortOrder",
    "TransactionType",
]
