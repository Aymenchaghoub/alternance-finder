"""
Tests du générateur d'emails.
"""

import sys
import os
import shutil
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.company import Company
from src.generation.email_generator import generate_emails, _select_template, _build_placeholders


class TestTemplateSelection:
    def test_startup_ia(self):
        company = Company(sector="IA / Machine Learning")
        assert _select_template(company) == "startup_ia"

    def test_saas(self):
        company = Company(sector="SaaS B2B")
        assert _select_template(company) == "saas_b2b"

    def test_esn(self):
        company = Company(sector="ESN / Conseil IT")
        assert _select_template(company) == "esn_cabinet"

    def test_with_offer(self):
        company = Company(has_apprenticeship_offer=True)
        assert _select_template(company) == "with_offer"

    def test_default(self):
        company = Company()
        assert _select_template(company) == "without_offer"


class TestPlaceholders:
    def test_greeting_with_name(self):
        company = Company(contact_name="Marie Dupont")
        placeholders = _build_placeholders(company)
        assert placeholders["greeting"] == "Marie Dupont"

    def test_greeting_without_name(self):
        company = Company()
        placeholders = _build_placeholders(company)
        assert "recrutement" in placeholders["greeting"]

    def test_company_name_in_placeholders(self):
        company = Company(company_name="Test Corp")
        placeholders = _build_placeholders(company)
        assert placeholders["company_name"] == "Test Corp"

    def test_ia_project_selection(self):
        company = Company(sector="IA", notes="Startup IA et LLM")
        placeholders = _build_placeholders(company)
        assert "RAG" in placeholders["relevant_project"]

    def test_saas_project_selection(self):
        company = Company(sector="SaaS", notes="Plateforme SaaS multi-tenant")
        placeholders = _build_placeholders(company)
        assert "MediBrief" in placeholders["relevant_project"]


class TestEmailGeneration:
    def setup_method(self):
        """Nettoyer le dossier de sortie avant chaque test."""
        self.output_dir = "outputs/emails/_test"
        os.makedirs(self.output_dir, exist_ok=True)

    def teardown_method(self):
        """Nettoyer après chaque test."""
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)

    def test_generates_files(self):
        companies = [
            Company(
                company_name="Test IA Corp",
                score=70,
                sector="IA",
                contact_email="test@test.com",
            ),
        ]
        files = generate_emails(companies, min_score=60, output_dir=self.output_dir)
        assert len(files) == 1
        assert os.path.exists(files[0])

    def test_skips_low_score(self):
        companies = [
            Company(company_name="Low Score", score=30),
        ]
        files = generate_emails(companies, min_score=60, output_dir=self.output_dir)
        assert len(files) == 0

    def test_skips_do_not_contact(self):
        companies = [
            Company(company_name="Blocked", score=90, do_not_contact=True),
        ]
        files = generate_emails(companies, min_score=60, output_dir=self.output_dir)
        assert len(files) == 0

    def test_email_content(self):
        companies = [
            Company(
                company_name="Content Test",
                score=80,
                sector="SaaS B2B",
                contact_email="rh@content.com",
            ),
        ]
        files = generate_emails(companies, min_score=60, output_dir=self.output_dir)
        with open(files[0], "r", encoding="utf-8") as f:
            content = f.read()
        assert "Content Test" in content
        assert "Aymen CHAGHOUB" in content
        assert "alternance" in content.lower() or "apprentissage" in content.lower()
