import json
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from auth import get_current_user
from database import get_database
from interviewer import FALLBACK_QUESTIONS, FIRST_QUESTIONS, QUESTION_FORMAT, SYSTEM_PROMPT, TOOLS, Claude, get_claude
from main import app
from member_data import (
    add_facts, compute_coverage, matching_context, search_link_keys, shareable_context,
)
from member_models import FactDraft
from onboarding import SORRY, take_turn
from fakes import FakeDatabase, ScriptedClaude, question, reply, text, tool

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
        response = self.client.post("/interview/sessions")
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()["interview"]

    def answer(self, interview, *responses, expect=200, **body):
        self.claude.responses = list(responses)
        response = self.client.post(
            f"/interview/sessions/{interview['session_id']}/answers",
            json={"question_id": interview["question"]["id"], **body},
        )
        self.assertEqual(response.status_code, expect, response.text)
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

    def test_first_question_is_ready_without_calling_claude(self):
        self.submit_basics()
        interview = self.start()
        self.assertEqual(self.claude.requests, [])
        fixed = FIRST_QUESTIONS["both"]
        self.assertEqual({key: interview["question"][key] for key in fixed}, fixed)
        self.assertEqual((interview["answered"], interview["added"], interview["done"]), (0, [], False))
        # Starting again (another tab, a double-click) returns the same interview and question.
        self.assertEqual(self.client.post("/interview/sessions").json()["interview"], interview)
        self.assertEqual(len(self.database.interview_sessions.documents), 1)

    def test_mentors_get_a_first_question_about_offering_help(self):
        self.submit_basics(seeking="give_help")
        self.assertEqual(self.start()["question"]["area"], "offers")

    def test_first_answer_opens_the_ai_conversation_with_context(self):
        self.submit_basics()
        self.answer(self.start(), reply(question("Next?")), choices=["Finding a mentor"])
        request = self.claude.requests[0]
        self.assertEqual(request["system"], SYSTEM_PROMPT)
        self.assertEqual(request["tools"], TOOLS)
        self.assertEqual(request["output_config"], {"effort": "medium", "format": QUESTION_FORMAT})
        first, note = request["messages"]
        self.assertEqual(first["role"], "user")
        self.assertIn("What would you most like help with right now?", first["content"])
        self.assertEqual(note["role"], "system")
        self.assertIn("Student at CWRU · Case School of Engineering · Class of 2027", note["content"])
        self.assertIn("standard first question", note["content"])

    def test_answer_saves_facts_and_reports_what_was_added(self):
        self.submit_basics()
        interview = self.start()
        data = self.answer(
            interview,
            reply(tool("save_facts", {"facts": [{**NEED, "links": ["Sport: Swimming"]}]})),
            reply(question("What's the deadline you're working toward?", placeholder="Demo day in December")),
            choices=["Starting or growing a project"], text="Pre-seed, med-device startup",
        )
        saved = [fact for fact in data["facts"] if fact["source"] == "interview"]
        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0]["links"], ["sport:swimming"])
        self.assertFalse(saved[0]["confirmed"])
        self.assertEqual(data["interview"]["added"], [saved[0]["id"]])
        self.assertEqual(data["interview"]["answered"], 1)
        self.assertEqual(data["interview"]["question"]["placeholder"], "Demo day in December")
        self.assertNotEqual(data["interview"]["question"]["id"], interview["question"]["id"])
        sent = self.claude.requests[0]["messages"][-2]["content"]
        self.assertIn("Picked: Starting or growing a project", sent)
        self.assertIn("In their own words: Pre-seed, med-device startup", sent)
        result = self.claude.requests[-1]["messages"][-1]["content"][0]
        self.assertEqual((result["type"], result["is_error"]), ("tool_result", False))
        self.assertEqual(json.loads(result["content"])[0]["id"], saved[0]["id"])
        profile = next(iter(self.database.profiles.documents.values()))
        self.assertEqual(profile["interests"], ["fundraising"])

    def test_answers_are_validated_against_the_current_question(self):
        self.submit_basics()
        interview = self.start()
        self.answer(interview, expect=422)  # nothing picked, typed or skipped
        self.answer(interview, expect=422, choices=["Not offered"])
        stale = {**interview, "question": {**interview["question"], "id": "old"}}
        self.answer(stale, expect=409, text="hi")
        self.assertEqual(self.claude.requests, [])
        single = self.answer(interview, reply(question("Which stage?", choices=["Idea", "Prototype"])), text="x")
        self.answer(single["interview"], expect=422, choices=["Idea", "Prototype"])

    def test_skipping_tells_claude_and_does_not_count_as_answered(self):
        self.submit_basics()
        data = self.answer(self.start(), reply(question("What could you help others with?", area="offers")), skipped=True)
        self.assertIn("skipped", self.claude.requests[-1]["messages"][-2]["content"])
        self.assertEqual(data["interview"]["answered"], 0)
        self.assertEqual(data["interview"]["question"]["area"], "offers")

    def test_overlong_question_parts_are_shortened_not_rejected(self):
        self.submit_basics()
        long_choice = "Getting advice on choosing between graduate school and industry jobs after I graduate"
        data = self.answer(self.start(), reply(question(
            "What next?", choices=[long_choice, "Short", "Short"], placeholder="x" * 300,
        )), text="Pitch help")
        asked = data["interview"]["question"]
        self.assertEqual(asked["prompt"], "What next?")
        self.assertEqual(len(asked["choices"]), 2)
        self.assertTrue(asked["choices"][0].endswith("…") and len(asked["choices"][0]) == 60)
        self.assertEqual(len(asked["placeholder"]), 120)

    def test_unreadable_reply_falls_back_to_a_plain_question(self):
        self.submit_basics()
        data = self.answer(self.start(), reply(text("not json")), text="Pitch help")
        self.assertIn(data["interview"]["question"]["prompt"], FALLBACK_QUESTIONS.values())
        self.assertEqual(data["interview"]["question"]["choices"], [])

    def test_transcript_is_append_only_across_turns(self):
        self.submit_basics()
        interview = self.answer(self.start(), reply(question("Tell me more.")), text="Pitching.")["interview"]
        stored = self.database.interview_sessions.documents[interview["session_id"]]["api_messages"]
        self.answer(interview, reply(question("And?")), text="More pitching.")
        sent = self.claude.requests[-1]["messages"]
        self.assertEqual(sent[:len(stored)], stored)
        self.assertEqual(sent[len(stored)]["role"], "user")
        self.assertEqual(sent[len(stored) + 1]["role"], "system")

    def test_fact_edits_are_reported_to_claude_next_turn(self):
        self.submit_basics()
        goal = {**NEED, "kind": "goal", "topic": "career", "text": "Wants to found a company"}
        data = self.answer(
            self.start(), reply(tool("save_facts", {"facts": [NEED, goal]})), reply(question("Next?")), text="x",
        )
        need, saved_goal = [fact for fact in data["facts"] if fact["source"] == "interview"]
        self.client.patch(f"/me/facts/{need['id']}", json={"visibility": "private"})
        self.client.delete(f"/me/facts/{saved_goal['id']}")
        self.answer(data["interview"], reply(question("And then?")), text="y")
        note = self.claude.requests[-1]["messages"][-1]["content"]
        self.assertIn(f"Changed {need['id']}", note)
        self.assertIn("(private)", note)
        self.assertIn(f"Deleted {saved_goal['id']}: Wants to found a company", note)

    def test_refusal_keeps_question_and_transcript(self):
        self.submit_basics()
        interview = self.answer(self.start(), reply(question("Tell me more.")), text="x")["interview"]
        before = self.database.interview_sessions.documents[interview["session_id"]]["api_messages"]
        data = self.answer(interview, reply(text(""), stop_reason="refusal"), text="hmm")
        self.assertEqual(data["interview"]["notice"], SORRY)
        self.assertEqual(data["interview"]["question"], interview["question"])
        self.assertEqual(self.database.interview_sessions.documents[interview["session_id"]]["api_messages"], before)
        # The notice clears once an answer goes through.
        self.assertIsNone(self.answer(data["interview"], reply(question("Ok")), text="again")["interview"]["notice"])

    def test_bad_tool_calls_return_errors_to_claude(self):
        self.submit_basics()
        self.answer(
            self.start(),
            reply(
                tool("update_fact", {"fact_id": "not-mine", "topic": None, "text": "x", "detail": None, "links": None,
                                     "strength": None, "visibility": None, "confidence": None}, "c1"),
                tool("save_facts", {"facts": [{**NEED, "links": ["no colon"]}]}, "c2"),
            ),
            reply(question("Let me ask differently.")),
            text="x",
        )
        results = self.claude.requests[-1]["messages"][-1]["content"]
        self.assertEqual([r["tool_use_id"] for r in results], ["c1", "c2"])
        self.assertTrue(all(r["is_error"] for r in results))
        self.assertFalse([f for f in self.facts() if f["source"] == "interview"])

    def test_ai_cannot_reshare_a_confirmed_fact(self):
        self.submit_basics()
        data = self.answer(self.start(), reply(tool("save_facts", {"facts": [NEED]})), reply(question("ok")), text="x")
        fact = [f for f in data["facts"] if f["source"] == "interview"][0]
        self.client.patch(f"/me/facts/{fact['id']}", json={"visibility": "private"})
        self.answer(
            data["interview"],
            reply(tool("update_fact", {"fact_id": fact["id"], "topic": None, "text": "Wants pitch coaching",
                                       "detail": None, "links": None, "strength": None, "visibility": "public",
                                       "confidence": None})),
            reply(question("ok")),
            text="y",
        )
        stored = self.database.facts.documents[fact["id"]]
        self.assertEqual(stored["text"], "Wants pitch coaching")
        self.assertEqual(stored["visibility"], "private")
        self.assertFalse(stored["confirmed"])

    def test_done_flag_and_finish_then_resume_without_a_new_ai_call(self):
        self.submit_basics()
        data = self.answer(self.start(), reply(question("Anything else?", done=True)), text="x")
        self.assertTrue(data["interview"]["done"])
        session_id = data["interview"]["session_id"]
        finished = self.client.post(f"/interview/sessions/{session_id}/finish").json()["interview"]
        self.assertEqual(finished["status"], "finished")
        self.answer(finished, expect=409, text="x")
        calls = len(self.claude.requests)
        resumed = self.client.post("/interview/sessions").json()["interview"]
        self.assertEqual((resumed["status"], resumed["question"]), ("active", finished["question"]))
        self.assertEqual(len(self.claude.requests), calls)

    def test_other_members_cannot_use_my_interview_or_facts(self):
        self.submit_basics()
        data = self.answer(self.start(), reply(tool("save_facts", {"facts": [NEED]})), reply(question("ok")), text="x")
        fact_id = next(f["_id"] for f in self.facts() if f["source"] == "interview")
        self.user = SAM
        self.answer(data["interview"], expect=404, text="x")
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


class ClaudeClientTests(unittest.TestCase):
    def test_fallbacks_are_only_sent_to_models_that_support_them(self):
        opus = Claude("test-key", "claude-opus-5-5").request({"max_tokens": 10})
        self.assertEqual((opus["model"], opus["fallbacks"], opus["betas"]),
                         ("claude-opus-5-5", "default", ["server-side-fallback-2026-07-01"]))
        haiku = Claude("test-key", "claude-haiku-5-5").request({"max_tokens": 10})
        self.assertEqual(haiku, {"model": "claude-haiku-5-5", "max_tokens": 10})


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
                   "known": {}, "question": None}
        await self.database.interview_sessions.insert_one({**session, "turns": 1})
        claude = ScriptedClaude(reply(question("Hello")))
        profile = await self.database.profiles.find_one({"_id": "p-alex"})
        with self.assertRaises(HTTPException) as caught:
            await take_turn(self.database, claude, ALEX, profile, session, "hi", "note", answered=True)
        self.assertEqual(caught.exception.status_code, 409)


if __name__ == "__main__":
    unittest.main()
