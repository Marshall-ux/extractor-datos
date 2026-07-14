"""
Generacion del Excel de salida (formato StImportarNeostar).

Columnas: Marca | Modelo | Chasis | Motor | Año | Color | Ubicación |
          Nro.Certificado | Interno

- Marca: codigo interno de la marca (ver BRAND_CODES). Las marcas sin codigo
  asignado todavia (KIA, SUBARU, SUZUKI) quedan vacias.
- Modelo: codigo del modelo si existe, sino nombre del modelo.
- Chasis: VIN.
- Motor: numero de motor (naftero en hibridos; electrico si solo electrico).
- Año: anio del vehiculo; si la factura no lo trae se usa el anio en curso.
- Color: codigo de color resuelto en la planilla.
- Ubicación: por ahora siempre 'FA' (Fabrica), porque en esta instancia todavia
  no se conocen los arribos. Neostar lo reemplaza despues por el destino real
  (RO, SF, GC, FU, RON, ROC).
- Nro.Certificado: certificado de fabrica. Las facturas que no lo emiten (BYD)
  quedan sin valor.
- Interno: numero interno de la unidad.
"""
import io

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill

HEADERS = [
    "Marca", "Modelo", "Chasis", "Motor", "Año", "Color", "Ubicación",
    "Nro.Certificado", "Interno",
]

# Codigo de marca usado por Neostar en la planilla de importacion.
BRAND_CODES = {
    "HONDA": 31,
    "NISSAN": 32,
    "BYD": "BYD",
}

# Ubicacion fija en esta etapa: todas las unidades estan en fabrica.
UBICACION_DEFAULT = "FA"


def _brand_value(row):
    return BRAND_CODES.get((row.get("brand") or "").upper(), "")


def _model_value(row):
    return row.get("model_code") or row.get("model_name") or ""


def build_excel(extractions):
    """Recibe una lista de dicts de extracciones y devuelve los bytes del .xlsx."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Facturas"

    header_fill = PatternFill("solid", fgColor="1F2A44")
    header_font = Font(bold=True, color="FFFFFF")
    center = Alignment(horizontal="center", vertical="center")

    for col, title in enumerate(HEADERS, start=1):
        cell = ws.cell(row=1, column=col, value=title)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = center

    for i, row in enumerate(extractions, start=2):
        ws.cell(row=i, column=1, value=_brand_value(row))
        ws.cell(row=i, column=2, value=_model_value(row))
        ws.cell(row=i, column=3, value=row.get("vin") or "")
        ws.cell(row=i, column=4, value=row.get("engine_number") or "")
        ws.cell(row=i, column=5, value=row.get("year") or "")
        ws.cell(row=i, column=6, value=row.get("color_code") or "")
        ws.cell(row=i, column=7, value=UBICACION_DEFAULT)
        ws.cell(row=i, column=8, value=row.get("certificate") or "")
        ws.cell(row=i, column=9, value=row.get("interno") or "")

    # Ancho de columnas aproximado al contenido.
    widths = [8, 28, 22, 22, 8, 10, 11, 20, 14]
    for col, width in enumerate(widths, start=1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = width

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.read()
