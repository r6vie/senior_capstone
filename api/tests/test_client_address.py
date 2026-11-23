"""Attempt limits are per caller. Behind a host's proxy the caller is in X-Forwarded-For (docs/deploy.md)."""

import pytest
from starlette.requests import Request

from trove.auth.service import client_address
from trove.core.config import get_settings


def request(forwarded: str | None, peer: str = "10.0.0.7") -> Request:
    headers = [(b"x-forwarded-for", forwarded.encode())] if forwarded is not None else []
    return Request({"type": "http", "headers": headers, "client": (peer, 5000)})


@pytest.fixture
def hops(monkeypatch):
    def set_hops(count: int):
        monkeypatch.setattr(get_settings(), "trusted_proxy_hops", count)

    return set_hops


def test_by_default_the_header_is_ignored(hops):
    hops(0)
    assert client_address(request("203.0.113.9")) == "10.0.0.7"


def test_one_proxy_the_last_address_is_the_caller(hops):
    hops(1)
    assert client_address(request("203.0.113.9")) == "203.0.113.9"


def test_a_caller_cannot_choose_their_address_by_writing_the_header(hops):
    hops(1)
    # The caller sent "1.1.1.1"; our proxy added the real address after it.
    assert client_address(request("1.1.1.1, 203.0.113.9")) == "203.0.113.9"


def test_two_proxies_count_two_from_the_right(hops):
    hops(2)
    assert client_address(request("1.1.1.1, 203.0.113.9, 172.16.0.4")) == "203.0.113.9"


def test_a_missing_or_short_header_falls_back_to_the_peer(hops):
    hops(1)
    assert client_address(request(None)) == "10.0.0.7"
    hops(2)
    assert client_address(request("203.0.113.9")) == "10.0.0.7"
