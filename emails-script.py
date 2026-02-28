import requests
import time

API_URL = "https://www.euratechnologies.com/api/companies"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/ld+json",
}

all_companies = []
emails_only = set()
page = 1

while True:
    url = f"{API_URL}?page={page}"
    print(f"[page {page}] {url} ... ", end="", flush=True)

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"ERREUR ({e})")
        break

    members = data.get("hydra:member", [])
    if not members:
        print("0 resultats, fin.")
        break

    count = 0
    for m in members:
        name = m.get("commercialName") or m.get("companyName") or "Inconnu"
        email = (m.get("email") or "").strip()
        phone = (m.get("phone") or "").strip()
        website = (m.get("website") or "").strip()

        if email:
            emails_only.add(email)
            count += 1

        all_companies.append({
            "name": name,
            "email": email,
            "phone": phone,
            "website": website,
        })

    total_pages = 1
    view = data.get("hydra:view", {})
    last_page_url = view.get("hydra:last", "")
    if "page=" in last_page_url:
        total_pages = int(last_page_url.split("page=")[-1])

    print(f"{len(members)} entreprises ({count} avec email) [page {page}/{total_pages}]")

    if "hydra:next" not in view:
        break

    page += 1
    time.sleep(0.3)

# --- Fichier 1 : emails.txt ---
with open("emails.txt", "w", encoding="utf-8") as f:
    for email in sorted(emails_only):
        f.write(email + "\n")

# --- Fichier 2 : entreprises_emails.txt (toutes celles qui ont un email) ---
seen = set()
with open("entreprises_emails.txt", "w", encoding="utf-8") as f:
    f.write(f"{'ENTREPRISE':<45} {'EMAIL':<45} {'TELEPHONE':<20} SITE WEB\n")
    f.write("=" * 160 + "\n")
    for c in sorted(all_companies, key=lambda x: x["name"].lower()):
        if c["email"] and c["email"] not in seen:
            seen.add(c["email"])
            f.write(f"{c['name']:<45} {c['email']:<45} {c['phone']:<20} {c['website']}\n")

# --- Fichier 3 : toutes_entreprises.txt (avec ou sans email) ---
with open("toutes_entreprises.txt", "w", encoding="utf-8") as f:
    f.write(f"{'ENTREPRISE':<45} {'EMAIL':<45} {'TELEPHONE':<20} SITE WEB\n")
    f.write("=" * 160 + "\n")
    for c in sorted(all_companies, key=lambda x: x["name"].lower()):
        f.write(f"{c['name']:<45} {c['email'] or '-':<45} {c['phone'] or '-':<20} {c['website'] or '-'}\n")

print("\n" + "=" * 55)
print(f"Total entreprises : {len(all_companies)}")
print(f"Entreprises avec email : {len(seen)}")
print(f"Emails uniques : {len(emails_only)}")
print("Fichiers crees :")
print("  -> emails.txt                (emails seulement)")
print("  -> entreprises_emails.txt    (entreprises avec email)")
print("  -> toutes_entreprises.txt    (toutes les entreprises)")