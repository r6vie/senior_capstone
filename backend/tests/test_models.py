import unittest
from copy import deepcopy
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from pydantic import ValidationError

from auth import get_current_user
from database import get_database
from main import app
from models import Profile
from sample_data import profiles


def sample():
    return deepcopy({key: value for key, value in profiles[0].items() if key != "_id"})


class ProfileModelTests(unittest.TestCase):
    def test_all_seed_profiles_are_valid(self):
        for document in profiles:
            data = {key: value for key, value in document.items() if key != "_id"}
            with self.subTest(name=data["name"]):
                self.assertEqual(Profile.model_validate(data).model_dump(), data)

    def test_each_field_is_required(self):
        for field in sample():
            with self.subTest(field=field):
                data = sample()
                del data[field]
                with self.assertRaises(ValidationError) as error:
                    Profile.model_validate(data)
                self.assertEqual(error.exception.errors()[0]["loc"], (field,))

    def test_text_fields_reject_blanks_and_wrong_types(self):
        for field in ("name", "affiliation", "location"):
            for value in ("", "   ", None, 123, True, []):
                with self.subTest(field=field, value=value):
                    with self.assertRaises(ValidationError):
                        Profile.model_validate({**sample(), field: value})

    def test_tag_lists_reject_wrong_containers_and_invalid_items(self):
        for field in ("expertise", "interests"):
            for value in ("mentoring", None, {}, ("mentoring",), [123], [None], ["   "]):
                with self.subTest(field=field, value=value):
                    with self.assertRaises(ValidationError):
                        Profile.model_validate({**sample(), field: value})

    def test_empty_tag_lists_are_allowed(self):
        profile = Profile.model_validate({**sample(), "expertise": [], "interests": []})
        self.assertEqual(profile.expertise, [])
        self.assertEqual(profile.interests, [])

    def test_extra_fields_are_rejected(self):
        with self.assertRaises(ValidationError) as error:
            Profile.model_validate({**sample(), "unexpected": "value"})
        self.assertEqual(error.exception.errors()[0]["type"], "extra_forbidden")

    def test_trims_text_and_list_items_without_mutating_input(self):
        data = {**sample(), "name": "  Alex  ", "expertise": [" mentoring "]}
        profile = Profile.model_validate(data)
        self.assertEqual(profile.name, "Alex")
        self.assertEqual(profile.expertise, ["mentoring"])
        self.assertEqual(data["name"], "  Alex  ")

    def test_json_round_trip(self):
        profile = Profile.model_validate(sample())
        self.assertEqual(Profile.model_validate_json(profile.model_dump_json()), profile)


class ProfileApiTests(unittest.TestCase):
    def setUp(self):
        # No Atlas credentials or live writes are used by these automated tests.
        self.settings = patch("database.database_settings", return_value=("", "test"))
        self.settings.start()
        self.client = TestClient(app)
        self.client.__enter__()
        self.database = MagicMock()
        self.database.profiles.find_one = AsyncMock(return_value=deepcopy(profiles[0]))
        app.dependency_overrides[get_current_user] = lambda: {"_id": "test-user"}

    def tearDown(self):
        app.dependency_overrides.clear()
        self.client.__exit__(None, None, None)
        self.settings.stop()

    def test_validation_does_not_access_profiles_after_authentication(self):
        def unexpected_database_access():
            self.fail("The validation endpoint must not access MongoDB")

        app.dependency_overrides[get_database] = unexpected_database_access
        response = self.client.post("/profiles/validate", json=sample())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), sample())

    def test_invalid_requests_report_the_field_with_422(self):
        for changes, field in [
            ({"name": "  "}, "name"),
            ({"expertise": "mentoring"}, "expertise"),
            ({"interests": [123]}, "interests"),
            ({"unexpected": True}, "unexpected"),
        ]:
            with self.subTest(field=field):
                response = self.client.post("/profiles/validate", json={**sample(), **changes})
                self.assertEqual(response.status_code, 422)
                self.assertEqual(response.json()["detail"][0]["loc"][:2], ["body", field])

    def test_missing_fields_return_422(self):
        response = self.client.post("/profiles/validate", json={})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(len(response.json()["detail"]), 5)

    def test_valid_database_response_preserves_profile_shape(self):
        app.dependency_overrides[get_database] = lambda: self.database
        response = self.client.get("/profiles/sample")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {**sample(), "id": "sample-alex"})

    def test_invalid_stored_profile_fails_response_validation(self):
        app.dependency_overrides[get_database] = lambda: self.database
        self.database.profiles.find_one.return_value = {**profiles[0], "expertise": "wrong type"}
        with self.assertRaises(ValidationError):
            self.client.get("/profiles/sample")

    def test_list_responses_are_validated_too(self):
        app.dependency_overrides[get_database] = lambda: self.database
        cursor = self.database.profiles.find.return_value.sort.return_value.limit.return_value
        cursor.to_list = AsyncMock(return_value=[deepcopy(profiles[0])])
        self.assertEqual(self.client.get("/profiles").json(), [{**sample(), "id": "sample-alex"}])
        cursor.to_list.return_value = [{**profiles[0], "name": " "}]
        with self.assertRaises(ValidationError):
            self.client.get("/profiles")

    def test_api_docs_expose_the_model_for_requests_and_responses(self):
        schema = self.client.get("/openapi.json").json()
        self.assertEqual(set(schema["components"]["schemas"]["Profile"]["required"]), set(sample()))
        operation = schema["paths"]["/profiles/validate"]["post"]
        body = operation["requestBody"]["content"]["application/json"]["schema"]
        self.assertEqual(body["$ref"], "#/components/schemas/Profile")
