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
Alert configurations service for MongoDB Ops Manager API.

Provides read access to alert configuration rules — the policies that define
when alerts are triggered, what thresholds apply, and who is notified.

Distinct from the Alerts service (which surfaces active alert instances).
This service answers "what are our alerting policies?" rather than "what is
currently firing?". Critical for governance and compliance reporting.

See: https://www.mongodb.com/docs/ops-manager/current/reference/api/alert-configurations/
"""

from typing import Any, Dict, List, Optional

from opsmanager.services.base import BaseService
from opsmanager.types import Alert, AlertConfiguration
from opsmanager.pagination import PageIterator


class AlertConfigurationsService(BaseService):
    """Service for reading alert configuration rules.

    Alert configurations define the conditions under which alerts fire
    (event type, metric threshold, matchers) and how notifications are sent.
    Use this service to audit alerting coverage and policy compliance.
    """

    def list(
        self,
        project_id: str,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> List[AlertConfiguration]:
        """Get all alert configurations for a project.

        Args:
            project_id: Project (group) ID.
            items_per_page: Number of items per page.
            as_obj: Return AlertConfiguration objects if True, dicts if False.

        Returns:
            List of alert configurations.
        """
        return self._fetch_all(
            path=f"groups/{project_id}/alertConfigs",
            item_type=AlertConfiguration if as_obj else None,
            items_per_page=items_per_page,
        )

    def list_iter(
        self,
        project_id: str,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> PageIterator[AlertConfiguration]:
        """Iterate over alert configurations for a project.

        Args:
            project_id: Project (group) ID.
            items_per_page: Number of items per page.
            as_obj: Return AlertConfiguration objects if True, dicts if False.

        Returns:
            Iterator over alert configurations.
        """
        return self._paginate(
            path=f"groups/{project_id}/alertConfigs",
            item_type=AlertConfiguration if as_obj else None,
            items_per_page=items_per_page,
        )

    def get(
        self,
        project_id: str,
        alert_config_id: str,
        as_obj: bool = True,
    ) -> AlertConfiguration:
        """Get a single alert configuration by ID.

        Args:
            project_id: Project (group) ID.
            alert_config_id: Alert configuration ID.
            as_obj: Return AlertConfiguration object if True, dict if False.

        Returns:
            Alert configuration details.
        """
        response = self._get(f"groups/{project_id}/alertConfigs/{alert_config_id}")
        return AlertConfiguration.from_dict(response) if as_obj else response

    def get_open_alerts(
        self,
        project_id: str,
        alert_config_id: str,
        as_obj: bool = True,
    ) -> List[Alert]:
        """Get all open alerts triggered by a specific alert configuration.

        Returns the active alert instances that were created by this configuration.
        Useful for answering "what is currently firing for this alert rule?"

        Args:
            project_id: Project (group) ID.
            alert_config_id: Alert configuration ID.
            as_obj: Return Alert objects if True, dicts if False.

        Returns:
            List of open alerts for this configuration.
        """
        response = self._get(
            f"groups/{project_id}/alertConfigs/{alert_config_id}/alerts"
        )
        results = response.get("results", [response]) if isinstance(response, dict) else [response]
        if as_obj:
            return [Alert.from_dict(item) for item in results]
        return results

    def list_matcher_fields(self) -> List[str]:
        """Get all valid field names that can be used in alert configuration matchers.

        Returns the list of field names supported by the Ops Manager API for
        scoping alert configurations to specific resources.

        Returns:
            List of valid matcher field name strings.
        """
        response = self._get("alertConfigs/matchers/fieldNames")
        if isinstance(response, list):
            return response
        return response.get("results", [])
