"""
Script d'envoi de candidatures spontanées de stage (SMTP + App Password)
========================================================================
Envoie un mail personnalisé avec CV à chaque entreprise listée dans
entreprises_emails.txt. Log chaque envoi dans envoi_log.csv pour éviter
les doublons si le script est relancé.
"""

import sys
import smtplib
import time
import csv
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime

# Forcer UTF-8 sur la console Windows
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ============================================================
# CONFIGURATION
# ============================================================

DRY_RUN = False  # False = envoi réel

# --- Compte Gmail ---
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_FROM = "ensm.chaghoub.aymen@gmail.com"
EMAIL_PASSWORD = open(os.path.join(os.path.dirname(__file__), ".env")).read().strip()  # Mot de passe dans .env (1 ligne)

# --- CV en pièce jointe ---
CV_PATH = r"C:\Users\Aymen\Desktop\Recherche-stage\CV-Aymen-CHAGHOUB-stage.pdf"
CV_FILENAME = "CV-Aymen-CHAGHOUB.pdf"  # nom affiché dans le mail

# --- Fichier source des entreprises ---
ENTREPRISES_FILE = "entreprises_emails.txt"

# --- Délai entre chaque mail (en secondes) ---
DELAY_BETWEEN_EMAILS = 8  # 8s pour éviter le rate-limiting Gmail

# --- Limite quotidienne (Gmail gratuit = 500/jour, on garde une marge) ---
DAILY_LIMIT = 480

# --- Fichier de log ---
LOG_FILE = "envoi_log.csv"

# ============================================================
# TEMPLATE DU MAIL
# ============================================================

SUBJECT = "Candidature spontanée – Stage Data Science / IA / Web Full-Stack (12 semaines)"

def make_email_body(company_name: str) -> str:
    """Génère le corps du mail personnalisé avec le nom de l'entreprise."""

    # Si pas de nom d'entreprise, version générique
    if company_name and company_name != "-":
        intro = f"Actuellement étudiant en L3 Informatique à l'Université de Lille, je me permets de vous contacter car le profil de {company_name} correspond parfaitement à mes aspirations professionnelles."
    else:
        intro = "Actuellement étudiant en L3 Informatique à l'Université de Lille, je me permets de vous adresser ma candidature spontanée."

    body = f"""Madame, Monsieur,

{intro}

Je suis à la recherche d'un stage de 12 semaines à partir du 13 avril 2026 dans le domaine de la Data Science, du Machine Learning ou du développement Full-Stack.

Mon parcours (Classes Préparatoires en Mathématiques & Informatique, puis Licence Informatique) m'a permis de développer des compétences solides en :

  • Data Science & Machine Learning : Python, Pandas, Scikit-learn, XGBoost, feature engineering
  • IA Générative : OpenAI API, LLM, prompt engineering
  • Développement Full-Stack : Next.js, React, Node.js, TypeScript, PostgreSQL, Docker

J'ai notamment conçu MediBrief, une plateforme SaaS multi-locataires intégrant des résumés médicaux générés par LLM en temps réel, ainsi que plusieurs projets de machine learning (prédiction immobilière, classification médicale, analyse de churn).

Je serais ravi de mettre ces compétences au service de votre équipe et de contribuer activement à vos projets.

Vous trouverez mon CV en pièce jointe. Je reste disponible pour un entretien à votre convenance.

Cordialement,

Aymen CHAGHOUB
L3 Informatique – Université de Lille
Tél : +33 7 58 26 37 06
Email : ensm.chaghoub.aymen@gmail.com
LinkedIn : linkedin.com/in/aymen-chaghoub-1a7796279
GitHub : github.com/Aymenchaghoub"""

    return body


# ============================================================
# LECTURE DES ENTREPRISES
# ============================================================

def load_companies(filepath: str) -> list[dict]:
    """Lit le fichier entreprises_emails.txt et retourne une liste de dicts (dédupliqué par email)."""
    companies = []
    seen_emails = set()
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Sauter l'en-tête (2 premières lignes)
    for line in lines[2:]:
        line = line.rstrip("\n")
        if not line.strip():
            continue
        # Format : NOM (45 chars) EMAIL (45 chars) TELEPHONE (20 chars) SITE
        # On parse par colonnes fixes
        name = line[:45].strip()
        email = line[45:90].strip()
        phone = line[90:110].strip()
        website = line[110:].strip()

        if email and "@" in email and " " not in email:
            key = email.lower()
            if key not in seen_emails:
                seen_emails.add(key)
                companies.append({
                    "name": name,
                    "email": email,
                    "phone": phone,
                    "website": website,
                })

    return companies


# ============================================================
# VÉRIFICATION DES ENVOIS DÉJÀ FAITS
# ============================================================

def load_already_sent(log_file: str) -> set:
    """Charge les emails déjà envoyés depuis le fichier de log."""
    sent = set()
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)  # skip header
            for row in reader:
                if len(row) >= 3 and row[2] == "OK":
                    sent.add(row[1])
    return sent


def count_sent_today(log_file: str) -> int:
    """Compte le nombre de mails envoyés avec succès aujourd'hui."""
    today = datetime.now().strftime("%Y-%m-%d")
    count = 0
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if len(row) >= 3 and row[2] == "OK" and row[0].startswith(today):
                    count += 1
    return count


def log_result(log_file: str, email: str, status: str, company: str):
    """Ajoute une ligne au fichier de log."""
    file_exists = os.path.exists(log_file)
    with open(log_file, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "email", "status", "company"])
        writer.writerow([datetime.now().isoformat(), email, status, company])


# ============================================================
# ENVOI D'UN MAIL
# ============================================================

def send_email(smtp_conn, to_email: str, company_name: str) -> bool:
    """Envoie un mail avec CV en pièce jointe. Retourne True si succès."""
    msg = MIMEMultipart()
    msg["From"] = EMAIL_FROM
    msg["To"] = to_email
    msg["Subject"] = SUBJECT

    # Corps du mail
    body = make_email_body(company_name)
    msg.attach(MIMEText(body, "plain", "utf-8"))

    # Pièce jointe CV
    with open(CV_PATH, "rb") as f:
        attachment = MIMEApplication(f.read(), _subtype="pdf")
        attachment.add_header(
            "Content-Disposition", "attachment", filename=CV_FILENAME
        )
        msg.attach(attachment)

    smtp_conn.sendmail(EMAIL_FROM, to_email, msg.as_string())
    return True


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 60)
    print("  ENVOI DES CANDIDATURES SPONTANÉES")
    print("=" * 60)

    # Vérifier que le CV existe
    if not os.path.exists(CV_PATH):
        print(f"\nERREUR : CV introuvable -> {CV_PATH}")
        return

    # Charger les entreprises
    companies = load_companies(ENTREPRISES_FILE)
    print(f"\n{len(companies)} entreprises avec email chargées")

    # Filtrer celles déjà contactées
    already_sent = load_already_sent(LOG_FILE)
    to_send = [c for c in companies if c["email"] not in already_sent]
    print(f"{len(already_sent)} déjà envoyés, {len(to_send)} restants")

    # Vérifier la limite quotidienne
    sent_today = count_sent_today(LOG_FILE)
    remaining_today = max(0, DAILY_LIMIT - sent_today)
    print(f"{sent_today} envoyés aujourd'hui, limite = {DAILY_LIMIT}, reste = {remaining_today}\n")

    if not to_send:
        print("Rien à envoyer !")
        return

    if remaining_today == 0:
        print(f"Limite quotidienne atteinte ({DAILY_LIMIT}). Relance demain !")
        return

    # Connexion SMTP
    print("Connexion à Gmail SMTP...")
    smtp_conn = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    smtp_conn.starttls()
    smtp_conn.login(EMAIL_FROM, EMAIL_PASSWORD)
    print("Connecté !\n")

    sent_count = 0
    error_count = 0

    for i, company in enumerate(to_send, 1):
        # Vérifier la limite quotidienne
        if sent_count + sent_today >= DAILY_LIMIT:
            print(f"\n⚠ Limite quotidienne atteinte ({DAILY_LIMIT} mails).")
            print(f"  Relance le script demain pour envoyer les {len(to_send) - i + 1} restants.")
            break

        email = company["email"]
        name = company["name"]

        print(f"[{i}/{len(to_send)}] {name:<40} -> {email}")

        try:
            send_email(smtp_conn, email, name)
            log_result(LOG_FILE, email, "OK", name)
            sent_count += 1
            time.sleep(DELAY_BETWEEN_EMAILS)
        except Exception as e:
            print(f"  ERREUR: {e}")
            log_result(LOG_FILE, email, f"ERREUR: {e}", name)
            error_count += 1
            # Reconnecter en cas de timeout
            try:
                smtp_conn.quit()
            except Exception:
                pass
            time.sleep(30)
            smtp_conn = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            smtp_conn.starttls()
            smtp_conn.login(EMAIL_FROM, EMAIL_PASSWORD)

    # Fermer la connexion SMTP
    smtp_conn.quit()

    print(f"\n{'=' * 60}")
    print(f"  Terminé ! {sent_count} envoyés, {error_count} erreurs")
    print(f"  Log -> {LOG_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    main()
