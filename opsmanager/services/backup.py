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
Backup service for MongoDB Ops Manager API.

Provides access to backup snapshots and backup configuration.

See: https://docs.opsmanager.mongodb.com/current/reference/api/snapshots/
"""

from typing import Any, Dict, List, Optional

from opsmanager.services.base import BaseService
from opsmanager.types import Snapshot
from opsmanager.pagination import PageIterator


class BackupService(BaseService):
    """Service for querying backup snapshots and configuration.

    Backup lag is not available as a direct metric. Instead, lag is derived
    by comparing the most recent snapshot's created.date against the expected
    snapshot frequency in the backup configuration.
    """

    def list_snapshots(
        self,
        project_id: str,
        cluster_id: str,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> List[Snapshot]:
        """Get all snapshots for a cluster.

        Args:
            project_id: Project (group) ID.
            cluster_id: Cluster ID.
            items_per_page: Number of items per page.
            as_obj: Return Snapshot objects if True, dicts if False.

        Returns:
            List of snapshots, most recent first.
        """
        return self._fetch_all(
            path=f"groups/{project_id}/clusters/{cluster_id}/snapshots",
            item_type=Snapshot if as_obj else None,
            items_per_page=items_per_page,
        )

    def list_snapshots_iter(
        self,
        project_id: str,
        cluster_id: str,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> PageIterator[Snapshot]:
        """Iterate over snapshots for a cluster.

        Args:
            project_id: Project (group) ID.
            cluster_id: Cluster ID.
            items_per_page: Number of items per page.
            as_obj: Return Snapshot objects if True, dicts if False.

        Returns:
            Iterator over snapshots.
        """
        return self._paginate(
            path=f"groups/{project_id}/clusters/{cluster_id}/snapshots",
            item_type=Snapshot if as_obj else None,
            items_per_page=items_per_page,
        )

    def get_snapshot(
        self,
        project_id: str,
        cluster_id: str,
        snapshot_id: str,
        as_obj: bool = True,
    ) -> Snapshot:
        """Get a single snapshot by ID.

        Args:
            project_id: Project (group) ID.
            cluster_id: Cluster ID.
            snapshot_id: Snapshot ID.
            as_obj: Return Snapshot object if True, dict if False.

        Returns:
            Snapshot details.
        """
        response = self._get(
            f"groups/{project_id}/clusters/{cluster_id}/snapshots/{snapshot_id}"
        )
        return Snapshot.from_dict(response) if as_obj else response

    def get_backup_config(
        self,
        project_id: str,
        cluster_id: str,
    ) -> Dict[str, Any]:
        """Get the backup configuration for a cluster.

        The backup config includes the snapshot schedule, which is needed
        to calculate backup lag (compare last snapshot time against frequency).

        Args:
            project_id: Project (group) ID.
            cluster_id: Cluster ID.

        Returns:
            Backup configuration as a dict (raw API response).
        """
        return self._get(f"groups/{project_id}/backupConfigs/{cluster_id}")
