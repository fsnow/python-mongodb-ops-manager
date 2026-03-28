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

"""Unit tests for MeasurementsService parameter validation."""

import pytest
from unittest.mock import MagicMock

from opsmanager.services.measurements import MeasurementsService


def _make_service():
    """Build a MeasurementsService with a mocked session."""
    session = MagicMock()
    session.get.return_value = {
        "measurements": [],
        "hostId": "h1",
        "processId": "h1:27017",
    }
    return MeasurementsService(session)


class TestHostMeasurementValidation:
    def test_period_and_start_raises(self):
        svc = _make_service()
        with pytest.raises(ValueError, match="mutually exclusive"):
            svc.host("proj", "host1", period="P1D", start="2024-01-01T00:00:00Z")

    def test_period_and_end_raises(self):
        svc = _make_service()
        with pytest.raises(ValueError, match="mutually exclusive"):
            svc.host("proj", "host1", period="P1D", end="2024-01-02T00:00:00Z")

    def test_start_without_end_raises(self):
        svc = _make_service()
        with pytest.raises(ValueError, match="both be provided"):
            svc.host("proj", "host1", period=None, start="2024-01-01T00:00:00Z")

    def test_end_without_start_raises(self):
        svc = _make_service()
        with pytest.raises(ValueError, match="both be provided"):
            svc.host("proj", "host1", period=None, end="2024-01-02T00:00:00Z")

    def test_period_alone_valid(self):
        svc = _make_service()
        svc.host("proj", "host1", period="P1D")  # should not raise

    def test_start_and_end_valid(self):
        svc = _make_service()
        svc.host(
            "proj", "host1",
            period=None,
            start="2024-01-01T00:00:00Z",
            end="2024-01-02T00:00:00Z",
        )  # should not raise

    def test_neither_valid(self):
        svc = _make_service()
        svc.host("proj", "host1", period=None)  # should not raise


class TestDatabaseMeasurementValidation:
    def test_period_and_start_raises(self):
        svc = _make_service()
        with pytest.raises(ValueError, match="mutually exclusive"):
            svc.database("proj", "host1", "mydb", period="P1D", start="2024-01-01T00:00:00Z")

    def test_start_without_end_raises(self):
        svc = _make_service()
        with pytest.raises(ValueError, match="both be provided"):
            svc.database("proj", "host1", "mydb", period=None, start="2024-01-01T00:00:00Z")

    def test_start_and_end_valid(self):
        svc = _make_service()
        svc.database(
            "proj", "host1", "mydb",
            period=None,
            start="2024-01-01T00:00:00Z",
            end="2024-01-02T00:00:00Z",
        )


class TestDiskMeasurementValidation:
    def test_period_and_start_raises(self):
        svc = _make_service()
        with pytest.raises(ValueError, match="mutually exclusive"):
            svc.disk("proj", "host1", "xvda", period="P1D", start="2024-01-01T00:00:00Z")

    def test_start_without_end_raises(self):
        svc = _make_service()
        with pytest.raises(ValueError, match="both be provided"):
            svc.disk("proj", "host1", "xvda", period=None, start="2024-01-01T00:00:00Z")

    def test_start_and_end_valid(self):
        svc = _make_service()
        svc.disk(
            "proj", "host1", "xvda",
            period=None,
            start="2024-01-01T00:00:00Z",
            end="2024-01-02T00:00:00Z",
        )
