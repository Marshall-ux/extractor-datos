from .base_extractor import BaseExtractor
from .byd_extractor import BydExtractor
from .nissan_extractor import NissanExtractor
from .inchcape_extractor import InchcapeExtractor
from .kia_extractor import KiaExtractor
from .honda_extractor import HondaExtractor

__all__ = [
    "BaseExtractor",
    "BydExtractor",
    "NissanExtractor",
    "InchcapeExtractor",
    "KiaExtractor",
    "HondaExtractor",
    "get_extractor",
]


def get_extractor(brand, text):
    """Devuelve la instancia de extractor adecuada para la marca detectada."""
    if brand == "BYD":
        return BydExtractor(text)
    if brand == "NISSAN":
        return NissanExtractor(text)
    if brand in ("SUBARU", "SUZUKI"):
        return InchcapeExtractor(text, brand=brand)
    if brand == "KIA":
        return KiaExtractor(text)
    if brand == "HONDA":
        return HondaExtractor(text)
    return None
