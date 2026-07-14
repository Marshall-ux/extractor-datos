"""
Extractor Inchcape: Subaru y Suzuki comparten el mismo formato de factura
(emisores INCHCAPE ARGENTINA / DISTRIBUIDORA AUTOMOTRIZ ARGENTINA).

Formato limpio con campos etiquetados. El codigo de modelo ya viene en la
factura (ej: ARCRTK02, ARSW0005). Solo se lee la pagina 1.
"""
import re

from .base_extractor import BaseExtractor


class InchcapeExtractor(BaseExtractor):
    brand = "INCHCAPE"  # se ajusta a SUBARU/SUZUKI en __init__

    def __init__(self, text, brand=None):
        super().__init__(text)
        if brand:
            self.brand = brand
        elif re.search(r"Marca:\s*Suzuki", text, re.I):
            self.brand = "SUZUKI"
        elif re.search(r"Marca:\s*Subaru", text, re.I):
            self.brand = "SUBARU"

    def extract(self):
        r = self.base_result()
        text = self.text

        r["model_code"] = self.search(r"Modelo:\s*(\S+)", text)
        r["vin"] = self.search(r"Chasis:\s*(\S+)", text)
        r["interno"] = self.compute_interno(r["vin"])
        r["engine_number"] = self.search(r"Motor:\s*(\S+)", text)
        r["certificate"] = self.search(r"Certificado\s*N.:\s*(\S+)", text)
        r["color_name"] = self.search(r"Color:\s*(.+)", text)
        r["model_name"] = self._model_name(text, r["model_code"])
        return r

    def _model_name(self, text, model_code):
        """'Modelo Comercial:' + parte de la linea siguiente (antes del codigo/precio)."""
        m = re.search(r"Modelo Comercial:\s*(.+)", text)
        if not m:
            return None
        name = m.group(1).strip()
        lines = text.splitlines()
        for i, ln in enumerate(lines):
            if "Modelo Comercial:" in ln and i + 1 < len(lines):
                nxt = lines[i + 1].strip()
                if model_code and model_code in nxt:
                    nxt = nxt[:nxt.index(model_code)]
                else:
                    # Cortar antes del precio (primer numero con separadores).
                    nxt = re.split(r"\s*\d[\d.,]*", nxt)[0]
                nxt = nxt.strip()
                if nxt:
                    name = f"{name} {nxt}".strip()
                break
        return name
