# alternance-finder

> Outil local d'automatisation intelligente de recherche d'alternance.

**⚠ Cet outil ne garantit pas l'obtention d'une alternance.** Il augmente fortement vos chances grâce à un meilleur ciblage, une meilleure personnalisation et un meilleur suivi.

---

## Objectif

**alternance-finder** automatise les étapes répétitives de la recherche d'alternance :

1. **Importer** des entreprises depuis un CSV manuel (ou futur API)
2. **Nettoyer** et dédupliquer les données
3. **Scorer** les entreprises selon votre profil (localisation, stack, secteur, offres)
4. **Générer** des emails personnalisés par type d'entreprise
5. **Préparer** des variantes de CV AltaCV
6. **Exporter** un tableau de suivi complet
7. **Simuler** l'envoi en dry-run (aucun envoi réel en V1)

Chaque étape peut être exécutée individuellement ou via le pipeline complet.

---

## Évolution depuis Recherche-stage

Ce projet est l'évolution de [Recherche-stage](https://github.com/Aymenchaghoub/Recherche-stage), un ensemble de scripts Python utilisés pour automatiser la recherche de stage. Les anciens scripts sont conservés dans le dossier `legacy/`.

Principales améliorations :
- Architecture modulaire et propre
- Pipeline configurable via YAML
- Scoring intelligent et personnalisable
- Emails personnalisés par type d'entreprise (8 templates)
- Génération de CV AltaCV automatisée
- Dry-run obligatoire — validation humaine avant tout contact
- Garde-fous RGPD et éthiques

---

## Installation

### Windows

```powershell
git clone https://github.com/Aymenchaghoub/alternance-finder.git
cd alternance-finder

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

cp .env.example .env
# Remplir .env avec vos identifiants (optionnel pour le pipeline de base)
```

### Linux / macOS

```bash
git clone https://github.com/Aymenchaghoub/alternance-finder.git
cd alternance-finder

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
```

---

## Utilisation rapide

### Pipeline complet

```bash
python -m src.cli pipeline
```

Cela exécute automatiquement :
1. Initialisation des répertoires
2. Import depuis `data/manual_imports/*.csv`
3. Déduplication
4. Enrichissement
5. Scoring
6. Génération d'emails
7. Génération de CV
8. Export des résultats
9. Mise à jour du tracking
10. Génération du rapport

### Commandes individuelles

```bash
# Initialiser les répertoires
python -m src.cli init

# Importer un CSV manuellement
python -m src.cli import-manual data/manual_imports/sample_companies.csv

# Enrichir les données
python -m src.cli enrich

# Calculer les scores
python -m src.cli score

# Générer les emails (score >= 60)
python -m src.cli generate-emails --min-score 60

# Générer les CV AltaCV (score >= 75)
python -m src.cli generate-cvs --min-score 75

# Exporter les résultats
python -m src.cli export

# Voir le rapport
python -m src.cli report

# Simuler l'envoi d'emails (dry-run)
python -m src.cli send-emails --dry-run

# Envoyer un email test à vous-même uniquement
python -m src.cli send-test-email --company "Demo AI Studio"
```

---
    
## Premier vrai lancement

1. **Remplir le fichier** :
   `data/manual_imports/paris_targets_seed.csv`
   
   Colonnes :
   `company_name,website,career_url,source,location,sector,job_titles_found,job_descriptions_found,contact_email,notes`

2. **Lancer le pipeline** :
   ```bash
   python -m src.cli pipeline --input data/manual_imports/paris_targets_seed.csv --skip-cv
   ```

3. **Inspecter** :
   - `outputs/reports/top_targets.csv`
   - `outputs/reports/high_priority_targets.csv`
   - `outputs/emails/`
   - `outputs/tracking/applications.csv`

4. **Relire manuellement** chaque email généré.

5. **Générer les CV ciblés** si besoin :
   ```bash
   python -m src.cli generate-cvs --min-score 75
   ```

6. **Faire un dry-run** :
   ```bash
   python -m src.cli send-emails --dry-run
   ```

7. **Pour un test d'envoi vers soi-même uniquement** :
   - créer un `.env` local à partir de `.env.example` ;
   - renseigner `TEST_RECIPIENT_EMAIL` ;
   - ne jamais mettre de secret dans Git ;
   - lancer :
     ```bash
     python -m src.cli send-test-email --company "Ouidou Nord"
     ```

8. **Rappel** :
   Aucun email réel ne doit être envoyé à une entreprise en V1.
   Les emails générés sont des brouillons à valider humainement.

---

## Import CSV manuel

Placez vos fichiers CSV dans `data/manual_imports/`. Format attendu :

```
company_name,website,career_url,source,location,sector,job_titles_found,job_descriptions_found,contact_email,notes
```

Un fichier d'exemple est fourni : `data/manual_imports/sample_companies.csv`

---

## Scoring

Le scoring est configurable via `config/scoring.yaml`. Règles principales :

| Critère | Points |
|---------|--------|
| Offre alternance tech active | +30 |
| Paris / Île-de-France | +25 |
| Stack correspond au profil | +20 |
| Recrute en dev/backend/IA | +20 |
| Secteur prioritaire (IA, SaaS, etc.) | +15 |
| Taille 10-500 personnes | +10 |
| Page carrière détectée | +10 |
| Email professionnel détecté | +10 |
| Mot-clé fort détecté | +5 chacun |
| Aucune activité tech | -15 |
| Aucun contact | -25 |
| do_not_contact | -100 |

**Seuils de priorité :**
- ≥ 80 : priorité haute (CV ciblé recommandé)
- ≥ 60 : bonne cible (email personnalisé)
- ≥ 45 : backup
- < 45 : ne pas contacter

---

## Génération d'emails

8 templates disponibles :
1. **Startup IA** — angle IA/ML/NLP
2. **SaaS B2B** — angle produit SaaS
3. **ESN / Cabinet tech** — angle polyvalence
4. **Éditeur logiciel** — angle produit logiciel
5. **Avec offre alternance** — candidature ciblée
6. **Sans offre mais pertinente** — candidature spontanée
7. **Relance 7 jours** — premier suivi
8. **Relance 14 jours** — dernier suivi

Les emails sont générés dans `outputs/emails/` (un fichier Markdown par entreprise).

---

## Génération CV AltaCV

Le template LaTeX (`cv/sample.tex`) n'est **jamais modifié**. Les variantes sont générées dans `cv/generated/`.

Si un compilateur LaTeX est disponible (latexmk, xelatex ou pdflatex), les PDF sont compilés automatiquement. Sinon, les fichiers `.tex` sont générés avec une instruction de compilation manuelle.

---

## Dry-run et envoi email

**En V1, l'envoi réel aux entreprises est désactivé.**

- `python -m src.cli send-emails --dry-run` : simule l'envoi
- `python -m src.cli send-test-email --company "Nom"` : envoie un test **à vous-même uniquement**

Pour activer l'envoi test, configurez `.env` :
```
GMAIL_ADDRESS=votre.email@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
TEST_RECIPIENT_EMAIL=votre.email@gmail.com
DRY_RUN=true
```

---

## Tracking

Le suivi des candidatures est dans `outputs/tracking/applications.csv`. Colonnes :

company_name, contact_email, email_subject, email_file, cv_file, score, priority, application_status, created_at, sent_at, follow_up_at, response_status, notes, do_not_contact

---

## Structure du projet

```
alternance-finder/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── legacy/              # Anciens scripts de Recherche-stage
├── notes/               # Documentation profil et contexte
├── config/              # Configuration YAML
│   ├── profile.yaml
│   ├── keywords.yaml
│   ├── scoring.yaml
│   ├── sources.yaml
│   └── email_templates.yaml
├── data/
│   ├── manual_imports/  # CSV manuels
│   ├── processed/       # Données nettoyées/scorées
│   └── ...
├── cv/
│   ├── sample.tex       # Template AltaCV (ne pas modifier)
│   └── generated/       # CV générés
├── outputs/
│   ├── emails/          # Emails générés
│   ├── cvs/             # PDF de CV
│   ├── reports/         # Rapports
│   └── tracking/        # Suivi des candidatures
├── src/
│   ├── cli.py           # Interface en ligne de commande
│   ├── main.py          # Pipeline principal
│   ├── collectors/      # Sources de données
│   ├── enrichment/      # Enrichissement
│   ├── scoring/         # Scoring
│   ├── generation/      # Génération emails/CV
│   ├── tracking/        # Suivi et envoi
│   ├── models/          # Modèles de données
│   └── utils/           # Utilitaires
└── tests/               # Tests pytest
```

---

## Configuration .env

Voir `.env.example` pour toutes les variables. Les variables critiques :

| Variable | Description | Requis pour V1 ? |
|----------|-------------|------------------|
| `GMAIL_ADDRESS` | Adresse Gmail | Non (envoi test uniquement) |
| `GMAIL_APP_PASSWORD` | Mot de passe d'application | Non |
| `TEST_RECIPIENT_EMAIL` | Email de test (le vôtre) | Non |
| `DRY_RUN` | Toujours `true` en V1 | Oui |
| `LLM_PROVIDER` | `template` en V1 | Oui |

---

## RGPD et éthique

Ce projet respecte les principes suivants :

- **Prospection B2B uniquement** — pas de récupération d'emails personnels
- **Droit d'opposition** — footer inclus dans chaque email
- **Validation humaine obligatoire** — aucun envoi sans confirmation
- **Dry-run par défaut** — l'envoi réel est désactivé en V1
- **do_not_contact** — respecté à tous les niveaux
- **Traçabilité** — source de chaque donnée conservée
- **Rate limiting** — limites configurables
- **Pas de scraping agressif** — pas de contournement anti-bot
- **Logs d'envoi** — chaque action est tracée

L'outil génère d'abord des **brouillons** que vous devez vérifier et approuver avant tout contact. Il n'effectue jamais d'envoi massif automatique.

---

## Roadmap

1. ✅ **V1 — CSV manuel** (actuel)
2. 🔜 France Travail API (offres d'emploi)
3. 🔜 API Sirene INSEE (données entreprises)
4. 🔜 La Bonne Alternance (offres alternance)
5. 🔜 Extraction email responsable RH
6. 🔜 Personnalisation LLM optionnelle

---

## Tests

```bash
pytest
```

---

## Commandes utiles

```bash
# Pipeline complet
python -m src.cli pipeline

# Voir les meilleurs prospects
# → outputs/reports/top_targets.csv

# Voir les emails générés
# → outputs/emails/

# Générer les CV
python -m src.cli generate-cvs --min-score 75

# Tests
pytest

# Dry-run
python -m src.cli send-emails --dry-run

# Email test vers soi-même
python -m src.cli send-test-email --company "Demo AI Studio"
```

---

## Renommage GitHub

Pour renommer le repo de `Recherche-stage` vers `alternance-finder` :

1. Aller sur GitHub → Settings → Repository name
2. Changer en `alternance-finder`
3. GitHub redirigera automatiquement l'ancienne URL

---

*Projet développé par [Aymen CHAGHOUB](https://github.com/Aymenchaghoub)*
