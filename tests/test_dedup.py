"""
Tests de déduplication.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.company import Company
from src.utils.dedup import deduplicate_companies
from src.utils.text import normalize_company_name


class TestNormalizeCompanyName:
    def test_basic(self):
        assert normalize_company_name("Demo AI Studio") == "demo ai studio"

    def test_accents(self):
        result = normalize_company_name("L'Atelier du Café")
        assert "atelier" in result
        assert "cafe" in result

    def test_legal_suffix(self):
        result = normalize_company_name("Ma Startup SAS")
        assert "sas" not in result
        assert "ma startup" == result

    def test_empty(self):
        assert normalize_company_name("") == ""

    def test_none_safe(self):
        assert normalize_company_name(None) == ""


class TestDeduplication:
    def test_no_duplicates(self):
        companies = [
            Company(company_name="Alpha"),
            Company(company_name="Beta"),
            Company(company_name="Gamma"),
        ]
        result = deduplicate_companies(companies)
        assert len(result) == 3

    def test_duplicate_by_name(self):
        companies = [
            Company(company_name="Alpha Corp", website="alpha.com"),
            Company(company_name="Alpha Corp", contact_email="info@alpha.com"),
        ]
        result = deduplicate_companies(companies)
        assert len(result) == 1

    def test_duplicate_by_name_case_insensitive(self):
        companies = [
            Company(company_name="DEMO AI STUDIO"),
            Company(company_name="Demo AI Studio"),
        ]
        result = deduplicate_companies(companies)
        assert len(result) == 1

    def test_duplicate_by_email_domain(self):
        companies = [
            Company(company_name="Alpha", contact_email="info@alpha.com"),
            Company(company_name="Alpha Corp", contact_email="rh@alpha.com"),
        ]
        result = deduplicate_companies(companies)
        assert len(result) == 1

    def test_keeps_most_complete(self):
        companies = [
            Company(company_name="Alpha", website=""),
            Company(company_name="Alpha", website="https://alpha.com",
                    contact_email="info@alpha.com", sector="SaaS"),
        ]
        result = deduplicate_companies(companies)
        assert len(result) == 1
        assert result[0].website == "https://alpha.com"

    def test_empty_list(self):
        assert deduplicate_companies([]) == []

    def test_duplicate_by_website(self):
        companies = [
            Company(company_name="First", website="https://example.com"),
            Company(company_name="Second", website="https://example.com"),
        ]
        result = deduplicate_companies(companies)
        assert len(result) == 1
