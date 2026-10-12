import json
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from auth import get_current_user
from database import get_database
from interviewer import KICKOFF, SYSTEM_PROMPT, TOOLS, get_claude
from main import app
from member_data import (
    add_facts, compute_coverage, matching_context, search_link_keys, shareable_context,
)
from member_models import FactDraft
from onboarding import SORRY, take_turn
from fakes import FakeDatabase, ScriptedClaude, reply, text, tool

ALEX = {"_id": "user-alex", "name": "Alex Chen", "email": "alex@example.com", "created_at": datetime.now(timezone.utc)}
SAM = {"_id": "user-sam", "name": "Sam Ortiz", "email": "sam@example.com", "created_at": datetime.now(timezone.utc)}
BASICS = {
    "role": "student", "school": "Case School of Engineering", "grad_year": 2027,
    "majors": ["Biomedical Engineering"], "seeking": "both", "location": "Cleveland, Ohio",
}
NEED = {
    "kind": "need", "topic": "fundraising", "text": "Wants help preparing a pre-seed pitch",
    "detail": [{"key": "stage", "value": "pre-seed"}], "links": [], "strength": 3,
    "visibility": "public", "confidence": 0.9,
}


def draft(**changes) -> FactDraft:
    return FactDraft.model_validate({**NEED, **changes})


class OnboardingApiTests(unittest.TestCase):
    def setUp(self):
        self.settings = patch("database.database_settings", return_value=("", "test"))
        self.settings.start()
        self.client = TestClient(app)
        self.client.__enter__()
        self.database = FakeDatabase()
        self.claude = ScriptedClaude()
        self.user = ALEX
        app.dependency_overrides[get_database] = lambda: self.database
        app.dependency_overrides[get_current_user] = lambda: self.user
        app.dependency_overrides[get_claude] = lambda: self.claude

    def tearDown(self):
        app.dependency_overrides.clear()
        self.client.__exit__(None, None, None)
        self.settings.stop()

    def submit_basics(self, **changes):
        response = self.client.post("/onboarding/basics", json={**BASICS, **changes})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def facts(self, user=ALEX):
        return [fact for fact in self.database.facts.documents.values() if fact["user_id"] == user["_id"]]

    def start(self):
        self.claude.responses = [reply(text("Hi Alex! What would you most like help with right now?"))]
        response = self.client.post("/interview/sessions")
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    # ------------------------------------------------------------ basics

    def test_basics_creates_profile_and_confirmed_public_facts(self):
        status = self.submit_basics()
        self.assertTrue(status["basics_done"])
        self.assertEqual(status["basics"], BASICS)
        profile = next(iter(self.database.profiles.documents.values()))
        self.assertEqual(profile["owner_user_id"], "user-alex")
        self.assertEqual(profile["name"], "Alex Chen")
        self.assertEqual(profile["core"]["grad_year"], 2027)
        self.assertEqual(profile["affiliation"], "CWRU student · Case School of Engineering")
        facts = self.facts()
        self.assertTrue(all(f["confirmed"] and f["visibility"] == "public" and f["source"] == "basics_form" for f in facts))
        links = {key for fact in facts for key in fact["links"]}
        self.assertLessEqual(
            {"school:cwru-case-school-of-engineering", "class-year:2027", "major:biomedical-engineering"}, links,
        )
        # Basics alone don't count as interview coverage.
        self.assertEqual(status["coverage"]["percent"], 0)

    def test_resubmitting_basics_replaces_only_basics_facts(self):
        self.submit_basics()
        self.database.facts.documents["kept"] = {
            **draft().model_dump(), "_id": "kept", "user_id": "user-alex", "confirmed": False,
            "source": "interview", "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc),
        }
        self.submit_basics(majors=["Physics", "Math"], location="Boston, Massachusetts")
        self.assertEqual(len(self.database.profiles.documents), 1)
        texts = [fact["text"] for fact in self.facts()]
        self.assertIn("Studies Physics and Math", texts)
        self.assertIn("Based in Boston, Massachusetts", texts)
        self.assertNotIn("Studies Biomedical Engineering", texts)
        self.assertIn("kept", self.database.facts.documents)

    def test_basics_validation(self):
        for body in ({**BASICS, "grad_year": None}, {**BASICS, "role": "wizard"}, {**BASICS, "extra": 1},
                     {**BASICS, "majors": ["a", "b", "c", "d", "e"]}, {**BASICS, "school": " "}):
            with self.subTest(body=body):
                self.assertEqual(self.client.post("/onboarding/basics", json=body).status_code, 422)
        faculty = {**BASICS, "role": "faculty", "grad_year": None}
        self.assertEqual(self.client.post("/onboarding/basics", json=faculty).status_code, 200)

    # ------------------------------------------------------------ interview

    def test_interview_requires_basics(self):
        self.assertEqual(self.client.post("/interview/sessions").status_code, 409)
        self.assertEqual(self.claude.requests, [])

    def test_missing_api_key_returns_503(self):
        self.submit_basics()
        del app.dependency_overrides[get_claude]
        with patch("interviewer.ai_settings", return_value=("", "claude-opus-5-5")):
            response = self.client.post("/interview/sessions")
        self.assertEqual(response.status_code, 503)
        self.assertIn("ANTHROPIC_API_KEY", response.json()["detail"])

    def test_start_sends_hidden_kickoff_with_context(self):
        self.submit_basics()
        data = self.start()
        self.assertEqual([m["role"] for m in data["interview"]["messages"]], ["assistant"])
        request = self.claude.requests[0]
        self.assertEqual(request["system"], SYSTEM_PROMPT)
        self.assertEqual(request["tools"], TOOLS)
        self.assertEqual(request["fallbacks"], "default")
        self.assertEqual(request["output_config"], {"effort": "low"})
        self.assertEqual(request["messages"][0], {"role": "user", "content": KICKOFF})
        note = request["messages"][1]
        self.assertEqual(note["role"], "system")
        self.assertIn("Alex Chen", note["content"])
        self.assertIn("Student at CWRU · Case School of Engineering · Class of 2027", note["content"])
        # Starting again returns the same open interview without calling Claude.
        self.assertEqual(self.client.post("/interview/sessions").json()["interview"]["session_id"],
                         data["interview"]["session_id"])
        self.assertEqual(len(self.claude.requests), 1)

    def test_answer_saves_facts_through_tools_and_returns_next_question(self):
        self.submit_basics()
        session_id = self.start()["interview"]["session_id"]
        self.claude.responses = [
            reply(tool("save_facts", {"facts": [{**NEED, "links": ["Sport: Swimming"]}]})),
            reply(text("What stage is the startup at?")),
        ]
        response = self.client.post(f"/interview/sessions/{session_id}/messages", json={"text": "I need pitch help."})
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertEqual([m["text"] for m in data["interview"]["messages"][-2:]],
                         ["I need pitch help.", "What stage is the startup at?"])
        saved = [fact for fact in data["facts"] if fact["source"] == "interview"]
        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0]["links"], ["sport:swimming"])
        self.assertFalse(saved[0]["confirmed"])
        self.assertEqual(next(a for a in data["coverage"]["areas"] if a["area"] == "needs")["status"], "started")
        # The tool result went back to Claude in the same turn, after the assistant's tool call.
        second = self.claude.requests[-1]["messages"]
        result = second[-1]["content"][0]
        self.assertEqual(result["type"], "tool_result")
        self.assertFalse(result["is_error"])
        self.assertEqual(json.loads(result["content"])[0]["id"], saved[0]["id"])
        # Interview facts update the directory card's interests.
        profile = next(iter(self.database.profiles.documents.values()))
        self.assertEqual(profile["interests"], ["fundraising"])

    def test_transcript_is_append_only_across_turns(self):
        self.submit_basics()
        session_id = self.start()["interview"]["session_id"]
        stored = self.database.interview_sessions.documents[session_id]["api_messages"]
        self.claude.responses = [reply(text("Tell me more."))]
        self.client.post(f"/interview/sessions/{session_id}/messages", json={"text": "Pitching."})
        sent = self.claude.requests[-1]["messages"]
        self.assertEqual(sent[:len(stored)], stored)
        self.assertEqual(sent[len(stored)], {"role": "user", "content": "Pitching."})
        self.assertEqual(sent[len(stored) + 1]["role"], "system")

    def test_panel_edits_are_reported_to_claude_next_turn(self):
        self.submit_basics()
        session_id = self.start()["interview"]["session_id"]
        self.claude.responses = [
            reply(tool("save_facts", {"facts": [NEED, {**NEED, "kind": "goal", "topic": "career", "text": "Wants to found a company"}]})),
            reply(text("Got it.")),
        ]
        facts = self.client.post(f"/interview/sessions/{session_id}/messages", json={"text": "x"}).json()["facts"]
        need, goal = [fact for fact in facts if fact["source"] == "interview"]
        self.client.patch(f"/me/facts/{need['id']}", json={"visibility": "private"})
        self.client.delete(f"/me/facts/{goal['id']}")
        self.claude.responses = [reply(text("Next question?"))]
        self.client.post(f"/interview/sessions/{session_id}/messages", json={"text": "y"})
        note = self.claude.requests[-1]["messages"][-1]["content"]
        self.assertIn(f"Changed {need['id']}", note)
        self.assertIn("(private)", note)
        self.assertIn(f"Deleted {goal['id']}: Wants to found a company", note)

    def test_refusal_keeps_transcript_unchanged(self):
        self.submit_basics()
        session_id = self.start()["interview"]["session_id"]
        before = self.database.interview_sessions.documents[session_id]["api_messages"]
        self.claude.responses = [reply(text(""), stop_reason="refusal")]
        data = self.client.post(f"/interview/sessions/{session_id}/messages", json={"text": "hmm"}).json()
        self.assertEqual(data["interview"]["messages"][-1]["text"], SORRY)
        self.assertEqual(self.database.interview_sessions.documents[session_id]["api_messages"], before)

    def test_bad_tool_calls_return_errors_to_claude(self):
        self.submit_basics()
        session_id = self.start()["interview"]["session_id"]
        self.claude.responses = [
            reply(
                tool("update_fact", {"fact_id": "not-mine", "topic": None, "text": "x", "detail": None, "links": None,
                                     "strength": None, "visibility": None, "confidence": None}, "c1"),
                tool("save_facts", {"facts": [{**NEED, "links": ["no colon"]}]}, "c2"),
            ),
            reply(text("Sorry, let me ask differently.")),
        ]
        self.client.post(f"/interview/sessions/{session_id}/messages", json={"text": "x"})
        results = self.claude.requests[-1]["messages"][-1]["content"]
        self.assertEqual([r["tool_use_id"] for r in results], ["c1", "c2"])
        self.assertTrue(all(r["is_error"] for r in results))
        self.assertFalse([f for f in self.facts() if f["source"] == "interview"])

    def test_ai_cannot_reshare_a_confirmed_fact(self):
        self.submit_basics()
        session_id = self.start()["interview"]["session_id"]
        self.claude.responses = [reply(tool("save_facts", {"facts": [NEED]})), reply(text("ok"))]
        fact = [f for f in self.client.post(f"/interview/sessions/{session_id}/messages", json={"text": "x"}).json()["facts"]
                if f["source"] == "interview"][0]
        self.client.patch(f"/me/facts/{fact['id']}", json={"visibility": "private"})
        self.claude.responses = [
            reply(tool("update_fact", {"fact_id": fact["id"], "topic": None, "text": "Wants pitch coaching",
                                       "detail": None, "links": None, "strength": None, "visibility": "public",
                                       "confidence": None})),
            reply(text("ok")),
        ]
        self.client.post(f"/interview/sessions/{session_id}/messages", json={"text": "y"})
        stored = self.database.facts.documents[fact["id"]]
        self.assertEqual(stored["text"], "Wants pitch coaching")
        self.assertEqual(stored["visibility"], "private")
        self.assertFalse(stored["confirmed"])

    def test_finish_and_resume(self):
        self.submit_basics()
        session_id = self.start()["interview"]["session_id"]
        finished = self.client.post(f"/interview/sessions/{session_id}/finish").json()
        self.assertEqual(finished["interview"]["status"], "finished")
        self.assertEqual(self.client.post(f"/interview/sessions/{session_id}/messages", json={"text": "x"}).status_code, 409)
        self.claude.responses = [reply(text("Welcome back! Last time we covered your pitch."))]
        resumed = self.client.post("/interview/sessions").json()
        self.assertEqual(resumed["interview"]["session_id"], session_id)
        self.assertEqual(resumed["interview"]["status"], "active")
        self.assertEqual([m["role"] for m in resumed["interview"]["messages"]], ["assistant", "assistant"])
        self.assertIn("came back", self.claude.requests[-1]["messages"][-1]["content"])

    def test_other_members_cannot_use_my_interview_or_facts(self):
        self.submit_basics()
        session_id = self.start()["interview"]["session_id"]
        self.claude.responses = [reply(tool("save_facts", {"facts": [NEED]})), reply(text("ok"))]
        self.client.post(f"/interview/sessions/{session_id}/messages", json={"text": "x"})
        fact_id = next(f["_id"] for f in self.facts() if f["source"] == "interview")
        self.user = SAM
        self.assertEqual(self.client.post(f"/interview/sessions/{session_id}/messages", json={"text": "x"}).status_code, 404)
        self.assertEqual(self.client.patch(f"/me/facts/{fact_id}", json={"confirmed": True}).status_code, 404)
        self.assertEqual(self.client.delete(f"/me/facts/{fact_id}").status_code, 404)
        self.assertEqual(self.client.get("/me/facts").json(), [])

    # ------------------------------------------------------------ facts and visibility

    def test_member_edit_confirms_and_validates(self):
        self.submit_basics()
        fact_id = self.facts()[0]["_id"]
        for body in ({}, {"confirmed": False}, {"visibility": "everyone"}, {"text": " "}, {"user_id": "x"}):
            with self.subTest(body=body):
                self.assertEqual(self.client.patch(f"/me/facts/{fact_id}", json=body).status_code, 422)
        data = self.client.patch(f"/me/facts/{fact_id}", json={"text": "Senior in BME"}).json()
        self.assertEqual((data["text"], data["source"], data["confirmed"]), ("Senior in BME", "member_edit", True))
        self.assertEqual(self.client.delete(f"/me/facts/{fact_id}").status_code, 204)
        self.assertEqual(self.client.delete(f"/me/facts/{fact_id}").status_code, 404)

    def test_other_viewers_see_only_public_facts(self):
        self.submit_basics()
        self.database.facts.documents.clear()
        for visibility in ("public", "matches_only", "private"):
            self.database.facts.documents[visibility] = {
                **draft(visibility=visibility, text=f"{visibility} fact").model_dump(), "_id": visibility,
                "user_id": "user-alex", "confirmed": True, "source": "interview",
                "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc),
            }
        profile_id = next(iter(self.database.profiles.documents))
        self.assertEqual(len(self.client.get(f"/profiles/{profile_id}/facts").json()), 3)
        self.user = SAM
        shared = self.client.get(f"/profiles/{profile_id}/facts").json()
        self.assertEqual([fact["text"] for fact in shared], ["public fact"])
        self.assertNotIn("confidence", shared[0])
        self.assertEqual(self.client.get("/profiles/missing/facts").status_code, 404)

    def test_profile_markdown_marks_hidden_facts(self):
        self.submit_basics()
        self.database.facts.documents["p"] = {
            **draft(visibility="private", text="Has a stammer").model_dump(), "_id": "p", "user_id": "user-alex",
            "confirmed": True, "source": "interview", "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        response = self.client.get("/me/profile.md")
        self.assertTrue(response.headers["content-type"].startswith("text/markdown"))
        self.assertIn("# Alex Chen", response.text)
        self.assertIn("## Needs\n- Has a stammer (priority 3/3; stage: pre-seed) [private]", response.text)


class MemberDataTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.database = FakeDatabase()
        for user, profile_id in ((ALEX, "p-alex"), (SAM, "p-sam")):
            await self.database.profiles.insert_one({
                "_id": profile_id, "owner_user_id": user["_id"], "name": user["name"], "affiliation": "x",
                "location": "x", "expertise": [], "interests": [], "core": {**BASICS},
            })

    async def test_matcher_sees_private_facts_but_shared_context_never_does(self):
        await add_facts(self.database, "user-alex", [draft(visibility="private", text="Secret need")], "interview")
        await add_facts(self.database, "user-alex", [draft(text="Open need")], "interview")
        full = await matching_context(self.database, "user-alex")
        self.assertEqual(len(full["facts"]), 2)
        self.assertIn("Secret need", full["profile_md"])
        shared = await shareable_context(self.database, "user-alex", "user-sam")
        self.assertEqual([fact["text"] for fact in shared["facts"]], ["Open need"])
        self.assertNotIn("Secret", shared["profile_md"])

    async def test_link_key_search_prefers_shared_spellings(self):
        await add_facts(self.database, "user-alex", [draft(links=["high-school:saint-ignatius-cleveland-oh"])], "interview")
        await add_facts(self.database, "user-sam", [draft(links=["high-school:saint-ignatius-cleveland-oh"])], "interview")
        await add_facts(self.database, "user-sam", [draft(links=["high-school:saint-ignatius-chicago-il"])], "interview")
        found = await search_link_keys(self.database, "Saint Ignatius")
        self.assertEqual(found[0], {"key": "high-school:saint-ignatius-cleveland-oh", "members": 2})
        self.assertEqual(len(found), 2)

    def test_coverage_depends_on_what_the_member_seeks(self):
        def fact(kind, **extra):
            return {**draft(kind=kind).model_dump(), "source": "interview", **extra}
        mentor = compute_coverage({"seeking": "give_help"}, [])
        self.assertFalse(next(a for a in mentor.areas if a.area == "needs").important)
        two_details = [{"key": "stage", "value": "pre-seed"}, {"key": "urgency", "value": "this month"}]
        full = compute_coverage({"seeking": "both"}, [
            fact("need", detail=two_details), fact("offer"), fact("experience"),
            fact("preference"), fact("availability"), fact("goal"),
        ])
        self.assertEqual(full.percent, 100)
        self.assertEqual(next(a for a in full.areas if a.area == "background").status, "missing")

    async def test_stale_turn_is_rejected(self):
        session = {"_id": "s", "user_id": "user-alex", "status": "active", "turns": 0, "api_messages": [],
                   "chat": [], "known": {}}
        await self.database.interview_sessions.insert_one({**session, "turns": 1})
        claude = ScriptedClaude(reply(text("Hello")))
        with self.assertRaises(HTTPException) as caught:
            await take_turn(self.database, claude, ALEX, session, "hi", "note", shown=True)
        self.assertEqual(caught.exception.status_code, 409)


if __name__ == "__main__":
    unittest.main()
