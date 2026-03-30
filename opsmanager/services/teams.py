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
Teams service for MongoDB Ops Manager API.

Provides read access to teams within an organization. Teams group users
and can be assigned to projects with specific roles.

See: https://www.mongodb.com/docs/ops-manager/current/reference/api/teams/
"""

from typing import Any, Dict, List

from opsmanager.services.base import BaseService
from opsmanager.types import Team, User
from opsmanager.pagination import PageIterator


class TeamsService(BaseService):
    """Service for reading Ops Manager teams.

    Teams are groups of users within an organization. Teams can be assigned
    to projects with specific roles, making them useful for managing access
    at scale. Reading teams is useful for organizational structure reporting.
    """

    def list(
        self,
        org_id: str,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> List[Team]:
        """Get all teams in an organization.

        Args:
            org_id: Organization ID.
            items_per_page: Number of items per page.
            as_obj: Return Team objects if True, dicts if False.

        Returns:
            List of teams.
        """
        return self._fetch_all(
            path=f"orgs/{org_id}/teams",
            item_type=Team if as_obj else None,
            items_per_page=items_per_page,
        )

    def list_iter(
        self,
        org_id: str,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> PageIterator[Team]:
        """Iterate over all teams in an organization.

        Args:
            org_id: Organization ID.
            items_per_page: Number of items per page.
            as_obj: Return Team objects if True, dicts if False.

        Returns:
            Iterator over teams.
        """
        return self._paginate(
            path=f"orgs/{org_id}/teams",
            item_type=Team if as_obj else None,
            items_per_page=items_per_page,
        )

    def get(
        self,
        org_id: str,
        team_id: str,
        as_obj: bool = True,
    ) -> Team:
        """Get a single team by ID.

        Args:
            org_id: Organization ID.
            team_id: Team ID.
            as_obj: Return Team object if True, dict if False.

        Returns:
            Team details.
        """
        response = self._get(f"orgs/{org_id}/teams/{team_id}")
        return Team.from_dict(response) if as_obj else response

    def get_by_name(
        self,
        org_id: str,
        team_name: str,
        as_obj: bool = True,
    ) -> Team:
        """Get a team by name.

        Args:
            org_id: Organization ID.
            team_name: Team name.
            as_obj: Return Team object if True, dict if False.

        Returns:
            Team details.
        """
        response = self._get(f"orgs/{org_id}/teams/byName/{team_name}")
        return Team.from_dict(response) if as_obj else response

    def list_users(
        self,
        org_id: str,
        team_id: str,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> List[User]:
        """Get all users assigned to a team.

        Args:
            org_id: Organization ID.
            team_id: Team ID.
            items_per_page: Number of items per page.
            as_obj: Return User objects if True, dicts if False.

        Returns:
            List of users in the team.
        """
        return self._fetch_all(
            path=f"orgs/{org_id}/teams/{team_id}/users",
            item_type=User if as_obj else None,
            items_per_page=items_per_page,
        )
