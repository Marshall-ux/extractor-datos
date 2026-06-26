"""
Generacion del Excel de salida con las 5 columnas requeridas.

Columnas: INTERNO | MODELO | Nº DE VIN | Nº DE MOTOR | CÓDIGO DE COLOR
- INTERNO: ultimos 8 caracteres del VIN.
- MODELO: codigo del modelo si existe, sino nombre del modelo.
- Nº DE MOTOR: numero de motor (naftero en hibridos; electrico si solo electrico).
- CÓDIGO DE COLOR: codigo resuelto en la planilla.
"""
import io

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill

HEADERS = ["INTERNO", "MODELO", "Nº DE VIN", "Nº DE MOTOR", "CÓDIGO DE COLOR"]


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
        ws.cell(row=i, column=1, value=row.get("interno") or "")
        ws.cell(row=i, column=2, value=_model_value(row))
        ws.cell(row=i, column=3, value=row.get("vin") or "")
        ws.cell(row=i, column=4, value=row.get("engine_number") or "")
        ws.cell(row=i, column=5, value=row.get("color_code") or "")

    # Ancho de columnas aproximado al contenido.
    widths = [14, 28, 22, 22, 18]
    for col, width in enumerate(widths, start=1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = width

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.read()
