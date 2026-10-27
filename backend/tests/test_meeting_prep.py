import unittest
from copy import deepcopy
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from auth import get_current_user
from database import get_database
from main import app
from sample_data import profiles


def student_profile() -> dict:
    return {
        "_id": "student-profile", "owner_user_id": "student-user",
        "name": "Student Example", "affiliation": "CWRU student",
        "location": "Cleveland, Ohio", "expertise": ["Biomedical engineering"],
        "interests": ["Healthcare technology", "Entrepreneurship"], "role": "student",
        "industry": "Healthcare", "background": "Building an early-stage medical device company.",
        "help_offered": [], "help_needed": ["Fundraising", "FDA strategy"],
        "availability": "available", "meeting_preference": "either", "graduation_year": 2027,
    }


class MeetingPrepTests(unittest.TestCase):
    def setUp(self):
        self.settings = patch("database.database_settings", return_value=("", "test"))
        self.settings.start()
        self.client = TestClient(app)
        self.client.__enter__()
        self.database = MagicMock()
        self.alumnus = deepcopy(profiles[2])
        self.student = student_profile()
        self.database.profiles.find_one = AsyncMock(side_effect=[self.alumnus, self.student])
        app.dependency_overrides[get_database] = lambda: self.database
        app.dependency_overrides[get_current_user] = lambda: {"_id": "student-user"}

    def tearDown(self):
        app.dependency_overrides.clear()
        self.client.__exit__(None, None, None)
        self.settings.stop()

    def reset_profiles(self, target=None, current=None):
        self.database.profiles.find_one.side_effect = [
            deepcopy(self.alumnus if target is None else target),
            deepcopy(self.student if current is None else current),
        ]

    def test_brief_uses_profile_facts_and_personalized_common_ground(self):
        response = self.client.post(
            "/meeting-prep/sample-taylor",
            json={"goal": "understand FDA strategy for my medical device"},
        )
        self.assertEqual(response.status_code, 200)
        brief = response.json()
        self.assertEqual(brief["profile"]["id"], "sample-taylor")
        self.assertIn("Medical-device operator", brief["overview"])
        self.assertTrue(any(item["marker"] == "2015" for item in brief["timeline"]))
        self.assertTrue(any("healthcare" in item.lower() for item in brief["shared_ground"]))
        self.assertEqual(len(brief["agenda"]), 4)
        self.assertIn("member-provided", brief["grounding_notice"])

    def test_ask_answers_from_the_requested_profile_and_returns_evidence(self):
        self.reset_profiles()
        response = self.client.post("/meeting-prep/sample-taylor/ask", json={
            "goal": "prepare a healthcare startup question",
            "question": "What experience and background should I know about?",
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["answer"], self.alumnus["background"])
        self.assertEqual(data["evidence"][0]["label"], "Background")
        self.assertTrue(data["follow_ups"])

    def test_practice_feedback_is_constructive_and_advances_the_prompt(self):
        self.reset_profiles()
        response = self.client.post("/meeting-prep/sample-taylor/practice", json={
            "goal": "learn about medical-device regulation",
            "answer": "I am building a device because I want to improve care. What early FDA mistake should I avoid?",
            "turn": 0,
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["strengths"])
        self.assertTrue(data["suggestions"])
        self.assertTrue(data["next_question"])
        self.assertIn("not a prediction", data["feedback"])

    def test_missing_and_non_alumni_profiles_are_rejected(self):
        self.database.profiles.find_one.side_effect = [None]
        response = self.client.post("/meeting-prep/missing", json={"goal": "career advice"})
        self.assertEqual(response.status_code, 404)

        self.database.profiles.find_one.side_effect = [self.student]
        response = self.client.post("/meeting-prep/student-profile", json={"goal": "career advice"})
        self.assertEqual(response.status_code, 422)

    def test_requests_are_strictly_validated(self):
        for body in ({"goal": "x"}, {"goal": "career advice", "extra": True}):
            with self.subTest(body=body):
                self.assertEqual(self.client.post("/meeting-prep/sample-taylor", json=body).status_code, 422)
