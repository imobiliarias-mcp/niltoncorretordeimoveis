# Reverse-Engineered API Specification: Nilton Corretor de Imóveis

## 1. Overview & Architecture

Nilton Corretor de Imóveis (`https://niltoncorretordeimoveis.com.br`) is an established real estate agency portal operating in the Vale do Aço region (Timóteo, Coronel Fabriciano, Ipatinga, and neighboring municipalities in Minas Gerais, Brazil).

The portal is built on top of the **ImobiBrasil** SaaS real estate platform, using template `t27` / `t32` (`/t27/js/lista_imoveis.js`, `/t27/lista_imoveis_fotos.php`).

The portal delivers server-side rendered HTML (charset `ISO-8859-1` / Latin1) augmented with structured microdata (`Schema.org` JSON-LD), inline JavaScript location catalogs (`dgCidadesBairros`), and a dedicated AJAX JSON endpoint for property photo galleries.

### 1.1 Authentication & Security Requirements
- **Authentication**: **None required**. All rental and sales listing searches, filter queries, pagination endpoints, property detail pages, location metadata, and photo galleries are publicly accessible without authentication, session cookies, API keys, or CSRF tokens.
- **Request Headers**: Standard desktop/mobile `User-Agent` is recommended to prevent generic Cloudflare bot protection challenges.
- **HTTP Methods**: All search, filtering, pagination, detail retrieval, and media operations strictly use `GET`.
- **Content Encoding**: Server returns `text/html; charset=iso-8859-1`. Parsers must decode using `iso-8859-1` (or Latin1) to preserve Portuguese accents (`Timóteo`, `Funcionários`, `São João Do Oriente`, etc.).

---

## 2. Rental & Sales Search Endpoints

The search engine maps high-level criteria into hierarchical SEO paths and query string parameters.

### 2.1 Canonical Search Routing Pattern

```http
GET /imovel/{finalidade}/{tipo}/{cidade}/{bairro}/?&{query_parameters} HTTP/1.1
Host: niltoncorretordeimoveis.com.br
```

#### Path Variables
| Segment | Type | Allowed Values | Description |
| :--- | :--- | :--- | :--- |
| `{finalidade}` | `string` | `locacao`, `venda` | Transaction purpose (`locacao` for rentals, `venda` for sales). |
| `{tipo}` | `string` | `todos`, `apartamento`, `casa`, `flat`, `kitnet`, `loja`, `lote`, `sala-comercial`, `cobertura`, `sitio`, `chacara`, `galpao`, `casa-geminada`, `barracao` | Property category. Default is `todos`. |
| `{cidade}` | `string` | `todos`, `timoteo`, `coronel-fabriciano`, `ipatinga`, `antonio-dias`, `bom-jesus-do-galho`, `caratinga`, `jaguaracu`, `marlieria`, `pingo_d\`agua`, `sao-joao-do-oriente` | City slug. Target default is `timoteo`. |
| `{bairro}` *(Optional)* | `string` | e.g. `eldorado-498991`, `timirim-498235`, `funcionarios-498264` | Single neighborhood slug with numeric ID. (When filtering multiple neighborhoods, this segment is omitted and `?&bairros=` is used instead). |

#### Routing & Normalization Rules
1. **Friendly URL Redirection**: Accessing `/imovel?finalidade=locacao&cidade=timoteo` triggers an HTTP 302 redirect to canonical `/imovel/locacao/todos/timoteo`.
2. **Single Neighborhood Redirection**: Passing query parameter `?&bairro=eldorado-498991` redirects via HTTP 302 to the path `/imovel/locacao/todos/timoteo/eldorado-498991`.
3. **Query Prefix Convention**: ImobiBrasil search forms format query parameters prefixed by `/?&` (e.g. `/imovel/locacao/todos/timoteo/?&dormitorios=3&vma=2000`). If accessed with `?pag=2`, the server issues a 302 redirect to `/?&pag=2`.

---

## 3. Request Parameters & Filter Behavior

All search filters can be combined in the query string:

| Parameter | Type | Example Values | Internal Platform Logic / Description |
| :--- | :--- | :--- | :--- |
| `dormitorios` | `integer` | `1`, `2`, `3`, `4`, `5`, `21`, `22`, `23`, `24`, `25` | **Bedrooms constraint**.<br>• Exact count: values `1` through `5`.<br>• Minimum ("N or more"): values `20 + N` (`21` for 1+, `22` for 2+, `23` for 3+, etc.). |
| `suites` | `integer` | `1`, `2`, `3`, `4`, `5`, `21`, `22`, `23`, `24`, `25` | **Suites constraint**.<br>• Exact count: `1`..`5`.<br>• Minimum: `21`..`25`. |
| `banheiros` | `integer` | `1`, `2`, `3`, `4`, `5`, `21`, `22`, `23`, `24`, `25` | **Bathrooms constraint**.<br>• Exact count: `1`..`5`.<br>• Minimum: `21`..`25`. |
| `vagas` | `integer` | `1`, `2`, `3`, `4`, `5`, `21`, `22`, `23`, `24`, `25` | **Parking spaces constraint**.<br>• Exact count: `1`..`5`.<br>• Minimum: `21`..`25`. |
| `vmi` | `integer` | `1000` | **Minimum value** (Valor Mínimo) in BRL. |
| `vma` | `integer` | `2500` | **Maximum value** (Valor Máximo) in BRL. |
| `areaMinima` | `integer` | `50` | Minimum built/land area in m². |
| `areaMaxima` | `integer` | `300` | Maximum built/land area in m². |
| `bairros` | `string` | `498991,498264` | Comma-separated list of numeric neighborhood IDs for multi-neighborhood filtering. |
| `ord` | `string` | `menor_valor`, `maior_valor`, `recentes` | Listing sort order. |
| `pag` | `integer` | `1`, `2`, `3`... | 1-indexed page number. Default is 1. |
| `ref` | `string` | `IM0670` | Property reference code. |
| `reftipo` | `string` | `exata` | Match precision for reference search (`exata`). |

---

## 4. Pagination Behavior

- **Page Size**: **15 listings per page** across all search categories.
- **Query Parameter**: `&pag={N}` (e.g. `/?&pag=2` or `/?&dormitorios=2&pag=2`).
- **DOM Pagination Block**:
  - Container class: `.lista_imoveis_paginacao`
  - Current active page element: `a.lipagina-btn-paginacao-atual`
  - Other page links: `a.lipagina-btn-paginacao`
  - Next page button: `a.lipagina-btn-paginacao[title="Próxima Página"]` containing text `>`.
  - Previous page button: `a.lipagina-btn-paginacao[title="Página Anterior"]` containing text `<`.
- **Critical DOM Quirk - Dummy Pagination Card**:
  - In ImobiBrasil template `t27`, the `.lista_imoveis_paginacao` block is enclosed in a `<div class="imovelcard" style="background-color:unset;">`.
  - **Important parsing rule**: Genuine listing cards always contain the attribute `data-link` (e.g. `data-link="/imovel/3561797/apartamento-locacao-timoteo-mg-eldorado"`).
  - To prevent counting or parsing the pagination block as a property, selectors must strictly target `.imovelcard[data-link]` or verify `card.get('data-link') is not None`.
- **Termination / Out-of-Bounds Behavior**:
  - Requesting an out-of-bounds page (e.g. `pag=3` when only 22 listings exist) returns HTTP 200 with **0** genuine listing cards (`.imovelcard[data-link]`).
  - The client detects end-of-results when the returned list of genuine cards is empty or when no next page link (`>`) is present.

---

## 5. Search Results Card Parsing

Search result cards are rendered with the class `.imovelcard` and carry structured attributes:

### 5.1 Card Structure & Selectors
```html
<div class="imovelcard" data-link="/imovel/3561797/apartamento-locacao-timoteo-mg-eldorado">
  <div class="row">
    <a class="col imovelcard__img" href="/imovel/3561797/apartamento-locacao-timoteo-mg-eldorado" title="Apartamento para Locação, em Timóteo, bairro Eldorado, 3 dormitórios, 1 banheiro, 1 suíte, 1 vaga">
      <img src="https://imgs2.cdn-imobibrasil.com.br/imagens/imoveis/thumb15-202504231737173044.jpeg" />
    </a>
    <div class="col imovelcard__infocontainer">
      <div class="row imovelcard__infotopcontainer">
        <div class="col imovelcard__info">
          <h2 class="imovelcard__info__tag">Locação</h2>
          <h2 class="imovelcard__info__local">Eldorado, Timóteo / MG</h2>
          <p class="imovelcard__info__ref"><strong>Ref: IM0670</strong> - Apartamento</p>
          <div class="imovelcard__info__feature"><i class="fa fa-bed"></i><p><b>3</b><span>Dormitórios</span></p></div>
          <div class="imovelcard__info__feature"><i class="fa fa-shower"></i><p><b>1</b><span>Banheiro</span></p></div>
          <div class="imovelcard__info__feature"><i class="fa fa-car"></i><p><b>1</b><span>Vaga</span></p></div>
          <div class="imovelcard__info__feature"><i class="fa fa-bath"></i><p><b>1</b><span>Suíte</span></p></div>
        </div>
        <div class="col imovelcard__valor">
          <p class="imovelcard__valor__valor"><span>R$</span> 1.500</p>
        </div>
      </div>
    </div>
  </div>
</div>
```

### 5.2 Field Extraction Matrix
| Domain Field | DOM Selector / Expression | Example Extracted Value |
| :--- | :--- | :--- |
| `property_id` | Numeric segment from the card's property route | `3561797` |
| `url_path` | Original `data-link`, or real detail-anchor `href` when absent | `/imovel/3561797/apartamento-locacao-timoteo-mg-eldorado` |
| `url` | `url_path` resolved against the configured public site origin | `https://niltoncorretordeimoveis.com.br/imovel/3561797/apartamento-locacao-timoteo-mg-eldorado` |
| `title` | `card.select_one('.imovelcard__img')['title']` | `Apartamento para Locação, em Timóteo...` |
| `thumbnail_url` | `card.select_one('.imovelcard__img img')['src']` | `https://imgs2.cdn-imobibrasil.com.br/...` |
| `neighborhood` | `.imovelcard__info__local` text before `,` | `Eldorado` |
| `city` | `.imovelcard__info__local` text between `,` and `/` | `Timóteo` |
| `state` | `.imovelcard__info__local` text after `/` | `MG` |
| `reference_code` | `.imovelcard__info__ref` regex `Ref:\s*([A-Za-z0-9_-]+)` | `IM0670` |
| `property_type` | `.imovelcard__info__ref` text after `-` | `Apartamento` |
| `price_text` | `.imovelcard__valor__valor` | `R$ 1.500` or `Consulte` |
| `bedrooms` | `.imovelcard__info__feature i.fa-bed` sibling text | `3` |
| `suites` | `.imovelcard__info__feature i.fa-bath` sibling text | `1` |
| `bathrooms` | `.imovelcard__info__feature i.fa-shower` sibling text | `1` |
| `parking_spaces` | `.imovelcard__info__feature i.fa-car` sibling text | `1` |
| `area_text` | `.imovelcard__info__feature i.fa-arrows-h` sibling text | `80 m²` |

### 5.3 Public Property URL Output

The core listing and collection serializers expose an absolute `url` and preserve the source `url_path`; the script adapter keeps its existing `media_url` and serializes the public `url` and native path as well. Links resolve against the configurable `public_base_url` (default: `https://niltoncorretordeimoveis.com.br`), including relative, absolute, and protocol-relative forms; identifying queries such as `?id=608` are retained. If the canonical `data-link` is missing, the parser uses only an actual card detail-anchor `href`. It does not synthesize a link or fetch property details to discover one. Unsupported schemes, other hosts, image/search destinations, the site root, and non-property routes raise a local URL-validation exception. The existing verification runner prints the public link with each search result.

---

## 6. Property Detail Retrieval

Full property details are available via direct property ID lookup or canonical SEO URL.

### 6.1 Detail Endpoints
- **Direct ID Endpoint**: `GET https://niltoncorretordeimoveis.com.br/imovel/{property_id}`
- **Full SEO Endpoint**: `GET https://niltoncorretordeimoveis.com.br/imovel/{property_id}/{slug}`
- **Non-Existent Property Handling**: Requesting an invalid or non-existent property ID returns an HTTP 302 redirecting to `/` (home page).

### 6.2 Structured Data (Schema.org JSON-LD)
The detail page embeds rich microdata:
- `RentAction` (or `BuyAction` for sales):
  - `price`: Exact float string (e.g. `"1500.00"`).
  - `priceSpecification.priceCurrency`: Currency (`BRL`).
  - `object.address.addressLocality`: Municipality (`"Timóteo"`).
  - `object.address.addressRegion`: State (`"MG"`).
- `Product`:
  - `mpn`: Property ID (`3561797`).
  - `name`: Full title.
  - `description`: Complete description text.
- `BreadcrumbList`:
  - Hierarchy links and category classification.

### 6.3 HTML Markup Extraction
- Headline: `h1` (`Apartamento para Locação, Timóteo / MG`).
- Reference & Neighborhood: `.imovelcard__info__ref` / `.info__col`.
- Quick Specification Badges: `.imovelcard__info__feature` / `.info__tag`.
- Description Text: `.imovelcard__info__tab__content__descricao` or `.descricao p`.

---

## 7. Property Photo Gallery AJAX Endpoint

While the detail page embeds thumbnail and lead images, all high-resolution images are retrieved via a dedicated internal AJAX endpoint.

### 7.1 AJAX Photos Request
```http
GET /t27/lista_imoveis_fotos.php?imovel={property_id} HTTP/1.1
Host: niltoncorretordeimoveis.com.br
Accept: application/json, text/javascript, */*; q=0.01
```

### 7.2 AJAX Response Payload
```json
{
  "0": {
    "codigo_imo": "3561797",
    "arquivo_imm": "202504231737173044.jpeg"
  },
  "1": {
    "codigo_imo": "3561797",
    "arquivo_imm": "202504231737185237.jpeg"
  },
  "2": {
    "codigo_imo": "3561797",
    "arquivo_imm": "20250423173718383.jpeg"
  },
  "3": {
    "codigo_imo": "3561797",
    "arquivo_imm": "202504231737189466.jpeg"
  }
}
```

### 7.3 Photo URL Resolution
- **Full Image Portal URL**: `https://niltoncorretordeimoveis.com.br/imagens/imoveis/{arquivo_imm}`
- **CDN Direct URL**: `https://imgs2.cdn-imobibrasil.com.br/imagens/imoveis/{arquivo_imm}`
- **Thumbnail URL**: `https://niltoncorretordeimoveis.com.br/imagens/imoveis/thumb15-{arquivo_imm}`

---

## 8. Location Metadata & Catalog Discovery

The search page embeds a JavaScript object named `dgCidadesBairros` containing complete city and neighborhood catalogs.

### 8.1 Municipalities Supported
- `antonio-dias` (Antônio Dias)
- `bom-jesus-do-galho` (Bom Jesus Do Galho)
- `caratinga` (Caratinga)
- `coronel-fabriciano` (Coronel Fabriciano)
- `ipatinga` (Ipatinga)
- `jaguaracu` (Jaguaraçu)
- `marlieria` (Marliéria)
- `pingo_d\`agua` (Pingo-d'Água)
- `sao-joao-do-oriente` (São João Do Oriente)
- `timoteo` (Timóteo)

### 8.2 Neighborhoods in Timóteo
Timóteo has 42 indexed neighborhoods with unique numeric IDs in `dgCidadesBairros`:
- `eldorado-498991` (ID: `498991`)
- `timirim-498235` (ID: `498235`)
- `funcionarios-498264` (ID: `498264`)
- `primavera-498208` (ID: `498208`)
- `centro-499035` (ID: `499035`)
- `alvorada-497513` (ID: `497513`)
- `serenata-498271` (ID: `498271`)
- `bromelias-498245` (ID: `498245`)
- `cachoeira-do-vale-498956` (ID: `498956`)
- `vila-dos-tecnicos-719387` (ID: `719387`)
- *(and 32 others)*

---

## 9. Target URL Reproduction Analysis

### Target URL from Prompt
`https://niltoncorretordeimoveis.com.br/imovel/locacao/todos/timoteo`

### Breakdown
1. **Transaction Purpose (`finalidade`)**: `locacao` (rentals)
2. **Property Type (`tipo`)**: `todos` (all types)
3. **Location (`cidade`)**: `timoteo` (Timóteo / MG)
4. **Behavior**:
   - Page 1 returns 15 genuine listings (`.imovelcard[data-link]`).
   - Page 2 returns remaining listings (e.g. 7 listings, total 22).
   - Page 3 returns 0 listings (out of bounds).
   - Filtering by bedrooms (`dormitorios=3`), maximum price (`vma=2000`), or reference (`ref=IM0670`) executes server-side matching and returns filtered listing collections.
