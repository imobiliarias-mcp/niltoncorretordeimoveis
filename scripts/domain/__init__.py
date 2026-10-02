"""Domain package exports."""

from scripts.domain.collections import (
    FacetCollection,
    RentalListingCollection,
    RentalSearchResult,
)
from scripts.domain.criteria import (
    LocationCriteria,
    PriceRange,
    RentalFilter,
    RentalSearchCriteria,
    SearchConstraints,
    SearchPagination,
    SpecificationCriteria,
)
from scripts.domain.entities import (
    DetailedProfile,
    ListingCore,
    ListingDetails,
    ListingIdentity,
    ListingValuation,
    RentalListing,
    RentalPropertyDetail,
)
from scripts.domain.exceptions import (
    InvalidFilterException,
    InvalidPriceException,
    InvalidPropertyCodeException,
    PropertyNotFoundException,
    RentalSearchException,
)
from scripts.domain.value_objects import (
    GeoCoordinate,
    ListingPrice,
    PropertyCode,
)

__all__ = [
    "DetailedProfile",
    "FacetCollection",
    "GeoCoordinate",
    "InvalidFilterException",
    "InvalidPriceException",
    "InvalidPropertyCodeException",
    "ListingCore",
    "ListingDetails",
    "ListingIdentity",
    "ListingPrice",
    "ListingValuation",
    "LocationCriteria",
    "PriceRange",
    "PropertyCode",
    "PropertyNotFoundException",
    "RentalFilter",
    "RentalListing",
    "RentalListingCollection",
    "RentalPropertyDetail",
    "RentalSearchCriteria",
    "RentalSearchException",
    "RentalSearchResult",
    "SearchConstraints",
    "SearchPagination",
    "SpecificationCriteria",
]
