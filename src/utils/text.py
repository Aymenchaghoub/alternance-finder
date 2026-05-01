"""
Utilitaires de traitement de texte — normalisation, extraction.
"""

import re
import unicodedata
from urllib.parse import urlparse


def normalize_text(text: str) -> str:
    """Normalise un texte : minuscules, sans accents, sans ponctuation."""
    if not text:
        return ""
    # Minuscules
    text = text.lower().strip()
    # Supprimer les accents
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    # Supprimer ponctuation sauf espaces et tirets
    text = re.sub(r"[^a-z0-9\s\-]", "", text)
    # Normaliser les espaces
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_company_name(name: str) -> str:
    """Normalise un nom d'entreprise pour la déduplication."""
    if not name:
        return ""
    normalized = normalize_text(name)
    # Supprimer les formes juridiques courantes
    suffixes = [
        "sas", "sarl", "sa", "eurl", "sasu", "sci", "snc",
        "groupe", "group", "france", "paris", "consulting",
    ]
    words = normalized.split()
    words = [w for w in words if w not in suffixes]
    return " ".join(words)


def extract_domain(url: str) -> str:
    """Extrait le domaine d'une URL."""
    if not url:
        return ""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        domain = domain.lower().strip()
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return ""


def extract_email_domain(email: str) -> str:
    """Extrait le domaine d'une adresse email."""
    if not email or "@" not in email:
        return ""
    return email.split("@")[1].lower().strip()


def contains_any(text: str, keywords: list[str], case_sensitive: bool = False) -> bool:
    """Vérifie si un texte contient l'un des mots-clés."""
    if not text or not keywords:
        return False
    if not case_sensitive:
        text = text.lower()
        keywords = [k.lower() for k in keywords]
    return any(kw in text for kw in keywords)


def count_keyword_matches(text: str, keywords: list[str]) -> int:
    """Compte le nombre de mots-clés présents dans un texte."""
    if not text or not keywords:
        return 0
    text_lower = text.lower()
    return sum(1 for kw in keywords if kw.lower() in text_lower)
