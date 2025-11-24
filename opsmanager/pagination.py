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
Pagination helpers for MongoDB Ops Manager API.

The Ops Manager API uses cursor-based pagination with pageNum and itemsPerPage
parameters. This module provides helpers for iterating through paginated results.
"""

from dataclasses import dataclass
from typing import Any, Callable, Dict, Generator, Generic, Iterator, List, Optional, Type, TypeVar

T = TypeVar("T")


@dataclass
class ListOptions:
    """Options for paginated list requests.

    Mirrors the Go SDK's ListOptions struct.
    """
    page_num: int = 1
    items_per_page: int = 100
    include_count: bool = True

    def to_params(self) -> Dict[str, Any]:
        """Convert to API query parameters."""
        return {
            "pageNum": self.page_num,
            "itemsPerPage": self.items_per_page,
            "includeCount": str(self.include_count).lower(),
        }


class PageIterator(Generic[T]):
    """Iterator over paginated API results.

    This class handles automatic pagination, fetching new pages as needed.
    It's useful for iterating over large result sets without loading
    everything into memory at once.

    Example:
        # Iterate over all hosts
        for host in client.deployments.list_hosts_iter(project_id):
            print(host.hostname)

        # Or collect all results
        all_hosts = list(client.deployments.list_hosts_iter(project_id))
    """

    def __init__(
        self,
        fetch_page: Callable[[int, int], Dict[str, Any]],
        item_type: Optional[Type[T]] = None,
        items_per_page: int = 100,
        max_items: Optional[int] = None,
    ):
        """Initialize the page iterator.

        Args:
            fetch_page: Function(page_num, items_per_page) that fetches a page.
            item_type: Optional type to convert items to (must have from_dict).
            items_per_page: Number of items per page.
            max_items: Maximum total items to return (None for unlimited).
        """
        self._fetch_page = fetch_page
        self._item_type = item_type
        self._items_per_page = items_per_page
        self._max_items = max_items
        self._current_page = 0
        self._items_yielded = 0
        self._current_items: List[Any] = []
        self._current_index = 0
        self._total_count: Optional[int] = None
        self._exhausted = False

    def __iter__(self) -> Iterator[T]:
        return self

    def __next__(self) -> T:
        # Check if we've hit the max items limit
        if self._max_items is not None and self._items_yielded >= self._max_items:
            raise StopIteration

        # Fetch next page if needed
        while self._current_index >= len(self._current_items):
            if self._exhausted:
                raise StopIteration

            self._current_page += 1
            response = self._fetch_page(self._current_page, self._items_per_page)

            results = response.get("results", [])
            self._total_count = response.get("totalCount")

            if not results:
                self._exhausted = True
                raise StopIteration

            # Convert items if type is provided
            if self._item_type and hasattr(self._item_type, "from_dict"):
                self._current_items = [self._item_type.from_dict(item) for item in results]
            else:
                self._current_items = results

            self._current_index = 0

            # Check if this is the last page
            if len(results) < self._items_per_page:
                self._exhausted = True

        item = self._current_items[self._current_index]
        self._current_index += 1
        self._items_yielded += 1
        return item

    @property
    def total_count(self) -> Optional[int]:
        """Return total count if available (after first page fetch)."""
        return self._total_count

    @property
    def items_yielded(self) -> int:
        """Return number of items yielded so far."""
        return self._items_yielded


def paginate(
    fetch_page: Callable[[int, int], Dict[str, Any]],
    item_type: Optional[Type[T]] = None,
    items_per_page: int = 100,
    max_items: Optional[int] = None,
) -> PageIterator[T]:
    """Create a paginated iterator over API results.

    Args:
        fetch_page: Function(page_num, items_per_page) that fetches a page.
        item_type: Optional type to convert items to (must have from_dict).
        items_per_page: Number of items per page.
        max_items: Maximum total items to return (None for unlimited).

    Returns:
        PageIterator: Iterator over all items across pages.

    Example:
        def fetch(page_num, items_per_page):
            return session.get(f"/hosts?pageNum={page_num}&itemsPerPage={items_per_page}")

        for host in paginate(fetch, Host, items_per_page=100):
            print(host.hostname)
    """
    return PageIterator(
        fetch_page=fetch_page,
        item_type=item_type,
        items_per_page=items_per_page,
        max_items=max_items,
    )


def fetch_all(
    fetch_page: Callable[[int, int], Dict[str, Any]],
    item_type: Optional[Type[T]] = None,
    items_per_page: int = 100,
    max_items: Optional[int] = None,
) -> List[T]:
    """Fetch all items from a paginated endpoint.

    This is a convenience function that collects all paginated results
    into a single list. Use with caution on large result sets.

    Args:
        fetch_page: Function(page_num, items_per_page) that fetches a page.
        item_type: Optional type to convert items to (must have from_dict).
        items_per_page: Number of items per page.
        max_items: Maximum total items to return (None for unlimited).

    Returns:
        List of all items across all pages.
    """
    return list(paginate(
        fetch_page=fetch_page,
        item_type=item_type,
        items_per_page=items_per_page,
        max_items=max_items,
    ))
