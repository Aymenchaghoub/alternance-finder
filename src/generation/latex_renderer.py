"""
Rendu LaTeX — détection de compilateur et compilation PDF.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from src.utils.logging import logger


def find_latex_compiler() -> str | None:
    """
    Cherche un compilateur LaTeX disponible.

    Ordre de préférence : latexmk > xelatex > pdflatex
    """
    compilers = ["latexmk", "xelatex", "pdflatex"]

    for compiler in compilers:
        try:
            result = subprocess.run(
                [compiler, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                return compiler
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue

    return None


def compile_latex(tex_path: str, compiler: str | None = None) -> Path | None:
    """
    Compile un fichier .tex en PDF.

    Args:
        tex_path: Chemin vers le fichier .tex
        compiler: Compilateur à utiliser (auto-détection si None)

    Returns:
        Path du PDF généré, ou None si échec.
    """
    if compiler is None:
        compiler = find_latex_compiler()

    if compiler is None:
        logger.warning(f"  ⚠ Pas de compilateur LaTeX. Fichier .tex non compilé : {tex_path}")
        logger.info("    Pour compiler manuellement :")
        logger.info(f"    latexmk -pdf -interaction=nonstopmode {tex_path}")
        return None

    tex_file = Path(tex_path)
    work_dir = tex_file.parent

    try:
        if compiler == "latexmk":
            cmd = [
                "latexmk", "-pdf",
                "-interaction=nonstopmode",
                "-outdir=" + str(work_dir),
                str(tex_file.name),
            ]
        elif compiler == "xelatex":
            cmd = [
                "xelatex",
                "-interaction=nonstopmode",
                f"-output-directory={work_dir}",
                str(tex_file.name),
            ]
        else:  # pdflatex
            cmd = [
                "pdflatex",
                "-interaction=nonstopmode",
                f"-output-directory={work_dir}",
                str(tex_file.name),
            ]

        logger.info(f"    Compilation : {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            cwd=str(work_dir),
            capture_output=True,
            text=True,
            timeout=60,
        )

        pdf_path = tex_file.with_suffix(".pdf")
        if pdf_path.exists():
            return pdf_path
        else:
            logger.warning(f"    ⚠ Compilation échouée pour {tex_path}")
            if result.stderr:
                # Show only first 5 lines of error
                errors = result.stderr.strip().split("\n")[:5]
                for line in errors:
                    logger.warning(f"      {line}")
            return None

    except subprocess.TimeoutExpired:
        logger.warning(f"    ⚠ Timeout de compilation pour {tex_path}")
        return None
    except Exception as e:
        logger.warning(f"    ⚠ Erreur de compilation : {e}")
        return None
