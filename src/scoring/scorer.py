"""
Moteur de scoring — calcule le score de chaque entreprise
selon les règles définies dans config/scoring.yaml.
"""

from __future__ import annotations

from src.models.company import Company
from src.scoring.rules import apply_rules
from src.utils.io import load_config
from src.utils.logging import logger


def score_companies(companies: list[Company]) -> list[Company]:
    """
    Calcule le score de chaque entreprise et trie par score décroissant.
    """
    logger.info(f"Scoring de {len(companies)} entreprises...")

    try:
        scoring_config = load_config("scoring.yaml")
        keywords_config = load_config("keywords.yaml")
    except FileNotFoundError as e:
        logger.error(f"Configuration manquante : {e}")
        return companies

    thresholds = scoring_config.get("thresholds", {})

    for company in companies:
        score, details = apply_rules(company, scoring_config, keywords_config)
        company.score = max(0, score)  # Score minimum 0
        company.score_details = details

        # Déterminer l'action recommandée
        if company.do_not_contact:
            company.recommended_action = "ne_pas_contacter"
        elif company.score >= thresholds.get("high_priority", 80):
            company.recommended_action = "priorite_haute_cv_cible"
        elif company.score >= thresholds.get("good_target", 60):
            company.recommended_action = "email_personnalise"
        elif company.score >= thresholds.get("backup", 45):
            company.recommended_action = "backup"
        else:
            company.recommended_action = "ne_pas_contacter"

    # Trier par score décroissant
    companies.sort(key=lambda c: c.score, reverse=True)

    # Stats
    high = sum(1 for c in companies if c.score >= thresholds.get("high_priority", 80))
    good = sum(1 for c in companies
               if thresholds.get("good_target", 60) <= c.score < thresholds.get("high_priority", 80))
    backup = sum(1 for c in companies
                 if thresholds.get("backup", 45) <= c.score < thresholds.get("good_target", 60))
    skip = sum(1 for c in companies if c.score < thresholds.get("backup", 45))

    logger.info(f"  → Priorité haute : {high}")
    logger.info(f"  → Bonne cible    : {good}")
    logger.info(f"  → Backup         : {backup}")
    logger.info(f"  → Non contactées : {skip}")

    return companies


def get_top_targets(companies: list[Company], min_score: int = 60) -> list[Company]:
    """Retourne les entreprises au-dessus du score minimum."""
    return [c for c in companies if c.score >= min_score and not c.do_not_contact]
