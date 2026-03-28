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
Admin backup store configuration services for MongoDB Ops Manager API.

Provides read access to all admin backup store configurations:
blockstores, S3 blockstores, file system stores, oplog stores, sync stores,
backup daemons, and project job configurations.

These are admin-level endpoints requiring global owner or backup admin role.

See: https://www.mongodb.com/docs/ops-manager/current/reference/api/admin/
"""

from typing import List

from opsmanager.services.base import BaseService
from opsmanager.types import (
    BackupStore,
    S3BlockstoreConfig,
    FileSystemStoreConfig,
    DaemonConfig,
    ProjectJobConfig,
)
from opsmanager.pagination import PageIterator


class AdminBackupStoresService(BaseService):
    """Service for admin backup store configuration reads.

    Provides List and Get access to all backup infrastructure configuration:
    blockstores, S3 stores, file system stores, oplog stores, sync stores,
    daemons, and project job configs. Useful for backup infrastructure audits.
    """

    # ---- Blockstore configs ----

    def list_blockstores(
        self,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> List[BackupStore]:
        """Get all blockstore configurations.

        Args:
            items_per_page: Number of items per page.
            as_obj: Return BackupStore objects if True, dicts if False.

        Returns:
            List of blockstore configurations.
        """
        return self._fetch_all(
            path="admin/backup/snapshot/mongoConfigs",
            item_type=BackupStore if as_obj else None,
            items_per_page=items_per_page,
        )

    def list_blockstores_iter(
        self,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> PageIterator[BackupStore]:
        """Iterate over blockstore configurations.

        Args:
            items_per_page: Number of items per page.
            as_obj: Return BackupStore objects if True, dicts if False.

        Returns:
            Iterator over blockstore configurations.
        """
        return self._paginate(
            path="admin/backup/snapshot/mongoConfigs",
            item_type=BackupStore if as_obj else None,
            items_per_page=items_per_page,
        )

    def get_blockstore(
        self,
        store_id: str,
        as_obj: bool = True,
    ) -> BackupStore:
        """Get a single blockstore configuration by ID.

        Args:
            store_id: Blockstore ID.
            as_obj: Return BackupStore object if True, dict if False.

        Returns:
            Blockstore configuration.
        """
        response = self._get(f"admin/backup/snapshot/mongoConfigs/{store_id}")
        return BackupStore.from_dict(response) if as_obj else response

    # ---- S3 blockstore configs ----

    def list_s3_blockstores(
        self,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> List[S3BlockstoreConfig]:
        """Get all S3 blockstore configurations.

        Args:
            items_per_page: Number of items per page.
            as_obj: Return S3BlockstoreConfig objects if True, dicts if False.

        Returns:
            List of S3 blockstore configurations.
        """
        return self._fetch_all(
            path="admin/backup/snapshot/s3Configs",
            item_type=S3BlockstoreConfig if as_obj else None,
            items_per_page=items_per_page,
        )

    def list_s3_blockstores_iter(
        self,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> PageIterator[S3BlockstoreConfig]:
        """Iterate over S3 blockstore configurations.

        Args:
            items_per_page: Number of items per page.
            as_obj: Return S3BlockstoreConfig objects if True, dicts if False.

        Returns:
            Iterator over S3 blockstore configurations.
        """
        return self._paginate(
            path="admin/backup/snapshot/s3Configs",
            item_type=S3BlockstoreConfig if as_obj else None,
            items_per_page=items_per_page,
        )

    def get_s3_blockstore(
        self,
        store_id: str,
        as_obj: bool = True,
    ) -> S3BlockstoreConfig:
        """Get a single S3 blockstore configuration by ID.

        Args:
            store_id: S3 blockstore ID.
            as_obj: Return S3BlockstoreConfig object if True, dict if False.

        Returns:
            S3 blockstore configuration.
        """
        response = self._get(f"admin/backup/snapshot/s3Configs/{store_id}")
        return S3BlockstoreConfig.from_dict(response) if as_obj else response

    # ---- File system store configs ----

    def list_file_system_stores(
        self,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> List[FileSystemStoreConfig]:
        """Get all file system store configurations.

        Args:
            items_per_page: Number of items per page.
            as_obj: Return FileSystemStoreConfig objects if True, dicts if False.

        Returns:
            List of file system store configurations.
        """
        return self._fetch_all(
            path="admin/backup/snapshot/fileSystemConfigs",
            item_type=FileSystemStoreConfig if as_obj else None,
            items_per_page=items_per_page,
        )

    def list_file_system_stores_iter(
        self,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> PageIterator[FileSystemStoreConfig]:
        """Iterate over file system store configurations.

        Args:
            items_per_page: Number of items per page.
            as_obj: Return FileSystemStoreConfig objects if True, dicts if False.

        Returns:
            Iterator over file system store configurations.
        """
        return self._paginate(
            path="admin/backup/snapshot/fileSystemConfigs",
            item_type=FileSystemStoreConfig if as_obj else None,
            items_per_page=items_per_page,
        )

    def get_file_system_store(
        self,
        store_id: str,
        as_obj: bool = True,
    ) -> FileSystemStoreConfig:
        """Get a single file system store configuration by ID.

        Args:
            store_id: File system store ID.
            as_obj: Return FileSystemStoreConfig object if True, dict if False.

        Returns:
            File system store configuration.
        """
        response = self._get(f"admin/backup/snapshot/fileSystemConfigs/{store_id}")
        return FileSystemStoreConfig.from_dict(response) if as_obj else response

    # ---- Oplog store configs ----

    def list_oplog_stores(
        self,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> List[BackupStore]:
        """Get all oplog store configurations.

        Args:
            items_per_page: Number of items per page.
            as_obj: Return BackupStore objects if True, dicts if False.

        Returns:
            List of oplog store configurations.
        """
        return self._fetch_all(
            path="admin/backup/oplog/mongoConfigs",
            item_type=BackupStore if as_obj else None,
            items_per_page=items_per_page,
        )

    def list_oplog_stores_iter(
        self,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> PageIterator[BackupStore]:
        """Iterate over oplog store configurations.

        Args:
            items_per_page: Number of items per page.
            as_obj: Return BackupStore objects if True, dicts if False.

        Returns:
            Iterator over oplog store configurations.
        """
        return self._paginate(
            path="admin/backup/oplog/mongoConfigs",
            item_type=BackupStore if as_obj else None,
            items_per_page=items_per_page,
        )

    def get_oplog_store(
        self,
        store_id: str,
        as_obj: bool = True,
    ) -> BackupStore:
        """Get a single oplog store configuration by ID.

        Args:
            store_id: Oplog store ID.
            as_obj: Return BackupStore object if True, dict if False.

        Returns:
            Oplog store configuration.
        """
        response = self._get(f"admin/backup/oplog/mongoConfigs/{store_id}")
        return BackupStore.from_dict(response) if as_obj else response

    # ---- Sync store configs ----

    def list_sync_stores(
        self,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> List[BackupStore]:
        """Get all sync store configurations.

        Args:
            items_per_page: Number of items per page.
            as_obj: Return BackupStore objects if True, dicts if False.

        Returns:
            List of sync store configurations.
        """
        return self._fetch_all(
            path="admin/backup/sync/mongoConfigs",
            item_type=BackupStore if as_obj else None,
            items_per_page=items_per_page,
        )

    def list_sync_stores_iter(
        self,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> PageIterator[BackupStore]:
        """Iterate over sync store configurations.

        Args:
            items_per_page: Number of items per page.
            as_obj: Return BackupStore objects if True, dicts if False.

        Returns:
            Iterator over sync store configurations.
        """
        return self._paginate(
            path="admin/backup/sync/mongoConfigs",
            item_type=BackupStore if as_obj else None,
            items_per_page=items_per_page,
        )

    def get_sync_store(
        self,
        store_id: str,
        as_obj: bool = True,
    ) -> BackupStore:
        """Get a single sync store configuration by ID.

        Args:
            store_id: Sync store ID.
            as_obj: Return BackupStore object if True, dict if False.

        Returns:
            Sync store configuration.
        """
        response = self._get(f"admin/backup/sync/mongoConfigs/{store_id}")
        return BackupStore.from_dict(response) if as_obj else response

    # ---- Daemon configs ----

    def list_daemons(
        self,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> List[DaemonConfig]:
        """Get all backup daemon configurations.

        Args:
            items_per_page: Number of items per page.
            as_obj: Return DaemonConfig objects if True, dicts if False.

        Returns:
            List of backup daemon configurations.
        """
        return self._fetch_all(
            path="admin/backup/daemon/configs",
            item_type=DaemonConfig if as_obj else None,
            items_per_page=items_per_page,
        )

    def list_daemons_iter(
        self,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> PageIterator[DaemonConfig]:
        """Iterate over backup daemon configurations.

        Args:
            items_per_page: Number of items per page.
            as_obj: Return DaemonConfig objects if True, dicts if False.

        Returns:
            Iterator over backup daemon configurations.
        """
        return self._paginate(
            path="admin/backup/daemon/configs",
            item_type=DaemonConfig if as_obj else None,
            items_per_page=items_per_page,
        )

    def get_daemon(
        self,
        daemon_id: str,
        as_obj: bool = True,
    ) -> DaemonConfig:
        """Get a single backup daemon configuration by ID.

        Args:
            daemon_id: Daemon ID.
            as_obj: Return DaemonConfig object if True, dict if False.

        Returns:
            Backup daemon configuration.
        """
        response = self._get(f"admin/backup/daemon/configs/{daemon_id}")
        return DaemonConfig.from_dict(response) if as_obj else response

    # ---- Project job configs ----

    def list_project_jobs(
        self,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> List[ProjectJobConfig]:
        """Get all admin backup project job configurations.

        Args:
            items_per_page: Number of items per page.
            as_obj: Return ProjectJobConfig objects if True, dicts if False.

        Returns:
            List of project job configurations.
        """
        return self._fetch_all(
            path="admin/backup/groups",
            item_type=ProjectJobConfig if as_obj else None,
            items_per_page=items_per_page,
        )

    def list_project_jobs_iter(
        self,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> PageIterator[ProjectJobConfig]:
        """Iterate over admin backup project job configurations.

        Args:
            items_per_page: Number of items per page.
            as_obj: Return ProjectJobConfig objects if True, dicts if False.

        Returns:
            Iterator over project job configurations.
        """
        return self._paginate(
            path="admin/backup/groups",
            item_type=ProjectJobConfig if as_obj else None,
            items_per_page=items_per_page,
        )

    def get_project_job(
        self,
        project_id: str,
        as_obj: bool = True,
    ) -> ProjectJobConfig:
        """Get a single admin backup project job configuration by project ID.

        Args:
            project_id: Project (group) ID.
            as_obj: Return ProjectJobConfig object if True, dict if False.

        Returns:
            Project job configuration.
        """
        response = self._get(f"admin/backup/groups/{project_id}")
        return ProjectJobConfig.from_dict(response) if as_obj else response
