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
Server usage service for MongoDB Ops Manager API.

Provides access to server usage and host assignment data for license
compliance and capacity reporting. Banks and regulated institutions often
have strict software licensing obligations and need to report server counts,
types, and assignments for compliance with licensing agreements.

See: https://www.mongodb.com/docs/ops-manager/current/reference/api/usage/
"""

from typing import Any, Dict, List, Optional

from opsmanager.services.base import BaseService
from opsmanager.types import HostAssignment, ServerType


class ServerUsageService(BaseService):
    """Service for server usage and license compliance reporting.

    Provides host assignment data at the global, organization, and project
    level. Use the ``download_report`` method to get a full usage report
    suitable for license audits.
    """

    def list_all_host_assignments(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        as_obj: bool = True,
    ) -> List[HostAssignment]:
        """Get host assignments across the entire Ops Manager deployment.

        Returns all host-to-server-type assignments for all organizations
        and projects. Use for fleet-wide license compliance reporting.

        Args:
            start_date: ISO 8601 start of reporting period.
            end_date: ISO 8601 end of reporting period.
            as_obj: Return HostAssignment objects if True, dicts if False.

        Returns:
            List of host assignments.
        """
        params = self._build_params(start_date=start_date, end_date=end_date)
        response = self._get("usage/assignments", params=params or None)
        results = response.get("results", [])
        if as_obj:
            return [HostAssignment.from_dict(item) for item in results]
        return results

    def get_project_host_assignments(
        self,
        project_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        as_obj: bool = True,
    ) -> List[HostAssignment]:
        """Get host assignments for a specific project.

        Args:
            project_id: Project (group) ID.
            start_date: ISO 8601 start of reporting period.
            end_date: ISO 8601 end of reporting period.
            as_obj: Return HostAssignment objects if True, dicts if False.

        Returns:
            List of host assignments for the project.
        """
        params = self._build_params(start_date=start_date, end_date=end_date)
        response = self._get(
            f"usage/groups/{project_id}/hosts", params=params or None
        )
        results = response.get("results", [])
        if as_obj:
            return [HostAssignment.from_dict(item) for item in results]
        return results

    def get_organization_host_assignments(
        self,
        org_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        as_obj: bool = True,
    ) -> List[HostAssignment]:
        """Get host assignments for a specific organization.

        Args:
            org_id: Organization ID.
            start_date: ISO 8601 start of reporting period.
            end_date: ISO 8601 end of reporting period.
            as_obj: Return HostAssignment objects if True, dicts if False.

        Returns:
            List of host assignments for the organization.
        """
        params = self._build_params(start_date=start_date, end_date=end_date)
        response = self._get(
            f"usage/organizations/{org_id}/hosts", params=params or None
        )
        results = response.get("results", [])
        if as_obj:
            return [HostAssignment.from_dict(item) for item in results]
        return results

    def get_project_server_type(
        self,
        project_id: str,
        as_obj: bool = True,
    ) -> ServerType:
        """Get the default server type for a project.

        Args:
            project_id: Project (group) ID.
            as_obj: Return ServerType object if True, dict if False.

        Returns:
            Default server type for the project.
        """
        response = self._get(f"usage/groups/{project_id}/defaultServerType")
        return ServerType.from_dict(response) if as_obj else response

    def get_organization_server_type(
        self,
        org_id: str,
        as_obj: bool = True,
    ) -> ServerType:
        """Get the default server type for an organization.

        Args:
            org_id: Organization ID.
            as_obj: Return ServerType object if True, dict if False.

        Returns:
            Default server type for the organization.
        """
        response = self._get(f"usage/organizations/{org_id}/defaultServerType")
        return ServerType.from_dict(response) if as_obj else response

    def download_report(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> bytes:
        """Download the full server usage report as a gzip archive.

        Returns a compressed report suitable for license audit submissions.
        Write the returned bytes to a ``.tar.gz`` file.

        Args:
            start_date: ISO 8601 start of reporting period.
            end_date: ISO 8601 end of reporting period.

        Returns:
            Raw gzip-compressed report bytes.
        """
        params = self._build_params(start_date=start_date, end_date=end_date)
        return self._download("usage/report", params=params or None)

    @staticmethod
    def _build_params(
        start_date: Optional[str],
        end_date: Optional[str],
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
        return params
