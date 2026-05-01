"""
Générateur d'emails personnalisés.

Sélectionne le template approprié selon le type d'entreprise,
remplit les placeholders, et génère un fichier Markdown par entreprise.
"""

from __future__ import annotations

import os
from pathlib import Path

from src.models.company import Company
from src.utils.io import load_config, ensure_dir
from src.utils.slugify import slugify
from src.utils.logging import logger


def generate_emails(
    companies: list[Company],
    min_score: int = 60,
    output_dir: str = "outputs/emails",
) -> list[str]:
    """
    Génère un email personnalisé par entreprise éligible.

    Args:
        companies: Liste d'entreprises scorées.
        min_score: Score minimum pour générer un email.
        output_dir: Dossier de sortie.

    Returns:
        Liste des chemins de fichiers générés.
    """
    logger.info(f"Génération d'emails (min_score={min_score})...")

    try:
        email_config = load_config("email_templates.yaml")
    except FileNotFoundError:
        logger.error("Configuration email_templates.yaml introuvable.")
        return []

    templates = email_config.get("templates", {})
    signature = email_config.get("signature", "")
    opt_out = email_config.get("opt_out_footer", "")
    default_subject = email_config.get("default_subject", "")

    eligible = [c for c in companies if c.score >= min_score and not c.do_not_contact]
    logger.info(f"  → {len(eligible)} entreprises éligibles (score >= {min_score})")

    ensure_dir(output_dir)
    generated_files = []

    for company in eligible:
        template_key = _select_template(company)
        template = templates.get(template_key, templates.get("without_offer", {}))

        # Remplir les placeholders
        subject = template.get("subject", default_subject)
        body = template.get("body", "")

        placeholders = _build_placeholders(company)
        for key, value in placeholders.items():
            subject = subject.replace(f"{{{key}}}", value)
            body = body.replace(f"{{{key}}}", value)

        # Stocker dans le modèle Company
        company.email_subject = subject
        company.email_body = body

        # Générer le fichier Markdown
        slug = slugify(company.company_name)
        filename = f"email_{slug}.md"
        filepath = os.path.join(output_dir, filename)

        content = _format_email_markdown(company, subject, body, signature, opt_out)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        generated_files.append(filepath)

    logger.info(f"  → {len(generated_files)} emails générés dans {output_dir}/")
    return generated_files


def _select_template(company: Company) -> str:
    """Sélectionne le template le plus approprié pour l'entreprise."""
    sector = company.sector.lower() if company.sector else ""
    notes = company.notes.lower() if company.notes else ""
    all_text = f"{sector} {notes}"

    if "ouidou" in company.company_name.lower() or "test_interne" in company.source.lower():
        return "interne_ouidou"
    elif company.has_apprenticeship_offer:
        return "with_offer"
    elif "ia" in all_text or "ai" in all_text or "machine learning" in all_text or "nlp" in all_text:
        return "startup_ia"
    elif "saas" in all_text:
        return "saas_b2b"
    elif "esn" in all_text or "conseil" in all_text or "consulting" in all_text:
        return "esn_cabinet"
    elif "éditeur" in all_text or "logiciel" in all_text or "software" in all_text:
        return "editeur_logiciel"
    else:
        return "without_offer"


def _build_placeholders(company: Company) -> dict[str, str]:
    """Construit le dictionnaire de placeholders pour le template."""
    # Greeting
    if company.contact_name:
        greeting = company.contact_name
    else:
        greeting = "l'équipe recrutement"

    # Angle de personnalisation
    angle = company.personalization_angle
    if not angle:
        if company.sector:
            angle = f"vous évoluez dans le secteur {company.sector}"
        elif company.notes:
            angle = company.notes[:150]
        else:
            angle = "votre activité correspond à mes compétences et aspirations"

    # Projet pertinent
    relevant_project = "MediBrief (SaaS IA multi-tenant)"
    relevant_tech = "Node.js, TypeScript, React, PostgreSQL, OpenAI API"

    sector_lower = (company.sector or "").lower()
    notes_lower = (company.notes or "").lower()
    combined = f"{sector_lower} {notes_lower}"

    if "ia" in combined or "ai" in combined or "rag" in combined or "llm" in combined:
        relevant_project = "Assistant RAG ArXiv (pipeline RAG complet)"
        relevant_tech = "Python, LangChain, ChromaDB, FastAPI, Mistral-7B"
    elif "saas" in combined or "multi-tenant" in combined:
        relevant_project = "MediBrief (SaaS IA multi-tenant)"
        relevant_tech = "Node.js, TypeScript, Next.js, PostgreSQL, Redis, Docker"
    elif "fullstack" in combined or "full-stack" in combined or "laravel" in combined:
        relevant_project = "SchoolSphere (application MVC multi-rôles)"
        relevant_tech = "Laravel, MySQL, JavaScript, API REST, RBAC"

    # Job title (pour template with_offer)
    job_title = company.job_titles_found.split(",")[0].strip() if company.job_titles_found else "développement logiciel"

    return {
        "greeting": greeting,
        "company_name": company.company_name,
        "personalization_angle": angle,
        "relevant_project": relevant_project,
        "relevant_tech": relevant_tech,
        "job_title": job_title,
    }


def _format_email_markdown(
    company: Company,
    subject: str,
    body: str,
    signature: str,
    opt_out: str,
) -> str:
    """Formate l'email complet en Markdown."""
    lines = [
        f"# Email — {company.company_name}",
        "",
        f"**Score** : {company.score} | **Priorité** : {company.recommended_action}",
        f"**Destinataire** : {company.contact_email or 'À renseigner'}",
        f"**Template** : {_select_template(company)}",
        "",
        "---",
        "",
        f"**Objet** : {subject}",
        "",
        "---",
        "",
        body.strip(),
        "",
        signature.strip(),
        "",
        opt_out.strip(),
        "",
    ]
    return "\n".join(lines)
