"""
alternance-finder — Interface en ligne de commande.

Usage :
    python -m src.cli <commande> [options]

Commandes :
    init              Initialise les répertoires
    import-manual     Importe depuis un CSV
    enrich            Enrichit les données
    score             Calcule les scores
    generate-emails   Génère les emails
    generate-cvs      Génère les CV AltaCV
    export            Exporte les résultats
    report            Génère le rapport
    pipeline          Exécute tout le pipeline
    send-emails       Simule l'envoi (dry-run)
    send-test-email   Envoie un email test vers soi-même
"""

import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        prog="alternance-finder",
        description="Outil d'automatisation de recherche d'alternance",
    )
    subparsers = parser.add_subparsers(dest="command", help="Commande à exécuter")

    # --- init ---
    subparsers.add_parser("init", help="Initialiser les répertoires du projet")

    # --- import-manual ---
    p_import = subparsers.add_parser("import-manual", help="Importer depuis un CSV")
    p_import.add_argument("csv_path", nargs="?", default="data/manual_imports/sample_companies.csv",
                          help="Chemin vers le fichier CSV")

    # --- enrich ---
    subparsers.add_parser("enrich", help="Enrichir les données des entreprises")

    # --- score ---
    subparsers.add_parser("score", help="Calculer les scores")

    # --- generate-emails ---
    p_emails = subparsers.add_parser("generate-emails", help="Générer les emails personnalisés")
    p_emails.add_argument("--min-score", type=int, default=60, help="Score minimum (défaut: 60)")

    # --- generate-cvs ---
    p_cvs = subparsers.add_parser("generate-cvs", help="Générer les CV AltaCV")
    p_cvs.add_argument("--min-score", type=int, default=75, help="Score minimum (défaut: 75)")

    # --- export ---
    subparsers.add_parser("export", help="Exporter les résultats")

    # --- report ---
    subparsers.add_parser("report", help="Générer le rapport")

    # --- pipeline ---
    p_pipeline = subparsers.add_parser("pipeline", help="Exécuter le pipeline complet")
    p_pipeline.add_argument("--input", "--csv", dest="csv", default="data/manual_imports/sample_companies.csv",
                            help="Chemin vers un fichier CSV (défaut: data/manual_imports/sample_companies.csv)")
    p_pipeline.add_argument("--min-score-email", type=int, default=60,
                            help="Score minimum pour générer un email (défaut: 60)")
    p_pipeline.add_argument("--min-score-cv", type=int, default=75,
                            help="Score minimum pour générer un CV (défaut: 75)")
    p_pipeline.add_argument("--skip-cv", action="store_true", help="Ignorer la génération de CV")

    # --- send-emails ---
    p_send = subparsers.add_parser("send-emails", help="Simuler l'envoi d'emails")
    p_send.add_argument("--dry-run", action="store_true", default=True,
                        help="Simulation uniquement (défaut: activé)")
    p_send.add_argument("--min-score", type=int, default=60)

    # --- send-test-email ---
    p_test = subparsers.add_parser("send-test-email", help="Envoyer un email test vers soi-même")
    p_test.add_argument("--company", required=True, help="Nom de l'entreprise à simuler")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # --- Dispatch ---
    if args.command == "init":
        _cmd_init()
    elif args.command == "import-manual":
        _cmd_import_manual(args.csv_path)
    elif args.command == "enrich":
        _cmd_enrich()
    elif args.command == "score":
        _cmd_score()
    elif args.command == "generate-emails":
        _cmd_generate_emails(args.min_score)
    elif args.command == "generate-cvs":
        _cmd_generate_cvs(args.min_score)
    elif args.command == "export":
        _cmd_export()
    elif args.command == "report":
        _cmd_report()
    elif args.command == "pipeline":
        _cmd_pipeline(args)
    elif args.command == "send-emails":
        _cmd_send_emails(args)
    elif args.command == "send-test-email":
        _cmd_send_test_email(args.company)


def _cmd_init():
    from src.utils.io import ensure_dir
    from src.utils.logging import logger

    dirs = [
        "data/raw", "data/processed", "data/exports", "data/manual_imports",
        "outputs/emails", "outputs/cvs", "outputs/reports", "outputs/tracking",
        "cv/generated", "notes", "config",
    ]
    for d in dirs:
        ensure_dir(d)
    logger.info("✓ Répertoires initialisés.")


def _cmd_import_manual(csv_path: str):
    from src.collectors.manual_import import import_from_csv
    from src.utils.io import save_csv
    from src.utils.logging import logger

    companies = import_from_csv(csv_path)
    if companies:
        save_csv(
            "data/processed/companies_clean.csv",
            [c.to_dict() for c in companies],
        )
        logger.info(f"✓ {len(companies)} entreprises importées → data/processed/companies_clean.csv")


def _cmd_enrich():
    from src.models.company import Company
    from src.enrichment.company_enricher import enrich_companies
    from src.utils.io import load_csv, save_csv
    from src.utils.logging import logger

    rows = load_csv("data/processed/companies_clean.csv")
    if not rows:
        logger.error("Aucune donnée dans data/processed/companies_clean.csv. Lancez import-manual d'abord.")
        return
    companies = [Company.from_dict(row) for row in rows]
    companies = enrich_companies(companies)
    save_csv("data/processed/companies_clean.csv", [c.to_dict() for c in companies])
    logger.info("✓ Enrichissement terminé.")


def _cmd_score():
    from src.models.company import Company
    from src.scoring.scorer import score_companies
    from src.utils.io import load_csv, save_csv
    from src.utils.logging import logger

    rows = load_csv("data/processed/companies_clean.csv")
    if not rows:
        logger.error("Aucune donnée. Lancez import-manual et enrich d'abord.")
        return
    companies = [Company.from_dict(row) for row in rows]
    companies = score_companies(companies)
    save_csv("data/processed/companies_scored.csv", [c.to_dict() for c in companies])
    logger.info("✓ Scoring terminé.")


def _cmd_generate_emails(min_score: int):
    from src.models.company import Company
    from src.generation.email_generator import generate_emails
    from src.utils.io import load_csv
    from src.utils.logging import logger

    rows = load_csv("data/processed/companies_scored.csv")
    if not rows:
        logger.error("Aucune donnée scorée. Lancez score d'abord.")
        return
    companies = [Company.from_dict(row) for row in rows]
    generate_emails(companies, min_score=min_score)
    save_csv("data/processed/companies_scored.csv", [c.to_dict() for c in companies])


def _cmd_generate_cvs(min_score: int):
    from src.models.company import Company
    from src.generation.cv_generator import generate_cvs
    from src.utils.io import load_csv
    from src.utils.logging import logger

    rows = load_csv("data/processed/companies_scored.csv")
    if not rows:
        logger.error("Aucune donnée scorée. Lancez score d'abord.")
        return
    companies = [Company.from_dict(row) for row in rows]
    generate_cvs(companies, min_score=min_score)


def _cmd_export():
    from src.models.company import Company
    from src.scoring.scorer import get_top_targets
    from src.utils.io import load_csv, save_csv, ensure_dir
    from src.utils.logging import logger

    rows = load_csv("data/processed/companies_scored.csv")
    if not rows:
        logger.error("Aucune donnée scorée.")
        return

    companies = [Company.from_dict(row) for row in rows]
    ensure_dir("outputs/reports")

    top = get_top_targets(companies, min_score=60)
    if top:
        save_csv("outputs/reports/top_targets.csv", [c.to_dict() for c in top])
        logger.info(f"✓ {len(top)} cibles exportées → outputs/reports/top_targets.csv")

    high = [c for c in companies if c.score >= 80 and not c.do_not_contact]
    if high:
        save_csv("outputs/reports/high_priority_targets.csv", [c.to_dict() for c in high])
        logger.info(f"✓ {len(high)} priorités hautes → outputs/reports/high_priority_targets.csv")


def _cmd_report():
    from src.utils.logging import logger
    logger.info("Utilisez 'pipeline' pour générer le rapport complet.")


def _cmd_pipeline(args):
    from src.main import run_pipeline
    run_pipeline(
        csv_path=args.csv,
        min_score_email=args.min_score_email,
        min_score_cv=args.min_score_cv,
        skip_cv=args.skip_cv,
    )


def _cmd_send_emails(args):
    from src.models.company import Company
    from src.tracking.send_mail_draft import dry_run_emails
    from src.utils.io import load_csv
    from src.utils.logging import logger

    rows = load_csv("data/processed/companies_scored.csv")
    if not rows:
        logger.error("Aucune donnée scorée. Lancez pipeline d'abord.")
        return
    companies = [Company.from_dict(row) for row in rows]
    dry_run_emails(companies, min_score=args.min_score)


def _cmd_send_test_email(company_name: str):
    from src.models.company import Company
    from src.tracking.send_mail_draft import send_test_email
    from src.utils.io import load_csv
    from src.utils.logging import logger

    rows = load_csv("data/processed/companies_scored.csv")
    if not rows:
        logger.error("Aucune donnée scorée. Lancez pipeline d'abord.")
        return

    companies = [Company.from_dict(row) for row in rows]
    target = None
    for c in companies:
        if c.company_name.lower() == company_name.lower():
            target = c
            break

    if not target:
        logger.error(f"Entreprise introuvable : {company_name}")
        logger.info("Entreprises disponibles :")
        for c in companies:
            logger.info(f"  - {c.company_name} (score: {c.score})")
        return

    if not target.email_body:
        logger.warning("Email non généré pour cette entreprise. Lancez generate-emails d'abord.")
        return

    logger.info(f"\n📧 Envoi test pour : {target.company_name}")
    logger.info(f"   → L'email sera envoyé à TEST_RECIPIENT_EMAIL, pas à l'entreprise.")

    send_test_email(target)


if __name__ == "__main__":
    main()
