"""Search criteria and parameter aggregations."""

from dataclasses import dataclass, field
from nilton_research.domain.enums import PropertyType, SortOrder, TransactionType
from nilton_research.domain.values import AreaRange, PageNumber, PriceRange, RoomCount


@dataclass(frozen=True)
class SearchScope:
    """Transaction type and property category."""

    transaction: TransactionType = TransactionType.LOCACAO
    property_type: PropertyType = PropertyType.TODOS


@dataclass(frozen=True)
class LocationCriteria:
    """Location parameters for search query."""

    city_slug: str = "timoteo"
    neighborhood_slug: str | None = None
    neighborhood_ids: tuple[str, ...] = field(default_factory=tuple)

    def query_parameters(self) -> dict[str, str]:
        """Generate query parameters for neighborhoods."""
        if not self.neighborhood_ids:
            return {}
        return {"bairros": ",".join(self.neighborhood_ids)}


@dataclass(frozen=True)
class FilterBundle:
    """Combines price and area constraints."""

    price_range: PriceRange = field(default_factory=PriceRange)
    area_range: AreaRange = field(default_factory=AreaRange)

    def query_parameters(self) -> dict[str, str]:
        """Assemble query parameters."""
        params = self.price_range.query_parameters()
        params.update(self.area_range.query_parameters())
        return params


@dataclass(frozen=True)
class RoomCriteria:
    """Room constraints."""

    bedrooms: RoomCount | None = None
    suites: RoomCount | None = None
    bathrooms: RoomCount | None = None
    parking_spaces: RoomCount | None = None

    def query_parameters(self) -> dict[str, str]:
        """Assemble query parameters for room counts."""
        params: dict[str, str] = {}
        self._add_param(params, "dormitorios", self.bedrooms)
        self._add_param(params, "suites", self.suites)
        self._add_param(params, "banheiros", self.bathrooms)
        self._add_param(params, "vagas", self.parking_spaces)
        return params

    def _add_param(self, params: dict[str, str], key: str, count: RoomCount | None) -> None:
        """Add parameter if count is present."""
        if count is None:
            return
        params[key] = count.to_param_code()


@dataclass(frozen=True)
class FeatureBundle:
    """Wraps room criteria."""

    room_criteria: RoomCriteria = field(default_factory=RoomCriteria)

    def query_parameters(self) -> dict[str, str]:
        """Assemble feature parameters."""
        return self.room_criteria.query_parameters()


@dataclass(frozen=True)
class SearchCriteria:
    """Aggregated search specification."""

    scope: SearchScope = field(default_factory=SearchScope)
    location: LocationCriteria = field(default_factory=LocationCriteria)
    filters: FilterBundle = field(default_factory=FilterBundle)
    features: FeatureBundle = field(default_factory=FeatureBundle)
    sort_order: SortOrder = SortOrder.DEFAULT
    page: PageNumber = field(default_factory=PageNumber)
    reference_code: str | None = None

    @classmethod
    def create_rental(
        cls,
        city: str = "timoteo",
        property_type: PropertyType = PropertyType.TODOS,
        bedrooms: int | None = None,
        min_bedrooms: bool = False,
        max_price: int | None = None,
        page: int = 1,
    ) -> "SearchCriteria":
        """Factory for building rental criteria."""
        scope = SearchScope(transaction=TransactionType.LOCACAO, property_type=property_type)
        location = LocationCriteria(city_slug=city)
        price_range = PriceRange(maximum=max_price)
        filters = FilterBundle(price_range=price_range)
        room_count = RoomCount(count=bedrooms, is_minimum=min_bedrooms) if bedrooms else None
        room_crit = RoomCriteria(bedrooms=room_count)
        features = FeatureBundle(room_criteria=room_crit)
        page_num = PageNumber(page)
        return cls(scope=scope, location=location, filters=filters, features=features, page=page_num)
