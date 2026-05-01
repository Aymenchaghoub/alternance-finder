"""
Utilitaires d'entrée/sortie — lecture YAML, CSV, écriture CSV.
"""

import csv
import os
from pathlib import Path
from typing import Any

import yaml


def load_yaml(filepath: str) -> dict:
    """Charge un fichier YAML et retourne un dictionnaire."""
    with open(filepath, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_csv(filepath: str) -> list[dict]:
    """Charge un fichier CSV et retourne une liste de dictionnaires."""
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def save_csv(filepath: str, data: list[dict], fieldnames: list[str] | None = None):
    """Écrit une liste de dictionnaires dans un fichier CSV."""
    if not data:
        return
    ensure_dir(os.path.dirname(filepath))
    if fieldnames is None:
        fieldnames = list(data[0].keys())
    with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def ensure_dir(dirpath: str):
    """Crée un répertoire s'il n'existe pas."""
    if dirpath:
        Path(dirpath).mkdir(parents=True, exist_ok=True)


def load_config(config_name: str) -> dict:
    """Charge un fichier de configuration depuis config/."""
    config_dir = Path(__file__).parent.parent.parent / "config"
    filepath = config_dir / config_name
    if not filepath.exists():
        raise FileNotFoundError(f"Configuration introuvable : {filepath}")
    return load_yaml(str(filepath))
