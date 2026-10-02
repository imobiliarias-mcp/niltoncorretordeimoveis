"""Domain enumerations for rental and sales criteria."""

from enum import Enum


class TransactionType(str, Enum):
    """Transaction purpose."""

    LOCACAO = "locacao"
    VENDA = "venda"


class PropertyType(str, Enum):
    """Property categories available on the portal."""

    TODOS = "todos"
    APARTAMENTO = "apartamento"
    CASA = "casa"
    FLAT = "flat"
    KITNET = "kitnet"
    LOJA = "loja"
    LOTE = "lote"
    SALA_COMERCIAL = "sala-comercial"
    COBERTURA = "cobertura"
    SITIO = "sitio"
    CHACARA = "chacara"
    GALPAO = "galpao"
    CASA_GEMINADA = "casa-geminada"
    BARRACAO = "barracao"


class SortOrder(str, Enum):
    """Listing sort orders."""

    DEFAULT = ""
    MENOR_VALOR = "menor_valor"
    MAIOR_VALOR = "maior_valor"
    RECENTES = "recentes"
