"""
Extractor BYD (alta complejidad).

El texto del PDF viene desordenado y concatenado. El color se resuelve luego
en data_extractor buscando la descripcion de la planilla BYD dentro del texto
(exterior/interior). El nombre de modelo se deriva de la linea de descripcion
final ("BYD SHARK DMO GS PALLAS WHITE BLACK") quitando el prefijo y el color.
"""
import re

from .base_extractor import BaseExtractor


def _clean_motor(value):
    """Normaliza un numero de motor: colapsa espacios internos a uno solo y
    quita separadores sueltos ('/') al final."""
    return re.sub(r"\s+", " ", value).strip().rstrip("/").strip()


class BydExtractor(BaseExtractor):
    brand = "BYD"

    def extract(self):
        r = self.base_result()
        text = self.text

        r["model_code"] = self.search(r"(\d{8}-\d{2})", text)
        # El VIN viene concatenado con texto adyacente, sin limites de palabra.
        r["vin"] = self.search(r"(L[A-Z0-9]{16})", text)
        r["interno"] = self.compute_interno(r["vin"])

        # Motor naftero: BYD + 3 digitos + 2 letras + serial. El serial puede
        # venir pegado ('BYD476ZQFT26000079') o separado por un espacio
        # ('BYD472QA 826504695'); en ambos casos se toma completo.
        naftero = self.search(r"(BYD\d{3}[A-Z]{2}\s*[A-Z0-9]+)", text)

        # Motores electricos (uno o mas): TZ + 3 digitos + X + letras + serial,
        # que tambien puede ir separado por un espacio ('TZ180XSX 3P5118355').
        electric = re.findall(r"TZ\d{3}X[A-Z]*\s*[A-Z0-9]+", text)

        if naftero:
            # Hay motor naftero (hibrido si ademas hay electrico). Se toma el
            # naftero completo, que es el que corresponde extraer.
            r["engine_number"] = _clean_motor(naftero)
            r["is_hybrid"] = bool(electric)
        elif electric:
            # Solo electrico (Dolphin, Yuan): el numero de motor es el electrico
            # completo.
            r["engine_number"] = _clean_motor(electric[0])
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
