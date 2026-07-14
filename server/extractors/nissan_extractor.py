"""
Extractor Nissan (complejidad media).

Campos etiquetados pero concatenados. Solo se lee la pagina 1.
"""
from .base_extractor import BaseExtractor


class NissanExtractor(BaseExtractor):
    brand = "NISSAN"

    def extract(self):
        r = self.base_result()
        text = self.text

        r["vin"] = self.search(r"VIN:\s*([A-Z0-9]{17})", text)
        r["interno"] = self.compute_interno(r["vin"])
        r["engine_number"] = self.search(r"MOTOR NRO:\s*(\S+)", text)
        # Certificado: viene pegado al despacho y al chasis ("...CERTIFICADO: 08-0160907/2026CHASIS...").
        r["certificate"] = self.search(r"CERTIFICADO:\s*([0-9][0-9\-/]+)", text)
        # Color: desde "COLOR:" hasta "VIN:".
        r["color_name"] = self.search(r"COLOR:\s*(.+?)(?=VIN:)", text)
        # Modelo (nombre): no hay codigo en la factura, se usa el nombre.
        r["model_name"] = self.search(r"MODELO:\s*(.+)", text)
        return r
