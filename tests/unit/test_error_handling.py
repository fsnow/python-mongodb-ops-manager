# Copyright 2024 Frank Snow
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Unit tests for error handling in NetworkSession."""

import json
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from opsmanager.network import NetworkSession
from opsmanager.errors import (
    OpsManagerAuthenticationError,
    OpsManagerNotFoundError,
    OpsManagerRateLimitError,
    OpsManagerServerError,
    OpsManagerConnectionError,
    OpsManagerTimeoutError,
)


def _make_session(base_url="http://om.example.com"):
    """Build a NetworkSession with a mocked requests.Session."""
    auth = MagicMock()
    session = NetworkSession(
        base_url=base_url,
        auth=auth,
        rate_limit=1000.0,   # fast — no real waiting in tests
        retry_count=0,        # no retries — fail fast
        retry_backoff=0.0,
    )
    return session


def _make_response(status_code, body=None, headers=None):
    """Build a mock requests.Response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.reason = {200: "OK", 401: "Unauthorized", 404: "Not Found",
                   429: "Too Many Requests", 500: "Internal Server Error"}.get(status_code, "")
    resp.ok = 200 <= status_code < 300
    resp.content = json.dumps(body or {}).encode()
    resp.text = json.dumps(body or {})
    resp.json.return_value = body or {}
    resp.headers = headers or {}
    return resp


class TestNetworkSession404:
    """404 responses raise OpsManagerNotFoundError."""

    def test_get_404_raises(self):
        session = _make_session()
        resp = _make_response(404, {"reason": "Not Found", "errorCode": "RESOURCE_NOT_FOUND"})
        session._session.request = MagicMock(return_value=resp)

        with pytest.raises(OpsManagerNotFoundError) as exc_info:
            session.get("api/public/v1.0/groups/bad-id")

        assert exc_info.value.status_code == 404


class TestNetworkSession401:
    """401 responses raise OpsManagerAuthenticationError."""

    def test_get_401_raises(self):
        session = _make_session()
        resp = _make_response(401, {"reason": "Unauthorized", "errorCode": "AUTH_FAILED"})
        session._session.request = MagicMock(return_value=resp)

        with pytest.raises(OpsManagerAuthenticationError) as exc_info:
            session.get("api/public/v1.0/groups")

        assert exc_info.value.status_code == 401


class TestNetworkSession429:
    """429 responses raise OpsManagerRateLimitError after retries exhausted."""

    def test_get_429_raises_after_no_retries(self):
        session = _make_session()
        resp = _make_response(429, {"reason": "Too Many Requests"}, headers={"Retry-After": "5"})
        session._session.request = MagicMock(return_value=resp)

        with pytest.raises(OpsManagerRateLimitError) as exc_info:
            session.get("api/public/v1.0/groups")

        assert exc_info.value.status_code == 429
        assert exc_info.value.retry_after == 5

    def test_get_429_retries_then_succeeds(self):
        """With retry_count=1: first call returns 429, second returns 200."""
        auth = MagicMock()
        session = NetworkSession(
            base_url="http://om.example.com",
            auth=auth,
            rate_limit=1000.0,
            retry_count=1,
            retry_backoff=0.0,
        )

        resp_429 = _make_response(429, {}, headers={"Retry-After": "0"})
        resp_200 = _make_response(200, {"results": [], "totalCount": 0})
        session._session.request = MagicMock(side_effect=[resp_429, resp_200])

        result = session.get("api/public/v1.0/groups")
        assert result == {"results": [], "totalCount": 0}
        assert session._session.request.call_count == 2


class TestNetworkSession500:
    """5xx responses raise OpsManagerServerError."""

    def test_get_500_raises(self):
        session = _make_session()
        resp = _make_response(500, {"reason": "Internal Server Error"})
        session._session.request = MagicMock(return_value=resp)

        with pytest.raises(OpsManagerServerError) as exc_info:
            session.get("api/public/v1.0/groups")

        assert exc_info.value.status_code == 500


class TestNetworkSessionSuccessful:
    """Successful responses return parsed JSON."""

    def test_get_200_returns_data(self):
        session = _make_session()
        body = {"results": [{"id": "abc"}], "totalCount": 1}
        resp = _make_response(200, body)
        session._session.request = MagicMock(return_value=resp)

        result = session.get("api/public/v1.0/groups")
        assert result == body

    def test_get_empty_content_returns_empty_dict(self):
        session = _make_session()
        resp = _make_response(200)
        resp.content = b""  # empty body
        session._session.request = MagicMock(return_value=resp)

        result = session.get("api/public/v1.0/groups")
        assert result == {}


class TestNetworkSessionConnectionErrors:
    """Connection and timeout errors."""

    def test_timeout_raises(self):
        import requests.exceptions
        session = _make_session()
        session._session.request = MagicMock(
            side_effect=requests.exceptions.Timeout("timed out")
        )

        with pytest.raises(OpsManagerTimeoutError):
            session.get("api/public/v1.0/groups")

    def test_connection_error_raises(self):
        import requests.exceptions
        session = _make_session()
        session._session.request = MagicMock(
            side_effect=requests.exceptions.ConnectionError("refused")
        )

        with pytest.raises(OpsManagerConnectionError):
            session.get("api/public/v1.0/groups")

    def test_timeout_retries(self):
        """With retry_count=1, timeout on first attempt retries."""
        import requests.exceptions
        auth = MagicMock()
        session = NetworkSession(
            base_url="http://om.example.com",
            auth=auth,
            rate_limit=1000.0,
            retry_count=1,
            retry_backoff=0.0,
        )

        resp_200 = _make_response(200, {"results": []})
        session._session.request = MagicMock(
            side_effect=[requests.exceptions.Timeout("first"), resp_200]
        )

        result = session.get("api/public/v1.0/groups")
        assert result == {"results": []}
        assert session._session.request.call_count == 2


class TestNetworkSessionNonJsonBody:
    """Non-JSON error bodies fall back to raw text."""

    def test_non_json_error_body_handled(self):
        session = _make_session()
        resp = MagicMock()
        resp.status_code = 503
        resp.reason = "Service Unavailable"
        resp.ok = False
        resp.content = b"Service Unavailable"
        resp.text = "Service Unavailable"
        resp.json.side_effect = ValueError("not json")
        resp.headers = {}
        session._session.request = MagicMock(return_value=resp)

        with pytest.raises(Exception):
            session.get("api/public/v1.0/groups")


class TestNetworkSessionCallbacks:
    """on_request and on_response callbacks are invoked."""

    def test_on_request_callback_called(self):
        session = _make_session()
        resp = _make_response(200, {})
        session._session.request = MagicMock(return_value=resp)

        callback = MagicMock()
        session.on_request(callback)
        session.get("api/public/v1.0/groups")

        callback.assert_called_once()
        args = callback.call_args[0]
        assert args[0] == "GET"
        assert "groups" in args[1]

    def test_on_response_callback_called(self):
        session = _make_session()
        resp = _make_response(200, {})
        session._session.request = MagicMock(return_value=resp)

        callback = MagicMock()
        session.on_response(callback)
        session.get("api/public/v1.0/groups")

        callback.assert_called_once_with(resp)
