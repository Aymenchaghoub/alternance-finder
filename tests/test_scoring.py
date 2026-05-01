"""
Tests du scoring.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.company import Company
from src.scoring.scorer import score_companies


class TestScoring:
    def _make_company(self, **kwargs) -> Company:
        defaults = {
            "company_name": "Test Corp",
            "location": "Paris, Île-de-France",
            "sector": "IA",
            "has_apprenticeship_offer": True,
            "contact_email": "rh@test.com",
            "career_url": "https://test.com/careers",
            "has_tech_jobs": True,
            "job_titles_found": "Développeur Backend Python - Alternance",
            "notes": "Startup IA, stack Python/FastAPI/LangChain",
        }
        defaults.update(kwargs)
        return Company(**defaults)

    def test_high_score_company(self):
        """Une entreprise IA à Paris avec alternance doit avoir un score élevé."""
        company = self._make_company()
        result = score_companies([company])
        assert len(result) == 1
        assert result[0].score >= 60  # Should be a good target

    def test_low_score_no_info(self):
        """Une entreprise sans info doit avoir un score bas."""
        company = Company(company_name="Unknown Corp")
        result = score_companies([company])
        assert result[0].score < 45

    def test_do_not_contact(self):
        """do_not_contact doit donner un score très bas."""
        company = self._make_company(do_not_contact=True)
        result = score_companies([company])
        assert result[0].recommended_action == "ne_pas_contacter"

    def test_scoring_sorts_descending(self):
        """Les entreprises doivent être triées par score décroissant."""
        companies = [
            Company(company_name="Low"),
            self._make_company(company_name="High"),
            Company(company_name="Medium", location="Paris", contact_email="a@b.com"),
        ]
        result = score_companies(companies)
        scores = [c.score for c in result]
        assert scores == sorted(scores, reverse=True)

    def test_paris_location_bonus(self):
        """Paris doit donner un bonus de localisation."""
        paris = Company(company_name="Paris Co", location="Paris, Île-de-France",
                        contact_email="a@b.com", has_tech_jobs=True)
        elsewhere = Company(company_name="Elsewhere Co", location="Marseille",
                            contact_email="a@c.com", has_tech_jobs=True)
        result = score_companies([paris, elsewhere])
        paris_score = next(c.score for c in result if c.company_name == "Paris Co")
        elsewhere_score = next(c.score for c in result if c.company_name == "Elsewhere Co")
        assert paris_score > elsewhere_score

    def test_apprenticeship_bonus(self):
        """Une offre d'alternance doit donner un bonus."""
        with_offer = Company(company_name="With Offer", has_apprenticeship_offer=True,
                             contact_email="a@b.com", has_tech_jobs=True)
        without_offer = Company(company_name="Without Offer", has_apprenticeship_offer=False,
                                contact_email="a@c.com", has_tech_jobs=True)
        result = score_companies([with_offer, without_offer])
        with_score = next(c.score for c in result if c.company_name == "With Offer")
        without_score = next(c.score for c in result if c.company_name == "Without Offer")
        assert with_score > without_score

    def test_recommended_action_set(self):
        """L'action recommandée doit être définie pour chaque entreprise."""
        company = self._make_company()
        result = score_companies([company])
        assert result[0].recommended_action != ""
