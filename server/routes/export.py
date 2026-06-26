"""
POST /api/export - genera un Excel con las extracciones seleccionadas.

Body JSON: {"ids": [1,2,3]}  (si se omite, exporta todas).
"""
from datetime import date

from flask import Blueprint, jsonify, request, send_file
import io

from models import database
from services import excel_generator

export_bp = Blueprint("export", __name__, url_prefix="/api")


@export_bp.route("/export", methods=["POST"])
def export():
    payload = request.get_json(silent=True) or {}
    ids = payload.get("ids")

    all_rows = database.list_extractions()
    if ids:
        id_set = set(ids)
        rows = [r for r in all_rows if r["id"] in id_set]
    else:
        rows = all_rows

    if not rows:
        return jsonify({"error": "No hay extracciones para exportar"}), 400

    content = excel_generator.build_excel(rows)
    filename = f"lectura_facturas_{date.today().isoformat()}.xlsx"
    return send_file(
        io.BytesIO(content),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=filename,
    )
