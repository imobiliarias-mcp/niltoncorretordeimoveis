"""HTTP transport abstractions and implementations."""

from dataclasses import dataclass
from typing import Protocol
import httpx


class PropertyNotFoundError(Exception):
    """Raised when a requested property listing does not exist."""


@dataclass(frozen=True)
class HttpResponse:
    """Encapsulates HTTP response data."""

    status_code: int
    text: str
    final_url: str
    headers: dict[str, str]


class HttpClientProtocol(Protocol):
    """Protocol for HTTP client implementations."""

    def get(self, url: str, headers: dict[str, str] | None = None) -> HttpResponse:
        """Execute HTTP GET request."""
        ...


class HttpxHttpClient:
    """Default HTTP client adapter backed by httpx."""

    def __init__(self, timeout: float = 20.0) -> None:
        """Initialize HTTP client."""
        self._timeout = timeout
        self._default_headers = {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        }

    def get(self, url: str, headers: dict[str, str] | None = None) -> HttpResponse:
        """Execute GET request with redirect resolution."""
        merged_headers = self._merge_headers(headers)
        with httpx.Client(timeout=self._timeout, follow_redirects=True) as client:
            resp = client.get(url, headers=merged_headers)
            # Use Latin1 encoding default if response is iso-8859-1
            text = resp.text
            return HttpResponse(
                status_code=resp.status_code,
                text=text,
                final_url=str(resp.url),
                headers=dict(resp.headers),
            )

    def _merge_headers(self, headers: dict[str, str] | None) -> dict[str, str]:
        """Merge default headers with custom overrides."""
        merged = dict(self._default_headers)
        if headers is not None:
            merged.update(headers)
        return merged
