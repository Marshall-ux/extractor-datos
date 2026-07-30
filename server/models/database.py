"""
Acceso a la base de datos SQLite.

Define el esquema (extractions, color_lookup, model_lookup) y helpers CRUD.
La ruta de la BD se toma de la config de Flask (DATABASE_PATH).
"""
import os
import sqlite3
from contextlib import contextmanager

from flask import current_app

SCHEMA = """
CREATE TABLE IF NOT EXISTS extractions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    brand TEXT,
    model_code TEXT,
    model_name TEXT,
    vin TEXT,
    interno TEXT,
    engine_number TEXT,
    year INTEGER,
    certificate TEXT,
    is_hybrid BOOLEAN DEFAULT FALSE,
    is_electric BOOLEAN DEFAULT FALSE,
    color_name TEXT,
    color_code TEXT,
    raw_text TEXT,
    confidence TEXT DEFAULT 'high',
    status TEXT DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS color_lookup (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand TEXT,
    color_name TEXT NOT NULL,
    color_code TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS model_lookup (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand TEXT,
    model_name TEXT NOT NULL,
    model_code TEXT NOT NULL
);
"""

# Columnas editables/insertables de extractions (sin id ni timestamps).
EXTRACTION_FIELDS = [
    "filename", "brand", "model_code", "model_name", "vin", "interno",
    "engine_number", "year", "certificate", "is_hybrid", "is_electric",
    "color_name", "color_code", "raw_text", "confidence", "status",
]

# Columnas agregadas despues de la version inicial: se aplican con ALTER TABLE
# sobre bases ya existentes (el server tiene la BD en un volumen persistente).
MIGRATIONS = [
    ("year", "INTEGER"),
    ("certificate", "TEXT"),
]


def _db_path():
    return current_app.config["DATABASE_PATH"]


@contextmanager
def get_connection():
    path = _db_path()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_connection() as conn:
        conn.executescript(SCHEMA)
        existing = {r["name"] for r in conn.execute("PRAGMA table_info(extractions)")}
        for column, coltype in MIGRATIONS:
            if column not in existing:
                conn.execute(f"ALTER TABLE extractions ADD COLUMN {column} {coltype}")


# ----------------------------- extractions -------------------------------- #

def insert_extraction(data):
    fields = [f for f in EXTRACTION_FIELDS if f in data]
    placeholders = ", ".join("?" for _ in fields)
    cols = ", ".join(fields)
    values = [data[f] for f in fields]
    with get_connection() as conn:
        cur = conn.execute(
            f"INSERT INTO extractions ({cols}) VALUES ({placeholders})", values
        )
        return cur.lastrowid


def list_extractions():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM extractions ORDER BY created_at DESC, id DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def get_extraction(extraction_id):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM extractions WHERE id = ?", (extraction_id,)
        ).fetchone()
        return dict(row) if row else None


def update_extraction(extraction_id, data):
    fields = [f for f in EXTRACTION_FIELDS if f in data]
    if not fields:
        return get_extraction(extraction_id)
    assignments = ", ".join(f"{f} = ?" for f in fields)
    values = [data[f] for f in fields]
    values.append(extraction_id)
    with get_connection() as conn:
        conn.execute(
            f"UPDATE extractions SET {assignments}, "
            f"updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            values,
        )
    return get_extraction(extraction_id)


def delete_extraction(extraction_id):
    with get_connection() as conn:
        cur = conn.execute("DELETE FROM extractions WHERE id = ?", (extraction_id,))
        return cur.rowcount > 0


def delete_all_extractions():
    """Borra todo el historial de extracciones. Devuelve la cantidad borrada."""
    with get_connection() as conn:
        cur = conn.execute("DELETE FROM extractions")
        return cur.rowcount


# ----------------------------- color_lookup ------------------------------- #

def replace_color_lookup(brand, entries):
    """Reemplaza todos los colores de una marca. entries: lista de (name, code)."""
    with get_connection() as conn:
        conn.execute("DELETE FROM color_lookup WHERE brand = ?", (brand,))
        conn.executemany(
            "INSERT INTO color_lookup (brand, color_name, color_code) VALUES (?, ?, ?)",
            [(brand, name, code) for name, code in entries],
        )


def get_color_lookup(brand=None):
    with get_connection() as conn:
        if brand:
            rows = conn.execute(
                "SELECT * FROM color_lookup WHERE brand = ?", (brand,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM color_lookup").fetchall()
        return [dict(r) for r in rows]


def count_color_lookup(brand=None):
    with get_connection() as conn:
        if brand:
            row = conn.execute(
                "SELECT COUNT(*) AS n FROM color_lookup WHERE brand = ?", (brand,)
            ).fetchone()
        else:
            row = conn.execute("SELECT COUNT(*) AS n FROM color_lookup").fetchone()
        return row["n"]


# ----------------------------- model_lookup ------------------------------- #

def replace_model_lookup(brand, entries):
    with get_connection() as conn:
        # brand None es el bucket unico de modelos (asi se cargan por seed): al
        # reemplazar hay que vaciar toda la tabla. 'WHERE brand = NULL' no borra
        # nada en SQLite, por eso se distingue el caso.
        if brand is None:
            conn.execute("DELETE FROM model_lookup")
        else:
            conn.execute("DELETE FROM model_lookup WHERE brand = ?", (brand,))
        conn.executemany(
            "INSERT INTO model_lookup (brand, model_name, model_code) VALUES (?, ?, ?)",
            [(brand, name, code) for name, code in entries],
        )


def get_model_lookup(brand=None):
    with get_connection() as conn:
        if brand:
            rows = conn.execute(
                "SELECT * FROM model_lookup WHERE brand = ?", (brand,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM model_lookup").fetchall()
        return [dict(r) for r in rows]
