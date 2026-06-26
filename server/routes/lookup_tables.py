"""
Gestion de planillas de busqueda (colores y modelos).

POST /api/lookup-tables/colors  - sube/actualiza planilla de colores
GET  /api/lookup-tables/colors  - lista colores cargados
POST /api/lookup-tables/models  - sube/actualiza planilla de modelos
GET  /api/lookup-tables/models  - lista modelos cargados
"""
import os

from flask import Blueprint, current_app, jsonify, request
from werkzeug.utils import secure_filename

from models import database
from services import lookup_service

lookup_bp = Blueprint("lookup_tables", __name__, url_prefix="/api/lookup-tables")


def _save_upload():
    f = request.files.get("file")
    if not f or not f.filename:
        return None, (jsonify({"error": "No se envio archivo"}), 400)
    if not f.filename.lower().endswith(".xlsx"):
        return None, (jsonify({"error": "El archivo debe ser .xlsx"}), 400)
    folder = current_app.config["LOOKUP_FOLDER"]
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, secure_filename(f.filename))
    f.save(path)
    return (path, f.filename), None


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
        count = lookup_service.load_colors_from_file(path, brand)
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": f"No se pudo leer la planilla: {exc}"}), 400
    return jsonify({"brand": brand, "loaded": count}), 201


@lookup_bp.route("/colors", methods=["GET"])
def list_colors():
    brand = request.args.get("brand")
    return jsonify(database.get_color_lookup(brand))


@lookup_bp.route("/models", methods=["POST"])
def upload_models():
    saved, error = _save_upload()
    if error:
        return error
    path, original = saved
    brand = (request.form.get("brand") or "").upper() or None
    try:
        entries = lookup_service.read_model_xlsx(path)
        database.replace_model_lookup(brand, entries)
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": f"No se pudo leer la planilla: {exc}"}), 400
    return jsonify({"brand": brand, "loaded": len(entries)}), 201


@lookup_bp.route("/models", methods=["GET"])
def list_models():
    brand = request.args.get("brand")
    return jsonify(database.get_model_lookup(brand))
