"""
Script de suivi des envois de candidatures
===========================================
Se connecte à Gmail via IMAP, récupère les bounces (mail not found)
depuis les messages archivés, puis génère un fichier de suivi avec
le statut de chaque entreprise :

  ✓ Envoyé        — mail envoyé et pas de bounce
  ✗ Non trouvé    — bounce reçu (adresse invalide)
  ⏳ En attente    — pas encore envoyé

Usage : python suivi-status-script.py
"""

import sys
import os
import re
import csv
import imaplib
import email
from email.header import decode_header
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ============================================================
# CONFIGURATION
# ============================================================

IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993
EMAIL_ACCOUNT = "ensm.chaghoub.aymen@gmail.com"
EMAIL_PASSWORD = open(os.path.join(os.path.dirname(__file__), ".env")).read().strip()

ENTREPRISES_FILE = "entreprises_emails.txt"
LOG_FILE = "envoi_log.csv"
OUTPUT_FILE = "suivi_envois.txt"

# ============================================================
# 1. CHARGER LES ENTREPRISES
# ============================================================

def load_companies(filepath: str) -> list[dict]:
    """Charge les entreprises depuis le fichier fixe."""
    companies = []
    seen = set()
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
    for line in lines[2:]:
        if not line.strip():
            continue
        name = line[:45].strip()
        em = line[45:90].strip()
        if em and "@" in em and " " not in em:
            key = em.lower()
            if key not in seen:
                seen.add(key)
                companies.append({"name": name, "email": em})
    return companies


# ============================================================
# 2. CHARGER LE LOG D'ENVOI
# ============================================================

def load_sent_emails(log_file: str) -> dict:
    """Retourne {email: 'OK' ou 'ERREUR: ...'}"""
    results = {}
    if not os.path.exists(log_file):
        return results
    with open(log_file, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            if len(row) >= 3:
                em = row[1].lower().strip()
                # Garder le dernier statut (si re-envoi)
                results[em] = row[2]
    return results


# ============================================================
# 3. RÉCUPÉRER LES BOUNCES DEPUIS GMAIL (IMAP)
# ============================================================

def fetch_bounced_emails() -> set:
    """
    Se connecte à Gmail IMAP, cherche les notifications de bounce
    (mailer-daemon) dans tous les messages y compris archivés,
    et extrait les adresses email qui ont bouncé.
    """
    bounced = set()

    print("Connexion IMAP à Gmail...")
    mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
    mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
    print("Connecté !")

    # "[Gmail]/Tous les messages" inclut les archivés
    # Le nom du dossier dépend de la langue du compte Gmail
    all_mail_folders = [
        '"[Gmail]/Tous les messages"',   # FR
        '"[Gmail]/All Mail"',            # EN
        '"[Gmail]/Alle Nachrichten"',    # DE
    ]

    folder_ok = False
    for folder in all_mail_folders:
        status, _ = mail.select(folder, readonly=True)
        if status == "OK":
            folder_ok = True
            print(f"  Dossier : {folder}")
            break

    if not folder_ok:
        # Fallback: lister les dossiers disponibles
        print("  Dossiers disponibles :")
        status, folders = mail.list()
        for f in folders:
            print(f"    {f.decode()}")
        mail.logout()
        return bounced

    # Chercher les messages de mailer-daemon (bounces)
    print("  Recherche des bounces (mailer-daemon)...")
    search_queries = [
        '(FROM "mailer-daemon")',
        '(FROM "postmaster")',
        '(SUBJECT "Delivery Status Notification")',
        '(SUBJECT "Mail Delivery Subsystem")',
        '(SUBJECT "Undeliverable")',
        '(SUBJECT "returned mail")',
    ]

    msg_ids = set()
    for query in search_queries:
        try:
            status, data = mail.search(None, query)
            if status == "OK" and data[0]:
                ids = data[0].split()
                msg_ids.update(ids)
        except Exception:
            pass

    print(f"  {len(msg_ids)} messages de bounce trouvés")

    # Regex pour extraire les emails qui ont échoué
    # Ces patterns couvrent les formats courants de bounce Gmail
    bounce_patterns = [
        # "The email account that you tried to reach does not exist" + adresse
        re.compile(r"(?:could not be delivered to|does not exist|wasn't found|"
                   r"no such user|user unknown|mailbox not found|"
                   r"address rejected|recipient rejected|"
                   r"delivery.*failed|non trouvé|n'existe pas)"
                   r".*?([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})",
                   re.IGNORECASE | re.DOTALL),
        # Ligne "To: <email>" ou "Original-Recipient: rfc822;email"
        re.compile(r"Original-Recipient:\s*rfc822;\s*([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})",
                   re.IGNORECASE),
        re.compile(r"Final-Recipient:\s*rfc822;\s*([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})",
                   re.IGNORECASE),
        # Format simple: "550 5.1.1 <email>"
        re.compile(r"[45]\d\d\s+\d\.\d\.\d\s+<?([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})>?",
                   re.IGNORECASE),
    ]

    processed = 0
    for msg_id in msg_ids:
        try:
            status, msg_data = mail.fetch(msg_id, "(RFC822)")
            if status != "OK":
                continue

            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)

            # Extraire le texte du message
            body_parts = []
            if msg.is_multipart():
                for part in msg.walk():
                    ct = part.get_content_type()
                    if ct in ("text/plain", "text/html", "message/delivery-status"):
                        try:
                            payload = part.get_payload(decode=True)
                            if payload:
                                charset = part.get_content_charset() or "utf-8"
                                body_parts.append(payload.decode(charset, errors="replace"))
                        except Exception:
                            pass
            else:
                try:
                    payload = msg.get_payload(decode=True)
                    if payload:
                        charset = msg.get_content_charset() or "utf-8"
                        body_parts.append(payload.decode(charset, errors="replace"))
                except Exception:
                    pass

            full_text = "\n".join(body_parts)

            # Chercher les emails bouncés
            for pattern in bounce_patterns:
                matches = pattern.findall(full_text)
                for m in matches:
                    addr = m.strip().lower()
                    # Ignorer les adresses système
                    if addr and not addr.startswith(("mailer-daemon@", "postmaster@")):
                        bounced.add(addr)

            processed += 1
            if processed % 20 == 0:
                print(f"  ... {processed}/{len(msg_ids)} traités")

        except Exception as e:
            pass

    print(f"  {len(bounced)} adresses bouncées extraites")
    mail.logout()
    return bounced


# ============================================================
# 4. GÉNÉRER LE FICHIER DE SUIVI
# ============================================================

def generate_report(companies, sent_log, bounced):
    """Génère suivi_envois.txt avec le statut de chaque entreprise."""

    count_ok = 0
    count_bounce = 0
    count_err = 0
    count_pending = 0

    lines = []
    for c in companies:
        em = c["email"]
        em_lower = em.lower()
        name = c["name"]

        if em_lower in bounced:
            status = "✗ Non trouvé"
            count_bounce += 1
        elif em_lower in sent_log:
            if sent_log[em_lower] == "OK":
                status = "✓ Envoyé"
                count_ok += 1
            else:
                status = "✗ Erreur envoi"
                count_err += 1
        else:
            status = "⏳ En attente"
            count_pending += 1

        lines.append((name, em, status))

    # Écrire le fichier
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f"SUIVI DES ENVOIS DE CANDIDATURES — {now}\n")
        f.write("=" * 110 + "\n\n")
        f.write(f"  ✓ Envoyé      : {count_ok}\n")
        f.write(f"  ✗ Non trouvé  : {count_bounce}\n")
        f.write(f"  ✗ Erreur      : {count_err}\n")
        f.write(f"  ⏳ En attente  : {count_pending}\n")
        f.write(f"  Total         : {len(lines)}\n\n")
        f.write("=" * 110 + "\n")
        f.write(f"{'ENTREPRISE':<40} {'EMAIL':<45} {'STATUT'}\n")
        f.write("-" * 110 + "\n")
        for name, em, status in lines:
            f.write(f"{name:<40} {em:<45} {status}\n")

    # Aussi écrire une version CSV pour Excel
    csv_file = OUTPUT_FILE.replace(".txt", ".csv")
    with open(csv_file, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["Entreprise", "Email", "Statut"])
        for name, em, status in lines:
            # Statut simplifié pour CSV
            if "Envoyé" in status:
                s = "Envoyé"
            elif "Non trouvé" in status:
                s = "Non trouvé"
            elif "Erreur" in status:
                s = "Erreur"
            else:
                s = "En attente"
            writer.writerow([name, em, s])

    return count_ok, count_bounce, count_err, count_pending, csv_file


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 60)
    print("  SUIVI DES ENVOIS DE CANDIDATURES")
    print("=" * 60)

    # 1. Charger les entreprises
    companies = load_companies(ENTREPRISES_FILE)
    print(f"\n{len(companies)} entreprises chargées")

    # 2. Charger le log d'envoi
    sent_log = load_sent_emails(LOG_FILE)
    print(f"{len(sent_log)} emails dans le log d'envoi")

    # 3. Récupérer les bounces depuis Gmail
    print()
    bounced = fetch_bounced_emails()

    if bounced:
        print("\n  Adresses bouncées :")
        for b in sorted(bounced):
            print(f"    - {b}")

    # 4. Générer le rapport
    print(f"\nGénération du rapport...")
    ok, bounce, err, pending, csv_file = generate_report(companies, sent_log, bounced)

    print(f"\n{'=' * 60}")
    print(f"  ✓ Envoyé      : {ok}")
    print(f"  ✗ Non trouvé  : {bounce}")
    print(f"  ✗ Erreur      : {err}")
    print(f"  ⏳ En attente  : {pending}")
    print(f"  Total         : {ok + bounce + err + pending}")
    print(f"\n  Fichiers générés :")
    print(f"    → {OUTPUT_FILE}")
    print(f"    → {csv_file}")
    print("=" * 60)


if __name__ == "__main__":
    main()
