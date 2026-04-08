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

"""Unit tests for the RateLimiter class."""

import time
import pytest
from unittest.mock import patch

from opsmanager.network import RateLimiter


class TestRateLimiterStrictMode:
    """Tests for RateLimiter in strict mode (burst=1)."""

    def test_first_request_immediate(self):
        """First request should be granted immediately."""
        limiter = RateLimiter(rate=2.0, burst=1)
        result = limiter.acquire(timeout=0.1)
        assert result is True

    def test_second_request_waits(self):
        """Second request within interval should wait."""
        limiter = RateLimiter(rate=10.0, burst=1)  # 100ms interval
        limiter.acquire()
        start = time.monotonic()
        limiter.acquire()
        elapsed = time.monotonic() - start
        # Should have waited roughly 100ms (allow wide margin for CI)
        assert elapsed >= 0.05

    def test_timeout_returns_false(self):
        """Acquire should return False when timeout expires."""
        limiter = RateLimiter(rate=1.0, burst=1)  # 1s interval
        limiter.acquire()  # use up the first slot
        result = limiter.acquire(timeout=0.01)  # 10ms timeout — too short
        assert result is False

    def test_set_rate_updates_limit(self):
        """set_rate should update the enforced rate."""
        limiter = RateLimiter(rate=1.0, burst=1)
        limiter.set_rate(100.0)
        assert limiter.rate == 100.0

    def test_none_timeout_waits(self):
        """None timeout means wait indefinitely (smoke test with fast rate)."""
        limiter = RateLimiter(rate=1000.0, burst=1)
        # With fast rate, two acquires should both succeed immediately
        assert limiter.acquire(timeout=None) is True
        assert limiter.acquire(timeout=None) is True


class TestRateLimiterBurstMode:
    """Tests for RateLimiter in token-bucket mode (burst>1)."""

    def test_burst_allows_multiple_immediate(self):
        """With burst=3, three requests should be granted immediately."""
        limiter = RateLimiter(rate=1.0, burst=3)
        results = [limiter.acquire(timeout=0.01) for _ in range(3)]
        assert all(results)

    def test_burst_throttles_after_burst(self):
        """After exhausting burst, next request should be delayed."""
        limiter = RateLimiter(rate=10.0, burst=2)  # 100ms interval
        limiter.acquire()
        limiter.acquire()
        # Burst exhausted — third request must wait for token replenishment
        start = time.monotonic()
        result = limiter.acquire(timeout=1.0)
        elapsed = time.monotonic() - start
        assert result is True
        assert elapsed >= 0.05, f"Expected wait after burst exhausted, got {elapsed:.3f}s"

    def test_consistent_spacing_across_requests(self):
        """Verify requests are spaced consistently at the configured rate."""
        limiter = RateLimiter(rate=20.0, burst=1)  # 50ms interval
        timestamps = []
        for _ in range(5):
            limiter.acquire()
            timestamps.append(time.monotonic())

        gaps = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps) - 1)]
        # First gap may be near-zero (first acquire is immediate), rest should be ~50ms
        for i, gap in enumerate(gaps[1:], start=2):
            assert gap >= 0.03, (
                f"Gap between request {i} and {i+1} was {gap*1000:.1f}ms, "
                f"expected ~50ms (rate=20/s)"
            )
