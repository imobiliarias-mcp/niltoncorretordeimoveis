# Nilton Corretor de Imóveis — Central Rental Research MCP Provider

Reverse-engineered rental search engine and API client for **Nilton Corretor de Imóveis** (`https://niltoncorretordeimoveis.com.br/`).

Engineered as a pluggable adapter for the **Central Rental Research MCP (Model Context Protocol)** server following **SOLID**, **Clean Code**, **Object Calisthenics**, and **Design Patterns** in Python, operating as a sister provider to **Epifânio Imóveis** and **Casa Linhares**.

---

## 📚 Documentation

- **[Reverse Engineering Analysis](docs/api-research.md)** (`docs/api-research.md`): Reverse-engineering technical specification, endpoint contracts, parameters, DOM selectors, and photo gallery AJAX endpoints.
- **[Research Plan & Findings Report](scripts/research-plan.md)** (`scripts/research-plan.md`): Reverse-engineering methodology, probing log, architectural design, and verification evidence.

---

## ⚡ Quickstart

### Environment Setup
```bash
uv venv
source .venv/bin/activate
uv pip install beautifulsoup4 httpx pytest
```

### Run Automated Unit & Live Integration Tests
```bash
pytest -v
```

### Run Live Research Verification Runner
```bash
python3 scripts/verify_research.py
```

---

## 🏛️ Code Architecture & Standards Compliance

- **No `else` Keyword**: 100% eliminated using guard clauses, early returns, and polymorphic handlers.
- **Single Level of Indentation**: All methods adhere to at most 1 indent level.
- **Wrapped Primitives**: Domain concepts (`PriceRange`, `AreaRange`, `RoomCount`, `PageNumber`, `PropertyCode`, `ListingPrice`) are immutable Value Objects.
- **First-Class Collections**: `ListingCollection`, `PhotoGallery`, `LocationCatalog`, and `RentalListingCollection` wrap items without leaking raw mutable collections.
- **Size Limits**: Functions ≤ 15 lines, Classes ≤ 100 lines, Modules < 200 lines.
- **Instance Variables**: All classes hold at most 2 instance variables (using collaborator bundles).
- **One Dot per Line**: Method chaining is eliminated in favor of explicit intermediate assignments.
- **Zero Abbreviations**: Clear, descriptive domain naming across all modules.
