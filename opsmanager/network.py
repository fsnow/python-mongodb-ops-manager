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

"""
Network layer for MongoDB Ops Manager API client.

Handles HTTP requests with:
- Rate limiting (critical for production safety)
- Retry logic with exponential backoff
- Request/response logging
- Error handling
"""

import logging
import time
from threading import Lock
from typing import Any, Callable, Dict, Optional, Union
from urllib.parse import urljoin

import requests
from requests.auth import AuthBase

from opsmanager.errors import (
    OpsManagerConnectionError,
    OpsManagerRateLimitError,
    OpsManagerTimeoutError,
    raise_for_status,
)

logger = logging.getLogger(__name__)


class RateLimiter:
    """Thread-safe rate limiter enforcing strict request spacing.

    This is critical for protecting production Ops Manager instances
    from being overwhelmed by API requests.

    By default (burst=1), this enforces strict spacing between requests.
    For example, with rate=2.0, requests are spaced at least 500ms apart,
    ensuring the rate limit is never violated at any time scale.

    With burst > 1, the traditional token bucket algorithm is used,
    allowing short bursts before throttling.

    Attributes:
        rate: Maximum requests per second.
        burst: Maximum burst size (1 = strict spacing, >1 = token bucket).
    """

    def __init__(self, rate: float = 2.0, burst: int = 1):
        """Initialize the rate limiter.

        Args:
            rate: Maximum requests per second. Default is 2 (conservative).
            burst: Maximum burst size. Default is 1 (strict spacing).
                Set to higher values to allow short bursts of requests.
        """
        self.rate = rate
        self.burst = burst
        self._tokens = float(burst)
        self._last_request: Optional[float] = None
        self._last_update = time.monotonic()
        self._lock = Lock()

    def acquire(self, timeout: Optional[float] = None) -> bool:
        """Acquire a token, blocking if necessary.

        Args:
            timeout: Maximum time to wait for a token (seconds).
                    None means wait indefinitely.

        Returns:
            True if token was acquired, False if timeout occurred.
        """
        start_time = time.monotonic()
        min_interval = 1.0 / self.rate

        while True:
            # Determine how long to wait (if any)
            wait_time = 0.0
            with self._lock:
                now = time.monotonic()

                if self.burst == 1:
                    # Strict mode: enforce minimum interval between requests
                    if self._last_request is not None:
                        elapsed_since_last = now - self._last_request
                        if elapsed_since_last < min_interval:
                            wait_time = min_interval - elapsed_since_last
                        else:
                            # Enough time has passed, acquire immediately
                            self._last_request = now
                            return True
                    else:
                        # First request, no waiting needed
                        self._last_request = now
                        return True
                else:
                    # Token bucket mode for burst > 1
                    elapsed = now - self._last_update
                    self._tokens = min(self.burst, self._tokens + elapsed * self.rate)
                    self._last_update = now

                    if self._tokens >= 1.0:
                        self._tokens -= 1.0
                        return True

                    # Calculate wait time for next token
                    wait_time = (1.0 - self._tokens) / self.rate

            # Check timeout before sleeping
            if timeout is not None:
                elapsed_total = time.monotonic() - start_time
                if elapsed_total + wait_time > timeout:
                    return False

            # Sleep outside the lock
            time.sleep(wait_time)

    def set_rate(self, rate: float) -> None:
        """Update the rate limit.

        Args:
            rate: New maximum requests per second.
        """
        with self._lock:
            self.rate = rate


class NetworkSession:
    """HTTP session manager with rate limiting and retry logic.

    This class wraps requests.Session to provide:
    - Rate limiting to protect Ops Manager
    - Automatic retries with exponential backoff
    - Consistent error handling
    - Request/response logging
    """

    DEFAULT_TIMEOUT = 30  # seconds
    DEFAULT_RATE_LIMIT = 2.0  # requests per second
    DEFAULT_RETRY_COUNT = 3
    DEFAULT_RETRY_BACKOFF = 1.0  # seconds

    DEFAULT_RATE_BURST = 1  # no bursting by default

    def __init__(
        self,
        base_url: str,
        auth: AuthBase,
        timeout: float = DEFAULT_TIMEOUT,
        rate_limit: float = DEFAULT_RATE_LIMIT,
        rate_burst: int = DEFAULT_RATE_BURST,
        retry_count: int = DEFAULT_RETRY_COUNT,
        retry_backoff: float = DEFAULT_RETRY_BACKOFF,
        verify_ssl: bool = True,
        user_agent: Optional[str] = None,
    ):
        """Initialize the network session.

        Args:
            base_url: Base URL for the Ops Manager API.
            auth: Authentication handler (typically OpsManagerAuth).
            timeout: Request timeout in seconds.
            rate_limit: Maximum requests per second.
            rate_burst: Maximum burst size (default 1 = no bursting).
                Set to higher values to allow short bursts of requests.
            retry_count: Number of retries for failed requests.
            retry_backoff: Base backoff time between retries.
            verify_ssl: Whether to verify SSL certificates.
            user_agent: Custom User-Agent string.
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.retry_count = retry_count
        self.retry_backoff = retry_backoff

        # Initialize session
        self._session = requests.Session()
        self._session.auth = auth
        self._session.verify = verify_ssl
        self._session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": user_agent or "python-opsmanager/0.1.0",
        })

        # Initialize rate limiter
        self._rate_limiter = RateLimiter(rate=rate_limit, burst=rate_burst)

        # Request/response callbacks
        self._on_request: Optional[Callable] = None
        self._on_response: Optional[Callable] = None

    def set_rate_limit(self, rate: float) -> None:
        """Update the rate limit.

        Args:
            rate: New maximum requests per second.
        """
        self._rate_limiter.set_rate(rate)

    def on_request(self, callback: Callable[[str, str, Dict], None]) -> None:
        """Set a callback to be invoked before each request.

        Args:
            callback: Function(method, url, kwargs) called before request.
        """
        self._on_request = callback

    def on_response(self, callback: Callable[[requests.Response], None]) -> None:
        """Set a callback to be invoked after each response.

        Args:
            callback: Function(response) called after response.
        """
        self._on_response = callback

    def request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Make an HTTP request to the Ops Manager API.

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE).
            path: API path (relative to base_url).
            params: Query parameters.
            json: JSON body for POST/PUT/PATCH requests.
            timeout: Request timeout (overrides default).

        Returns:
            Parsed JSON response.

        Raises:
            OpsManagerError: For API errors.
            OpsManagerTimeoutError: If request times out.
            OpsManagerConnectionError: If connection fails.
            OpsManagerRateLimitError: If rate limit is exceeded.
        """
        url = urljoin(self.base_url + "/", path.lstrip("/"))
        request_timeout = timeout or self.timeout

        last_exception: Optional[Exception] = None

        for attempt in range(self.retry_count + 1):
            # Acquire rate limit token
            if not self._rate_limiter.acquire(timeout=request_timeout):
                raise OpsManagerRateLimitError(
                    message="Rate limit acquisition timed out",
                    detail=f"Could not acquire rate limit token within {request_timeout}s",
                )

            # Invoke pre-request callback AFTER rate limiting
            # This ensures accurate timing for monitoring actual request spacing
            if self._on_request:
                self._on_request(method, url, {"params": params, "json": json})

            try:
                logger.debug(
                    "Request [%d/%d]: %s %s",
                    attempt + 1,
                    self.retry_count + 1,
                    method,
                    url,
                )

                response = self._session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json,
                    timeout=request_timeout,
                )

                # Invoke post-response callback
                if self._on_response:
                    self._on_response(response)

                logger.debug(
                    "Response: %d %s",
                    response.status_code,
                    response.reason,
                )

                # Handle rate limit response from server
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    if attempt < self.retry_count:
                        logger.warning(
                            "Rate limited by server, waiting %ds before retry",
                            retry_after,
                        )
                        time.sleep(retry_after)
                        continue
                    raise OpsManagerRateLimitError(
                        message="Rate limit exceeded",
                        retry_after=retry_after,
                    )

                # Parse response
                try:
                    response_data = response.json() if response.content else {}
                except ValueError:
                    response_data = {"raw": response.text}

                # Check for errors
                raise_for_status(response.status_code, response_data)

                return response_data

            except requests.exceptions.Timeout as e:
                last_exception = OpsManagerTimeoutError(
                    message="Request timed out",
                    detail=str(e),
                )
                if attempt < self.retry_count:
                    wait_time = self.retry_backoff * (2 ** attempt)
                    logger.warning(
                        "Request timed out, retrying in %.1fs",
                        wait_time,
                    )
                    time.sleep(wait_time)
                    continue

            except requests.exceptions.ConnectionError as e:
                last_exception = OpsManagerConnectionError(
                    message="Connection failed",
                    detail=str(e),
                )
                if attempt < self.retry_count:
                    wait_time = self.retry_backoff * (2 ** attempt)
                    logger.warning(
                        "Connection failed, retrying in %.1fs",
                        wait_time,
                    )
                    time.sleep(wait_time)
                    continue

            except OpsManagerRateLimitError:
                raise

            except Exception as e:
                # Don't retry on other errors
                logger.error("Request failed: %s", e)
                raise

        # All retries exhausted
        if last_exception:
            raise last_exception

        raise OpsManagerConnectionError(message="Request failed after all retries")

    def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Make a GET request."""
        return self.request("GET", path, params=params, **kwargs)

    def post(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Make a POST request."""
        return self.request("POST", path, params=params, json=json, **kwargs)

    def put(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Make a PUT request."""
        return self.request("PUT", path, params=params, json=json, **kwargs)

    def patch(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Make a PATCH request."""
        return self.request("PATCH", path, params=params, json=json, **kwargs)

    def delete(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Make a DELETE request."""
        return self.request("DELETE", path, params=params, **kwargs)

    def close(self) -> None:
        """Close the underlying session."""
        self._session.close()

    def __enter__(self) -> "NetworkSession":
        return self

    def __exit__(self, *args) -> None:
        self.close()
