"""Sending through Brevo's web API, for hosts that block SMTP ports. Nothing here touches the network."""

import json
import logging
from io import BytesIO
from urllib.error import HTTPError

import pytest

from trove.core.config import get_settings
from trove.notifications import service
from trove.notifications.service import notify_welcome


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self):
        return b"{}"


@pytest.fixture
def brevo(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "brevo_api_key", "test-key-not-real")
    monkeypatch.setattr(settings, "email_from", "Trove <trove@example.com>")
    sent = []

    def fake_urlopen(request, timeout):
        sent.append(request)
        return FakeResponse()

    def no_smtp(*_args, **_kwargs):
        raise AssertionError("SMTP must not be used when a Brevo key is set")

    monkeypatch.setattr(service, "urlopen", fake_urlopen)
    monkeypatch.setattr(service.smtplib, "SMTP", no_smtp)
    return sent


async def make_member(database) -> str:
    await database.users.insert_one({"_id": "u1", "email": "sam@case.edu", "is_active": True})
    return "u1"


async def test_mail_goes_through_the_web_api_not_smtp(database, brevo):
    status = await notify_welcome(database, await make_member(database), "Sam")
    assert status == "sent"
    request = brevo[0]
    assert request.full_url == "https://api.brevo.com/v3/smtp/email"
    assert request.get_method() == "POST"
    assert request.get_header("Api-key") == "test-key-not-real"
    body = json.loads(request.data)
    assert body["sender"] == {"email": "trove@example.com", "name": "Trove"}
    assert body["to"] == [{"email": "sam@case.edu"}]
    assert body["subject"] == "Welcome to Trove"
    assert "Hi Sam," in body["textContent"]
    assert "<h2" in body["htmlContent"]


async def test_the_key_is_never_in_the_message(database, brevo):
    await notify_welcome(database, await make_member(database), "Sam")
    assert "test-key-not-real" not in brevo[0].data.decode()


async def test_a_refusal_is_a_failed_send_with_the_reason_logged(database, brevo, monkeypatch, caplog):
    def refuse(request, timeout):
        raise HTTPError(request.full_url, 401, "Unauthorized", {}, BytesIO(b'{"message":"Key not found"}'))

    monkeypatch.setattr(service, "urlopen", refuse)
    with caplog.at_level(logging.WARNING):
        status = await notify_welcome(database, await make_member(database), "Sam")
    assert status == "failed"
    assert "HTTPError 401" in caplog.text
    assert "Key not found" in caplog.text
    assert "sam@case.edu" not in caplog.text
    assert "test-key-not-real" not in caplog.text


async def test_a_failed_send_is_retried_by_the_next_call(database, brevo, monkeypatch):
    calls = []

    def flaky(request, timeout):
        calls.append(request)
        if len(calls) == 1:
            raise TimeoutError
        return FakeResponse()

    monkeypatch.setattr(service, "urlopen", flaky)
    user = await make_member(database)
    assert await notify_welcome(database, user, "Sam") == "failed"
    assert await notify_welcome(database, user, "Sam") == "sent"


async def test_without_any_key_or_smtp_the_email_is_printed(database, capsys, monkeypatch):
    monkeypatch.setattr(get_settings(), "brevo_api_key", "")
    status = await notify_welcome(database, await make_member(database), "Sam")
    assert status == "logged"
    assert "Welcome to Trove" in capsys.readouterr().out
