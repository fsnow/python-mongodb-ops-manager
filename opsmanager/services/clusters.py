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
Clusters service for MongoDB Ops Manager API.

Provides operations for managing MongoDB clusters (replica sets and sharded clusters).

See: https://docs.opsmanager.mongodb.com/current/reference/api/clusters/
"""

from typing import Any, Dict, List, Optional

from opsmanager.services.base import BaseService
from opsmanager.types import Cluster
from opsmanager.pagination import PageIterator


class ClustersService(BaseService):
    """Service for managing MongoDB clusters.

    Clusters can be either replica sets or sharded clusters.
    Note that sharded clusters contain replica sets (shards), and
    the API models these relationships hierarchically.
    """

    def list(
        self,
        project_id: str,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> List[Cluster]:
        """Get all clusters in a project.

        Args:
            project_id: Project (group) ID.
            items_per_page: Number of items per page (max 500).
            as_obj: Return Cluster objects if True, dicts if False.

        Returns:
            List of clusters.
        """
        return self._fetch_all(
            path=f"groups/{project_id}/clusters",
            item_type=Cluster if as_obj else None,
            items_per_page=items_per_page,
        )

    def list_iter(
        self,
        project_id: str,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> PageIterator[Cluster]:
        """Iterate over all clusters in a project.

        Args:
            project_id: Project (group) ID.
            items_per_page: Number of items per page.
            as_obj: Return Cluster objects if True, dicts if False.

        Returns:
            Iterator over clusters.
        """
        return self._paginate(
            path=f"groups/{project_id}/clusters",
            item_type=Cluster if as_obj else None,
            items_per_page=items_per_page,
        )

    def get(
        self,
        project_id: str,
        cluster_id: str,
        as_obj: bool = True,
    ) -> Cluster:
        """Get a single cluster by ID.

        Args:
            project_id: Project (group) ID.
            cluster_id: Cluster ID.
            as_obj: Return Cluster object if True, dict if False.

        Returns:
            Cluster details.
        """
        response = self._get(f"groups/{project_id}/clusters/{cluster_id}")
        return Cluster.from_dict(response) if as_obj else response

    def list_all(
        self,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> List[Cluster]:
        """Get all clusters across all projects.

        This endpoint returns clusters from all projects the user can access.

        Args:
            items_per_page: Number of items per page (max 500).
            as_obj: Return Cluster objects if True, dicts if False.

        Returns:
            List of all clusters.
        """
        return self._fetch_all(
            path="clusters",
            item_type=Cluster if as_obj else None,
            items_per_page=items_per_page,
        )

    def list_all_iter(
        self,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> PageIterator[Cluster]:
        """Iterate over all clusters across all projects.

        Args:
            items_per_page: Number of items per page.
            as_obj: Return Cluster objects if True, dicts if False.

        Returns:
            Iterator over all clusters.
        """
        return self._paginate(
            path="clusters",
            item_type=Cluster if as_obj else None,
            items_per_page=items_per_page,
        )
