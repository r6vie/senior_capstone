import unittest
from copy import deepcopy
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from auth import get_current_user
from database import get_database
from main import app
from matching import public_profile, score_candidate
from models import SavedProfile
from sample_data import profiles


def student_profile() -> dict:
    return {
        "_id": "student-profile",
        "owner_user_id": "student-user",
        "name": "Student Example",
        "affiliation": "CWRU student",
        "location": "Cleveland, Ohio",
        "expertise": ["Biomedical engineering"],
        "interests": ["Healthcare technology", "Entrepreneurship"],
        "role": "student",
        "industry": "Healthcare",
        "background": "Building an early-stage medical device company.",
        "help_offered": [],
        "help_needed": ["Fundraising", "FDA strategy"],
        "availability": "available",
        "meeting_preference": "either",
        "graduation_year": 2027,
    }


class MatchingAlgorithmTests(unittest.TestCase):
    def test_legacy_student_profile_is_not_mislabeled_as_alumni(self):
        legacy = {
            "_id": "legacy-student", "name": "Legacy Student",
            "affiliation": "CWRU student", "location": "Cleveland, Ohio",
            "expertise": [], "interests": [],
        }
        self.assertEqual(public_profile(legacy).role, "student")

    def test_relevant_alumnus_scores_above_irrelevant_alumnus(self):
        student_document = student_profile()
        student = SavedProfile.model_validate({
            **{key: value for key, value in student_document.items() if key not in {"_id", "owner_user_id"}},
            "id": "student-profile",
        })
        relevant = SavedProfile.model_validate({
            **{key: value for key, value in profiles[2].items() if key != "_id"},
            "id": profiles[2]["_id"],
        })
        irrelevant = SavedProfile.model_validate({
            "id": "unrelated", "name": "Unrelated Alumni", "affiliation": "CWRU alumni",
            "location": "Seattle, Washington", "expertise": ["Classical music"],
            "interests": ["Orchestral performance"], "role": "alumni",
            "industry": "Arts", "background": "Professional musician.",
            "help_offered": ["Audition preparation"], "help_needed": [],
            "availability": "available", "meeting_preference": "remote",
            "graduation_year": 2010,
        })

        query = "I need FDA and regulatory advice for a healthcare product"
        relevant_match = score_candidate(relevant, student, query)
        irrelevant_match = score_candidate(irrelevant, student, query)

        self.assertGreater(relevant_match.score, irrelevant_match.score)
        self.assertTrue(any("regulation" in reason for reason in relevant_match.reasons))
        self.assertEqual(sum(relevant_match.score_breakdown.values()), relevant_match.score)


class MatchingApiTests(unittest.TestCase):
    def setUp(self):
        self.settings = patch("database.database_settings", return_value=("", "test"))
        self.settings.start()
        self.client = TestClient(app)
        self.client.__enter__()
        self.database = MagicMock()
        self.database.profiles.find_one = AsyncMock(return_value=student_profile())
        cursor = self.database.profiles.find.return_value.limit.return_value
        cursor.to_list = AsyncMock(return_value=[deepcopy(profiles[1]), deepcopy(profiles[2])])
        app.dependency_overrides[get_database] = lambda: self.database
        app.dependency_overrides[get_current_user] = lambda: {"_id": "student-user"}

    def tearDown(self):
        app.dependency_overrides.clear()
        self.client.__exit__(None, None, None)
        self.settings.stop()

    def test_search_returns_ranked_explainable_alumni(self):
        response = self.client.post("/matches/search", json={
            "query": "fundraising for a healthcare startup",
        })
        self.assertEqual(response.status_code, 200)
        results = response.json()
        self.assertEqual(len(results), 2)
        self.assertGreaterEqual(results[0]["score"], results[1]["score"])
        self.assertTrue(results[0]["reasons"])
        self.assertIn("expertise", results[0]["score_breakdown"])
        query = self.database.profiles.find.call_args.args[0]
        self.assertEqual(query["owner_user_id"], {"$ne": "student-user"})

    def test_recommendations_use_saved_profile(self):
        response = self.client.get("/matches/recommended")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)

    def test_profile_is_required_for_personalized_matching(self):
        self.database.profiles.find_one.return_value = None
        response = self.client.post("/matches/search", json={"query": "fundraising advice"})
        self.assertEqual(response.status_code, 409)
        self.assertIn("Create your profile", response.json()["detail"])

    def test_search_request_rejects_unknown_or_short_input(self):
        for body in ({"query": "x"}, {"query": "fundraising", "unexpected": True}):
            with self.subTest(body=body):
                self.assertEqual(self.client.post("/matches/search", json=body).status_code, 422)
