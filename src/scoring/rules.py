"""
Règles de scoring individuelles.

Chaque règle évalue un aspect d'une entreprise et retourne
un bonus ou un malus en points.
"""

from __future__ import annotations

from src.models.company import Company
from src.utils.text import contains_any, count_keyword_matches


def apply_rules(
    company: Company,
    scoring_config: dict,
    keywords_config: dict,
) -> tuple[int, str]:
    """
    Applique toutes les règles de scoring à une entreprise.

    Returns:
        (score_total, détails_texte)
    """
    total = 0
    details = []

    # --- Appliquer les bonus ---
    for rule in scoring_config.get("rules", []):
        points = _evaluate_rule(company, rule, keywords_config)
        if points > 0:
            total += points
            details.append(f"+{points} {rule['name']}")

    # --- Appliquer les malus ---
    for penalty in scoring_config.get("penalties", []):
        points = _evaluate_penalty(company, penalty)
        if points < 0:
            total += points
            details.append(f"{points} {penalty['name']}")

    return total, " | ".join(details)


def _evaluate_rule(company: Company, rule: dict, keywords_config: dict) -> int:
    """Évalue une règle de bonus."""
    field_name = rule.get("field", "")
    condition = rule.get("condition", "")
    value = rule.get("value")
    points = rule.get("points", 0)

    field_value = _get_field(company, field_name)

    if condition == "equals":
        if field_value == value:
            return points

    elif condition == "not_empty":
        if field_value:
            return points

    elif condition == "contains_any":
        if isinstance(value, list) and contains_any(str(field_value), value):
            return points

    elif condition == "contains":
        if isinstance(value, str) and value.lower() in str(field_value).lower():
            return points

    elif condition == "between":
        if isinstance(value, list) and len(value) == 2:
            try:
                num = int(field_value) if field_value else 0
                if value[0] <= num <= value[1]:
                    return points
            except (ValueError, TypeError):
                pass

    elif condition == "keywords_match":
        # Compare against keywords from keywords.yaml
        kw_key = value if isinstance(value, str) else "strong_keywords"
        keywords = keywords_config.get(kw_key, [])
        if keywords and contains_any(str(field_value), keywords):
            return points

    elif condition == "count_keywords":
        # Points par mot-clé trouvé
        kw_key = value if isinstance(value, str) else "strong_keywords"
        keywords = keywords_config.get(kw_key, [])
        # Combine multiple text fields for keyword search
        all_text = " ".join([
            str(_get_field(company, "keywords_found")),
            str(_get_field(company, "tech_stack")),
            str(_get_field(company, "job_descriptions_found")),
            str(_get_field(company, "notes")),
        ])
        count = count_keyword_matches(all_text, keywords)
        if count > 0:
            per_match = rule.get("points_per_match", 5)
            max_pts = rule.get("max_points", 25)
            return min(count * per_match, max_pts)

    return 0


def _evaluate_penalty(company: Company, penalty: dict) -> int:
    """Évalue une règle de malus."""
    field_name = penalty.get("field", "")
    condition = penalty.get("condition", "")
    value = penalty.get("value")
    points = penalty.get("points", 0)

    field_value = _get_field(company, field_name)

    if condition == "equals":
        if field_value == value:
            return points

    elif condition == "contains":
        if isinstance(value, str) and value.lower() in str(field_value).lower():
            return points

    elif condition == "contains_all":
        if isinstance(value, list):
            text = str(field_value).lower()
            if all(v.lower() in text for v in value):
                return points

    elif condition == "not_contains_any":
        if isinstance(value, list):
            if not contains_any(str(field_value), value):
                return points

    elif condition == "empty_and":
        other_field = penalty.get("other_field", "")
        other_value = _get_field(company, other_field)
        if not field_value and not other_value:
            return points

    return 0


def _get_field(company: Company, field_name: str):
    """Récupère la valeur d'un champ de l'entreprise."""
    return getattr(company, field_name, "")
