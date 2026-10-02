"""Parser for photo gallery AJAX responses."""

import json
from nilton_research.domain.property import PhotoGallery


class PhotoGalleryParser:
    """Parses JSON response from /t27/lista_imoveis_fotos.php into PhotoGallery."""

    def __init__(self, base_url: str = "https://niltoncorretordeimoveis.com.br") -> None:
        """Initialize parser."""
        self._image_base = f"{base_url.rstrip('/')}/imagens/imoveis"

    def parse_ajax_json(self, json_text: str) -> PhotoGallery:
        """Parse AJAX JSON string into PhotoGallery."""
        if not json_text or not json_text.strip():
            return PhotoGallery(())
        try:
            payload = json.loads(json_text)
        except json.JSONDecodeError:
            return PhotoGallery(())

        urls: list[str] = []
        entries = payload.values() if isinstance(payload, dict) else payload
        for item in entries:
            if not isinstance(item, dict):
                continue
            filename = item.get("arquivo_imm")
            if filename:
                urls.append(f"{self._image_base}/{filename}")
        return PhotoGallery(tuple(urls))
