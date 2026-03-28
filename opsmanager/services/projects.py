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
Projects service for MongoDB Ops Manager API.

Projects are also known as Groups in the API. This service provides
operations for managing projects.

See: https://docs.opsmanager.mongodb.com/current/reference/api/groups/
"""

from typing import Any, Dict, List, Optional

from opsmanager.services.base import BaseService
from opsmanager.types import Project, User, Team
from opsmanager.pagination import PageIterator


class ProjectsService(BaseService):
    """Service for managing Ops Manager projects (groups).

    Projects are containers for clusters, hosts, and other resources.
    In the API, projects are referred to as "groups".
    """

    def list(
        self,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> List[Project]:
        """Get all projects the authenticated user can access.

        Args:
            items_per_page: Number of items per page (max 500).
            as_obj: Return Project objects if True, dicts if False.

        Returns:
            List of projects.
        """
        return self._fetch_all(
            path="groups",
            item_type=Project if as_obj else None,
            items_per_page=items_per_page,
        )

    def list_iter(
        self,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> PageIterator[Project]:
        """Iterate over all projects.

        Args:
            items_per_page: Number of items per page.
            as_obj: Return Project objects if True, dicts if False.

        Returns:
            Iterator over projects.
        """
        return self._paginate(
            path="groups",
            item_type=Project if as_obj else None,
            items_per_page=items_per_page,
        )

    def get(
        self,
        project_id: str,
        as_obj: bool = True,
    ) -> Project:
        """Get a single project by ID.

        Args:
            project_id: Project (group) ID.
            as_obj: Return Project object if True, dict if False.

        Returns:
            Project details.
        """
        response = self._get(f"groups/{project_id}")
        return Project.from_dict(response) if as_obj else response

    def get_by_name(
        self,
        project_name: str,
        as_obj: bool = True,
    ) -> Project:
        """Get a project by name.

        Args:
            project_name: Project name.
            as_obj: Return Project object if True, dict if False.

        Returns:
            Project details.
        """
        response = self._get(f"groups/byName/{project_name}")
        return Project.from_dict(response) if as_obj else response

    def list_users(
        self,
        project_id: str,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> List[User]:
        """Get all users with access to a project.

        Returns all users who have been granted access to this project.
        Use for granular access control reviews alongside
        ``organizations.list_users``.

        Args:
            project_id: Project (group) ID.
            items_per_page: Number of items per page.
            as_obj: Return User objects if True, dicts if False.

        Returns:
            List of users.
        """
        return self._fetch_all(
            path=f"groups/{project_id}/users",
            item_type=User if as_obj else None,
            items_per_page=items_per_page,
        )

    def get_teams(
        self,
        project_id: str,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> List[Team]:
        """Get all teams assigned to a project.

        Args:
            project_id: Project (group) ID.
            items_per_page: Number of items per page.
            as_obj: Return Team objects if True, dicts if False.

        Returns:
            List of teams with their roles in this project.
        """
        return self._fetch_all(
            path=f"groups/{project_id}/teams",
            item_type=Team if as_obj else None,
            items_per_page=items_per_page,
        )
