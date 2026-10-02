"""Extracts specification features from listing HTML elements."""

import re
from bs4 import Tag
from nilton_research.domain.listing import ListingSpecs


class FeatureExtractor:
    """Extracts room counts and area specs from listing card feature elements."""

    def extract(self, card: Tag) -> ListingSpecs:
        """Extract specifications from card markup."""
        features = card.select(".imovelcard__info__feature")
        bedrooms = self._extract_icon_number(features, "fa-bed")
        suites = self._extract_icon_number(features, "fa-bath")
        bathrooms = self._extract_icon_number(features, "fa-shower")
        parking = self._extract_icon_number(features, "fa-car")
        area = self._extract_area_text(features)
        return ListingSpecs(
            bedrooms=bedrooms,
            suites=suites,
            bathrooms=bathrooms,
            parking_spaces=parking,
            area_description=area,
        )

    def _extract_icon_number(self, features: list[Tag], icon_class: str) -> int | None:
        """Extract integer associated with a specific font-awesome icon."""
        for feat in features:
            if not feat.find("i", class_=icon_class):
                continue
            text = feat.get_text(separator=" ", strip=True)
            match = re.search(r"(\d+)", text)
            if match:
                return int(match.group(1))
        return None

    def _extract_area_text(self, features: list[Tag]) -> str | None:
        """Extract area text if present."""
        for feat in features:
            if feat.find("i", class_="fa-arrows-h"):
                return feat.get_text(separator=" ", strip=True)
        return None
