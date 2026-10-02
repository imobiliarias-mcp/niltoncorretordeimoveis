"""Unit tests for SearchPageParser, PropertyDetailParser, PhotoGalleryParser, and MetadataParser."""

from nilton_research.parsers.detail_parser import PropertyDetailParser
from nilton_research.parsers.metadata_parser import MetadataParser
from nilton_research.parsers.photo_parser import PhotoGalleryParser
from nilton_research.parsers.search_parser import SearchPageParser

SAMPLE_SEARCH_HTML = """
<!DOCTYPE html>
<html>
<body>
  <div class="imovelcard" data-link="/imovel/3561797/apartamento-locacao-timoteo-mg-eldorado">
    <div class="row">
      <a class="col imovelcard__img" href="/imovel/3561797" title="Apartamento para Locação, em Timóteo, bairro Eldorado">
        <img src="https://imgs.cdn.com/thumb.jpeg" />
      </a>
      <div class="col imovelcard__infocontainer">
        <div class="col imovelcard__info">
          <h2 class="imovelcard__info__tag">Locação</h2>
          <h2 class="imovelcard__info__local">Eldorado, Timóteo / MG</h2>
          <p class="imovelcard__info__ref"><strong>Ref: IM0670</strong> - Apartamento</p>
          <div class="imovelcard__info__feature"><i class="fa fa-bed"></i><p><b>3</b><span>Dormitórios</span></p></div>
          <div class="imovelcard__info__feature"><i class="fa fa-shower"></i><p><b>1</b><span>Banheiro</span></p></div>
          <div class="imovelcard__info__feature"><i class="fa fa-bath"></i><p><b>1</b><span>Suíte</span></p></div>
          <div class="imovelcard__info__feature"><i class="fa fa-car"></i><p><b>1</b><span>Vaga</span></p></div>
        </div>
        <div class="col imovelcard__valor">
          <p class="imovelcard__valor__valor"><span>R$</span> 1.500</p>
        </div>
      </div>
    </div>
  </div>

  <!-- Dummy pagination wrapper in ImobiBrasil t27 -->
  <div class="imovelcard" style="background-color:unset;">
    <div class="lista_imoveis_paginacao">
      <a class="lipagina-btn-paginacao-atual" href="/imovel/locacao/todos/timoteo/?pag=1">1</a>
      <a class="lipagina-btn-paginacao" href="/imovel/locacao/todos/timoteo/?pag=2" title="Próxima Página">&gt;</a>
    </div>
  </div>
</body>
</html>
"""

SAMPLE_DETAIL_HTML = """
<!DOCTYPE html>
<html>
<head>
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "RentAction",
    "price": "1500.00",
    "priceSpecification": {"@type": "PriceSpecification", "priceCurrency": "BRL"},
    "object": {
      "@type": "Place",
      "address": {"addressLocality": "Timóteo", "addressRegion": "MG", "streetAddress": "Rua Principal"}
    }
  }
  </script>
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "Product",
    "mpn": "3561797",
    "name": "Apartamento para Locação no Eldorado",
    "description": "Excelente apartamento com 3 quartos."
  }
  </script>
</head>
<body>
  <h1>Apartamento para Locação, Timóteo / MG</h1>
  <div class="info__col">
    Ref: IM0670, bairro Eldorado, 3 dormitórios, sendo 1 suíte, 1 banheiro, 1 vaga
  </div>
  <div class="info__tag">3 Dormitórios</div>
  <div class="info__tag">1 Suíte</div>
  <div class="info__tag">1 Banheiro</div>
  <div class="info__tag">1 Vaga</div>
</body>
</html>
"""

SAMPLE_METADATA_JS = """
dgCidadesBairros.prototype = {
  cidades : [
    ['','- todas as cidades -'],
    ['timoteo','Timóteo'],
    ['ipatinga','Ipatinga']
  ],
  bairros : [
    [''],
    ['Eldorado', 'Timirim'],
    ['Centro']
  ],
  bairros_value : [
    [''],
    ['eldorado-498991', 'timirim-498235'],
    ['centro-499035']
  ]
};
"""


def test_search_page_parser():
    """Verify search parser extracts listings and ignores dummy pagination card."""
    parser = SearchPageParser()
    collection = parser.parse(SAMPLE_SEARCH_HTML, page_number=1)

    assert len(collection) == 1
    assert collection.pagination.current_page == 1
    assert collection.pagination.has_next_page is True

    item = collection[0]
    assert item.identity.property_id == "3561797"
    assert item.identity.reference_code == "IM0670"
    assert item.identity.property_type == "Apartamento"
    assert item.location.neighborhood == "Eldorado"
    assert item.location.city == "Timóteo"
    assert item.location.state == "MG"
    assert item.specs.bedrooms == 3
    assert item.specs.bathrooms == 1
    assert item.specs.suites == 1
    assert item.specs.parking_spaces == 1
    assert item.price_text == "R$ 1.500"


def test_property_detail_parser():
    """Verify property detail parser extracts JSON-LD, specs, and reference code."""
    parser = PropertyDetailParser()
    detail = parser.parse(SAMPLE_DETAIL_HTML, property_id="3561797", canonical_url="https://site.com/3561797")

    assert detail.overview.property_id == "3561797"
    assert detail.overview.reference_code == "IM0670"
    assert detail.overview.title == "Apartamento para Locação no Eldorado"
    assert detail.pricing.amount == 1500.0
    assert detail.location.neighborhood == "Eldorado"
    assert detail.location.city == "Timóteo"
    assert detail.specs.bedrooms == 3
    assert detail.specs.suites == 1
    assert detail.specs.bathrooms == 1
    assert detail.specs.parking_spaces == 1


def test_photo_gallery_parser():
    """Verify photo gallery parser converts AJAX JSON into full URLs."""
    parser = PhotoGalleryParser(base_url="https://niltoncorretordeimoveis.com.br")
    json_data = '{"0": {"arquivo_imm": "photo1.jpg"}, "1": {"arquivo_imm": "photo2.jpg"}}'
    gallery = parser.parse_ajax_json(json_data)

    assert len(gallery) == 2
    assert gallery[0] == "https://niltoncorretordeimoveis.com.br/imagens/imoveis/photo1.jpg"
    assert gallery[1] == "https://niltoncorretordeimoveis.com.br/imagens/imoveis/photo2.jpg"


def test_metadata_parser():
    """Verify metadata parser extracts cities and neighborhoods with numeric IDs."""
    parser = MetadataParser()
    catalog = parser.parse(SAMPLE_METADATA_JS)

    assert len(catalog) == 2
    timoteo = catalog.find_city_by_slug("timoteo")
    assert timoteo is not None
    assert timoteo.name == "Timóteo"
    assert len(timoteo.neighborhoods) == 2

    eldorado = timoteo.find_neighborhood_by_slug("eldorado-498991")
    assert eldorado is not None
    assert eldorado.name == "Eldorado"
    assert eldorado.numeric_id == "498991"


def test_search_parser_exposes_absolute_public_url_and_preserves_path():
    """Resolve the listing URL without discarding the card's native path."""
    listing = SearchPageParser().parse(SAMPLE_SEARCH_HTML)[0]

    assert listing.identity.url_path == (
        "/imovel/3561797/apartamento-locacao-timoteo-mg-eldorado"
    )
    assert getattr(listing, "url", None) == (
        "https://niltoncorretordeimoveis.com.br"
        "/imovel/3561797/apartamento-locacao-timoteo-mg-eldorado"
    )


def test_search_parser_rejects_non_public_property_links():
    """Reject schemes, image/search destinations, and site roots."""
    import pytest

    invalid_links = (
        "javascript:alert(1)",
        "https://evil.example/imovel/3561797/apartamento",
        "https://niltoncorretordeimoveis.com.br/imagens/3561797.jpg",
        "https://niltoncorretordeimoveis.com.br/imovel/locacao/todos/timoteo",
        "https://niltoncorretordeimoveis.com.br/",
    )
    for invalid_link in invalid_links:
        invalid_html = SAMPLE_SEARCH_HTML.replace(
            'data-link="/imovel/3561797/apartamento-locacao-timoteo-mg-eldorado"',
            f'data-link="{invalid_link}"',
        ).replace('href="/imovel/3561797"', f'href="{invalid_link}"')
        with pytest.raises(ValueError, match="invalid public URL"):
            SearchPageParser().parse(invalid_html)


def test_scripts_search_serializes_url_and_preserves_path():
    """Expose the public URL in the script-layer listing serializer."""
    from scripts.client.parsers import SearchResultParser

    result = SearchResultParser().parse_search_response(SAMPLE_SEARCH_HTML)
    listing = result.to_dictionary()["listings"][0]

    assert listing["url"] == (
        "https://niltoncorretordeimoveis.com.br"
        "/imovel/3561797/apartamento-locacao-timoteo-mg-eldorado"
    )
    assert listing["url_path"] == (
        "/imovel/3561797/apartamento-locacao-timoteo-mg-eldorado"
    )


def test_scripts_search_rejects_non_public_property_links():
    """Reject schemes, image/search destinations, and site roots."""
    import pytest

    from scripts.client.parsers import SearchResultParser

    invalid_links = (
        "javascript:alert(1)",
        "https://evil.example/imovel/3561797/apartamento",
        "https://niltoncorretordeimoveis.com.br/imagens/3561797.jpg",
        "https://niltoncorretordeimoveis.com.br/imovel/locacao/todos/timoteo",
        "https://niltoncorretordeimoveis.com.br/",
    )
    for invalid_link in invalid_links:
        invalid_html = SAMPLE_SEARCH_HTML.replace(
            'data-link="/imovel/3561797/apartamento-locacao-timoteo-mg-eldorado"',
            f'data-link="{invalid_link}"',
        ).replace('href="/imovel/3561797"', f'href="{invalid_link}"')
        with pytest.raises(ValueError, match="invalid public URL"):
            SearchResultParser().parse_search_response(invalid_html)


def test_search_parser_normalizes_absolute_and_protocol_relative_links():
    """Preserve card paths and identifying queries for both URL forms."""
    path = "/imovel/3561797/apartamento-locacao-timoteo-mg-eldorado?id=608"
    route = path.split("?", maxsplit=1)[0]
    for source in (
        f"https://niltoncorretordeimoveis.com.br{path}",
        f"//niltoncorretordeimoveis.com.br{path}",
    ):
        html = SAMPLE_SEARCH_HTML.replace(f'data-link="{route}"', f'data-link="{source}"')
        listing = SearchPageParser().parse(html)[0]
        assert listing.identity.url_path == source
        assert listing.url == f"https://niltoncorretordeimoveis.com.br{path}"


def test_search_parser_uses_anchor_fallback_and_rejects_missing_urls():
    """Resolve only a real detail anchor when a canonical link is absent."""
    import pytest

    from nilton_research.domain.listing import InvalidPublicPropertyUrlError

    html = SAMPLE_SEARCH_HTML.replace(
        ' data-link="/imovel/3561797/apartamento-locacao-timoteo-mg-eldorado"', ""
    )
    listing = SearchPageParser().parse(html)[0]
    assert listing.identity.url_path == "/imovel/3561797"
    assert listing.url == "https://niltoncorretordeimoveis.com.br/imovel/3561797"

    unrecoverable = html.replace('href="/imovel/3561797"', "")
    with pytest.raises(InvalidPublicPropertyUrlError, match="recoverable"):
        SearchPageParser().parse(unrecoverable)


def test_scripts_search_normalizes_absolute_and_protocol_relative_links():
    """Preserve script-layer URL paths and identifying queries."""
    from scripts.client.parsers import SearchResultParser

    path = "/imovel/3561797/apartamento-locacao-timoteo-mg-eldorado?id=608"
    route = path.split("?", maxsplit=1)[0]
    for source in (
        f"https://niltoncorretordeimoveis.com.br{path}",
        f"//niltoncorretordeimoveis.com.br{path}",
    ):
        html = SAMPLE_SEARCH_HTML.replace(f'data-link="{route}"', f'data-link="{source}"')
        listing = SearchResultParser().parse_search_response(html).to_dictionary()["listings"][0]
        assert listing["url_path"] == source
        assert listing["url"] == f"https://niltoncorretordeimoveis.com.br{path}"


def test_scripts_search_uses_anchor_fallback_and_rejects_missing_urls():
    """Use a real detail anchor and reject cards with no usable link."""
    import pytest

    from scripts.client.parsers import SearchResultParser
    from scripts.domain.exceptions import InvalidPublicPropertyUrlException

    html = SAMPLE_SEARCH_HTML.replace(
        ' data-link="/imovel/3561797/apartamento-locacao-timoteo-mg-eldorado"', ""
    )
    listing = SearchResultParser().parse_search_response(html).to_dictionary()["listings"][0]
    assert listing["url_path"] == "/imovel/3561797"
    assert listing["url"] == "https://niltoncorretordeimoveis.com.br/imovel/3561797"

    unrecoverable = html.replace('href="/imovel/3561797"', "")
    with pytest.raises(InvalidPublicPropertyUrlException, match="recoverable"):
        SearchResultParser().parse_search_response(unrecoverable)


def test_scripts_search_serializes_zero_and_multiple_results():
    """Serialize empty and multi-listing responses without count drift."""
    from scripts.client.parsers import SearchResultParser

    empty = SearchResultParser().parse_search_response("<html></html>").to_dictionary()
    second_card = (
        '<div class="imovelcard" data-link="/imovel/3561798/apartamento">'
        '<div class="imovelcard__info"><h2 class="imovelcard__info__local">Centro, Timóteo / MG</h2></div>'
        "</div>"
    )
    multi_html = SAMPLE_SEARCH_HTML.replace("</body>", f"{second_card}</body>")
    multiple = SearchResultParser().parse_search_response(multi_html).to_dictionary()

    assert empty["returned_count"] == 0
    assert len(multiple["listings"]) == 2
    assert multiple["returned_count"] == 2


def test_research_runner_prints_public_property_url(capsys):
    """Print each public listing URL in the existing verification runner."""
    from scripts.verify_research import run_target_search

    results = SearchPageParser().parse(SAMPLE_SEARCH_HTML)

    class StubClient:
        def search(self, criteria):
            return results

    run_target_search(StubClient())

    assert "Link: https://niltoncorretordeimoveis.com.br/imovel/3561797/" in (
        capsys.readouterr().out
    )


def test_adapter_listing_serializer_rejects_missing_and_relative_public_urls():
    """Reject manually constructed adapter listings with unusable public URLs."""
    from dataclasses import replace

    import pytest

    from scripts.client.parsers import SearchResultParser
    from scripts.domain.exceptions import InvalidPublicPropertyUrlException

    listing = SearchResultParser().parse_search_response(SAMPLE_SEARCH_HTML).listings().listings[0]
    for url in ("", "/imovel/3561797"):
        public_link = replace(listing.details.media.public_link, url=url)
        media = replace(listing.details.media, public_link=public_link)
        details = replace(listing.details, media=media)
        invalid_listing = replace(listing, details=details)
        with pytest.raises(InvalidPublicPropertyUrlException, match="3561797"):
            invalid_listing.to_dictionary()


def test_malformed_core_card_links_raise_the_local_public_url_exception():
    """Wrap malformed canonical links and detail anchors with URL context."""
    import pytest

    from nilton_research.domain.listing import InvalidPublicPropertyUrlError

    malformed_link = "https://[broken/imovel/3561797"
    canonical_html = SAMPLE_SEARCH_HTML.replace(
        'data-link="/imovel/3561797/apartamento-locacao-timoteo-mg-eldorado"',
        f'data-link="{malformed_link}"',
    )
    anchor_html = SAMPLE_SEARCH_HTML.replace(
        ' data-link="/imovel/3561797/apartamento-locacao-timoteo-mg-eldorado"', ""
    ).replace('href="/imovel/3561797"', f'href="{malformed_link}"')

    for invalid_html in (canonical_html, anchor_html):
        with pytest.raises(InvalidPublicPropertyUrlError, match="malformed public URL") as error:
            SearchPageParser().parse(invalid_html)
        assert malformed_link in str(error.value)


def test_malformed_adapter_card_links_raise_the_local_exception():
    """Wrap malformed adapter links and detail anchors with URL context."""
    import pytest

    from scripts.client.parsers import SearchResultParser
    from scripts.domain.exceptions import InvalidPublicPropertyUrlException

    malformed_link = "https://[broken/imovel/3561797"
    canonical_html = SAMPLE_SEARCH_HTML.replace(
        'data-link="/imovel/3561797/apartamento-locacao-timoteo-mg-eldorado"',
        f'data-link="{malformed_link}"',
    )
    anchor_html = SAMPLE_SEARCH_HTML.replace(
        ' data-link="/imovel/3561797/apartamento-locacao-timoteo-mg-eldorado"', ""
    ).replace('href="/imovel/3561797"', f'href="{malformed_link}"')

    for invalid_html in (canonical_html, anchor_html):
        with pytest.raises(InvalidPublicPropertyUrlException, match="malformed public URL") as error:
            SearchResultParser().parse_search_response(invalid_html)
        assert malformed_link in str(error.value)
