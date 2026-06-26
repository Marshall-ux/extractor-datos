"""
POST /api/upload - sube uno o varios PDFs, extrae datos y los persiste.
"""
import os
import uuid

from flask import Blueprint, current_app, jsonify, request
from werkzeug.utils import secure_filename

from models import database
from services import data_extractor

upload_bp = Blueprint("upload", __name__, url_prefix="/api")


@upload_bp.route("/upload", methods=["POST"])
def upload():
    files = request.files.getlist("files")
    if not files:
        # Compatibilidad: tambien aceptar un unico campo "file".
        single = request.files.get("file")
        if single:
            files = [single]
    if not files:
        return jsonify({"error": "No se enviaron archivos"}), 400

    upload_folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_folder, exist_ok=True)

    results = []
    for f in files:
        if not f or not f.filename:
            continue
        original_name = f.filename
        if not original_name.lower().endswith(".pdf"):
            results.append({"filename": original_name,
                            "error": "No es un PDF"})
            continue

        # Guardar con nombre unico para evitar colisiones.
        safe = secure_filename(original_name) or "factura.pdf"
        stored = f"{uuid.uuid4().hex}_{safe}"
        path = os.path.join(upload_folder, stored)
        f.save(path)

        try:
            data = data_extractor.extract_from_pdf(path, original_name)
        except Exception as exc:  # noqa: BLE001
            data = {
                "filename": original_name, "raw_text": "",
                "confidence": "low", "status": "review",
                "error": str(exc),
            }

        error = data.pop("error", None)
        new_id = database.insert_extraction(data)
        saved = database.get_extraction(new_id)
        if error:
            saved["error"] = error
        results.append(saved)

    return jsonify({"count": len(results), "extractions": results}), 201
