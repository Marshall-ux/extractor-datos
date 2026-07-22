"""
Orquestador de extraccion.

Flujo: PDF -> texto (pagina 1) -> deteccion de marca -> extractor de marca ->
resolucion de color en planilla -> calculo de confianza/estado.

Devuelve un dict listo para insertar en la tabla extractions.
"""
import re
from datetime import date

from extractors import get_extractor
from services import brand_detector, lookup_service, pdf_parser


def _normalize_year(value):
    """El anio se extrae como texto. Si la factura no lo trae (Nissan, Subaru,
    Suzuki), se usa el anio en curso."""
    if value and str(value).strip().isdigit():
        return int(str(value).strip())
    return date.today().year


def _byd_model_name(desc_line, color_name):
    """Deriva el nombre de modelo BYD quitando el prefijo 'BYD' y las palabras
    del color de la linea de descripcion."""
    if not desc_line:
        return None
    words = desc_line.split()
    if words and words[0].upper() == "BYD":
        words = words[1:]
    color_words = set()
    if color_name:
        color_words = {w for w in re.split(r"[^A-Za-z0-9]+",
                                            lookup_service.normalize(color_name)) if w}
    kept = [w for w in words if lookup_service.normalize(w) not in color_words]
    name = " ".join(kept).strip()
    return name or None


def _assess(result):
    """Calcula confianza y estado segun campos faltantes."""
    critical = [result.get("vin"), result.get("engine_number"),
                result.get("color_code")]
    has_model = bool(result.get("model_code") or result.get("model_name"))
    missing = sum(1 for c in critical if not c) + (0 if has_model else 1)

    if missing == 0:
        result["confidence"] = "high"
        result["status"] = "pending"
    elif missing == 1:
        result["confidence"] = "medium"
        result["status"] = "review"
    else:
        result["confidence"] = "low"
        result["status"] = "review"
    return result


def extract_from_pdf(filepath, filename):
    """Procesa un PDF y devuelve el dict de extraccion."""
    text = pdf_parser.extract_first_page_text(filepath)

    # Fallback: algunas facturas repiten/desplazan contenido en otras paginas.
    if not text.strip():
        text = pdf_parser.extract_all_text(filepath)

    result = {
        "filename": filename,
        "brand": None,
        "model_code": None,
        "model_name": None,
        "vin": None,
        "interno": None,
        "engine_number": None,
        "year": None,
        "certificate": None,
        "is_hybrid": False,
        "is_electric": False,
        "color_name": None,
        "color_code": None,
        "raw_text": text,
    }

    # PDF sin capa de texto (escaneado): no se puede extraer.
    if not text.strip():
        result["confidence"] = "low"
        result["status"] = "review"
        return result

    brand = brand_detector.detect_brand(text)
    extractor = get_extractor(brand, text)
    if extractor is None:
        result["confidence"] = "low"
        result["status"] = "review"
        return result

    fields = extractor.extract()
    desc_line = fields.pop("_desc_line", None)
    result.update(fields)
    result["brand"] = extractor.brand

    # Resolucion de color contra la planilla.
    matched_name, code = lookup_service.resolve_color(
        extractor.brand, result.get("color_name"), result.get("raw_text", ""),
        desc_line,
    )
    if code:
        result["color_code"] = code
        # Para BYD, el nombre de color confiable viene de la planilla.
        if extractor.brand == "BYD":
            result["color_name"] = matched_name

    # Nombre de modelo BYD (derivado de la descripcion y el color).
    if extractor.brand == "BYD" and not result.get("model_name"):
        result["model_name"] = _byd_model_name(desc_line, result.get("color_name"))

    # Resolucion del codigo de modelo en la planilla cuando la factura no lo trae
    # (Nissan, Honda): se busca por el nombre/descripcion del modelo.
    if not result.get("model_code") and result.get("model_name"):
        _, model_code = lookup_service.resolve_model(result["model_name"])
        if model_code:
            result["model_code"] = model_code

    result["year"] = _normalize_year(result.get("year"))

    return _assess(result)
