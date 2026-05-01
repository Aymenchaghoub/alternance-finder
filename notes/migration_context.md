# Contexte de migration — Recherche-stage → alternance-finder

## Date de migration

1er mai 2026

## Motivation

Le repo `Recherche-stage` contenait des scripts Python pour automatiser la recherche de stage (scraping API Euratechnologies, extraction emails, envoi de candidatures). Ces scripts ont permis de trouver le stage actuel chez Ouidou Nord.

Pour la recherche d'alternance (24 mois à partir de septembre 2026), le projet a été repensé et restructuré en `alternance-finder` avec :

- Une architecture propre et modulaire
- Un pipeline configurable (import → enrichissement → scoring → génération → suivi)
- Des garde-fous RGPD et éthiques
- Un scoring intelligent basé sur le profil
- Une génération d'emails personnalisés par type d'entreprise
- Un dry-run obligatoire (pas d'envoi réel en V1)

## Fichiers migrés

Les anciens scripts sont conservés dans `legacy/` :
- `legacy/emails-script.py` — Scraping API Euratechnologies
- `legacy/find-missing-emails.py` — Extraction emails depuis sites web
- `legacy/send-emails-script.py` — Envoi candidatures SMTP
- `legacy/suivi-status-script.py` — Suivi IMAP des réponses et bounces
- `legacy/README-stage.md` — Ancien README
- `legacy/CV-Aymen-CHAGHOUB-stage.pdf` — Ancien CV
- `legacy/reports/` — Anciens rapports
- `legacy/data/` — Données et logs historiques (non versionnés)

## Renommage GitHub

Le repo GitHub sera renommé de `Recherche-stage` à `alternance-finder`.
Le renommage doit être fait manuellement sur GitHub (Settings → Repository name).
GitHub redirigera automatiquement l'ancienne URL.

## Prochaines étapes

1. ✅ CSV manuel (MVP)
2. 🔜 France Travail API
3. 🔜 API Sirene INSEE
4. 🔜 La Bonne Alternance
5. 🔜 Extraction email responsable
6. 🔜 Personnalisation LLM optionnelle
