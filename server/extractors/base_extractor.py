"""
Clase base para los extractores por marca.

Cada extractor recibe el texto de la primera pagina y devuelve un dict con los
campos normalizados. La logica comun (interno, motor, color) vive aqui.
"""
import re


class BaseExtractor:
    brand = None

    def __init__(self, text):
        self.text = text or ""

    # --- a implementar por cada marca --- #
    def extract(self):
        """Devuelve un dict con los campos extraidos."""
        raise NotImplementedError

    # --- helpers comunes --- #
    @staticmethod
    def search(pattern, text, flags=0, group=1):
        m = re.search(pattern, text, flags)
        if not m:
            return None
        return m.group(group).strip()

    @staticmethod
    def compute_interno(vin):
        """INTERNO = ultimos 8 caracteres del VIN."""
        if not vin:
            return None
        return vin[-8:]

    def base_result(self):
        """Estructura base con valores por defecto."""
        return {
            "brand": self.brand,
            "model_code": None,
            "model_name": None,
            "vin": None,
            "interno": None,
            "engine_number": None,
            "year": None,          # anio del vehiculo (si la factura lo trae)
            "certificate": None,   # Nro. de certificado de fabrica
            "is_hybrid": False,
            "is_electric": False,
            "color_name": None,   # color crudo extraido (previo a lookup)
            "color_code": None,
            "raw_text": self.text,
        }
