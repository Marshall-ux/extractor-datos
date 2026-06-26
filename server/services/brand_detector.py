"""
Deteccion de marca a partir del texto de la factura.

Cada marca se identifica por un emisor o etiqueta caracteristica. El orden
importa: se evalua BYD y Nissan (por emisor) antes que las etiquetas "Marca:"
para evitar falsos positivos (ej. "Marca de Chasis: BYD").
"""

# Marcas soportadas
BYD = "BYD"
NISSAN = "NISSAN"
SUBARU = "SUBARU"
SUZUKI = "SUZUKI"
KIA = "KIA"
HONDA = "HONDA"


def detect_brand(text):
    """Devuelve el nombre de la marca o None si no se reconoce."""
    if not text:
        return None

    t = text.upper()

    # BYD: emisor BYD AUTO ARGENTINA
    if "BYD AUTO ARGENTINA" in t:
        return BYD

    # Nissan: emisor NISSAN ARGENTINA S.A.
    if "NISSAN ARGENTINA" in t:
        return NISSAN

    # KIA: campos "MARCAMOTOR: KIA" / "MARCA:KIA"
    if "MARCAMOTOR: KIA" in t or "MARCA:KIA" in t or "MARCA: KIA" in t:
        return KIA

    # Honda: "Marca: HONDA"
    if "MARCA: HONDA" in t or "MARCA:HONDA" in t:
        return HONDA

    # Inchcape / DAASA: Subaru y Suzuki comparten formato, se distinguen
    # por la etiqueta "Marca:".
    if "MARCA: SUBARU" in t or "MARCA:SUBARU" in t:
        return SUBARU
    if "MARCA: SUZUKI" in t or "MARCA:SUZUKI" in t:
        return SUZUKI

    return None
