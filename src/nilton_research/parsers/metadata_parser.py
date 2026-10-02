"""Parser for geographic taxonomy and metadata from dgCidadesBairros."""

import re
from nilton_research.domain.metadata import City, LocationCatalog, Neighborhood


class MetadataParser:
    """Extracts cities and neighborhoods from portal search page JavaScript."""

    def parse(self, html: str) -> LocationCatalog:
        """Parse cities and neighborhoods from page HTML."""
        cidades_pairs = self._extract_cidades(html)
        bairros_names = self._extract_array_block(html, "bairros : [", "bairros_value : [")
        bairros_values = self._extract_array_block(html, "bairros_value : [", "};")

        cities: list[City] = []
        for idx, (slug, name) in enumerate(cidades_pairs):
            if not slug:
                continue
            names_row = bairros_names[idx] if idx < len(bairros_names) else []
            values_row = bairros_values[idx] if idx < len(bairros_values) else []
            neighborhoods = self._build_neighborhoods(names_row, values_row)
            cities.append(City(name=name, slug=slug, neighborhoods=tuple(neighborhoods)))

        return LocationCatalog(tuple(cities))

    def _extract_cidades(self, html: str) -> list[tuple[str, str]]:
        """Extract cidade (slug, name) pairs."""
        start = html.find("cidades : [")
        end = html.find("bairros : [")
        if start == -1 or end == -1:
            return []
        block = html[start:end]
        return re.findall(r"\[\s*'([^']*)'\s*,\s*'([^']*)'\s*\]", block)

    def _extract_array_block(self, html: str, start_marker: str, end_marker: str) -> list[list[str]]:
        """Extract multi-dimensional array of strings."""
        start = html.find(start_marker)
        if start == -1:
            return []
        end = html.find(end_marker, start)
        if end == -1:
            return []
        block = html[start:end]
        inner_matches = re.findall(r"\[([^\]]*)\]", block)
        return [re.findall(r"'([^']*)'", row) for row in inner_matches]

    def _build_neighborhoods(self, names: list[str], values: list[str]) -> list[Neighborhood]:
        """Combine names and values into Neighborhood entities."""
        neighborhoods: list[Neighborhood] = []
        for name, val in zip(names, values):
            if not val or val == "-":
                continue
            numeric_id = self._extract_id(val)
            neighborhoods.append(Neighborhood(name=name, slug=val, numeric_id=numeric_id))
        return neighborhoods

    def _extract_id(self, val: str) -> str | None:
        """Extract numeric suffix ID from slug."""
        parts = val.split("-")
        last_part = parts[-1]
        if last_part.isdigit():
            return last_part
        return None
