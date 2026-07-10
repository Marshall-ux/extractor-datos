"""
Rutas CRUD de extracciones.

GET    /api/extractions       - lista
DELETE /api/extractions       - limpia todo el historial
GET    /api/extractions/<id>  - detalle
PUT    /api/extractions/<id>  - edicion manual
DELETE /api/extractions/<id>  - eliminar
"""
from flask import Blueprint, jsonify, request

from models import database

extractions_bp = Blueprint("extractions", __name__, url_prefix="/api")

# Campos que el usuario puede editar manualmente desde la tabla.
EDITABLE = [
    "brand", "model_code", "model_name", "vin", "interno", "engine_number",
    "is_hybrid", "is_electric", "color_name", "color_code", "status",
]


@extractions_bp.route("/extractions", methods=["GET"])
def list_all():
    return jsonify(database.list_extractions())


@extractions_bp.route("/extractions", methods=["DELETE"])
def delete_all():
    """Limpia todo el historial de facturas analizadas."""
    count = database.delete_all_extractions()
    return jsonify({"deleted": count})


@extractions_bp.route("/extractions/<int:extraction_id>", methods=["GET"])
def get_one(extraction_id):
    row = database.get_extraction(extraction_id)
    if not row:
        return jsonify({"error": "No encontrado"}), 404
    return jsonify(row)


@extractions_bp.route("/extractions/<int:extraction_id>", methods=["PUT"])
def update(extraction_id):
    if not database.get_extraction(extraction_id):
        return jsonify({"error": "No encontrado"}), 404
    payload = request.get_json(silent=True) or {}
    data = {k: payload[k] for k in EDITABLE if k in payload}

    # Si se edita el VIN, recalcular el interno (ultimos 8) salvo que venga explicito.
    if "vin" in data and "interno" not in payload:
        vin = data["vin"] or ""
        data["interno"] = vin[-8:] if vin else None

    updated = database.update_extraction(extraction_id, data)
    return jsonify(updated)


@extractions_bp.route("/extractions/<int:extraction_id>", methods=["DELETE"])
def delete(extraction_id):
    if not database.delete_extraction(extraction_id):
        return jsonify({"error": "No encontrado"}), 404
    return jsonify({"deleted": extraction_id})
