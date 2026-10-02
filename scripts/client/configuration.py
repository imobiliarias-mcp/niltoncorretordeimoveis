"""Configuration settings for Nilton Corretor de Imóveis API client."""

from dataclasses import dataclass


@dataclass(frozen=True)
class NiltonConfiguration:
    """Holds configuration parameters for portal communication."""

    base_hostname: str = "niltoncorretordeimoveis.com.br"
    base_url: str = "https://niltoncorretordeimoveis.com.br"

    def origin_header_value(self) -> str:
        """Return canonical portal origin."""
        return f"https://{self.base_hostname}"

    def referer_header_value(self) -> str:
        """Return canonical portal referer."""
        return f"https://{self.base_hostname}/"

    def public_site_base_url(self) -> str:
        """Return the configured public listing-site origin."""
        return f"https://{self.base_hostname}"
