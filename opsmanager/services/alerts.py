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
Alerts service for MongoDB Ops Manager API.

Provides access to alerts and alert configurations.

See: https://docs.opsmanager.mongodb.com/current/reference/api/alerts/
"""

from typing import Any, Dict, List, Optional

from opsmanager.services.base import BaseService
from opsmanager.types import Alert
from opsmanager.pagination import PageIterator


class AlertsService(BaseService):
    """Service for managing alerts.

    Provides access to current alerts and the ability to acknowledge them.
    """

    # Alert status values
    STATUS_OPEN = "OPEN"
    STATUS_CLOSED = "CLOSED"
    STATUS_TRACKING = "TRACKING"

    def list(
        self,
        project_id: str,
        status: Optional[str] = None,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> List[Alert]:
        """Get all alerts in a project.

        Args:
            project_id: Project (group) ID.
            status: Filter by status (OPEN, CLOSED, TRACKING).
            items_per_page: Number of items per page.
            as_obj: Return Alert objects if True, dicts if False.

        Returns:
            List of alerts.
        """
        params = {}
        if status:
            params["status"] = status

        return self._fetch_all(
            path=f"groups/{project_id}/alerts",
            item_type=Alert if as_obj else None,
            params=params,
            items_per_page=items_per_page,
        )

    def list_iter(
        self,
        project_id: str,
        status: Optional[str] = None,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> PageIterator[Alert]:
        """Iterate over all alerts in a project.

        Args:
            project_id: Project (group) ID.
            status: Filter by status.
            items_per_page: Number of items per page.
            as_obj: Return Alert objects if True, dicts if False.

        Returns:
            Iterator over alerts.
        """
        params = {}
        if status:
            params["status"] = status

        return self._paginate(
            path=f"groups/{project_id}/alerts",
            item_type=Alert if as_obj else None,
            params=params,
            items_per_page=items_per_page,
        )

    def get(
        self,
        project_id: str,
        alert_id: str,
        as_obj: bool = True,
    ) -> Alert:
        """Get a single alert by ID.

        Args:
            project_id: Project (group) ID.
            alert_id: Alert ID.
            as_obj: Return Alert object if True, dict if False.

        Returns:
            Alert details.
        """
        response = self._get(f"groups/{project_id}/alerts/{alert_id}")
        return Alert.from_dict(response) if as_obj else response

    def acknowledge(
        self,
        project_id: str,
        alert_id: str,
        acknowledge_until: str,
        comment: Optional[str] = None,
    ) -> Alert:
        """Acknowledge an alert.

        Args:
            project_id: Project (group) ID.
            alert_id: Alert ID.
            acknowledge_until: ISO 8601 timestamp until which to acknowledge.
            comment: Optional comment explaining the acknowledgement.

        Returns:
            Updated alert.
        """
        body = {"acknowledgedUntil": acknowledge_until}
        if comment:
            body["acknowledgementComment"] = comment

        response = self._patch(
            f"groups/{project_id}/alerts/{alert_id}",
            json=body,
        )
        return Alert.from_dict(response)

    def list_open(
        self,
        project_id: str,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> List[Alert]:
        """Get all open alerts in a project.

        Convenience method for filtering by OPEN status.

        Args:
            project_id: Project (group) ID.
            items_per_page: Number of items per page.
            as_obj: Return Alert objects if True, dicts if False.

        Returns:
            List of open alerts.
        """
        return self.list(
            project_id=project_id,
            status=self.STATUS_OPEN,
            items_per_page=items_per_page,
            as_obj=as_obj,
        )
