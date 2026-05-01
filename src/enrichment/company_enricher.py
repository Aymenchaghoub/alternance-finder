"""
Enrichissement des entreprises — nettoyage, normalisation, détection.

En V1, fait un enrichissement léger basé sur les données disponibles :
- Normalisation du nom
- Détection de localisation (Paris/IDF, HdF)
- Détection de secteur à partir des mots-clés
- Détection de signaux tech
- Détection de type de contrat
"""

from __future__ import annotations

from src.models.company import Company
from src.utils.text import normalize_company_name, contains_any
from src.utils.logging import logger


def enrich_companies(companies: list[Company]) -> list[Company]:
    """Enrichit une liste d'entreprises avec des données dérivées."""
    logger.info(f"Enrichissement de {len(companies)} entreprises...")

    for company in companies:
        _normalize(company)
        _detect_location(company)
        _detect_sector_signals(company)
        _detect_tech_signals(company)
        _detect_contract_types(company)

    logger.info("  → Enrichissement terminé.")
    return companies


def _normalize(company: Company):
    """Normalise le nom de l'entreprise."""
    if not company.normalized_company_name:
        company.normalized_company_name = normalize_company_name(company.company_name)


def _detect_location(company: Company):
    """Détecte la ville, département et région depuis le champ location."""
    loc = company.location.lower()
    if not loc:
        return

    # Extraction ville simple
    if "," in company.location:
        parts = [p.strip() for p in company.location.split(",")]
        company.city = parts[0]
        if len(parts) > 1:
            company.region = parts[1]

    # Détection région
    if contains_any(loc, ["île-de-france", "ile-de-france", "idf", "paris",
                          "92", "93", "94", "95", "78", "91", "77"]):
        if not company.region:
            company.region = "Île-de-France"
    elif contains_any(loc, ["hauts-de-france", "lille", "nord", "59"]):
        if not company.region:
            company.region = "Hauts-de-France"


def _detect_sector_signals(company: Company):
    """Détecte des signaux sectoriels."""
    all_text = " ".join([
        company.sector, company.notes, company.job_titles_found,
        company.job_descriptions_found,
    ]).lower()

    if not all_text.strip():
        return

    # Détection du secteur si non renseigné
    if not company.sector:
        sector_keywords = {
            "IA / Machine Learning": ["ia", "ai", "machine learning", "deep learning", "nlp", "llm"],
            "SaaS": ["saas", "plateforme", "platform"],
            "Cybersécurité": ["cyber", "sécurité", "security"],
            "DevTools": ["devtools", "developer tools", "outils développeur"],
            "HealthTech": ["health", "santé", "médical", "medical"],
            "FinTech": ["fintech", "finance", "banque", "trading"],
            "GreenTech": ["greentech", "énergie", "environnement", "climat"],
            "EdTech": ["edtech", "éducation", "formation", "e-learning"],
            "LegalTech": ["legaltech", "juridique", "droit"],
        }
        for sector, keywords in sector_keywords.items():
            if contains_any(all_text, keywords):
                company.sector = sector
                break


def _detect_tech_signals(company: Company):
    """Détecte les signaux tech dans les données disponibles."""
    all_text = " ".join([
        company.job_titles_found, company.job_descriptions_found,
        company.notes, company.tech_stack, company.sector,
    ]).lower()

    if not all_text.strip():
        return

    tech_indicators = [
        "développeur", "developer", "ingénieur", "engineer",
        "backend", "frontend", "fullstack", "devops",
        "python", "java", "javascript", "react", "node",
        "api", "saas", "cloud", "docker", "ci/cd",
        "ia", "ai", "machine learning", "data",
    ]
    company.has_tech_jobs = contains_any(all_text, tech_indicators)

    # Extraction des mots-clés trouvés
    if not company.keywords_found:
        from src.utils.io import load_config
        try:
            kw_config = load_config("keywords.yaml")
            strong = kw_config.get("strong_keywords", [])
            found = [kw for kw in strong if kw.lower() in all_text]
            company.keywords_found = ", ".join(found)
        except FileNotFoundError:
            pass


def _detect_contract_types(company: Company):
    """Détecte les types de contrats mentionnés."""
    all_text = " ".join([
        company.job_titles_found, company.job_descriptions_found,
        company.contract_types_found,
    ]).lower()

    if contains_any(all_text, ["alternance", "apprentissage", "contrat d'apprentissage"]):
        company.has_apprenticeship_offer = True
        if "alternance" not in company.contract_types_found.lower():
            company.contract_types_found = (
                (company.contract_types_found + ", " if company.contract_types_found else "")
                + "alternance"
            )

    if contains_any(all_text, ["stage", "internship"]):
        company.has_internship_offer = True
