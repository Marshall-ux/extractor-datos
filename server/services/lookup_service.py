"""
Servicio de planillas de busqueda (lookup) de colores.

- Carga planillas Excel (BYD y AUTOPAK multi-marca) a la tabla color_lookup.
- Resuelve el codigo de color a partir del texto/color extraido de la factura.

Normalizacion: mayusculas, sin acentos, espacios colapsados. El mojibake que
produce PyPDF2 sobre caracteres acentuados coincide con el de las planillas
(ambos pierden el mismo caracter al quitar lo no-ASCII), por lo que el match
sigue funcionando.
"""
import re
import unicodedata

import openpyxl

from models import database

# Marca logica usada en color_lookup para la planilla multi-marca AUTOPAK.
AUTOPAK = "AUTOPAK"
BYD = "BYD"


def normalize(text):
    if text is None:
        return ""
    s = str(text).strip().upper()
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"\s+", " ", s)
    return s.strip()


# --------------------------- carga de planillas --------------------------- #

def _read_color_xlsx(filepath):
    """Lee filas (codigo, descripcion) de una planilla de colores.

    Soporta ambos formatos:
    - BYD: encabezado en fila 1, datos desde fila 2.
    - AUTOPAK: encabezados en filas 1-5, datos despues. Se descartan filas sin
      codigo/descripcion y la propia fila de encabezado "Codigo/Descripcion".
    """
    wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
    ws = wb.active
    entries = []
    for row in ws.iter_rows(values_only=True):
        if not row or len(row) < 2:
            continue
        code, desc = row[0], row[1]
        if code is None or desc is None:
            continue
        code_s = str(code).strip()
        desc_s = str(desc).strip()
        if not code_s or not desc_s:
            continue
        if normalize(code_s) in ("CODIGO", "CODIGO DE COLOR"):
            continue
        entries.append((desc_s, code_s))  # (color_name, color_code)
    wb.close()
    return entries


def load_colors_from_file(filepath, brand):
    """Carga una planilla en color_lookup bajo la marca indicada.
    brand: 'BYD' o 'AUTOPAK'. Devuelve cantidad cargada."""
    entries = _read_color_xlsx(filepath)
    database.replace_color_lookup(brand, entries)
    return len(entries)


def read_model_xlsx(filepath):
    """Lee filas (model_name, model_code) de una planilla de modelos.
    Convencion: columna A = codigo, columna B = nombre. Funcionalidad a futuro."""
    wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
    ws = wb.active
    entries = []
    for row in ws.iter_rows(values_only=True):
        if not row or len(row) < 2:
            continue
        code, name = row[0], row[1]
        if code is None or name is None:
            continue
        code_s, name_s = str(code).strip(), str(name).strip()
        if not code_s or not name_s:
            continue
        if normalize(code_s) in ("CODIGO", "CODIGO DE MODELO"):
            continue
        entries.append((name_s, code_s))
    wb.close()
    return entries


def detect_table_brand(filename):
    """Decide a que tabla pertenece una planilla por su nombre de archivo."""
    name = filename.lower()
    if "byd" in name:
        return BYD
    return AUTOPAK


def seed_from_folder(folder):
    """Carga planillas presentes en una carpeta si las tablas estan vacias.
    Util para el primer arranque (datos semilla)."""
    import glob
    import os

    if database.count_color_lookup() > 0:
        return
    for path in glob.glob(os.path.join(folder, "*.xlsx")):
        brand = detect_table_brand(os.path.basename(path))
        try:
            load_colors_from_file(path, brand)
        except Exception:
            # Una planilla invalida no debe impedir el arranque.
            continue


# --------------------------- resolucion de color -------------------------- #

def _byd_entries():
    return [
        (normalize(e["color_name"]).replace("/", " ").replace("&", " "),
         e["color_name"], e["color_code"])
        for e in database.get_color_lookup(BYD)
    ]


def _autopak_entries():
    return [
        (normalize(e["color_name"]), e["color_name"], e["color_code"])
        for e in database.get_color_lookup(AUTOPAK)
    ]


def match_color_byd(raw_text):
    """Resuelve color BYD buscando, dentro del texto completo de la factura,
    la descripcion de la planilla (con '/' y '&' como espacios) que aparezca
    como subcadena contigua. Se elige la coincidencia mas larga (mas especifica),
    lo que distingue EXTERIOR/INTERIOR de INTERIOR/EXTERIOR.
    Devuelve (color_name, color_code) o (None, None).
    """
    norm_text = re.sub(r"\s+", " ",
                       normalize(raw_text).replace("/", " ").replace("&", " "))
    best = None
    for needle, name, code in _byd_entries():
        if needle and needle in norm_text:
            if best is None or len(needle) > best[0]:
                best = (len(needle), name, code)
    if best:
        return best[1], best[2]
    return None, None


def match_color_autopak(color_text):
    """Resuelve color para marcas en la planilla AUTOPAK.
    Estrategia: match exacto > descripcion contenida en el color (mas larga) >
    color contenido en descripcion (mas corta).
    Devuelve (color_name, color_code) o (None, None).
    """
    target = normalize(color_text)
    if not target:
        return None, None

    entries = _autopak_entries()

    # 1. Coincidencia exacta (preferir la descripcion mas larga si empata).
    exact = [(name, code) for nd, name, code in entries if nd == target]
    if exact:
        exact.sort(key=lambda x: len(x[0]), reverse=True)
        return exact[0]

    # 2. La descripcion es subcadena del color extraido (ej. "URBAN GRAY" en
    #    "URBAN GRAY P."). Elegir la descripcion mas larga.
    contained = [(name, code, nd) for nd, name, code in entries
                 if nd and nd in target]
    if contained:
        contained.sort(key=lambda x: len(x[2]), reverse=True)
        return contained[0][0], contained[0][1]

    # 3. El color extraido es subcadena de la descripcion. Elegir la mas corta.
    reverse = [(name, code, nd) for nd, name, code in entries
               if target in nd]
    if reverse:
        reverse.sort(key=lambda x: len(x[2]))
        return reverse[0][0], reverse[0][1]

    return None, None


def resolve_color(brand, color_text, raw_text=""):
    """Punto de entrada unico. Para BYD usa el texto completo; para el resto,
    el color etiquetado extraido."""
    if brand == BYD:
        return match_color_byd(raw_text or color_text)
    return match_color_autopak(color_text)
