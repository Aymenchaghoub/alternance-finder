"""
Modèle Application — représente une candidature envoyée.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Application:
    """Suivi d'une candidature envoyée à une entreprise."""

    company_name: str = ""
    contact_email: str = ""
    email_subject: str = ""
    email_file: str = ""
    cv_file: str = ""
    score: int = 0
    priority: str = ""           # high, good, backup
    application_status: str = "draft"  # draft, sent, replied, rejected
    created_at: str = ""
    sent_at: str = ""
    follow_up_at: str = ""
    response_status: str = ""
    notes: str = ""
    do_not_contact: bool = False

    def to_dict(self) -> dict:
        """Convertit en dictionnaire pour export CSV."""
        return {
            "company_name": self.company_name,
            "contact_email": self.contact_email,
            "email_subject": self.email_subject,
            "email_file": self.email_file,
            "cv_file": self.cv_file,
            "score": self.score,
            "priority": self.priority,
            "application_status": self.application_status,
            "created_at": self.created_at,
            "sent_at": self.sent_at,
            "follow_up_at": self.follow_up_at,
            "response_status": self.response_status,
            "notes": self.notes,
            "do_not_contact": self.do_not_contact,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Application":
        """Crée une Application depuis un dictionnaire."""
        if "do_not_contact" in data and isinstance(data["do_not_contact"], str):
            data["do_not_contact"] = data["do_not_contact"].lower() in ("true", "1", "yes")
        if "score" in data:
            try:
                data["score"] = int(data["score"]) if data["score"] else 0
            except (ValueError, TypeError):
                data["score"] = 0
        known = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in data.items() if k in known})

    @classmethod
    def from_company(cls, company) -> "Application":
        """Crée une Application depuis un objet Company."""
        priority = "high" if company.score >= 80 else "good" if company.score >= 60 else "backup"
        return cls(
            company_name=company.company_name,
            contact_email=company.contact_email,
            email_subject=company.email_subject,
            score=company.score,
            priority=priority,
            application_status="draft",
            created_at=datetime.now().isoformat(),
            do_not_contact=company.do_not_contact,
        )
