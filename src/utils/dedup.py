"""
Déduplication des entreprises par nom normalisé et domaine email.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .text import normalize_company_name, extract_email_domain, extract_domain

if TYPE_CHECKING:
    from src.models.company import Company


def deduplicate_companies(companies: list["Company"]) -> list["Company"]:
    """
    Déduplique une liste d'entreprises.

    Critères de déduplication (dans l'ordre) :
    1. Nom normalisé identique
    2. Domaine email identique (si non vide)
    3. Domaine website identique (si non vide)

    En cas de doublon, on garde l'entrée avec le plus d'informations.
    """
    seen_names: dict[str, int] = {}       # normalized_name -> index
    seen_emails: dict[str, int] = {}      # email_domain -> index
    seen_domains: dict[str, int] = {}     # website_domain -> index
    result: list["Company"] = []

    for company in companies:
        norm_name = normalize_company_name(company.company_name)
        email_domain = extract_email_domain(company.contact_email)
        web_domain = extract_domain(company.website)

        # Chercher un doublon existant
        existing_idx = None

        if norm_name and norm_name in seen_names:
            existing_idx = seen_names[norm_name]
        elif email_domain and email_domain in seen_emails:
            existing_idx = seen_emails[email_domain]
        elif web_domain and web_domain in seen_domains:
            existing_idx = seen_domains[web_domain]

        if existing_idx is not None:
            # Garder l'entrée avec le plus d'informations
            existing = result[existing_idx]
            if _info_score(company) > _info_score(existing):
                result[existing_idx] = company
                # Mettre à jour les index
                if norm_name:
                    seen_names[norm_name] = existing_idx
                if email_domain:
                    seen_emails[email_domain] = existing_idx
                if web_domain:
                    seen_domains[web_domain] = existing_idx
        else:
            idx = len(result)
            result.append(company)
            if norm_name:
                seen_names[norm_name] = idx
            if email_domain:
                seen_emails[email_domain] = idx
            if web_domain:
                seen_domains[web_domain] = idx

    return result


def _info_score(company: "Company") -> int:
    """Score de complétude d'une entreprise (plus c'est élevé, plus il y a d'info)."""
    score = 0
    for field in ["company_name", "website", "contact_email", "sector",
                   "location", "career_url", "tech_stack", "job_titles_found",
                   "contact_name"]:
        if getattr(company, field, ""):
            score += 1
    return score
