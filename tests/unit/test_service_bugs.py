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
Unit tests for known bugs and test coverage gaps identified in CODE_REVIEW.md.

Each test class is tagged with the review issue ID it covers.
"""

import pytest
from unittest.mock import MagicMock, call


# ---------------------------------------------------------------------------
# BUG-1: alert_configurations.get_open_alerts() wrong fallback
# ---------------------------------------------------------------------------

class TestAlertConfigGetOpenAlerts:
    """BUG-1: get_open_alerts() wraps response in list when 'results' key missing."""

    def _make_service(self):
        from opsmanager.services.alert_configurations import AlertConfigurationsService
        session = MagicMock()
        return AlertConfigurationsService(session), session

    def test_normal_paginated_response(self):
        """Normal response with 'results' key works correctly."""
        svc, session = self._make_service()
        session.get.return_value = {
            "results": [
                {"id": "alert1", "status": "OPEN", "eventTypeName": "HOST_DOWN",
                 "created": "2026-01-01", "updated": "2026-01-01", "groupId": "g1"},
            ],
            "totalCount": 1,
        }
        alerts = svc.get_open_alerts("proj1", "config1", as_obj=False)
        assert len(alerts) == 1
        assert alerts[0]["id"] == "alert1"

    def test_response_without_results_key_should_return_empty(self):
        """BUG-1: Response without 'results' should return [], not [response].

        Currently returns [response_dict] which creates a bogus Alert object.
        This test documents the expected behavior — it will FAIL until BUG-1 is fixed.
        """
        svc, session = self._make_service()
        # API returns a dict without 'results' key (e.g. error shape or empty response)
        session.get.return_value = {
            "totalCount": 0,
            "links": [{"rel": "self", "href": "..."}],
        }
        alerts = svc.get_open_alerts("proj1", "config1", as_obj=False)
        # Expected: empty list. BUG-1 causes this to be [entire_response_dict]
        assert alerts == [], (
            f"BUG-1: Expected empty list but got {len(alerts)} items. "
            f"get_open_alerts() wraps entire response in list when 'results' key is missing."
        )

    def test_empty_results_returns_empty_list(self):
        """Empty 'results' array returns empty list."""
        svc, session = self._make_service()
        session.get.return_value = {"results": [], "totalCount": 0}
        alerts = svc.get_open_alerts("proj1", "config1", as_obj=False)
        assert alerts == []


# ---------------------------------------------------------------------------
# BUG-2: performance_advisor NExamples casing
# ---------------------------------------------------------------------------

class TestPerformanceAdvisorNExamples:
    """Verify NExamples casing matches the Go SDK (uppercase N is correct).

    The Go SDK uses `NExamples` (uppercase N) per:
    opsmngr/performance_advisor.go: `url:"NExamples,omitempty"`
    This is NOT a bug — the Ops Manager API expects uppercase N.
    """

    def _make_service(self):
        from opsmanager.services.performance_advisor import PerformanceAdvisorService
        session = MagicMock()
        return PerformanceAdvisorService(session), session

    def test_suggested_indexes_sends_NExamples_uppercase(self):
        """NExamples uses uppercase N, matching the Go SDK and OM API."""
        svc, session = self._make_service()
        session.get.return_value = {
            "suggestedIndexes": [],
            "shapes": [],
        }
        svc.get_suggested_indexes(
            project_id="proj1",
            host_id="host1:27017",
            n_examples=5,
        )
        actual_params = session.get.call_args
        params_sent = actual_params[1].get("params", {}) if actual_params[1] else {}

        assert "NExamples" in params_sent, (
            f"Expected 'NExamples' (uppercase N, matching Go SDK) but got keys: {list(params_sent.keys())}"
        )
        assert params_sent.get("NExamples") == 5

    def test_perf_advisor_options_to_params_uses_NExamples(self):
        """PerformanceAdvisorOptions.to_params() uses uppercase N, matching Go SDK."""
        try:
            from opsmanager.services.performance_advisor import PerformanceAdvisorOptions
            opts = PerformanceAdvisorOptions(n_examples=3)
            params = opts.to_params()
            assert "NExamples" in params, (
                f"Expected 'NExamples' (uppercase N) but got keys: {list(params.keys())}"
            )
            assert params["NExamples"] == 3
        except ImportError:
            pytest.skip("PerformanceAdvisorOptions not found")


# ---------------------------------------------------------------------------
# PAG-1: maintenance_windows.list() not paginated
# ---------------------------------------------------------------------------

class TestMaintenanceWindowsPagination:
    """PAG-1: Verify maintenance_windows.list() paginates correctly."""

    def _make_service(self):
        from opsmanager.services.maintenance_windows import MaintenanceWindowsService
        session = MagicMock()
        return MaintenanceWindowsService(session), session

    def test_list_fetches_multiple_pages(self):
        """PAG-1 FIXED: list() now uses _fetch_all and paginates."""
        svc, session = self._make_service()
        page1 = [{"id": f"mw-{i}", "startDate": "2026-01-01", "endDate": "2026-01-02"}
                 for i in range(3)]
        page2 = [{"id": "mw-3", "startDate": "2026-01-01", "endDate": "2026-01-02"}]
        session.get.side_effect = [
            {"results": page1, "totalCount": 4},
            {"results": page2, "totalCount": 4},
        ]
        result = svc.list("proj1", items_per_page=3, as_obj=False)
        assert len(result) == 4
        assert session.get.call_count == 2


# ---------------------------------------------------------------------------
# PAG-3: teams.list_users() pagination
# ---------------------------------------------------------------------------

class TestTeamsListUsersPagination:
    """PAG-3: Verify teams.list_users() paginates correctly."""

    def _make_service(self):
        from opsmanager.services.teams import TeamsService
        session = MagicMock()
        return TeamsService(session), session

    def test_list_users_fetches_multiple_pages(self):
        """PAG-3 FIXED: list_users() now uses _fetch_all and paginates."""
        svc, session = self._make_service()
        page1 = [{"id": f"user-{i}", "username": f"user{i}@example.com",
                  "firstName": "User", "lastName": str(i)} for i in range(3)]
        page2 = [{"id": "user-3", "username": "user3@example.com",
                  "firstName": "User", "lastName": "3"}]
        session.get.side_effect = [
            {"results": page1, "totalCount": 4},
            {"results": page2, "totalCount": 4},
        ]
        result = svc.list_users("org1", "team1", items_per_page=3, as_obj=False)
        assert len(result) == 4
        assert session.get.call_count == 2


# ---------------------------------------------------------------------------
# PAG-4: alert_configurations.get_open_alerts() pagination
# ---------------------------------------------------------------------------

class TestAlertConfigPagination:
    """PAG-4: Verify get_open_alerts() paginates correctly."""

    def _make_service(self):
        from opsmanager.services.alert_configurations import AlertConfigurationsService
        session = MagicMock()
        return AlertConfigurationsService(session), session

    def test_get_open_alerts_fetches_multiple_pages(self):
        """PAG-4 FIXED: get_open_alerts() now uses _fetch_all and paginates."""
        svc, session = self._make_service()
        # _fetch_all uses items_per_page=100 by default, so use 100-item pages
        page1 = [{"id": f"alert-{i}", "status": "OPEN", "eventTypeName": "HOST_DOWN",
                  "created": "2026-01-01", "updated": "2026-01-01", "groupId": "g1"}
                 for i in range(100)]
        page2 = [{"id": "alert-100", "status": "OPEN", "eventTypeName": "HOST_DOWN",
                  "created": "2026-01-01", "updated": "2026-01-01", "groupId": "g1"}]
        session.get.side_effect = [
            {"results": page1, "totalCount": 101},
            {"results": page2, "totalCount": 101},
        ]
        result = svc.get_open_alerts("proj1", "config1", as_obj=False)
        assert len(result) == 101
        assert session.get.call_count == 2


# ---------------------------------------------------------------------------
# SEC-1: APIKey.to_dict() exposes private_key
# ---------------------------------------------------------------------------

class TestAPIKeyPrivateKeyExposure:
    """SEC-1: APIKey.to_dict() includes private_key in output."""

    def test_to_dict_should_not_expose_private_key(self):
        """SEC-1: If private_key is set, to_dict() should mask or omit it.

        This test documents the expected behavior — it will FAIL until SEC-1 is fixed.
        """
        from opsmanager.types import APIKey
        key = APIKey(
            id="key1",
            public_key="abc123",
            desc="test key",
            roles=[],
            private_key="super-secret-private-key",
        )
        d = key.to_dict()
        assert d.get("private_key") != "super-secret-private-key", (
            "SEC-1: APIKey.to_dict() exposes private_key in plaintext. "
            "Should mask or omit the private_key field."
        )


# ---------------------------------------------------------------------------
# TYPE-4: Cluster.from_dict() non-idiomatic enum check
# ---------------------------------------------------------------------------

class TestClusterUnknownType:
    """TYPE-4: Cluster.from_dict() with unknown cluster type should default gracefully."""

    def test_unknown_cluster_type_defaults_to_replica_set(self):
        """Verify unknown type_name doesn't crash and defaults to REPLICA_SET."""
        from opsmanager.types import Cluster, ClusterType
        data = {
            "id": "c1",
            "typeName": "SOME_FUTURE_TYPE",
            "clusterName": "test-cluster",
            "groupId": "g1",
        }
        cluster = Cluster.from_dict(data)
        assert cluster.type_name == ClusterType.REPLICA_SET

    def test_known_cluster_type_works(self):
        """Known type_name values are properly parsed."""
        from opsmanager.types import Cluster, ClusterType
        data = {
            "id": "c1",
            "typeName": "SHARDED_REPLICA_SET",
            "clusterName": "test-cluster",
            "groupId": "g1",
        }
        cluster = Cluster.from_dict(data)
        assert cluster.type_name == ClusterType.SHARDED_REPLICA_SET


# ---------------------------------------------------------------------------
# DEAD-4: PerformanceAdvisorOptions exists but is unused
# ---------------------------------------------------------------------------

class TestPerformanceAdvisorOptionsUnused:
    """DEAD-4: PerformanceAdvisorOptions is defined but no service method accepts it."""

    def test_options_class_exists_but_no_method_uses_it(self):
        """Document that PerformanceAdvisorOptions is dead code."""
        from opsmanager.services.performance_advisor import PerformanceAdvisorService
        import inspect

        # Check that no method accepts an 'options' parameter of type PerformanceAdvisorOptions
        for name, method in inspect.getmembers(PerformanceAdvisorService, predicate=inspect.isfunction):
            if name.startswith("_"):
                continue
            sig = inspect.signature(method)
            param_names = list(sig.parameters.keys())
            assert "options" not in param_names, (
                f"DEAD-4: {name}() accepts 'options' parameter — "
                f"PerformanceAdvisorOptions may no longer be dead code."
            )
