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
Organizations service for MongoDB Ops Manager API.

See: https://docs.opsmanager.mongodb.com/current/reference/api/organizations/
"""

from typing import Any, Dict, Iterator, List, Optional

from opsmanager.services.base import BaseService
from opsmanager.types import Organization, Project
from opsmanager.pagination import PageIterator


class OrganizationsService(BaseService):
    """Service for managing Ops Manager organizations.

    Organizations are the top-level entity in Ops Manager. Each organization
    can contain multiple projects (groups).
    """

    def list(
        self,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> List[Organization]:
        """Get all organizations the authenticated user can access.

        Args:
            items_per_page: Number of items per page (max 500).
            as_obj: Return Organization objects if True, dicts if False.

        Returns:
            List of organizations.
        """
        results = self._fetch_all(
            path="orgs",
            item_type=Organization if as_obj else None,
            items_per_page=items_per_page,
        )
        return results

    def list_iter(
        self,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> PageIterator[Organization]:
        """Iterate over all organizations.

        Args:
            items_per_page: Number of items per page.
            as_obj: Return Organization objects if True, dicts if False.

        Returns:
            Iterator over organizations.
        """
        return self._paginate(
            path="orgs",
            item_type=Organization if as_obj else None,
            items_per_page=items_per_page,
        )

    def get(
        self,
        org_id: str,
        as_obj: bool = True,
    ) -> Organization:
        """Get a single organization by ID.

        Args:
            org_id: Organization ID.
            as_obj: Return Organization object if True, dict if False.

        Returns:
            Organization details.
        """
        response = self._get(f"orgs/{org_id}")
        return Organization.from_dict(response) if as_obj else response

    def list_projects(
        self,
        org_id: str,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> List[Project]:
        """Get all projects in an organization.

        Args:
            org_id: Organization ID.
            items_per_page: Number of items per page.
            as_obj: Return Project objects if True, dicts if False.

        Returns:
            List of projects in the organization.
        """
        return self._fetch_all(
            path=f"orgs/{org_id}/groups",
            item_type=Project if as_obj else None,
            items_per_page=items_per_page,
        )

    def list_projects_iter(
        self,
        org_id: str,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> PageIterator[Project]:
        """Iterate over all projects in an organization.

        Args:
            org_id: Organization ID.
            items_per_page: Number of items per page.
            as_obj: Return Project objects if True, dicts if False.

        Returns:
            Iterator over projects.
        """
        return self._paginate(
            path=f"orgs/{org_id}/groups",
            item_type=Project if as_obj else None,
            items_per_page=items_per_page,
        )
