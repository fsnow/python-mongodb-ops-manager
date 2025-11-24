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
Performance Advisor service for MongoDB Ops Manager API.

Provides access to slow query analysis and index recommendations.
This is critical for health check reporting and performance optimization.

See: https://docs.opsmanager.mongodb.com/current/reference/api/performance-advisor/
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from opsmanager.services.base import BaseService
from opsmanager.types import Namespace, SlowQuery, SuggestedIndex, QueryShape


@dataclass
class PerformanceAdvisorOptions:
    """Options for Performance Advisor queries.

    Attributes:
        since: Point in time (milliseconds since Unix Epoch) from which to
            receive results.
        duration: Length of time from `since` in milliseconds.
        namespaces: Comma-separated list of namespaces to filter by.
        n_logs: Maximum number of slow query log lines to return.
        n_indexes: Maximum number of indexes to suggest.
        n_examples: Maximum number of example queries per suggestion.
    """
    since: Optional[int] = None
    duration: Optional[int] = None
    namespaces: Optional[str] = None
    n_logs: Optional[int] = None
    n_indexes: Optional[int] = None
    n_examples: Optional[int] = None

    def to_params(self) -> Dict[str, Any]:
        """Convert to API query parameters."""
        params = {}
        if self.since is not None:
            params["since"] = self.since
        if self.duration is not None:
            params["duration"] = self.duration
        if self.namespaces:
            params["namespaces"] = self.namespaces
        if self.n_logs is not None:
            params["nLogs"] = self.n_logs
        if self.n_indexes is not None:
            params["nIndexes"] = self.n_indexes
        if self.n_examples is not None:
            params["NExamples"] = self.n_examples
        return params


class PerformanceAdvisorService(BaseService):
    """Service for accessing Performance Advisor data.

    Provides:
    - Namespaces with slow queries
    - Slow query logs
    - Suggested indexes
    """

    def get_namespaces(
        self,
        project_id: str,
        host_id: str,
        since: Optional[int] = None,
        duration: Optional[int] = None,
        as_obj: bool = True,
    ) -> List[Union[Namespace, Dict[str, Any]]]:
        """Get namespaces experiencing slow queries.

        Args:
            project_id: Project (group) ID.
            host_id: Host ID (process ID in format hostname:port).
            since: Start time in milliseconds since Unix Epoch.
            duration: Duration in milliseconds from `since`.
            as_obj: Return Namespace objects if True, dicts if False.

        Returns:
            List of namespaces with slow queries.
        """
        params = {}
        if since is not None:
            params["since"] = since
        if duration is not None:
            params["duration"] = duration

        response = self._get(
            f"groups/{project_id}/hosts/{host_id}/performanceAdvisor/namespaces",
            params=params,
        )

        namespaces = response.get("namespaces", [])
        if as_obj:
            return [Namespace.from_dict(ns) for ns in namespaces]
        return namespaces

    def get_slow_queries(
        self,
        project_id: str,
        host_id: str,
        since: Optional[int] = None,
        duration: Optional[int] = None,
        namespaces: Optional[str] = None,
        n_logs: int = 20000,
        as_obj: bool = True,
    ) -> List[Union[SlowQuery, Dict[str, Any]]]:
        """Get slow query logs.

        Args:
            project_id: Project (group) ID.
            host_id: Host ID (process ID).
            since: Start time in milliseconds since Unix Epoch.
            duration: Duration in milliseconds from `since`.
            namespaces: Comma-separated namespace filter (e.g., "db.collection").
            n_logs: Maximum number of log lines to return (default 20000).
            as_obj: Return SlowQuery objects if True, dicts if False.

        Returns:
            List of slow query log entries.
        """
        params = {"nLogs": n_logs}
        if since is not None:
            params["since"] = since
        if duration is not None:
            params["duration"] = duration
        if namespaces:
            params["namespaces"] = namespaces

        response = self._get(
            f"groups/{project_id}/hosts/{host_id}/performanceAdvisor/slowQueryLogs",
            params=params,
        )

        queries = response.get("slowQueries", [])
        if as_obj:
            return [SlowQuery.from_dict(q) for q in queries]
        return queries

    def get_suggested_indexes(
        self,
        project_id: str,
        host_id: str,
        since: Optional[int] = None,
        duration: Optional[int] = None,
        namespaces: Optional[str] = None,
        n_indexes: Optional[int] = None,
        n_examples: int = 5,
        as_obj: bool = True,
    ) -> Dict[str, Any]:
        """Get suggested indexes.

        Returns both suggested indexes and the query shapes they would improve.

        Args:
            project_id: Project (group) ID.
            host_id: Host ID (process ID).
            since: Start time in milliseconds since Unix Epoch.
            duration: Duration in milliseconds from `since`.
            namespaces: Comma-separated namespace filter.
            n_indexes: Maximum number of indexes to suggest.
            n_examples: Maximum number of example queries per suggestion.
            as_obj: Return typed objects if True, raw dicts if False.

        Returns:
            Dictionary with 'suggestedIndexes' and 'shapes' keys.
        """
        params = {"NExamples": n_examples}
        if since is not None:
            params["since"] = since
        if duration is not None:
            params["duration"] = duration
        if namespaces:
            params["namespaces"] = namespaces
        if n_indexes is not None:
            params["nIndexes"] = n_indexes

        response = self._get(
            f"groups/{project_id}/hosts/{host_id}/performanceAdvisor/suggestedIndexes",
            params=params,
        )

        if as_obj:
            return {
                "suggested_indexes": [
                    SuggestedIndex.from_dict(idx)
                    for idx in response.get("suggestedIndexes", [])
                ],
                "shapes": [
                    QueryShape.from_dict(shape)
                    for shape in response.get("shapes", [])
                ],
            }
        return response

    # Convenience methods

    def get_all_suggestions_for_cluster(
        self,
        project_id: str,
        host_ids: List[str],
        since: Optional[int] = None,
        duration: Optional[int] = None,
        as_obj: bool = True,
    ) -> Dict[str, Any]:
        """Get suggested indexes from multiple hosts.

        Queries all provided hosts and aggregates the results.
        Useful for getting recommendations across all nodes in a replica set.

        Args:
            project_id: Project (group) ID.
            host_ids: List of host IDs to query.
            since: Start time in milliseconds since Unix Epoch.
            duration: Duration in milliseconds from `since`.
            as_obj: Return typed objects if True, raw dicts if False.

        Returns:
            Dictionary with aggregated suggestions keyed by host_id.
        """
        results = {}
        for host_id in host_ids:
            try:
                suggestions = self.get_suggested_indexes(
                    project_id=project_id,
                    host_id=host_id,
                    since=since,
                    duration=duration,
                    as_obj=as_obj,
                )
                results[host_id] = suggestions
            except Exception as e:
                # Log but continue with other hosts
                results[host_id] = {"error": str(e)}

        return results
