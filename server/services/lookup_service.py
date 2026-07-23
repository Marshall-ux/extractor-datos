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


def _is_model_file(filename):
    return "modelo" in filename.lower()


def seed_from_folder(folder):
    """Carga planillas de colores presentes en una carpeta si la tabla esta vacia.
    Util para el primer arranque (datos semilla)."""
    import glob
    import os

    if database.count_color_lookup() == 0:
        for path in glob.glob(os.path.join(folder, "*.xlsx")):
            name = os.path.basename(path)
            if _is_model_file(name):
                continue  # las planillas de modelos se cargan aparte
            brand = detect_table_brand(name)
            try:
                load_colors_from_file(path, brand)
            except Exception:
                # Una planilla invalida no debe impedir el arranque.
                continue

    seed_models_from_folder(folder)


def seed_models_from_folder(folder):
    """Carga planillas de modelos (archivos con 'modelo' en el nombre) si la
    tabla model_lookup esta vacia."""
    import glob
    import os

    if database.get_model_lookup():
        return
    all_entries = []
    for path in glob.glob(os.path.join(folder, "*.xlsx")):
        name = os.path.basename(path)
        if not _is_model_file(name):
            continue
        try:
            all_entries.extend(read_model_xlsx(path))
        except Exception:
            continue
    if all_entries:
        database.replace_model_lookup(None, all_entries)


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


def _byd_parts(color_name):
    """Partes exterior/interior de una descripcion BYD ('PALLAS WHITE/BLACK'
    -> ['PALLAS WHITE', 'BLACK']). '&' se trata como separador de parte."""
    normalized = normalize(color_name).replace("&", " ")
    return [re.sub(r"\s+", " ", p).strip()
            for p in normalized.split("/") if p.strip()]


def _tok_list(text):
    """Lista ordenada de tokens alfanumericos (conserva repetidos y orden)."""
    return [t for t in re.split(r"[^A-Z0-9]+", normalize(text)) if t]


def _entry_token_seq(parts):
    """Secuencia de tokens de una entrada, en orden exterior/interior."""
    seq = []
    for part in parts:
        seq.extend(_tok_list(part))
    return seq


def _subseq_len(entry_seq, text_toks):
    """Cantidad de tokens de entry_seq presentes en text_toks como subsecuencia
    (mismo orden, posiciones crecientes). Es el nucleo del puntaje."""
    i = 0
    for tok in text_toks:
        if i < len(entry_seq) and tok == entry_seq[i]:
            i += 1
    return i


def _best_by_tokens(candidates, text):
    """Mejor entrada por puntaje de tokens en orden dentro de text.

    Puntaje: (tokens_coincidentes, -tokens_faltantes, es_combo, largo). Gana la
    entrada que matchea MAS tokens (la mas especifica); a igualdad, la que menos
    tokens deja sin matchear (la mas ajustada); y recien ahi se prefiere una
    combinacion exterior/interior sobre un color simple. Asi:
    - 'TIME GREY/BASALT BLACK+READ HA' (4 matcheados) le gana a 'TIME GREY/
      BLACK' (3) cuando la factura dice 'Time Grey - Basalt Black+Red Hare Brown'.
    - para 'Time Grey - Black' gana 'TIME GREY/BLACK' por dejar 0 faltantes.
    - para 'Obsidian Black' (sin interior) gana el color simple OBLA sobre
      'OBSIDIAN BLACK/BLACK', que dejaria un token sin matchear.
    - cuando exterior e interior figuran repetidos en el texto (grilla + otra
      copia) y empatan un color simple con el mismo par de palabras al reves
      ('BLACK TIME GREY' vs 'TIME GREY/BLACK'), gana el combo, que es la
      lectura correcta de dos campos de color separados.
    Se exige un minimo de 2 tokens para evitar matches debiles.
    """
    text_toks = _tok_list(text)
    best = None
    for parts, name, code in candidates:
        seq = _entry_token_seq(parts)
        if not seq:
            continue
        matched = _subseq_len(seq, text_toks)
        if matched < 2:
            continue
        is_combo = 1 if len(parts) > 1 else 0
        key = (matched, -(len(seq) - matched), is_combo, len(seq))
        if best is None or key > best[0]:
            best = (key, name, code)
    return (best[1], best[2]) if best else None


def match_color_byd(raw_text, desc_line=None):
    """Resuelve color BYD. Devuelve (color_name, color_code) o (None, None).

    La descripcion trae el color en orden exterior/interior
    ('SEAL U DM-i Snow White - Black'), que es la fuente confiable y respeta
    el orden que distingue combinaciones opuestas ('PALLAS WHITE/BLACK' vs
    'BLACK/PALLAS WHITE'). Por eso se busca primero sobre la linea de
    descripcion y, si no alcanza, sobre el texto completo (donde igual aparece
    la descripcion en el mismo orden).

    Combinaciones y colores simples compiten juntos: el puntaje (mas tokens,
    menos faltantes) evita que un combo matcheado a medias le gane a su color
    simple ('OBSIDIAN BLACK' resuelve OBLA, no OBSIDIAN BLACK/BLACK).
    """
    entries = [(_byd_parts(name), name, code) for _, name, code in _byd_entries()]
    entries = [(parts, name, code) for parts, name, code in entries if parts]

    # 1. Linea de descripcion (mas confiable; fija el orden exterior/interior).
    if desc_line:
        found = _best_by_tokens(entries, desc_line)
        if found:
            return found

    # 2. Texto completo, mismo orden.
    return _best_by_tokens(entries, raw_text) or (None, None)


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


def resolve_color(brand, color_text, raw_text="", desc_line=None):
    """Punto de entrada unico. Para BYD usa el texto completo mas la linea de
    descripcion; para el resto, el color etiquetado extraido."""
    if brand == BYD:
        return match_color_byd(raw_text or color_text, desc_line)
    return match_color_autopak(color_text)


# --------------------------- resolucion de modelo ------------------------- #

# Umbral minimo de similitud (Jaccard de tokens) para aceptar un match no exacto.
MODEL_MATCH_THRESHOLD = 0.6


def _tokens(text):
    return {t for t in re.split(r"[^A-Z0-9]+", normalize(text)) if t}


def resolve_model(model_name, brand=None):
    """Busca el codigo de modelo en la planilla model_lookup a partir del
    nombre/descripcion extraido de la factura.

    Estrategia conservadora:
    1. Coincidencia exacta normalizada.
    2. Mejor similitud por tokens (Jaccard) si supera MODEL_MATCH_THRESHOLD.
    Devuelve (model_name_planilla, model_code) o (None, None).
    """
    if not model_name:
        return None, None

    entries = database.get_model_lookup(brand) if brand else database.get_model_lookup()
    if not entries:
        return None, None

    target_norm = normalize(model_name)
    target_tokens = _tokens(model_name)

    best = None  # (score, name, code)
    for e in entries:
        cand_name = e["model_name"]
        cand_norm = normalize(cand_name)
        if cand_norm == target_norm:
            return cand_name, e["model_code"]
        cand_tokens = _tokens(cand_name)
        if not cand_tokens or not target_tokens:
            continue
        score = len(target_tokens & cand_tokens) / len(target_tokens | cand_tokens)
        if best is None or score > best[0]:
            best = (score, cand_name, e["model_code"])

    if best and best[0] >= MODEL_MATCH_THRESHOLD:
        return best[1], best[2]
    return None, None
