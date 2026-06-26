"""
Extractor KIA (complejidad media).

Emisor KIA ARGENTINA. Campos etiquetados pero muy concatenados. El nombre del
modelo aparece como linea suelta despues de los datos del chasis (ej: K2500).
Solo se lee la pagina 1.
"""
import re

from .base_extractor import BaseExtractor


class KiaExtractor(BaseExtractor):
    brand = "KIA"

    def extract(self):
        r = self.base_result()
        text = self.text

        r["model_code"] = self.search(r"CODIGO DEMODELO:\s*(\S+)", text)
        r["vin"] = self.search(r"NUMERO DECHASIS:\s*([A-Z0-9]{17})", text)
        r["interno"] = self.compute_interno(r["vin"])
        r["engine_number"] = self.search(r"NUMERO DEMOTOR:\s*(\S+)", text)
        # Color: en la linea que tiene "MODELO: COLOR:BLANCO CLARO".
        r["color_name"] = self.search(r"COLOR:\s*(.+)", text)
        # Nombre de modelo: linea suelta luego de "MARCA:KIA".
        r["model_name"] = self.search(
            r"MARCA:\s*KIA\s*\r?\n\s*([A-Za-z0-9][A-Za-z0-9\- ]*)", text
        )
        return r
