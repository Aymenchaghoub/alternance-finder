"""
Modèle Company — représente une entreprise cible.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Company:
    """Données complètes d'une entreprise cible."""

    # --- Identification ---
    company_name: str = ""
    normalized_company_name: str = ""
    website: str = ""
    career_url: str = ""

    # --- Source ---
    source: str = ""          # csv_manual, france_travail, sirene, etc.
    source_url: str = ""

    # --- Localisation ---
    location: str = ""
    city: str = ""
    department: str = ""
    region: str = ""

    # --- Activité ---
    sector: str = ""
    naf_code: str = ""
    naf_label: str = ""
    company_size: Optional[int] = None
    is_active: bool = True

    # --- Offres et signaux ---
    job_titles_found: str = ""
    job_descriptions_found: str = ""
    keywords_found: str = ""
    tech_stack: str = ""
    contract_types_found: str = ""
    has_apprenticeship_offer: bool = False
    has_internship_offer: bool = False
    has_tech_jobs: bool = False

    # --- Contact ---
    contact_email: str = ""
    contact_name: str = ""
    contact_role: str = ""
    linkedin_company_url: str = ""

    # --- Scoring ---
    score: int = 0
    score_details: str = ""
    personalization_angle: str = ""
    recommended_action: str = ""

    # --- Génération ---
    email_subject: str = ""
    email_body: str = ""
    cv_variant: str = ""

    # --- Suivi ---
    application_status: str = ""      # draft, sent, replied, rejected, etc.
    last_contact_date: str = ""
    follow_up_date: str = ""
    response_status: str = ""
    notes: str = ""
    do_not_contact: bool = False

    def to_dict(self) -> dict:
        """Convertit en dictionnaire pour export CSV."""
        return {
            "company_name": self.company_name,
            "normalized_company_name": self.normalized_company_name,
            "website": self.website,
            "career_url": self.career_url,
            "source": self.source,
            "source_url": self.source_url,
            "location": self.location,
            "city": self.city,
            "department": self.department,
            "region": self.region,
            "sector": self.sector,
            "naf_code": self.naf_code,
            "naf_label": self.naf_label,
            "company_size": self.company_size if self.company_size else "",
            "is_active": self.is_active,
            "job_titles_found": self.job_titles_found,
            "job_descriptions_found": self.job_descriptions_found,
            "keywords_found": self.keywords_found,
            "tech_stack": self.tech_stack,
            "contract_types_found": self.contract_types_found,
            "has_apprenticeship_offer": self.has_apprenticeship_offer,
            "has_internship_offer": self.has_internship_offer,
            "has_tech_jobs": self.has_tech_jobs,
            "contact_email": self.contact_email,
            "contact_name": self.contact_name,
            "contact_role": self.contact_role,
            "linkedin_company_url": self.linkedin_company_url,
            "score": self.score,
            "score_details": self.score_details,
            "personalization_angle": self.personalization_angle,
            "recommended_action": self.recommended_action,
            "email_subject": self.email_subject,
            "email_body": self.email_body,
            "cv_variant": self.cv_variant,
            "application_status": self.application_status,
            "last_contact_date": self.last_contact_date,
            "follow_up_date": self.follow_up_date,
            "response_status": self.response_status,
            "notes": self.notes,
            "do_not_contact": self.do_not_contact,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Company":
        """Crée une Company depuis un dictionnaire."""
        # Handle boolean fields
        for bool_field in ["is_active", "has_apprenticeship_offer",
                           "has_internship_offer", "has_tech_jobs",
                           "do_not_contact"]:
            if bool_field in data and isinstance(data[bool_field], str):
                data[bool_field] = data[bool_field].lower() in ("true", "1", "yes", "oui")

        # Handle int fields
        if "company_size" in data:
            try:
                data["company_size"] = int(data["company_size"]) if data["company_size"] else None
            except (ValueError, TypeError):
                data["company_size"] = None

        if "score" in data:
            try:
                data["score"] = int(data["score"]) if data["score"] else 0
            except (ValueError, TypeError):
                data["score"] = 0

        # Only pass known fields
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known_fields}
        return cls(**filtered)
