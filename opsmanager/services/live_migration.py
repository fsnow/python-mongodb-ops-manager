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
Live data migration service for MongoDB Ops Manager API.

Provides read access to the live data migration connection status for an
organization. Useful for monitoring ongoing Atlas live migrations.

See: https://www.mongodb.com/docs/ops-manager/current/reference/api/
"""

from typing import Any, Dict

from opsmanager.services.base import BaseService
from opsmanager.types import ConnectionStatus


class LiveMigrationService(BaseService):
    """Service for live data migration status.

    Provides read access to the migration link connection status for an
    organization. Useful for monitoring the state of Atlas live migrations.
    """

    def get_connection_status(
        self,
        org_id: str,
        as_obj: bool = True,
    ) -> ConnectionStatus:
        """Get the live migration connection status for an organization.

        Returns the current connection status of the live data migration
        link for the given organization.

        Args:
            org_id: Organization ID.
            as_obj: Return ConnectionStatus object if True, dict if False.

        Returns:
            Connection status for the live migration link.
        """
        response = self._get(f"orgs/{org_id}/liveExport/migrationLink/status")
        return ConnectionStatus.from_dict(response) if as_obj else response
