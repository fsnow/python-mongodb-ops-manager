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
from opsmanager.types import BackupConfig, Checkpoint, RestoreJob, Snapshot, SnapshotSchedule
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

    def list_backup_configs(
        self,
        project_id: str,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> List[BackupConfig]:
        """Get backup configurations for all clusters in a project.

        Returns the backup configuration for every cluster in the project.
        Use this to check backup coverage — any cluster absent from the results
        or with ``statusName != "STARTED"`` is not being backed up.

        Args:
            project_id: Project (group) ID.
            items_per_page: Number of items per page.
            as_obj: Return BackupConfig objects if True, dicts if False.

        Returns:
            List of backup configurations, one per cluster.
        """
        return self._fetch_all(
            path=f"groups/{project_id}/backupConfigs",
            item_type=BackupConfig if as_obj else None,
            items_per_page=items_per_page,
        )

    def get_backup_config(
        self,
        project_id: str,
        cluster_id: str,
        as_obj: bool = True,
    ) -> BackupConfig:
        """Get the backup configuration for a specific cluster.

        Args:
            project_id: Project (group) ID.
            cluster_id: Cluster ID.
            as_obj: Return BackupConfig object if True, dict if False.

        Returns:
            Backup configuration for the cluster.
        """
        response = self._get(f"groups/{project_id}/backupConfigs/{cluster_id}")
        return BackupConfig.from_dict(response) if as_obj else response

    def get_snapshot_schedule(
        self,
        project_id: str,
        cluster_id: str,
        as_obj: bool = True,
    ) -> SnapshotSchedule:
        """Get the snapshot retention schedule for a cluster.

        Returns the snapshot frequency and retention policy. This is the
        primary document for evidencing backup retention compliance — e.g.,
        "snapshots are taken every 6 hours and retained for 7 days".

        Args:
            project_id: Project (group) ID.
            cluster_id: Cluster ID.
            as_obj: Return SnapshotSchedule object if True, dict if False.

        Returns:
            Snapshot schedule with retention periods.
        """
        response = self._get(
            f"groups/{project_id}/backupConfigs/{cluster_id}/snapshotSchedule"
        )
        return SnapshotSchedule.from_dict(response) if as_obj else response

    def list_restore_jobs(
        self,
        project_id: str,
        cluster_id: str,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> List[RestoreJob]:
        """Get all restore jobs for a cluster.

        Returns the history of restore operations. Use this to document
        DR test results — evidence that backups have been successfully
        restored as required by continuity planning obligations.

        Args:
            project_id: Project (group) ID.
            cluster_id: Cluster ID.
            items_per_page: Number of items per page.
            as_obj: Return RestoreJob objects if True, dicts if False.

        Returns:
            List of restore jobs.
        """
        return self._fetch_all(
            path=f"groups/{project_id}/clusters/{cluster_id}/restoreJobs",
            item_type=RestoreJob if as_obj else None,
            items_per_page=items_per_page,
        )

    def get_restore_job(
        self,
        project_id: str,
        cluster_id: str,
        job_id: str,
        as_obj: bool = True,
    ) -> RestoreJob:
        """Get a single restore job by ID.

        Args:
            project_id: Project (group) ID.
            cluster_id: Cluster ID.
            job_id: Restore job ID.
            as_obj: Return RestoreJob object if True, dict if False.

        Returns:
            Restore job details.
        """
        response = self._get(
            f"groups/{project_id}/clusters/{cluster_id}/restoreJobs/{job_id}"
        )
        return RestoreJob.from_dict(response) if as_obj else response

    def list_checkpoints(
        self,
        project_id: str,
        cluster_name: str,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> List[Checkpoint]:
        """Get all backup checkpoints for a sharded cluster.

        Checkpoints are created between snapshots for sharded clusters, allowing
        point-in-time restores at finer granularity than snapshot intervals.

        Args:
            project_id: Project (group) ID.
            cluster_name: Cluster name (not ID — the API uses name here).
            items_per_page: Number of items per page.
            as_obj: Return Checkpoint objects if True, dicts if False.

        Returns:
            List of checkpoints.
        """
        return self._fetch_all(
            path=f"groups/{project_id}/clusters/{cluster_name}/checkpoints",
            item_type=Checkpoint if as_obj else None,
            items_per_page=items_per_page,
        )

    def get_checkpoint(
        self,
        project_id: str,
        cluster_id: str,
        checkpoint_id: str,
        as_obj: bool = True,
    ) -> Checkpoint:
        """Get a single checkpoint by ID.

        Note: This method takes cluster_id (not cluster_name), unlike
        list_checkpoints() which takes cluster_name. This reflects the
        Ops Manager API inconsistency.

        Args:
            project_id: Project (group) ID.
            cluster_id: Cluster ID (not name — see list_checkpoints()).
            checkpoint_id: Checkpoint ID.
            as_obj: Return Checkpoint object if True, dict if False.

        Returns:
            Checkpoint details.
        """
        response = self._get(
            f"groups/{project_id}/clusters/{cluster_id}/checkpoints/{checkpoint_id}"
        )
        return Checkpoint.from_dict(response) if as_obj else response
