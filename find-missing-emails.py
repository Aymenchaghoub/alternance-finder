"""
Script de recherche d'emails pour les entreprises d'Euratechnologies
====================================================================
Enrichit entreprises_emails.txt avec les emails trouvés via le
scraping des sites web des entreprises (homepage + pages contact).

Usage : python find-missing-emails.py
"""

import sys
import re
import os
import time
import csv
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ============================================================
# CONFIGURATION
# ============================================================

TOUTES_ENTREPRISES_FILE = "toutes_entreprises.txt"
ENTREPRISES_EMAILS_FILE = "entreprises_emails.txt"
FOUND_EMAILS_LOG = "found_emails_log.csv"

# Délais (en secondes)
DELAY_WEBSITE = 2      # entre chaque requête website

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
}

# Emails à ignorer (génériques, faux positifs)
BLACKLISTED_DOMAINS = {
    "example.com", "sentry.io", "wixpress.com", "sentry-next.wixpress.com",
    "googleusercontent.com", "w3.org", "schema.org", "jquery.com",
    "wordpress.org", "facebook.com", "twitter.com", "instagram.com",
    "tutao.de", "tutanota.com", "protonmail.com",
    "duckduckgo.com",       # DDG error pages
    "ag-grid.com",          # library placeholder
    "ingest.sentry.io",     # sentry ingest
    "contact-manager.net",
    "nameify.com",          # template placeholder
    "techland.com",         # template placeholder
    "mysite.com",           # Wix default placeholder
    "company.com",          # generic placeholder
    "uber.com",             # sample/demo data
    "ginger.com",           # unrelated library
    "corner.com",           # template placeholder
    "codeglen.com",         # website builder template
}

BLACKLISTED_PREFIXES = {
    "noreply", "no-reply", "mailer-daemon", "postmaster",
    "webmaster", "admin@wordpress", "info@example", "abuse",
    "error-lite",           # DDG error page
    "addresscontact",       # obfuscated placeholder
}

# Emails-placeholders exacts trouvés dans des templates
PLACEHOLDER_EMAILS = {
    "votre@email.com", "votre@email.fr", "ton@email.com",
    "example@mail.com", "example@domain.com", "example@email.com",
    "example@yourdomain.com", "email@website.com", "email@email.com",
    "email@exemple.com", "monmail@exemple.fr", "user@domain.com",
    "guest@domain.com", "name@domain.com", "your@email.com",
    "info@example.com", "test@test.com", "email@domain.com",
    "john.smith@breeze.co",       # sample data
    "coolwanglu@gmail.com",       # pdf.js dev
    "your.email@company.com",     # generic placeholder
    "techlab@mail.com",           # template
    "info@mysite.com",            # Wix default
    "admin@codeglen.com",         # template builder
    "hello@dotlife.com",          # unrelated
    "security@ginger.com",        # unrelated library
    "la@corner.com",              # template
}

# Patterns regex de placeholders (local part ou domain)
PLACEHOLDER_PATTERNS = re.compile(
    r"^(votre|example|email|ton|user|guest|monmail|your|name|test)@"
    r"|@(exemple|email|domain|website|yourdomain|mysite)\.",
    re.IGNORECASE,
)

# ============================================================
# REGEX EMAIL
# ============================================================

EMAIL_REGEX = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
    re.IGNORECASE,
)


def is_valid_email(email: str) -> bool:
    """Filtre les faux positifs."""
    email = email.lower().strip()
    # Trop court ou trop long
    if len(email) < 6 or len(email) > 80:
        return False
    # Contient des caractères bizarres (* utilisé pour obfusquer)
    if "*" in email:
        return False
    local, _, domain = email.partition("@")
    if not domain:
        return False
    # Domaine blacklisté (vérifie aussi les sous-domaines)
    if any(domain == bd or domain.endswith("." + bd) for bd in BLACKLISTED_DOMAINS):
        return False
    # Préfixe blacklisté
    for prefix in BLACKLISTED_PREFIXES:
        if local.startswith(prefix):
            return False
    # Extensions de fichier (image.png@2x etc.)
    if re.search(r"\.(png|jpg|jpeg|gif|svg|css|js|webp)$", domain):
        return False
    # Local part trop long (probablement un hash ou du garbage)
    if len(local) > 40:
        return False
    # Domaine qui ressemble à du garbage (pas de voyelle ou TLD bizarre)
    tld = domain.rsplit(".", 1)[-1]
    if len(tld) > 10:
        return False
    # Hash dans le local part (>= 16 car hex)
    if re.fullmatch(r"[a-f0-9]{16,}", local):
        return False
    # Placeholder exact
    if email in PLACEHOLDER_EMAILS:
        return False
    # Placeholder pattern
    if PLACEHOLDER_PATTERNS.search(email):
        return False
    # Email incomplet (domaine sans TLD valide, ex: "barbara@madeleine")
    if "." not in domain:
        return False
    return True


def _clean_email(raw: str) -> str:
    """Nettoie un email brut (retire %20, espaces, points finaux)."""
    e = raw.strip().strip(".").lower()
    # Retirer les artefacts d'URL encoding au début
    e = re.sub(r"^(%20|%09|%0a|%0d)+", "", e)
    return e


def extract_emails_from_text(text: str) -> set:
    """Extrait les emails valides d'un texte."""
    # Limiter la taille du texte pour éviter les hangs de regex
    text = text[:500_000]
    raw = set(EMAIL_REGEX.findall(text))
    cleaned = set()
    for e in raw:
        c = _clean_email(e)
        if c and is_valid_email(c):
            cleaned.add(c)
    return cleaned


# ============================================================
# LECTURE DES ENTREPRISES
# ============================================================

def load_all_companies(filepath: str) -> list[dict]:
    """Charge toutes les entreprises depuis toutes_entreprises.txt."""
    companies = []
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
    for line in lines[2:]:  # skip header
        line = line.rstrip("\n")
        if not line.strip():
            continue
        name = line[:45].strip()
        email = line[45:90].strip()
        phone = line[90:110].strip()
        website = line[110:].strip()
        if email == "-":
            email = ""
        if website == "-":
            website = ""
        companies.append({
            "name": name,
            "email": email,
            "phone": phone,
            "website": website,
        })
    return companies


def load_existing_emails(filepath: str) -> set:
    """Charge les emails déjà connus."""
    emails = set()
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
        for line in lines[2:]:
            email = line[45:90].strip() if len(line) > 45 else ""
            if email and "@" in email:
                emails.add(email.lower())
    return emails


def load_already_searched(log_file: str) -> set:
    """Charge les entreprises déjà recherchées depuis le log."""
    searched = set()
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)  # skip header
            for row in reader:
                if len(row) >= 2:
                    searched.add(row[1])
    return searched


def log_found(log_file: str, company: str, email: str, source: str):
    """Log un email trouvé."""
    file_exists = os.path.exists(log_file)
    with open(log_file, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "company", "email", "source"])
        writer.writerow([datetime.now().isoformat(), company, email, source])


# ============================================================
# SCRAPING SITE WEB
# ============================================================

def normalize_url(url: str) -> str:
    """Normalise une URL (ajoute https:// si manquant)."""
    url = url.strip().rstrip("/")
    if not url:
        return ""
    # Ignorer les URLs non-web
    if any(x in url for x in ["facebook.com", "instagram.com", "linkedin.com",
                                "twitter.com", "youtube.com", "linktr.ee",
                                "drive.google.com", "docs.google.com",
                                "github.com", "github.io"]):
        return ""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def scrape_emails_from_url(url: str, timeout: int = 10) -> set:
    """Récupère les emails depuis une page web."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout,
                          allow_redirects=True, verify=False)
        resp.raise_for_status()
        # Chercher dans le HTML brut
        emails = extract_emails_from_text(resp.text)
        # Chercher aussi dans les liens mailto:
        soup = BeautifulSoup(resp.text, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.startswith("mailto:"):
                addr = href.replace("mailto:", "").split("?")[0].strip()
                if is_valid_email(addr):
                    emails.add(addr.lower())
        return emails
    except Exception:
        return set()


def scrape_website_emails(website: str) -> set:
    """Scrape le site web : homepage + page contact."""
    base_url = normalize_url(website)
    if not base_url:
        return set()

    all_emails = set()

    # 1. Homepage
    emails = scrape_emails_from_url(base_url)
    all_emails.update(emails)

    # 2. Pages contact courantes
    contact_paths = ["/contact", "/contact/", "/contactez-nous", "/nous-contacter",
                     "/contact-us", "/about", "/a-propos"]
    for path in contact_paths:
        contact_url = base_url.rstrip("/") + path
        emails = scrape_emails_from_url(contact_url, timeout=8)
        all_emails.update(emails)
        if all_emails:
            break  # Dès qu'on a trouvé, on arrête
        time.sleep(0.5)

    return all_emails



# ============================================================
# MISE À JOUR DU FICHIER entreprises_emails.txt
# ============================================================

def append_to_entreprises_file(filepath: str, company: dict):
    """Ajoute une entreprise au fichier entreprises_emails.txt."""
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(f"{company['name']:<45} {company['email']:<45} "
                f"{company['phone']:<20} {company['website']}\n")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 65)
    print("  RECHERCHE D'EMAILS MANQUANTS")
    print("=" * 65)

    # Charger les données
    all_companies = load_all_companies(TOUTES_ENTREPRISES_FILE)
    existing_emails = load_existing_emails(ENTREPRISES_EMAILS_FILE)
    already_searched = load_already_searched(FOUND_EMAILS_LOG)

    # Entreprises sans email
    missing = [c for c in all_companies if not c["email"]]
    # Filtrer celles déjà cherchées
    to_search = [c for c in missing if c["name"] not in already_searched]

    print(f"\n  Total entreprises    : {len(all_companies)}")
    print(f"  Avec email (déjà)   : {len(existing_emails)}")
    print(f"  Sans email          : {len(missing)}")
    print(f"  Déjà recherchées    : {len(already_searched)}")
    print(f"  Restant à chercher  : {len(to_search)}")
    print()

    if not to_search:
        print("Rien à chercher !")
        return

    found_count = 0
    searched_count = 0

    # --- PHASE 1 : Scraping des sites web ---
    with_website = [c for c in to_search if c["website"]]
    without_website = [c for c in to_search if not c["website"]]

    print(f"── PHASE 1 : Scraping des sites web ({len(with_website)} entreprises)")
    print()

    for i, company in enumerate(with_website, 1):
        name = company["name"]
        website = company["website"]
        print(f"  [{i}/{len(with_website)}] {name:<35} ({website[:40]})", end="", flush=True)

        emails = scrape_website_emails(website)

        if emails:
            email = sorted(emails)[0]  # Prendre le premier email trouvé
            print(f"  ✓ {email}")
            company["email"] = email
            append_to_entreprises_file(ENTREPRISES_EMAILS_FILE, company)
            log_found(FOUND_EMAILS_LOG, name, email, f"website:{website}")
            existing_emails.add(email.lower())
            found_count += 1
        else:
            print(f"  ✗")
            log_found(FOUND_EMAILS_LOG, name, "", "website:not_found")

        searched_count += 1
        time.sleep(DELAY_WEBSITE)

    # --- Résumé ---
    print(f"\n{'=' * 65}")
    print(f"  Terminé !")
    print(f"  Entreprises cherchées : {searched_count}")
    print(f"  Nouveaux emails       : {found_count}")
    print(f"  Total emails connus   : {len(existing_emails) + found_count}")
    print(f"  Log -> {FOUND_EMAILS_LOG}")
    print("=" * 65)

    # Mettre à jour emails.txt
    all_known_emails = set()
    with open(ENTREPRISES_EMAILS_FILE, "r", encoding="utf-8") as f:
        for line in f.readlines()[2:]:
            email = line[45:90].strip()
            if email and "@" in email:
                all_known_emails.add(email)

    with open("emails.txt", "w", encoding="utf-8") as f:
        for email in sorted(all_known_emails):
            f.write(email + "\n")

    print(f"  emails.txt mis à jour ({len(all_known_emails)} emails)")


if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    main()
