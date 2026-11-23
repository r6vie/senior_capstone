"""scripts/dev.py: which AI a developer's copy runs, and the clear stop when it can't start."""

import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "dev.py"
spec = importlib.util.spec_from_file_location("dev_script", SCRIPT)
dev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dev)


def settings(**changes):
    return {
        "key": True,
        "mode": "real",
        "database": "trove_dev_maya",
        "model": "claude-opus-5-5",
        "environment": "development",
        **changes,
    }


def test_a_key_runs_the_real_ai_and_names_the_model():
    assert dev.choose_ai(settings(), asked_scripted=False) == (False, "real (claude-opus-5-5)", None)


def test_no_key_falls_back_to_the_scripted_ai_and_says_why():
    scripted, line, problem = dev.choose_ai(settings(key=False), asked_scripted=False)
    assert (scripted, problem) == (True, None)
    assert "no ANTHROPIC_API_KEY" in line


@pytest.mark.parametrize("change", [{"mode": "scripted"}, {}])
def test_asking_for_the_scripted_ai_runs_it(change):
    scripted, line, problem = dev.choose_ai(settings(**change), asked_scripted=not change)
    assert (scripted, line, problem) == (True, "scripted (canned replies, no key, no cost)", None)


def test_scripted_on_another_database_stops_with_the_fix():
    scripted, _, problem = dev.choose_ai(settings(database="founderscircle"), asked_scripted=True)
    assert scripted
    assert "MONGODB_DATABASE is founderscircle" in problem
    assert "trove_dev_<yourname>" in problem


def test_no_key_on_another_database_names_both_ways_out():
    _, _, problem = dev.choose_ai(settings(key=False, database="alvisa"), asked_scripted=False)
    assert "no ANTHROPIC_API_KEY" in problem
    assert "Add a key, or set MONGODB_DATABASE=trove_dev_<yourname>" in problem


def test_a_key_on_any_database_still_runs_the_real_ai():
    assert dev.choose_ai(settings(database="founderscircle"), asked_scripted=False)[2] is None


def test_scripted_outside_development_stops_with_the_fix():
    _, _, problem = dev.choose_ai(settings(environment="production"), asked_scripted=True)
    assert "ENVIRONMENT is production" in problem


def test_it_matches_the_apis_list_of_development_environments():
    from trove.ai.scripted import DEV_ENVIRONMENTS

    assert dev.DEV_ENVIRONMENTS == DEV_ENVIRONMENTS
