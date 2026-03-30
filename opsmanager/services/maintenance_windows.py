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
Maintenance windows service for MongoDB Ops Manager API.

Provides read access to scheduled maintenance windows. Maintenance windows
suppress alerts during known downtime periods. Reading them is important for
change management documentation and CAB (Change Advisory Board) submissions.

See: https://www.mongodb.com/docs/ops-manager/current/reference/api/maintenance-windows/
"""

from typing import Any, Dict, List

from opsmanager.services.base import BaseService
from opsmanager.types import MaintenanceWindow
from opsmanager.pagination import PageIterator


class MaintenanceWindowsService(BaseService):
    """Service for reading scheduled maintenance windows.

    Maintenance windows define periods during which alerts are suppressed.
    Use this service to enumerate scheduled maintenance for reporting,
    change management documentation, or DR planning.
    """

    def list(
        self,
        project_id: str,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> List[MaintenanceWindow]:
        """Get all maintenance windows for a project.

        Args:
            project_id: Project (group) ID.
            items_per_page: Number of items per page.
            as_obj: Return MaintenanceWindow objects if True, dicts if False.

        Returns:
            List of maintenance windows.
        """
        return self._fetch_all(
            path=f"groups/{project_id}/maintenanceWindows",
            item_type=MaintenanceWindow if as_obj else None,
            items_per_page=items_per_page,
        )

    def get(
        self,
        project_id: str,
        maintenance_window_id: str,
        as_obj: bool = True,
    ) -> MaintenanceWindow:
        """Get a single maintenance window by ID.

        Args:
            project_id: Project (group) ID.
            maintenance_window_id: Maintenance window ID.
            as_obj: Return MaintenanceWindow object if True, dict if False.

        Returns:
            Maintenance window details.
        """
        response = self._get(
            f"groups/{project_id}/maintenanceWindows/{maintenance_window_id}"
        )
        return MaintenanceWindow.from_dict(response) if as_obj else response
