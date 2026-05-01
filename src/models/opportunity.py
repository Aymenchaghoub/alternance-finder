"""
Modèle Opportunity — représente une offre d'alternance détectée.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Opportunity:
    """Offre d'alternance ou de stage détectée."""

    company_name: str = ""
    title: str = ""
    description: str = ""
    location: str = ""
    contract_type: str = ""       # alternance, stage, CDI, etc.
    source: str = ""              # france_travail, la_bonne_alternance, website
    source_url: str = ""
    posted_date: str = ""
    keywords: str = ""
    tech_stack: str = ""
    is_relevant: bool = False
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "company_name": self.company_name,
            "title": self.title,
            "description": self.description,
            "location": self.location,
            "contract_type": self.contract_type,
            "source": self.source,
            "source_url": self.source_url,
            "posted_date": self.posted_date,
            "keywords": self.keywords,
            "tech_stack": self.tech_stack,
            "is_relevant": self.is_relevant,
            "notes": self.notes,
        }
