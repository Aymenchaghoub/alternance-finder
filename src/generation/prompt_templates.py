"""
TODO — Templates de prompts pour la génération LLM.

En V1, la génération se fait via templates YAML sans LLM.
Ce module sera utilisé quand LLM_PROVIDER != "template".
"""

SYSTEM_PROMPT = """Tu es un assistant qui aide à rédiger des emails de candidature
professionnels, personnalisés et concis pour des alternances en développement logiciel / IA.

Règles :
- Être direct et professionnel
- Ne pas faire de survente
- Personnaliser selon l'entreprise cible
- Rester court (< 200 mots pour le corps)
- Ne jamais inventer de compétences ou projets
"""

EMAIL_PROMPT_TEMPLATE = """Rédige un email de candidature pour une alternance chez {company_name}.

Informations sur l'entreprise :
- Secteur : {sector}
- Localisation : {location}
- Offres détectées : {job_titles}
- Notes : {notes}

Profil du candidat :
- Nom : Aymen CHAGHOUB
- Formation : L3 Informatique, admis en Master IA/développement
- Stage actuel : Ouidou Nord (SaaS multi-tenant, React, Spring Boot)
- Projets : MediBrief (SaaS IA), Assistant RAG ArXiv, SchoolSphere
- Recherche : alternance 24 mois à partir de sept. 2026

Angle de personnalisation suggéré : {personalization_angle}

Génère :
1. Un objet d'email
2. Le corps de l'email
"""
