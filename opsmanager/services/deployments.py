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
Deployments service for MongoDB Ops Manager API.

Provides operations for managing hosts, databases, and disk partitions.
This service handles the infrastructure-level details of MongoDB deployments.

See: https://docs.opsmanager.mongodb.com/current/reference/api/hosts/
"""

from typing import Any, Dict, List, Optional

from opsmanager.services.base import BaseService
from opsmanager.types import Host, Database, Disk
from opsmanager.pagination import PageIterator


class DeploymentsService(BaseService):
    """Service for managing deployment infrastructure.

    Handles hosts (MongoDB processes), databases, and disk partitions.
    Corresponds to the DeploymentsService in the Go SDK.
    """

    # Host operations

    def list_hosts(
        self,
        project_id: str,
        cluster_id: Optional[str] = None,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> List[Host]:
        """Get all hosts (processes) in a project.

        Args:
            project_id: Project (group) ID.
            cluster_id: Optional cluster ID to filter by.
            items_per_page: Number of items per page (max 500).
            as_obj: Return Host objects if True, dicts if False.

        Returns:
            List of hosts.
        """
        params = {}
        if cluster_id:
            params["clusterId"] = cluster_id

        return self._fetch_all(
            path=f"groups/{project_id}/hosts",
            item_type=Host if as_obj else None,
            params=params,
            items_per_page=items_per_page,
        )

    def list_hosts_iter(
        self,
        project_id: str,
        cluster_id: Optional[str] = None,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> PageIterator[Host]:
        """Iterate over all hosts in a project.

        Args:
            project_id: Project (group) ID.
            cluster_id: Optional cluster ID to filter by.
            items_per_page: Number of items per page.
            as_obj: Return Host objects if True, dicts if False.

        Returns:
            Iterator over hosts.
        """
        params = {}
        if cluster_id:
            params["clusterId"] = cluster_id

        return self._paginate(
            path=f"groups/{project_id}/hosts",
            item_type=Host if as_obj else None,
            params=params,
            items_per_page=items_per_page,
        )

    def get_host(
        self,
        project_id: str,
        host_id: str,
        as_obj: bool = True,
    ) -> Host:
        """Get a single host by ID.

        Args:
            project_id: Project (group) ID.
            host_id: Host ID.
            as_obj: Return Host object if True, dict if False.

        Returns:
            Host details.
        """
        response = self._get(f"groups/{project_id}/hosts/{host_id}")
        return Host.from_dict(response) if as_obj else response

    def get_host_by_name(
        self,
        project_id: str,
        hostname: str,
        port: int,
        as_obj: bool = True,
    ) -> Host:
        """Get a host by hostname and port.

        Args:
            project_id: Project (group) ID.
            hostname: Host's hostname.
            port: Host's port.
            as_obj: Return Host object if True, dict if False.

        Returns:
            Host details.
        """
        response = self._get(f"groups/{project_id}/hosts/byName/{hostname}:{port}")
        return Host.from_dict(response) if as_obj else response

    # Database operations

    def list_databases(
        self,
        project_id: str,
        host_id: str,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> List[Database]:
        """Get all databases on a host.

        Args:
            project_id: Project (group) ID.
            host_id: Host ID.
            items_per_page: Number of items per page.
            as_obj: Return Database objects if True, dicts if False.

        Returns:
            List of databases.
        """
        return self._fetch_all(
            path=f"groups/{project_id}/hosts/{host_id}/databases",
            item_type=Database if as_obj else None,
            items_per_page=items_per_page,
        )

    def get_database(
        self,
        project_id: str,
        host_id: str,
        database_name: str,
        as_obj: bool = True,
    ) -> Database:
        """Get a single database by name.

        Args:
            project_id: Project (group) ID.
            host_id: Host ID.
            database_name: Database name.
            as_obj: Return Database object if True, dict if False.

        Returns:
            Database details.
        """
        response = self._get(f"groups/{project_id}/hosts/{host_id}/databases/{database_name}")
        return Database.from_dict(response) if as_obj else response

    # Disk operations

    def list_disks(
        self,
        project_id: str,
        host_id: str,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> List[Disk]:
        """Get all disk partitions on a host.

        Args:
            project_id: Project (group) ID.
            host_id: Host ID.
            items_per_page: Number of items per page.
            as_obj: Return Disk objects if True, dicts if False.

        Returns:
            List of disk partitions.
        """
        return self._fetch_all(
            path=f"groups/{project_id}/hosts/{host_id}/disks",
            item_type=Disk if as_obj else None,
            items_per_page=items_per_page,
        )

    def get_disk(
        self,
        project_id: str,
        host_id: str,
        partition_name: str,
        as_obj: bool = True,
    ) -> Disk:
        """Get a single disk partition by name.

        Args:
            project_id: Project (group) ID.
            host_id: Host ID.
            partition_name: Partition name.
            as_obj: Return Disk object if True, dict if False.

        Returns:
            Disk partition details.
        """
        response = self._get(f"groups/{project_id}/hosts/{host_id}/disks/{partition_name}")
        return Disk.from_dict(response) if as_obj else response

    # Helper methods for common operations

    def get_primaries(
        self,
        project_id: str,
        cluster_id: Optional[str] = None,
        as_obj: bool = True,
    ) -> List[Host]:
        """Get all primary nodes in a project.

        Args:
            project_id: Project (group) ID.
            cluster_id: Optional cluster ID to filter by.
            as_obj: Return Host objects if True, dicts if False.

        Returns:
            List of primary hosts.
        """
        hosts = self.list_hosts(project_id, cluster_id=cluster_id, as_obj=as_obj)
        if as_obj:
            return [h for h in hosts if h.is_primary]
        else:
            return [h for h in hosts if h.get("replicaStateName") == "PRIMARY"]

    def get_mongos_hosts(
        self,
        project_id: str,
        cluster_id: Optional[str] = None,
        as_obj: bool = True,
    ) -> List[Host]:
        """Get all mongos routers in a project.

        Args:
            project_id: Project (group) ID.
            cluster_id: Optional cluster ID to filter by.
            as_obj: Return Host objects if True, dicts if False.

        Returns:
            List of mongos hosts.
        """
        hosts = self.list_hosts(project_id, cluster_id=cluster_id, as_obj=as_obj)
        if as_obj:
            return [h for h in hosts if h.is_mongos]
        else:
            return [h for h in hosts if "MONGOS" in h.get("typeName", "").upper()]
