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
Global admin service for MongoDB Ops Manager API.

Provides read access to global (cross-organization) admin resources:
global API keys and global API key IP whitelists.

These are admin-level endpoints requiring global owner role.

See: https://www.mongodb.com/docs/ops-manager/current/reference/api/api-keys/
"""

from typing import List

from opsmanager.services.base import BaseService
from opsmanager.types import APIKey, GlobalWhitelistAPIKey
from opsmanager.pagination import PageIterator


class GlobalAdminService(BaseService):
    """Service for global admin API key reads.

    Provides access to the global API key inventory and IP whitelist.
    Useful for security audits across all organizations in Ops Manager.
    """

    # ---- Global API Keys ----

    def list_api_keys(
        self,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> List[APIKey]:
        """Get all global API keys.

        Args:
            items_per_page: Number of items per page.
            as_obj: Return APIKey objects if True, dicts if False.

        Returns:
            List of global API keys.
        """
        return self._fetch_all(
            path="admin/apiKeys",
            item_type=APIKey if as_obj else None,
            items_per_page=items_per_page,
        )

    def list_api_keys_iter(
        self,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> PageIterator[APIKey]:
        """Iterate over global API keys.

        Args:
            items_per_page: Number of items per page.
            as_obj: Return APIKey objects if True, dicts if False.

        Returns:
            Iterator over global API keys.
        """
        return self._paginate(
            path="admin/apiKeys",
            item_type=APIKey if as_obj else None,
            items_per_page=items_per_page,
        )

    def get_api_key(
        self,
        api_key_id: str,
        as_obj: bool = True,
    ) -> APIKey:
        """Get a single global API key by ID.

        Args:
            api_key_id: API key ID.
            as_obj: Return APIKey object if True, dict if False.

        Returns:
            Global API key details.
        """
        response = self._get(f"admin/apiKeys/{api_key_id}")
        return APIKey.from_dict(response) if as_obj else response

    # ---- Global API Key Whitelist ----

    def list_whitelist(
        self,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> List[GlobalWhitelistAPIKey]:
        """Get all global API key IP whitelist entries.

        Args:
            items_per_page: Number of items per page.
            as_obj: Return GlobalWhitelistAPIKey objects if True, dicts if False.

        Returns:
            List of global API key whitelist entries.
        """
        return self._fetch_all(
            path="admin/whitelist",
            item_type=GlobalWhitelistAPIKey if as_obj else None,
            items_per_page=items_per_page,
        )

    def list_whitelist_iter(
        self,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> PageIterator[GlobalWhitelistAPIKey]:
        """Iterate over global API key IP whitelist entries.

        Args:
            items_per_page: Number of items per page.
            as_obj: Return GlobalWhitelistAPIKey objects if True, dicts if False.

        Returns:
            Iterator over global API key whitelist entries.
        """
        return self._paginate(
            path="admin/whitelist",
            item_type=GlobalWhitelistAPIKey if as_obj else None,
            items_per_page=items_per_page,
        )

    def get_whitelist_entry(
        self,
        entry_id: str,
        as_obj: bool = True,
    ) -> GlobalWhitelistAPIKey:
        """Get a single global API key whitelist entry by ID.

        Args:
            entry_id: Whitelist entry ID.
            as_obj: Return GlobalWhitelistAPIKey object if True, dict if False.

        Returns:
            Global API key whitelist entry.
        """
        response = self._get(f"admin/whitelist/{entry_id}")
        return GlobalWhitelistAPIKey.from_dict(response) if as_obj else response
