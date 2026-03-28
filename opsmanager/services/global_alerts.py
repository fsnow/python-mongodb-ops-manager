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
Global alerts service for MongoDB Ops Manager API.

Provides access to global alerts that span all projects in an Ops Manager
deployment. Complements the project-scoped AlertsService for enterprise-wide
monitoring dashboards and reporting.

See: https://www.mongodb.com/docs/ops-manager/current/reference/api/global-alerts/
"""

from typing import Any, Dict, List, Optional

from opsmanager.services.base import BaseService
from opsmanager.types import Alert
from opsmanager.pagination import PageIterator


class GlobalAlertsService(BaseService):
    """Service for accessing global alerts across all projects.

    Global alerts are raised at the Ops Manager instance level rather than
    at the project level. Use this service alongside the project-scoped
    AlertsService for complete alert coverage.
    """

    def list(
        self,
        status: Optional[str] = None,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> List[Alert]:
        """Get all global alerts.

        Args:
            status: Filter by status (``OPEN``, ``CLOSED``, ``TRACKING``).
            items_per_page: Number of items per page.
            as_obj: Return Alert objects if True, dicts if False.

        Returns:
            List of global alerts.
        """
        params: Dict[str, Any] = {}
        if status:
            params["status"] = status
        return self._fetch_all(
            path="globalAlerts",
            item_type=Alert if as_obj else None,
            params=params,
            items_per_page=items_per_page,
        )

    def list_iter(
        self,
        status: Optional[str] = None,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> PageIterator[Alert]:
        """Iterate over global alerts.

        Args:
            status: Filter by status.
            items_per_page: Number of items per page.
            as_obj: Return Alert objects if True, dicts if False.

        Returns:
            Iterator over global alerts.
        """
        params: Dict[str, Any] = {}
        if status:
            params["status"] = status
        return self._paginate(
            path="globalAlerts",
            item_type=Alert if as_obj else None,
            params=params,
            items_per_page=items_per_page,
        )

    def get(
        self,
        alert_id: str,
        as_obj: bool = True,
    ) -> Alert:
        """Get a single global alert by ID.

        Args:
            alert_id: Alert ID.
            as_obj: Return Alert object if True, dict if False.

        Returns:
            Alert details.
        """
        response = self._get(f"globalAlerts/{alert_id}")
        return Alert.from_dict(response) if as_obj else response

    def list_open(
        self,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> List[Alert]:
        """Get all open global alerts.

        Convenience method that filters by ``OPEN`` status.

        Args:
            items_per_page: Number of items per page.
            as_obj: Return Alert objects if True, dicts if False.

        Returns:
            List of open global alerts.
        """
        return self.list(status="OPEN", items_per_page=items_per_page, as_obj=as_obj)
