"""
Entry point de la aplicacion Flask.

Extractor de Facturas de Vehiculos - Backend.
Las rutas y servicios se registran aqui; la logica de negocio vive en
los modulos routes/, services/ y extractors/.
"""
import os

from flask import Flask, jsonify
from flask_cors import CORS


def create_app():
    app = Flask(__name__)
    CORS(app)

    # Configuracion
    app.config["DATABASE_PATH"] = os.environ.get("DATABASE_PATH", "data/app.db")
    app.config["UPLOAD_FOLDER"] = os.environ.get("UPLOAD_FOLDER", "uploads")
    app.config["LOOKUP_FOLDER"] = os.environ.get("LOOKUP_FOLDER", "lookup_tables")
    app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB

    # Asegurar carpetas necesarias
    for folder in (
        os.path.dirname(app.config["DATABASE_PATH"]) or ".",
        app.config["UPLOAD_FOLDER"],
        app.config["LOOKUP_FOLDER"],
    ):
        os.makedirs(folder, exist_ok=True)

    @app.route("/api/health")
    def health():
        return jsonify({"status": "ok"})

    # Los blueprints se registran en fases posteriores (Fase 4).
    _register_blueprints(app)

    return app


def _register_blueprints(app):
    """Registra los blueprints de la API si existen (se completan en Fase 4)."""
    try:
        from routes.upload import upload_bp
        from routes.extractions import extractions_bp
        from routes.export import export_bp
        from routes.lookup_tables import lookup_bp

        app.register_blueprint(upload_bp)
        app.register_blueprint(extractions_bp)
        app.register_blueprint(export_bp)
        app.register_blueprint(lookup_bp)
    except ImportError:
        # Durante Fase 1 los blueprints aun no existen.
        pass


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
