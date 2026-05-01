"""
Envoi d'email — dry-run et envoi test uniquement.

IMPORTANT (V1) :
- Dry-run obligatoire par défaut
- Aucun envoi réel aux entreprises
- Seul l'envoi test vers TEST_RECIPIENT_EMAIL est autorisé
- Confirmation explicite requise avant tout envoi
"""

from __future__ import annotations

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

from src.models.company import Company
from src.utils.logging import logger


def dry_run_emails(companies: list[Company], min_score: int = 60):
    """
    Simule l'envoi d'emails (dry-run, aucun email réel envoyé).

    Affiche ce qui serait envoyé pour vérification.
    """
    eligible = [c for c in companies if c.score >= min_score and not c.do_not_contact]
    logger.info("=" * 60)
    logger.info("  DRY-RUN — Simulation d'envoi (aucun email réel)")
    logger.info("=" * 60)
    logger.info(f"  {len(eligible)} emails seraient envoyés :\n")

    for i, company in enumerate(eligible, 1):
        status = "✓" if company.contact_email else "⚠ PAS D'EMAIL"
        logger.info(
            f"  [{i}] {company.company_name:<35} "
            f"→ {company.contact_email or 'N/A':<35} "
            f"Score: {company.score} {status}"
        )

    logger.info(f"\n  Total : {len(eligible)} emails")
    logger.info("  ℹ Pour envoyer un test : python -m src.cli send-test-email --company \"Nom\"")
    logger.info("  ⚠ Aucun email n'a été envoyé.")


def send_test_email(company: Company) -> bool:
    """
    Envoie un email de test uniquement à TEST_RECIPIENT_EMAIL.

    Jamais d'envoi à l'email de l'entreprise en V1.

    Returns:
        True si envoi réussi, False sinon.
    """
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    gmail_address = os.environ.get("GMAIL_ADDRESS", "")
    gmail_password = os.environ.get("GMAIL_APP_PASSWORD", "")
    test_recipient = os.environ.get("TEST_RECIPIENT_EMAIL", "")

    if not gmail_address or not gmail_password:
        logger.warning("  ⚠ SMTP non configuré (GMAIL_ADDRESS / GMAIL_APP_PASSWORD manquants).")
        logger.info("  → L'email a été généré en brouillon mais non envoyé.")
        logger.info("  → Configurer .env pour activer l'envoi test.")
        return False

    if not test_recipient:
        logger.warning("  ⚠ TEST_RECIPIENT_EMAIL non configuré dans .env")
        logger.info("  → Ajoutez TEST_RECIPIENT_EMAIL=votre.email@gmail.com dans .env")
        return False

    # SÉCURITÉ : ne JAMAIS envoyer à l'email de l'entreprise
    if test_recipient == company.contact_email:
        logger.error("  ✗ BLOQUÉ : TEST_RECIPIENT_EMAIL est identique au contact de l'entreprise !")
        logger.error("  → L'envoi test doit aller vers VOTRE propre email, pas celui de l'entreprise.")
        return False

    logger.info(f"  📧 Envoi test vers : {test_recipient}")
    logger.info(f"  📋 Objet : {company.email_subject}")
    logger.info(f"  🏢 Entreprise simulée : {company.company_name}")

    try:
        msg = MIMEMultipart()
        msg["From"] = gmail_address
        msg["To"] = test_recipient
        msg["Subject"] = f"[TEST] {company.email_subject}"

        # Corps avec mention TEST
        body = (
            f"⚠ CECI EST UN EMAIL DE TEST — Non envoyé à {company.company_name}\n"
            f"Destinataire réel serait : {company.contact_email}\n"
            f"{'=' * 60}\n\n"
            f"{company.email_body}\n"
        )
        msg.attach(MIMEText(body, "plain", "utf-8"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(gmail_address, gmail_password)
            server.sendmail(gmail_address, test_recipient, msg.as_string())

        logger.info(f"  ✓ Email test envoyé avec succès à {test_recipient}")
        return True

    except smtplib.SMTPAuthenticationError:
        logger.error("  ✗ Erreur d'authentification SMTP.")
        logger.info("  → Vérifiez GMAIL_APP_PASSWORD dans .env")
        return False
    except Exception as e:
        logger.error(f"  ✗ Erreur d'envoi : {e}")
        return False
