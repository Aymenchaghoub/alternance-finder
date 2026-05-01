"""
Tracker — gestion du fichier applications.csv et suivi des candidatures.
"""

from __future__ import annotations

import os
from datetime import datetime

from src.models.company import Company
from src.models.application import Application
from src.utils.io import load_csv, save_csv, ensure_dir
from src.utils.logging import logger


APPLICATIONS_FILE = os.path.join("outputs", "tracking", "applications.csv")

APPLICATION_FIELDS = [
    "company_name", "contact_email", "email_subject", "email_file",
    "cv_file", "score", "priority", "application_status", "created_at",
    "sent_at", "follow_up_at", "response_status", "notes", "do_not_contact",
]


class ApplicationTracker:
    """Gère le fichier de suivi des candidatures."""

    def __init__(self, filepath: str = APPLICATIONS_FILE):
        self.filepath = filepath
        self.applications: list[Application] = []
        self._load()

    def _load(self):
        """Charge les applications existantes depuis le CSV."""
        rows = load_csv(self.filepath)
        self.applications = [Application.from_dict(row) for row in rows]

    def save(self):
        """Sauvegarde les applications dans le CSV."""
        ensure_dir(os.path.dirname(self.filepath))
        data = [app.to_dict() for app in self.applications]
        save_csv(self.filepath, data, APPLICATION_FIELDS)

    def add_from_companies(self, companies: list[Company], min_score: int = 60):
        """Crée des entrées de suivi pour les entreprises éligibles."""
        existing_names = {app.company_name.lower() for app in self.applications}
        added = 0

        for company in companies:
            if company.score < min_score or company.do_not_contact:
                continue
            if company.company_name.lower() in existing_names:
                continue

            app = Application.from_company(company)

            # Trouver le fichier email correspondant
            from src.utils.slugify import slugify
            slug = slugify(company.company_name)
            email_file = os.path.join("outputs", "emails", f"email_{slug}.md")
            if os.path.exists(email_file):
                app.email_file = email_file
            app.cv_file = company.cv_variant or ""

            self.applications.append(app)
            added += 1

        if added > 0:
            self.save()
            logger.info(f"  → {added} candidatures ajoutées au tracking.")

    def get_pending(self) -> list[Application]:
        """Retourne les candidatures en attente d'envoi."""
        return [a for a in self.applications if a.application_status == "draft"]

    def mark_sent(self, company_name: str):
        """Marque une candidature comme envoyée."""
        for app in self.applications:
            if app.company_name.lower() == company_name.lower():
                app.application_status = "sent"
                app.sent_at = datetime.now().isoformat()
                break
        self.save()

    def get_stats(self) -> dict[str, int]:
        """Retourne les statistiques de suivi."""
        stats = {"total": len(self.applications)}
        for app in self.applications:
            status = app.application_status or "draft"
            stats[status] = stats.get(status, 0) + 1
        return stats
