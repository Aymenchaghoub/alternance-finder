# Recherche de Stage – Envoi automatisé de candidatures

Trois scripts Python pour :
1. **Scraper** les emails des entreprises d’Euratechnologies via l’API
2. **Enrichir** la liste en scrapant les sites web des entreprises sans email
3. **Envoyer** des candidatures spontanées personnalisées à chacune

---

## Prérequis

- **Python 3.10+** installé ([python.org](https://www.python.org/downloads/))
- **Un compte Gmail** avec un [mot de passe d'application](https://myaccount.google.com/apppasswords) (nécessite la validation en 2 étapes)
- **Ton CV en PDF** dans ce dossier

---

## Installation rapide

```powershell
# 1. Ouvrir un terminal dans ce dossier

# 2. Créer un environnement virtuel
python -m venv .venv

# 3. Activer l'environnement
.\.venv\Scripts\Activate.ps1

# 4. Installer les dépendances
pip install requests beautifulsoup4
```

---

## Étape 1 – Scraper les emails (API)

```powershell
python emails-script.py
```

Ce script interroge l'API d'Euratechnologies et génère 3 fichiers :

| Fichier                   | Contenu                                      |
| ------------------------- | -------------------------------------------- |
| `emails.txt`              | Tous les emails uniques (1 par ligne)        |
| `entreprises_emails.txt`  | Entreprises avec email (nom, email, tel, site) |
| `toutes_entreprises.txt`  | Toutes les entreprises (avec ou sans email)  |

---

## Étape 2 – Trouver les emails manquants (scraping web)

```powershell
python find-missing-emails.py
```

Ce script parcourt les sites web des ~800 entreprises qui ont un site mais pas d’email, et extrait les emails depuis :
- La **homepage**
- Les pages **/contact**, **/contactez-nous**, **/nous-contacter**, **/about**, **/a-propos**
- Les liens **mailto:**

Il génère un log `found_emails_log.csv` et met à jour automatiquement `entreprises_emails.txt` et `emails.txt`.

**Résumé support** : si le script est interrompu, il reprend là où il s’était arrêté.

---

## Étape 3 – Envoyer les candidatures

### Configuration

Crée un fichier `.env` à la racine du projet avec ton mot de passe d'application Gmail (une seule ligne) :

```
xxxx xxxx xxxx xxxx
```

Vérifie aussi le chemin du CV dans le script :

```python
CV_PATH = r"C:\chemin\vers\ton\CV.pdf"
```

### Lancer l'envoi

```powershell
python send-emails-script.py
```

Le script va :
- Charger la liste depuis `entreprises_emails.txt`
- Ignorer les entreprises déjà contactées (grâce à `envoi_log.csv`)
- **Respecter la limite de 450 mails/jour** (Gmail autorise 500, marge de sécurité)
- Envoyer un mail personnalisé avec le CV en pièce jointe à chaque entreprise
- Attendre 8 secondes entre chaque envoi (anti rate-limiting)
- Se reconnecter automatiquement en cas de coupure

Si la limite quotidienne est atteinte, le script s’arrête proprement. **Relance-le le lendemain** pour envoyer le reste.

### Suivi

Chaque envoi est loggé dans `envoi_log.csv` :

```
timestamp,email,status,company
2026-02-28T14:30:00,contact@example.com,OK,Example SAS
```

**Si le script est interrompu**, il suffit de le relancer : il reprend là où il s'est arrêté grâce au log.

---

## Structure du projet

```
Recherche-stage/
├── .venv/                              # Environnement virtuel Python
├── emails-script.py                    # Script 1 : scraping API Euratechnologies
├── find-missing-emails.py              # Script 2 : scraping sites web (emails manquants)
├── send-emails-script.py               # Script 3 : envoi des candidatures
├── CV-Aymen-CHAGHOUB-stage_compressed.pdf  # CV en pièce jointe
├── emails.txt                          # Emails extraits (~650)
├── entreprises_emails.txt              # Entreprises avec email (~1150)
├── toutes_entreprises.txt              # Toutes les entreprises (1934)
├── envoi_log.csv                       # Log des envois (généré automatiquement)
├── found_emails_log.csv                # Log du scraping web (généré automatiquement)
└── README.md                           # Ce fichier
```

---

## Notes importantes

- **Gmail limite à 500 mails/jour** pour les comptes gratuits. Le script s’arrête automatiquement à 450 (marge de sécurité). Avec ~650 emails, il faut **2 jours** (relancer le lendemain).
- Avec 8s de délai, chaque tranche de 450 prend environ **1 heure**.
- Le mot de passe d'application est différent du mot de passe Gmail normal. Pour en générer un : Compte Google → Sécurité → Validation en 2 étapes → Mots de passe des applications.
- Pour modifier le contenu du mail, édite la fonction `make_email_body()` dans `send-emails-script.py`.

---

## Copier-coller : du clone à l'envoi

```powershell
# 1. Cloner le repo
git clone https://github.com/Aymenchaghoub/Recherche-stage.git
cd Recherche-stage

# 2. Créer et activer l'environnement virtuel
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Installer les dépendances
pip install requests beautifulsoup4


# 4. Scraper les emails des entreprises (API)
python emails-script.py

# 5. Trouver les emails manquants (sites web)
python find-missing-emails.py

# 6. Envoyer les candidatures (450/jour max, relancer le lendemain)
python send-emails-script.py
```
