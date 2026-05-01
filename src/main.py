"""
alternance-finder — Pipeline principal.

Orchestre toutes les étapes : import → enrichissement → scoring →
génération emails/CV → export → tracking.
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from src.collectors.manual_import import import_all_manual_csvs, import_from_csv
from src.enrichment.company_enricher import enrich_companies
from src.scoring.scorer import score_companies, get_top_targets
from src.generation.email_generator import generate_emails
from src.generation.cv_generator import generate_cvs
from src.tracking.tracker import ApplicationTracker
from src.models.company import Company
from src.utils.io import save_csv, ensure_dir
from src.utils.dedup import deduplicate_companies
from src.utils.logging import logger


def run_pipeline(
    csv_path: str | None = None,
    min_score_email: int = 60,
    min_score_cv: int = 75,
    skip_cv: bool = False,
):
    """
    Exécute le pipeline complet.

    Étapes :
    1. Init (créer les répertoires)
    2. Import CSV manuel
    3. Déduplication
    4. Enrichissement
    5. Scoring
    6. Génération d'emails
    7. Génération de CV (optionnel)
    8. Export des résultats
    9. Tracking
    10. Rapport
    """
    logger.info("=" * 60)
    logger.info("  alternance-finder — Pipeline complet")
    logger.info("=" * 60)
    start_time = datetime.now()

    # --- 1. Init ---
    logger.info("\n[1/10] Initialisation...")
    _init_directories()

    # --- 2. Import ---
    logger.info("\n[2/10] Import des entreprises...")
    if csv_path:
        companies = import_from_csv(csv_path)
    else:
        companies = import_all_manual_csvs()

    if not companies:
        logger.error("Aucune entreprise importée. Vérifiez vos fichiers CSV.")
        return

    # --- 3. Déduplication ---
    logger.info(f"\n[3/10] Déduplication...")
    before = len(companies)
    companies = deduplicate_companies(companies)
    logger.info(f"  → {before} → {len(companies)} entreprises (dédupliquées)")

    # Sauvegarder les données nettoyées
    save_csv(
        "data/processed/companies_clean.csv",
        [c.to_dict() for c in companies],
    )

    # --- 4. Enrichissement ---
    logger.info(f"\n[4/10] Enrichissement...")
    companies = enrich_companies(companies)

    # --- 5. Scoring ---
    logger.info(f"\n[5/10] Scoring...")
    companies = score_companies(companies)

    # --- 6. Génération emails ---
    logger.info(f"\n[6/10] Génération d'emails...")
    email_files = generate_emails(companies, min_score=min_score_email)

    # Sauvegarder les données scorées AVEC les emails générés
    save_csv(
        "data/processed/companies_scored.csv",
        [c.to_dict() for c in companies],
    )

    # --- 7. Génération CV ---
    if not skip_cv:
        logger.info(f"\n[7/10] Génération de CV...")
        cv_files = generate_cvs(companies, min_score=min_score_cv)
    else:
        logger.info(f"\n[7/10] Génération de CV (ignorée)")
        cv_files = []

    # --- 8. Export ---
    logger.info(f"\n[8/10] Export des résultats...")
    _export_reports(companies, min_score_email)

    # --- 9. Tracking ---
    logger.info(f"\n[9/10] Mise à jour du tracking...")
    tracker = ApplicationTracker()
    tracker.add_from_companies(companies, min_score=min_score_email)

    # --- 10. Rapport ---
    logger.info(f"\n[10/10] Génération du rapport...")
    _generate_report(companies, email_files, cv_files, tracker)

    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info(f"\n{'=' * 60}")
    logger.info(f"  Pipeline terminé en {elapsed:.1f}s")
    logger.info(f"{'=' * 60}")


def _init_directories():
    """Crée tous les répertoires nécessaires."""
    dirs = [
        "data/raw", "data/processed", "data/exports", "data/manual_imports",
        "outputs/emails", "outputs/cvs", "outputs/reports", "outputs/tracking",
        "cv/generated",
    ]
    for d in dirs:
        ensure_dir(d)


def _export_reports(companies: list[Company], min_score: int = 60):
    """Exporte les rapports CSV."""
    ensure_dir("outputs/reports")

    # Top targets (score >= export_min_score)
    top = get_top_targets(companies, min_score=min_score)
    if top:
        save_csv(
            "outputs/reports/top_targets.csv",
            [c.to_dict() for c in top],
        )
        logger.info(f"  → {len(top)} cibles dans outputs/reports/top_targets.csv")

    # High priority (score >= 80)
    high = [c for c in companies if c.score >= 80 and not c.do_not_contact]
    if high:
        save_csv(
            "outputs/reports/high_priority_targets.csv",
            [c.to_dict() for c in high],
        )
        logger.info(f"  → {len(high)} priorités hautes dans outputs/reports/high_priority_targets.csv")


def _generate_report(
    companies: list[Company],
    email_files: list[str],
    cv_files: list[str],
    tracker: ApplicationTracker,
):
    """Génère le rapport Markdown."""
    ensure_dir("outputs/reports")
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        f"# Rapport alternance-finder — {now}",
        "",
        "## Résumé",
        "",
        f"- **Entreprises analysées** : {len(companies)}",
        f"- **Emails générés** : {len(email_files)}",
        f"- **CV générés** : {len(cv_files)}",
        f"- **Candidatures en suivi** : {len(tracker.applications)}",
        "",
        "## Classement par score",
        "",
        "| # | Entreprise | Score | Secteur | Localisation | Action |",
        "|---|-----------|-------|---------|--------------|--------|",
    ]

    for i, c in enumerate(companies, 1):
        lines.append(
            f"| {i} | {c.company_name} | {c.score} | "
            f"{c.sector or '-'} | {c.location or '-'} | "
            f"{c.recommended_action} |"
        )

    lines.extend([
        "",
        "## Prochaines étapes",
        "",
        "1. Vérifier les emails générés dans `outputs/emails/`",
        "2. Ajuster les personnalisations si nécessaire",
        "3. Lancer `python -m src.cli send-emails --dry-run` pour simuler",
        "4. Lancer `python -m src.cli send-test-email --company \"Nom\"` pour tester",
        "5. Ajouter de vraies entreprises dans `data/manual_imports/`",
        "",
        "---",
        f"*Généré automatiquement par alternance-finder le {now}*",
    ])

    report_path = "outputs/reports/report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    logger.info(f"  → Rapport : {report_path}")
