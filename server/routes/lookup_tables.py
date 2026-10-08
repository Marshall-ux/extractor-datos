"""
Gestion de planillas de busqueda (colores y modelos).

POST /api/lookup-tables/colors           - sube/actualiza planilla de colores
PUT  /api/lookup-tables/colors           - guarda la planilla editada en la app
                                           (?brand=AUTOPAK|BYD)
GET  /api/lookup-tables/colors           - lista colores cargados
GET  /api/lookup-tables/colors/download  - descarga la planilla de colores
                                           cargada (?brand=AUTOPAK|BYD)
POST /api/lookup-tables/models           - sube/actualiza planilla de modelos
PUT  /api/lookup-tables/models           - guarda la planilla editada en la app
GET  /api/lookup-tables/models           - lista modelos cargados
GET  /api/lookup-tables/models/download  - descarga la planilla de modelos cargada
"""
import os
import tempfile

from flask import Blueprint, jsonify, request, send_file

from models import database
from services import lookup_service

lookup_bp = Blueprint("lookup_tables", __name__, url_prefix="/api/lookup-tables")

XLSX_MIMETYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

# Nombre del archivo descargado por planilla de colores.
COLOR_FILENAMES = {
    lookup_service.AUTOPAK: "CODIGOS COLORES AUTOPAK.xlsx",
    lookup_service.BYD: "codigos de colores byd.xlsx",
}
MODELS_FILENAME = "codigos modelos nissan.xlsx"


def _save_upload():
    """Guarda el .xlsx subido en un archivo temporal. No se escribe en la
    carpeta de planillas semilla: la planilla vigente es la que queda en la BD
    (y se descarga desde ahi)."""
    f = request.files.get("file")
    if not f or not f.filename:
        return None, (jsonify({"error": "No se envio archivo"}), 400)
    if not f.filename.lower().endswith(".xlsx"):
        return None, (jsonify({"error": "El archivo debe ser .xlsx"}), 400)
    fd, path = tempfile.mkstemp(suffix=".xlsx")
    os.close(fd)
    f.save(path)
    return (path, f.filename), None


def _edited_rows():
    """Lee las filas editadas en la app: JSON {"rows": [[col_a, col_b], ...]}
    en el mismo orden que la planilla (codigo/descripcion para colores,
    modelo/codigo para modelos). Las filas totalmente vacias se descartan.
    Devuelve (filas, None) o (None, respuesta_de_error)."""
    data = request.get_json(silent=True) or {}
    raw = data.get("rows")
    if not isinstance(raw, list):
        return None, (jsonify({"error": "Formato invalido: falta 'rows'"}), 400)
    rows = []
    for i, row in enumerate(raw, start=1):
        if not isinstance(row, list) or len(row) != 2:
            return None, (jsonify({"error": f"Fila {i} invalida"}), 400)
        a, b = (str(v if v is not None else "").strip() for v in row)
        if not a and not b:
            continue
        if not a or not b:
            return None, (jsonify({"error": f"Fila {i}: completa las dos columnas"}), 400)
        rows.append((a, b))
    if not rows:
        return None, _empty_table_error()
    return rows, None


def _empty_table_error():
    return jsonify({
        "error": "La planilla no tiene filas validas (columna A y B completas). "
                 "No se modifico la planilla cargada."
    }), 400


@lookup_bp.route("/colors", methods=["POST"])
def upload_colors():
    saved, error = _save_upload()
    if error:
        return error
    path, original = saved
    # La marca puede venir por form-data; sino se infiere del nombre del archivo.
    brand = request.form.get("brand") or lookup_service.detect_table_brand(original)
    brand = brand.upper()
    try:
        entries = lookup_service.read_color_xlsx(path)
        if not entries:
            return _empty_table_error()
        database.replace_color_lookup(brand, entries)
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": f"No se pudo leer la planilla: {exc}"}), 400
    finally:
        os.remove(path)
    return jsonify({"brand": brand, "loaded": len(entries)}), 201


@lookup_bp.route("/colors", methods=["PUT"])
def save_colors():
    brand = (request.args.get("brand") or "").upper()
    if brand not in COLOR_FILENAMES:
        return jsonify({"error": "Marca de planilla invalida"}), 400
    rows, error = _edited_rows()
    if error:
        return error
    # Las filas llegan como (codigo, descripcion); la tabla guarda (nombre, codigo).
    database.replace_color_lookup(brand, [(name, code) for code, name in rows])
    return jsonify({"brand": brand, "loaded": len(rows)})


@lookup_bp.route("/colors", methods=["GET"])
def list_colors():
    brand = request.args.get("brand")
    return jsonify(database.get_color_lookup(brand))


@lookup_bp.route("/colors/download", methods=["GET"])
def download_colors():
    brand = (request.args.get("brand") or "").upper()
    if brand not in COLOR_FILENAMES:
        return jsonify({"error": "Marca de planilla invalida"}), 400
    rows = [(c["color_code"], c["color_name"])
            for c in database.get_color_lookup(brand)]
    buffer = lookup_service.build_lookup_xlsx(
        ["Código", "Descripción"], rows, [18, 40])
    return send_file(buffer, mimetype=XLSX_MIMETYPE, as_attachment=True,
                     download_name=COLOR_FILENAMES[brand])


@lookup_bp.route("/models", methods=["POST"])
def upload_models():
    saved, error = _save_upload()
    if error:
        return error
    path, _ = saved
    brand = (request.form.get("brand") or "").upper() or None
    try:
        entries = lookup_service.read_model_xlsx(path)
        if not entries:
            return _empty_table_error()
        database.replace_model_lookup(brand, entries)
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": f"No se pudo leer la planilla: {exc}"}), 400
    finally:
        os.remove(path)
    return jsonify({"brand": brand, "loaded": len(entries)}), 201


@lookup_bp.route("/models", methods=["PUT"])
def save_models():
    rows, error = _edited_rows()
    if error:
        return error
    # Mismo bucket sin marca que usan el seed y la subida de la planilla.
    database.replace_model_lookup(None, rows)
    return jsonify({"brand": None, "loaded": len(rows)})


@lookup_bp.route("/models", methods=["GET"])
def list_models():
    brand = request.args.get("brand")
    return jsonify(database.get_model_lookup(brand))


@lookup_bp.route("/models/download", methods=["GET"])
def download_models():
    rows = [(m["model_name"], m["model_code"])
            for m in database.get_model_lookup()]
    buffer = lookup_service.build_lookup_xlsx(
        ["Modelo", "Código"], rows, [40, 24])
    return send_file(buffer, mimetype=XLSX_MIMETYPE, as_attachment=True,
                     download_name=MODELS_FILENAME)
