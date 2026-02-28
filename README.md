# Recherche de Stage – Envoi automatisé de candidatures

Deux scripts Python pour :
1. **Scraper** les emails des entreprises d'Euratechnologies
2. **Envoyer** des candidatures spontanées personnalisées à chacune

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
pip install requests
```

---

## Étape 1 – Scraper les emails

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

## Étape 2 – Envoyer les candidatures

### Configuration

Avant de lancer le script, définis la variable d'environnement avec ton mot de passe d'application Gmail :

```powershell
$env:GMAIL_APP_PASSWORD = "xxxx xxxx xxxx xxxx"
```

Si besoin, tu peux aussi changer l'adresse d'expédition :

```powershell
$env:GMAIL_FROM = "ton.email@gmail.com"
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
- Envoyer un mail personnalisé avec le CV en pièce jointe à chaque entreprise
- Attendre 8 secondes entre chaque envoi (anti rate-limiting)
- Se reconnecter automatiquement en cas de coupure

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
├── emails-script.py                    # Script de scraping des emails
├── send-emails-script.py               # Script d'envoi des candidatures
├── CV-Aymen-CHAGHOUB-stage_compressed.pdf  # CV en pièce jointe
├── emails.txt                          # Emails extraits
├── entreprises_emails.txt              # Entreprises avec email
├── toutes_entreprises.txt              # Toutes les entreprises
├── envoi_log.csv                       # Log des envois (généré automatiquement)
└── README.md                           # Ce fichier
```

---

## Notes importantes

- **Gmail limite à ~500 mails/jour** pour les comptes gratuits. Avec 391 entreprises et 8s de délai, l'envoi prend environ **52 minutes**.
- Le mot de passe d'application est différent du mot de passe Gmail normal. Pour en générer un : Compte Google → Sécurité → Validation en 2 étapes → Mots de passe des applications.
- Pour modifier le contenu du mail, édite la fonction `make_email_body()` dans `send-emails-script.py`.
