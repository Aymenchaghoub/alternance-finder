"""
Script de suivi des envois de candidatures
===========================================
Se connecte à Gmail via IMAP, récupère les bounces (mail not found)
depuis les messages archivés, puis génère un fichier de suivi avec
le statut de chaque entreprise :

  ✉ Répondu       — l'entreprise a répondu
  ✓ Envoyé        — mail envoyé et pas de bounce
  ✗ Non trouvé    — bounce reçu (adresse invalide)
  ⏳ En attente    — pas encore envoyé

Usage : python suivi-status-script.py
"""

import sys
import os
import re
import csv
import time
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
REPLIES_LOG = "reponses_log.txt"

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

def connect_imap():
    """Ouvre une connexion IMAP à Gmail et sélectionne 'All Mail'."""
    print("Connexion IMAP à Gmail...")
    mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT, timeout=60)
    mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
    print("Connecté !")

    all_mail_folders = [
        '"[Gmail]/Tous les messages"',   # FR
        '"[Gmail]/All Mail"',            # EN
        '"[Gmail]/Alle Nachrichten"',    # DE
    ]

    for folder in all_mail_folders:
        status, _ = mail.select(folder, readonly=True)
        if status == "OK":
            print(f"  Dossier : {folder}")
            return mail

    # Fallback
    print("  Dossiers disponibles :")
    status, folders = mail.list()
    for f in folders:
        print(f"    {f.decode()}")
    mail.logout()
    return None


def fetch_bounced_emails(mail) -> set:
    """
    Cherche les notifications de bounce (mailer-daemon) dans Gmail
    et extrait les adresses email qui ont bouncé.
    """
    bounced = set()

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
    return bounced


# ============================================================
# 4. RÉCUPÉRER LES RÉPONSES DEPUIS GMAIL (IMAP)
# ============================================================

def _decode_header_value(raw):
    """Décode un header MIME (sujet, from, etc.)."""
    if not raw:
        return ""
    try:
        decoded_parts = decode_header(raw)
        result = ""
        for part, charset in decoded_parts:
            if isinstance(part, bytes):
                result += part.decode(charset or "utf-8", errors="replace")
            else:
                result += part
        return result.strip()
    except Exception:
        return str(raw).strip()


def _extract_text_body(msg):
    """Extrait le corps texte d'un email (text/plain prioritaire, sinon text/html nettoyé)."""
    text_parts = []
    html_parts = []

    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            if part.get("Content-Disposition", "").startswith("attachment"):
                continue
            try:
                payload = part.get_payload(decode=True)
                if not payload:
                    continue
                charset = part.get_content_charset() or "utf-8"
                decoded = payload.decode(charset, errors="replace")
            except Exception:
                continue
            if ct == "text/plain":
                text_parts.append(decoded)
            elif ct == "text/html":
                html_parts.append(decoded)
    else:
        try:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or "utf-8"
                decoded = payload.decode(charset, errors="replace")
                if msg.get_content_type() == "text/html":
                    html_parts.append(decoded)
                else:
                    text_parts.append(decoded)
        except Exception:
            pass

    if text_parts:
        return "\n".join(text_parts)

    # Nettoyage basique du HTML
    if html_parts:
        raw_html = "\n".join(html_parts)
        # Supprimer les balises
        clean = re.sub(r'<br\s*/?>', '\n', raw_html, flags=re.IGNORECASE)
        clean = re.sub(r'<[^>]+>', ' ', clean)
        # Décoder les entités courantes
        clean = clean.replace('&nbsp;', ' ').replace('&amp;', '&')
        clean = clean.replace('&lt;', '<').replace('&gt;', '>')
        # Nettoyer les espaces multiples
        clean = re.sub(r'[ \t]+', ' ', clean)
        clean = re.sub(r'\n{3,}', '\n\n', clean)
        return clean.strip()

    return ""


def fetch_replies(mail, company_emails: set) -> dict:
    """
    Cherche les emails reçus dont l'expéditeur correspond à une entreprise.
    Retourne {email: {"subject": str, "body": str, "date": str, "from": str}}.
    """
    replies = {}
    email_re = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')

    # Chercher les emails reçus depuis la date d'envoi (TO = notre adresse)
    print("  Recherche des réponses reçues...")
    since_date = "01-Mar-2026"  # date du premier envoi
    status, data = mail.search(None, f'(TO "{EMAIL_ACCOUNT}" SINCE {since_date})')
    if status != "OK" or not data[0]:
        print("  0 réponses trouvées")
        return replies

    msg_ids = data[0].split()
    print(f"  {len(msg_ids)} messages reçus à analyser...")

    company_domains = {e.split("@")[1] for e in company_emails if "@" in e}
    matched_msg_ids = []  # (msg_id, matched_email)

    def _noop(m, i):
        """Envoie NOOP tous les 200 messages pour maintenir la connexion."""
        if i > 0 and i % 200 == 0:
            try:
                m.noop()
            except Exception:
                pass

    # ── Passe 1 : identifier les messages via les headers ──
    processed = 0
    retries = 0
    i = 0
    while i < len(msg_ids):
        msg_id = msg_ids[i]
        try:
            _noop(mail, processed)
            status, msg_data = mail.fetch(msg_id, "(BODY[HEADER.FIELDS (FROM SUBJECT DATE)])")
            if status != "OK":
                i += 1
                continue
            retries = 0  # reset on success

            raw_header = msg_data[0][1]
            hdr = email.message_from_bytes(raw_header)

            from_raw = hdr.get("From", "")
            from_matches = email_re.findall(from_raw)
            if not from_matches:
                i += 1
                continue

            sender = from_matches[0].lower()

            if sender.startswith(("mailer-daemon@", "postmaster@", "noreply@", "no-reply@")):
                i += 1
                continue
            if sender == EMAIL_ACCOUNT.lower():
                i += 1
                continue

            sender_domain = sender.split("@")[1] if "@" in sender else ""

            matched_email = None
            if sender in company_emails:
                matched_email = sender
            elif sender_domain in company_domains:
                for ce in company_emails:
                    if ce.split("@")[1] == sender_domain:
                        matched_email = ce
                        break

            if matched_email:
                matched_msg_ids.append((msg_id, matched_email))

            processed += 1
            if processed % 100 == 0:
                print(f"  ... {processed}/{len(msg_ids)} analysés")

            i += 1

        except (imaplib.IMAP4.abort, OSError, ConnectionError,
                TimeoutError, KeyboardInterrupt) as e:
            retries += 1
            if retries > 3:
                print(f"  ⚠ Trop d'erreurs IMAP, arrêt à {processed}/{len(msg_ids)}")
                break
            print(f"  ⚠ Connexion IMAP perdue, reconnexion ({retries}/3)...")
            time.sleep(3)
            mail = connect_imap()
            if not mail:
                break
            # on réessaie le même message (i n'est pas incrémenté)
        except Exception:
            i += 1

    # ── Passe 2 : récupérer le contenu complet des messages matchés ──
    print(f"  {len(matched_msg_ids)} réponses détectées, récupération du contenu...")
    for idx, (msg_id, matched_email) in enumerate(matched_msg_ids):
        try:
            _noop(mail, idx)
            status, msg_data = mail.fetch(msg_id, "(RFC822)")
            if status != "OK":
                continue

            raw_msg = msg_data[0][1]
            msg = email.message_from_bytes(raw_msg)

            subject = _decode_header_value(msg.get("Subject", "(sans objet)"))
            from_field = _decode_header_value(msg.get("From", ""))
            date_field = msg.get("Date", "")
            body = _extract_text_body(msg)

            # On garde une seule réponse par entreprise (la dernière trouvée)
            replies[matched_email] = {
                "subject": subject[:120],
                "from": from_field,
                "date": date_field,
                "body": body[:5000],  # limiter à 5000 chars
            }

        except (imaplib.IMAP4.abort, OSError, ConnectionError,
                TimeoutError, KeyboardInterrupt):
            print(f"  ⚠ Reconnexion pour récupérer le contenu...")
            time.sleep(3)
            mail = connect_imap()
            if not mail:
                break
        except Exception:
            pass

    print(f"  {len(replies)} réponses d'entreprises avec contenu récupérées")
    return replies


# ============================================================
# 5. SAUVEGARDER LE LOG DES RÉPONSES
# ============================================================

def save_replies_log(replies: dict, companies: list):
    """
    Écrit reponses_log.txt avec le contenu complet de chaque réponse,
    classé par entreprise.
    """
    # Mapper email → nom entreprise
    email_to_name = {c["email"].lower(): c["name"] for c in companies}

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    sep = "=" * 80

    with open(REPLIES_LOG, "w", encoding="utf-8") as f:
        f.write(f"LOG DES RÉPONSES REÇUES — {now}\n")
        f.write(f"{len(replies)} réponse(s)\n")
        f.write(sep + "\n\n")

        for em in sorted(replies.keys()):
            r = replies[em]
            name = email_to_name.get(em, "(inconnu)")
            f.write(sep + "\n")
            f.write(f"ENTREPRISE : {name}\n")
            f.write(f"DE         : {r['from']}\n")
            f.write(f"EMAIL      : {em}\n")
            f.write(f"DATE       : {r['date']}\n")
            f.write(f"SUJET      : {r['subject']}\n")
            f.write("-" * 80 + "\n")
            f.write(r["body"] if r["body"] else "(contenu vide)")
            f.write("\n\n")

    print(f"  → {REPLIES_LOG} ({len(replies)} réponses sauvegardées)")


# ============================================================
# 4. GÉNÉRER LE FICHIER DE SUIVI
# ============================================================

def generate_report(companies, sent_log, bounced, replies):
    """Génère suivi_envois.txt avec le statut de chaque entreprise."""

    count_replied = 0
    count_ok = 0
    count_bounce = 0
    count_err = 0
    count_pending = 0

    lines = []
    for c in companies:
        em = c["email"]
        em_lower = em.lower()
        name = c["name"]

        # Priorité : Répondu > Non trouvé > Envoyé > Erreur > En attente
        if em_lower in replies:
            status = "✉ Répondu"
            count_replied += 1
        elif em_lower in bounced:
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
    w = 160  # largeur totale
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f"SUIVI DES ENVOIS DE CANDIDATURES — {now}\n")
        f.write("=" * w + "\n\n")
        f.write(f"  ✉ Répondu     : {count_replied}\n")
        f.write(f"  ✓ Envoyé      : {count_ok}\n")
        f.write(f"  ✗ Non trouvé  : {count_bounce}\n")
        f.write(f"  ✗ Erreur      : {count_err}\n")
        f.write(f"  ⏳ En attente  : {count_pending}\n")
        f.write(f"  Total         : {len(lines)}\n\n")
        f.write("=" * w + "\n")
        f.write(f"{'ENTREPRISE':<40} {'EMAIL':<45} {'STATUT':<16} {'DÉTAIL'}\n")
        f.write("-" * w + "\n")
        for name, em, status in lines:
            em_lower = em.lower()
            detail = ""
            if em_lower in replies:
                detail = replies[em_lower]["subject"]
            f.write(f"{name:<40} {em:<45} {status:<16} {detail}\n")

    # Aussi écrire une version CSV pour Excel
    csv_file = OUTPUT_FILE.replace(".txt", ".csv")
    with open(csv_file, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["Entreprise", "Email", "Statut", "Détail"])
        for name, em, status in lines:
            em_lower = em.lower()
            detail = replies[em_lower]["subject"] if em_lower in replies else ""
            if "Répondu" in status:
                s = "Répondu"
            elif "Envoyé" in status:
                s = "Envoyé"
            elif "Non trouvé" in status:
                s = "Non trouvé"
            elif "Erreur" in status:
                s = "Erreur"
            else:
                s = "En attente"
            writer.writerow([name, em, s, detail])

    return count_replied, count_ok, count_bounce, count_err, count_pending, csv_file


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

    # 3. Connexion IMAP
    print()
    mail = connect_imap()
    if not mail:
        print("ERREUR : impossible de se connecter à Gmail IMAP")
        return

    # 4. Récupérer les bounces
    bounced = fetch_bounced_emails(mail)
    if bounced:
        print("\n  Adresses bouncées :")
        for b in sorted(bounced):
            print(f"    - {b}")

    # 5. Récupérer les réponses d'entreprises
    print()
    company_emails = {c["email"].lower() for c in companies}
    replies = fetch_replies(mail, company_emails)
    if replies:
        print("\n  Réponses reçues :")
        for em, r in sorted(replies.items()):
            print(f"    ✉ {em} — {r['subject']}")

    mail.logout()

    # 6. Sauvegarder le log des réponses
    print()
    save_replies_log(replies, companies)

    # 7. Générer le rapport
    print(f"\nGénération du rapport...")
    replied, ok, bounce, err, pending, csv_file = generate_report(
        companies, sent_log, bounced, replies
    )

    print(f"\n{'=' * 60}")
    print(f"  ✉ Répondu     : {replied}")
    print(f"  ✓ Envoyé      : {ok}")
    print(f"  ✗ Non trouvé  : {bounce}")
    print(f"  ✗ Erreur      : {err}")
    print(f"  ⏳ En attente  : {pending}")
    print(f"  Total         : {replied + ok + bounce + err + pending}")
    print(f"\n  Fichiers générés :")
    print(f"    → {OUTPUT_FILE}")
    print(f"    → {csv_file}")
    print(f"    → {REPLIES_LOG}")
    print("=" * 60)


if __name__ == "__main__":
    main()
