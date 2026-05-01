"""
Import CSV manuel — source principale du MVP.

Lit un fichier CSV depuis data/manual_imports/ et retourne
une liste d'objets Company.
"""

import os
from pathlib import Path

from src.models.company import Company
from src.utils.io import load_csv
from src.utils.text import normalize_company_name
from src.utils.logging import logger


# Colonnes attendues dans le CSV
EXPECTED_COLUMNS = [
    "company_name", "website", "career_url", "source", "location",
    "sector", "job_titles_found", "job_descriptions_found",
    "contact_email", "notes",
]


def import_from_csv(filepath: str) -> list[Company]:
    """
    Importe des entreprises depuis un fichier CSV.

    Args:
        filepath: Chemin vers le fichier CSV.

    Returns:
        Liste d'objets Company.
    """
    if not os.path.exists(filepath):
        logger.error(f"Fichier introuvable : {filepath}")
        return []

    logger.info(f"Import CSV : {filepath}")
    rows = load_csv(filepath)

    if not rows:
        logger.warning("Fichier CSV vide ou invalide.")
        return []

    # Vérifier les colonnes
    actual_cols = set(rows[0].keys())
    missing = set(EXPECTED_COLUMNS) - actual_cols
    if missing:
        logger.warning(f"Colonnes manquantes dans le CSV : {missing}")

    companies = []
    for i, row in enumerate(rows, 1):
        name = (row.get("company_name") or "").strip()
        if not name:
            logger.warning(f"Ligne {i} : nom d'entreprise vide, ignorée.")
            continue

        company = Company(
            company_name=name,
            normalized_company_name=normalize_company_name(name),
            website=(row.get("website") or "").strip(),
            career_url=(row.get("career_url") or "").strip(),
            source=row.get("source", "csv_manual").strip() or "csv_manual",
            location=(row.get("location") or "").strip(),
            sector=(row.get("sector") or "").strip(),
            job_titles_found=(row.get("job_titles_found") or "").strip(),
            job_descriptions_found=(row.get("job_descriptions_found") or "").strip(),
            contact_email=(row.get("contact_email") or "").strip(),
            notes=(row.get("notes") or "").strip(),
        )
        companies.append(company)

    logger.info(f"  → {len(companies)} entreprises importées depuis CSV.")
    return companies


def import_all_manual_csvs(directory: str = "data/manual_imports") -> list[Company]:
    """Importe toutes les entreprises depuis tous les CSV du dossier."""
    all_companies = []
    dirpath = Path(directory)

    if not dirpath.exists():
        logger.warning(f"Dossier d'import introuvable : {directory}")
        return []

    csv_files = sorted(dirpath.glob("*.csv"))
    if not csv_files:
        logger.warning(f"Aucun fichier CSV trouvé dans {directory}")
        return []

    for csv_file in csv_files:
        companies = import_from_csv(str(csv_file))
        all_companies.extend(companies)

    logger.info(f"Total importé : {len(all_companies)} entreprises depuis {len(csv_files)} fichier(s).")
    return all_companies
