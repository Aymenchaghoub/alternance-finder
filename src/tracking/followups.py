"""
Logique de relances — détermine quand relancer une entreprise.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from src.models.application import Application
from src.utils.logging import logger


def get_followups_due(applications: list[Application]) -> list[Application]:
    """
    Retourne les candidatures nécessitant une relance.

    Critères :
    - Status = "sent"
    - Envoyé il y a >= 7 jours sans réponse
    - Pas de do_not_contact
    """
    now = datetime.now()
    due = []

    for app in applications:
        if app.application_status != "sent":
            continue
        if app.do_not_contact:
            continue
        if app.response_status:
            continue

        try:
            sent_date = datetime.fromisoformat(app.sent_at)
            days_since = (now - sent_date).days

            if days_since >= 14:
                app.notes = (app.notes or "") + " | Relance 14j recommandée"
                due.append(app)
            elif days_since >= 7:
                app.notes = (app.notes or "") + " | Relance 7j recommandée"
                due.append(app)
        except (ValueError, TypeError):
            continue

    if due:
        logger.info(f"  → {len(due)} relances recommandées.")
    return due
