"""
Slugification — conversion de noms en identifiants fichier-safe.
"""

import re
import unicodedata


def slugify(text: str, max_length: int = 60) -> str:
    """
    Convertit un texte en slug fichier-safe.

    Exemples :
        "Demo AI Studio"  -> "demo_ai_studio"
        "L'Atelier du Code" -> "latelier_du_code"
        "Ma Super Startup SAS" -> "ma_super_startup_sas"
    """
    if not text:
        return "unknown"

    # Normaliser les caractères Unicode
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))

    # Minuscules
    text = text.lower()

    # Remplacer les caractères spéciaux par des underscores
    text = re.sub(r"[^a-z0-9]+", "_", text)

    # Supprimer les underscores en début/fin
    text = text.strip("_")

    # Limiter la longueur
    if len(text) > max_length:
        text = text[:max_length].rstrip("_")

    return text or "unknown"
