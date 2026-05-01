"""
Fournisseur LLM — abstraction pour la génération de texte.

En V1, seul le mode "template" est supporté (pas d'API IA).
"""

from src.utils.logging import logger


def get_llm_provider(provider_name: str = "template"):
    """
    Retourne le fournisseur LLM configuré.

    Args:
        provider_name: "template" (défaut) ou "openai" (TODO).

    Returns:
        Instance du provider.
    """
    if provider_name == "template":
        return TemplateProvider()
    elif provider_name == "openai":
        logger.warning("OpenAI provider pas encore implémenté. Utilisation du mode template.")
        return TemplateProvider()
    else:
        logger.warning(f"Provider inconnu : {provider_name}. Utilisation du mode template.")
        return TemplateProvider()


class TemplateProvider:
    """Provider basé sur les templates YAML (pas d'IA)."""

    def __init__(self):
        self.name = "template"

    def generate(self, prompt: str, **kwargs) -> str:
        """En mode template, pas de génération IA."""
        logger.info("Mode template : pas de génération IA.")
        return ""
