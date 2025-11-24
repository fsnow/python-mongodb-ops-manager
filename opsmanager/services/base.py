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
Base service class for MongoDB Ops Manager API services.

All service classes inherit from BaseService, which provides common
functionality for making API requests.
"""

from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Type, TypeVar

from opsmanager.pagination import PageIterator, paginate

if TYPE_CHECKING:
    from opsmanager.network import NetworkSession

T = TypeVar("T")


class BaseService:
    """Base class for all API service classes.

    Provides common functionality for making API requests and handling
    pagination. Each service class represents a section of the API.
    """

    # API path prefix for this service (override in subclasses)
    BASE_PATH = "api/public/v1.0"

    def __init__(self, session: "NetworkSession"):
        """Initialize the service.

        Args:
            session: NetworkSession instance for making HTTP requests.
        """
        self._session = session

    def _get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make a GET request.

        Args:
            path: API path (relative to BASE_PATH).
            params: Query parameters.

        Returns:
            Parsed JSON response.
        """
        full_path = f"{self.BASE_PATH}/{path.lstrip('/')}"
        return self._session.get(full_path, params=params)

    def _post(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make a POST request.

        Args:
            path: API path (relative to BASE_PATH).
            json: Request body.
            params: Query parameters.

        Returns:
            Parsed JSON response.
        """
        full_path = f"{self.BASE_PATH}/{path.lstrip('/')}"
        return self._session.post(full_path, json=json, params=params)

    def _put(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make a PUT request.

        Args:
            path: API path (relative to BASE_PATH).
            json: Request body.
            params: Query parameters.

        Returns:
            Parsed JSON response.
        """
        full_path = f"{self.BASE_PATH}/{path.lstrip('/')}"
        return self._session.put(full_path, json=json, params=params)

    def _patch(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make a PATCH request.

        Args:
            path: API path (relative to BASE_PATH).
            json: Request body.
            params: Query parameters.

        Returns:
            Parsed JSON response.
        """
        full_path = f"{self.BASE_PATH}/{path.lstrip('/')}"
        return self._session.patch(full_path, json=json, params=params)

    def _delete(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make a DELETE request.

        Args:
            path: API path (relative to BASE_PATH).
            params: Query parameters.

        Returns:
            Parsed JSON response.
        """
        full_path = f"{self.BASE_PATH}/{path.lstrip('/')}"
        return self._session.delete(full_path, params=params)

    def _paginate(
        self,
        path: str,
        item_type: Optional[Type[T]] = None,
        params: Optional[Dict[str, Any]] = None,
        items_per_page: int = 100,
        max_items: Optional[int] = None,
    ) -> PageIterator[T]:
        """Create a paginated iterator for a list endpoint.

        Args:
            path: API path (relative to BASE_PATH).
            item_type: Optional type to convert items to.
            params: Additional query parameters.
            items_per_page: Number of items per page.
            max_items: Maximum items to return.

        Returns:
            PageIterator for iterating through results.
        """
        base_params = params or {}

        def fetch_page(page_num: int, per_page: int) -> Dict[str, Any]:
            page_params = {
                **base_params,
                "pageNum": page_num,
                "itemsPerPage": per_page,
                "includeCount": "true",
            }
            return self._get(path, params=page_params)

        return paginate(
            fetch_page=fetch_page,
            item_type=item_type,
            items_per_page=items_per_page,
            max_items=max_items,
        )

    def _fetch_all(
        self,
        path: str,
        item_type: Optional[Type[T]] = None,
        params: Optional[Dict[str, Any]] = None,
        items_per_page: int = 100,
        max_items: Optional[int] = None,
    ) -> List[T]:
        """Fetch all items from a paginated endpoint.

        Args:
            path: API path (relative to BASE_PATH).
            item_type: Optional type to convert items to.
            params: Additional query parameters.
            items_per_page: Number of items per page.
            max_items: Maximum items to return.

        Returns:
            List of all items.
        """
        return list(self._paginate(
            path=path,
            item_type=item_type,
            params=params,
            items_per_page=items_per_page,
            max_items=max_items,
        ))
