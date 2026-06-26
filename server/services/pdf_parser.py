"""
Extraccion de texto de facturas PDF usando PyPDF2.

Los PDFs de las terminales son digitales (texto seleccionable). Algunos
ejemplares escaneados no tienen capa de texto: en ese caso se devuelve
cadena vacia y el flujo posterior marca la extraccion como baja confianza.
"""
from PyPDF2 import PdfReader


def extract_first_page_text(filepath):
    """Devuelve el texto de la primera pagina (las facturas repiten el
    contenido en Original/Duplicado/Triplicado)."""
    reader = PdfReader(filepath)
    if not reader.pages:
        return ""
    return reader.pages[0].extract_text() or ""


def extract_all_text(filepath):
    """Texto concatenado de todas las paginas (fallback)."""
    reader = PdfReader(filepath)
    return "\n".join((p.extract_text() or "") for p in reader.pages)


def get_page_count(filepath):
    return len(PdfReader(filepath).pages)
