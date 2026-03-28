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
API keys service for MongoDB Ops Manager API.

Provides read access to API key inventories at the organization and project
level. Useful for access control audits ("what programmatic API keys exist
and what roles do they have?").

See: https://www.mongodb.com/docs/ops-manager/current/reference/api/api-keys/
"""

from typing import List

from opsmanager.services.base import BaseService
from opsmanager.types import APIKey
from opsmanager.pagination import PageIterator


class APIKeysService(BaseService):
    """Service for reading API key inventories.

    Provides access to organization-level and project-level API keys.
    Use for access control audits and programmatic key rotation tracking.
    """

    def list_organization_keys(
        self,
        org_id: str,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> List[APIKey]:
        """Get all API keys for an organization.

        Args:
            org_id: Organization ID.
            items_per_page: Number of items per page.
            as_obj: Return APIKey objects if True, dicts if False.

        Returns:
            List of organization API keys.
        """
        return self._fetch_all(
            path=f"orgs/{org_id}/apiKeys",
            item_type=APIKey if as_obj else None,
            items_per_page=items_per_page,
        )

    def list_organization_keys_iter(
        self,
        org_id: str,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> PageIterator[APIKey]:
        """Iterate over API keys for an organization.

        Args:
            org_id: Organization ID.
            items_per_page: Number of items per page.
            as_obj: Return APIKey objects if True, dicts if False.

        Returns:
            Iterator over organization API keys.
        """
        return self._paginate(
            path=f"orgs/{org_id}/apiKeys",
            item_type=APIKey if as_obj else None,
            items_per_page=items_per_page,
        )

    def get_organization_key(
        self,
        org_id: str,
        api_key_id: str,
        as_obj: bool = True,
    ) -> APIKey:
        """Get a single organization API key by ID.

        Args:
            org_id: Organization ID.
            api_key_id: API key ID.
            as_obj: Return APIKey object if True, dict if False.

        Returns:
            API key details.
        """
        response = self._get(f"orgs/{org_id}/apiKeys/{api_key_id}")
        return APIKey.from_dict(response) if as_obj else response

    def list_project_keys(
        self,
        project_id: str,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> List[APIKey]:
        """Get all API keys assigned to a project.

        Args:
            project_id: Project (group) ID.
            items_per_page: Number of items per page.
            as_obj: Return APIKey objects if True, dicts if False.

        Returns:
            List of API keys assigned to the project.
        """
        return self._fetch_all(
            path=f"groups/{project_id}/apiKeys",
            item_type=APIKey if as_obj else None,
            items_per_page=items_per_page,
        )
