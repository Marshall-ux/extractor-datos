"""
Extractor BYD (alta complejidad).

El texto del PDF viene desordenado y concatenado. El color se resuelve luego
en data_extractor buscando la descripcion de la planilla BYD dentro del texto
(exterior/interior). El nombre de modelo se deriva de la linea de descripcion
final ("BYD SHARK DMO GS PALLAS WHITE BLACK") quitando el prefijo y el color.
"""
import re

from .base_extractor import BaseExtractor


class BydExtractor(BaseExtractor):
    brand = "BYD"

    def extract(self):
        r = self.base_result()
        text = self.text

        r["model_code"] = self.search(r"(\d{8}-\d{2})", text)
        # El VIN viene concatenado con texto adyacente, sin limites de palabra.
        r["vin"] = self.search(r"(L[A-Z0-9]{16})", text)
        r["interno"] = self.compute_interno(r["vin"])

        # Motor naftero: BYD + 3 digitos + 2 letras + resto.
        r["engine_number"] = self.search(r"(BYD\d{3}[A-Z]{2}\S+)", text)

        # Motores electricos (uno o mas): TZ + 3 digitos + X + resto.
        electric = re.findall(r"TZ\d{3}X\S*", text)
        if electric:
            if r["engine_number"]:
                # Tiene motor naftero y electrico -> hibrido. Se conserva el naftero.
                r["is_hybrid"] = True
            else:
                # Solo electrico: el numero de motor es el electrico.
                r["engine_number"] = electric[0].rstrip("/")
                r["is_electric"] = True

        # Anio: aparece pegado a la etiqueta "Modelo" del bloque de encabezados
        # ("2025Modelo"). BYD no emite certificado de fabrica: queda sin valor.
        r["year"] = self.search(r"(20\d{2})Modelo", text)

        # Linea de descripcion para derivar modelo y color (la final, mas limpia).
        r["_desc_line"] = self._description_line(text)
        return r

    @staticmethod
    def _description_line(text):
        """Texto de descripcion luego del ultimo 'BYD ' hasta fin de linea.

        Ej: '...45.700.00BYD SHARK DMO GS PALLAS WHITE BLACK' -> devuelve
        'SHARK DMO GS PALLAS WHITE BLACK' (modelo + color exterior/interior).
        """
        idx = text.rfind("BYD ")
        if idx == -1:
            return None
        tail = text[idx + 4:].splitlines()[0].strip()
        return tail or None
