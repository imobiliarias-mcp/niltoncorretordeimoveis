"""Parser for single property detail pages combining JSON-LD and HTML."""

import json
import re
from bs4 import BeautifulSoup, Tag
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


class PropertyDetailParser:
    """Parses property detail HTML pages into PropertyDetail aggregate."""

    def parse(self, html: str, property_id: str, canonical_url: str = "") -> PropertyDetail:
        """Parse detail page content."""
        soup = BeautifulSoup(html, "html.parser")
        json_ld = self._extract_json_ld(soup)
        overview = self._build_overview(soup, json_ld, property_id, canonical_url)
        pricing = self._build_pricing(soup, json_ld)
        location = self._build_location(soup, json_ld)
        specs = self._build_specs(soup)
        gallery = self._extract_inline_gallery(soup)

        identity = PropertyIdentityBundle(overview=overview, pricing=pricing)
        content = PropertyContentBundle(location=location, specs=specs, gallery=gallery)
        return PropertyDetail(identity=identity, content=content)

    def _extract_json_ld(self, soup: BeautifulSoup) -> dict[str, dict]:
        """Extract structured microdata scripts."""
        data: dict[str, dict] = {}
        for script in soup.select('script[type="application/ld+json"]'):
            text = script.string
            if not text:
                continue
            self._try_load_json(data, text)
        return data

    def _try_load_json(self, data: dict[str, dict], text: str) -> None:
        """Parse individual JSON script safely."""
        try:
            parsed = json.loads(text.strip())
            if isinstance(parsed, dict) and "@type" in parsed:
                data[parsed["@type"]] = parsed
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass

    def _build_overview(
        self,
        soup: BeautifulSoup,
        json_ld: dict[str, dict],
        property_id: str,
        canonical_url: str,
    ) -> PropertyOverview:
        """Construct overview from JSON-LD Product or HTML h1."""
        product = json_ld.get("Product", {})
        title = product.get("name")
        if not title:
            h1 = soup.find("h1")
            title = h1.get_text(strip=True) if h1 else ""
        desc = product.get("description", "")
        if not desc:
            desc_tag = soup.select_one(".imovelcard__info__tab__content__descricao") or soup.select_one(".descricao p")
            desc = desc_tag.get_text(separator="\n", strip=True) if desc_tag else ""
        ref_code = self._extract_reference(soup)
        return PropertyOverview(
            property_id=property_id,
            reference_code=ref_code,
            title=title,
            canonical_url=canonical_url,
            description=desc,
        )

    def _build_pricing(self, soup: BeautifulSoup, json_ld: dict[str, dict]) -> PropertyPricing:
        """Construct pricing from RentAction or HTML."""
        action = json_ld.get("RentAction") or json_ld.get("BuyAction")
        if action and "price" in action:
            raw_price = action.get("price")
            amount = float(str(raw_price).replace(",", "."))
            return PropertyPricing(amount=amount, formatted=f"R$ {amount:,.2f}")
        val_tag = soup.select_one(".imovelcard__valor__valor, .info__valor")
        if val_tag:
            text = val_tag.get_text(strip=True)
            match = re.search(r"[\d.]+", text)
            amount = float(match.group(0).replace(".", "")) if match else 0.0
            return PropertyPricing(amount=amount, formatted=text)
        return PropertyPricing(amount=0.0, formatted="Consulte")

    def _build_location(self, soup: BeautifulSoup, json_ld: dict[str, dict]) -> PropertyLocation:
        """Construct location from RentAction or HTML."""
        action = json_ld.get("RentAction") or json_ld.get("BuyAction")
        city = ""
        state = ""
        street = ""
        if action and "object" in action and "address" in action["object"]:
            addr = action["object"]["address"]
            city = addr.get("addressLocality", "")
            state = addr.get("addressRegion", "")
            street = addr.get("streetAddress", "")

        info_col = soup.select_one(".info__col, .imovelcard__info__local")
        info_text = info_col.get_text(strip=True) if info_col else ""
        m_bairro = re.search(r"bairro\s+([^,]+)", info_text, re.IGNORECASE)
        neighborhood = m_bairro.group(1).strip() if m_bairro else ""
        if not city and "/" in info_text:
            city_part = info_text.split("/")[0]
            city = city_part.split(",")[-1].strip()
            state = info_text.split("/")[1][:2].strip()

        return PropertyLocation(street=street, neighborhood=neighborhood, city=city, state=state)

    def _build_specs(self, soup: BeautifulSoup) -> PropertySpecs:
        """Extract room and area specifications from info__tag or features."""
        tags = [t.get_text(" ", strip=True) for t in soup.select(".info__tag, .imovelcard__info__feature")]
        bedrooms = self._extract_count(tags, r"(\d+)\s*Dorm")
        suites = self._extract_count(tags, r"(\d+)\s*Su[íi]te")
        bathrooms = self._extract_count(tags, r"(\d+)\s*Banh")
        parking = self._extract_count(tags, r"(\d+)\s*Vaga")
        return PropertySpecs(bedrooms=bedrooms, suites=suites, bathrooms=bathrooms, parking_spaces=parking)

    def _extract_count(self, tags: list[str], pattern: str) -> int | None:
        """Extract count matching regex pattern from tags."""
        for t in tags:
            match = re.search(pattern, t, re.IGNORECASE)
            if match:
                return int(match.group(1))
        return None

    def _extract_reference(self, soup: BeautifulSoup) -> str:
        """Extract reference code from info tags or elements."""
        for selector in [".imovelcard__info__ref", ".info__col", ".info", "h1"]:
            node = soup.select_one(selector)
            if not node:
                continue
            text = node.get_text(strip=True)
            match = re.search(r"Ref:\s*([A-Za-z0-9_-]+)", text)
            if match:
                return match.group(1)
        return ""

    def _extract_inline_gallery(self, soup: BeautifulSoup) -> PhotoGallery:
        """Extract photos embedded in markup or carousel."""
        urls: list[str] = []
        for img in soup.select("#galeria-inicial img, .imovel_detalhes_galeria img, .glide__slide img"):
            src = img.get("src")
            if src and src.startswith("http") and "logo" not in src:
                urls.append(src)
        return PhotoGallery(tuple(urls))
