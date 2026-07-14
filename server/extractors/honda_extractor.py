"""
Extractor Honda (facil).

Emisor Honda Motor de Argentina. Campos etiquetados claros, uno por linea.
Una sola pagina. No trae codigo de modelo explicito: se usa el nombre.
"""
from .base_extractor import BaseExtractor


class HondaExtractor(BaseExtractor):
    brand = "HONDA"

    def extract(self):
        r = self.base_result()
        text = self.text

        r["vin"] = self.search(r"Nro Chasis:\s*(\S+)", text)
        # INTERNO Honda: ultimos 6 digitos del "Equipo Nro:" (viene en la
        # linea siguiente a la etiqueta). Fallback a VIN si no aparece.
        equipo = self.search(r"Equipo Nro:\s*(\d+)", text)
        r["interno"] = equipo[-6:] if equipo else self.compute_interno(r["vin"])
        r["engine_number"] = self.search(r"Nro Motor:\s*(\S+)", text)
        r["year"] = self.search(r"A.o:\s*(\d{4})", text)
        # Certificado: las facturas Honda vistas no lo traen; se extrae si aparece.
        r["certificate"] = self.search(r"Certificado\s*(?:N.)?:\s*([\w\-/]+)", text)
        r["color_name"] = self.search(r"Color:\s*(.+)", text)
        # Nombre de modelo: preferir "Descripcion:", sino "Modelo:".
        r["model_name"] = (
            self.search(r"Descripci.n:\s*(.+)", text)
            or self.search(r"Modelo:\s*(.+?)(?:\s{2,}|$)", text)
        )
        return r
