"""
Générateur de CV AltaCV — copie et personnalisation du template.

Règles :
- Ne jamais modifier cv/sample.tex
- Générer les variantes dans cv/generated/
- Copier aussi dans outputs/cvs/
- Vérifier la présence de profile-pic.JPG
- Compiler en PDF si un compilateur LaTeX est disponible
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from src.models.company import Company
from src.utils.slugify import slugify
from src.utils.io import ensure_dir
from src.utils.logging import logger
from src.generation.latex_renderer import compile_latex, find_latex_compiler


# Chemins relatifs au repo
SAMPLE_TEX = os.path.join("cv", "sample.tex")
PROFILE_PIC = os.path.join("cv", "profile-pic.JPG")
CV_GENERATED_DIR = os.path.join("cv", "generated")
CV_OUTPUT_DIR = os.path.join("outputs", "cvs")


def generate_cvs(
    companies: list[Company],
    min_score: int = 75,
) -> list[str]:
    """
    Génère une variante de CV pour chaque entreprise éligible.

    En V1, copie simplement sample.tex avec un nom personnalisé.
    Les placeholders seront remplacés dans une future version.

    Args:
        companies: Liste d'entreprises scorées.
        min_score: Score minimum pour générer un CV.

    Returns:
        Liste des chemins de fichiers .tex générés.
    """
    logger.info(f"Génération de CV AltaCV (min_score={min_score})...")

    # Vérifier que sample.tex existe
    if not os.path.exists(SAMPLE_TEX):
        logger.error(f"Template CV introuvable : {SAMPLE_TEX}")
        return []

    # Vérifier profile-pic.JPG
    if os.path.exists(PROFILE_PIC):
        logger.info(f"  ✓ Photo de profil trouvée : {PROFILE_PIC}")
    else:
        logger.warning(f"  ⚠ Photo de profil absente : {PROFILE_PIC}")
        logger.warning("    Le CV utilisera le fallback textuel (nom affiché).")

    ensure_dir(CV_GENERATED_DIR)
    ensure_dir(CV_OUTPUT_DIR)

    eligible = [c for c in companies if c.score >= min_score and not c.do_not_contact]
    logger.info(f"  → {len(eligible)} entreprises éligibles (score >= {min_score})")

    # Vérifier le compilateur LaTeX
    compiler = find_latex_compiler()
    if compiler:
        logger.info(f"  ✓ Compilateur LaTeX détecté : {compiler}")
    else:
        logger.warning("  ⚠ Aucun compilateur LaTeX détecté (latexmk, xelatex, pdflatex).")
        logger.warning("    Les fichiers .tex seront générés mais pas compilés.")
        logger.warning("    Pour compiler : installer TeX Live ou MiKTeX.")

    generated_files = []

    for company in eligible:
        slug = slugify(company.company_name)
        tex_filename = f"cv_Aymen_CHAGHOUB_{slug}.tex"
        tex_path = os.path.join(CV_GENERATED_DIR, tex_filename)

        # Copier le template
        shutil.copy2(SAMPLE_TEX, tex_path)

        # Copier les fichiers nécessaires dans le dossier generated
        _copy_cv_assets(CV_GENERATED_DIR)

        # Stocker le chemin dans le modèle
        company.cv_variant = tex_path

        generated_files.append(tex_path)

        # Tenter la compilation
        if compiler:
            pdf_path = compile_latex(tex_path, compiler)
            if pdf_path:
                # Copier le PDF dans outputs/cvs/
                output_pdf = os.path.join(CV_OUTPUT_DIR, pdf_path.name)
                shutil.copy2(str(pdf_path), output_pdf)
                logger.info(f"    ✓ PDF compilé : {output_pdf}")

    logger.info(f"  → {len(generated_files)} CV générés dans {CV_GENERATED_DIR}/")
    return generated_files


def _copy_cv_assets(target_dir: str):
    """Copie les fichiers nécessaires au build LaTeX dans le dossier cible."""
    cv_dir = "cv"
    assets = [
        "altacv.cls",
        "profile-pic.JPG",
        "sample.bib",
        "latexmkrc",
    ]
    for asset in assets:
        src = os.path.join(cv_dir, asset)
        dst = os.path.join(target_dir, asset)
        if os.path.exists(src) and not os.path.exists(dst):
            shutil.copy2(src, dst)
