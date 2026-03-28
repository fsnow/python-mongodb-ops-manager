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

"""Unit tests for pagination (PageIterator)."""

import pytest
from unittest.mock import MagicMock

from opsmanager.pagination import PageIterator, paginate, fetch_all


def _make_page(items, total_count=None):
    """Helper: build an API page response dict."""
    return {
        "results": items,
        "totalCount": total_count if total_count is not None else len(items),
    }


class TestPageIteratorEmpty:
    """PageIterator behaviour when the first page returns no results."""

    def test_empty_results_stops_immediately(self):
        fetch = MagicMock(return_value=_make_page([]))
        items = list(PageIterator(fetch_page=fetch, items_per_page=10))
        assert items == []
        fetch.assert_called_once_with(1, 10)

    def test_total_count_none_before_iteration(self):
        fetch = MagicMock(return_value=_make_page([]))
        it = PageIterator(fetch_page=fetch, items_per_page=10)
        assert it.total_count is None
        list(it)
        assert it.total_count == 0

    def test_items_yielded_zero(self):
        fetch = MagicMock(return_value=_make_page([]))
        it = PageIterator(fetch_page=fetch, items_per_page=10)
        list(it)
        assert it.items_yielded == 0


class TestPageIteratorSingleItem:
    """PageIterator with exactly one item."""

    def test_yields_single_item_as_dict(self):
        fetch = MagicMock(return_value=_make_page([{"id": "abc"}]))
        items = list(PageIterator(fetch_page=fetch, items_per_page=10))
        assert items == [{"id": "abc"}]

    def test_single_item_converted_by_item_type(self):
        class Thing:
            def __init__(self, id):
                self.id = id

            @classmethod
            def from_dict(cls, d):
                return cls(d["id"])

        fetch = MagicMock(return_value=_make_page([{"id": "xyz"}]))
        items = list(PageIterator(fetch_page=fetch, item_type=Thing, items_per_page=10))
        assert len(items) == 1
        assert items[0].id == "xyz"

    def test_only_one_page_fetched(self):
        fetch = MagicMock(return_value=_make_page([{"id": "a"}]))
        list(PageIterator(fetch_page=fetch, items_per_page=10))
        assert fetch.call_count == 1


class TestPageIteratorExactlyFullLastPage:
    """Edge case: last page has exactly items_per_page items.

    The iterator cannot know this is the last page until it tries to fetch
    the next page and gets an empty response.
    """

    def test_exact_page_size_fetches_extra_page(self):
        """When last page is full, iterator fetches one more page to confirm end."""
        page1 = _make_page([{"id": str(i)} for i in range(3)], total_count=3)
        page2 = _make_page([])

        fetch = MagicMock(side_effect=[page1, page2])
        items = list(PageIterator(fetch_page=fetch, items_per_page=3))

        assert len(items) == 3
        assert fetch.call_count == 2

    def test_two_full_pages_plus_partial(self):
        page1 = _make_page([{"id": str(i)} for i in range(3)])
        page2 = _make_page([{"id": str(i)} for i in range(3, 5)])

        fetch = MagicMock(side_effect=[page1, page2])
        items = list(PageIterator(fetch_page=fetch, items_per_page=3))

        assert len(items) == 5
        assert fetch.call_count == 2

    def test_three_pages(self):
        """Three pages: two full + one partial."""
        page1 = _make_page([{"id": "a"}, {"id": "b"}])
        page2 = _make_page([{"id": "c"}, {"id": "d"}])
        page3 = _make_page([{"id": "e"}])

        fetch = MagicMock(side_effect=[page1, page2, page3])
        items = list(PageIterator(fetch_page=fetch, items_per_page=2))

        assert [x["id"] for x in items] == ["a", "b", "c", "d", "e"]
        assert fetch.call_count == 3


class TestPageIteratorMaxItems:
    """max_items cap."""

    def test_max_items_stops_early(self):
        page1 = _make_page([{"id": str(i)} for i in range(10)])
        fetch = MagicMock(return_value=page1)
        items = list(PageIterator(fetch_page=fetch, items_per_page=10, max_items=3))
        assert len(items) == 3

    def test_max_items_zero_yields_nothing(self):
        page1 = _make_page([{"id": "a"}])
        fetch = MagicMock(return_value=page1)
        items = list(PageIterator(fetch_page=fetch, items_per_page=10, max_items=0))
        assert items == []


class TestFetchAll:
    """fetch_all convenience function."""

    def test_fetch_all_collects_all_pages(self):
        page1 = _make_page([{"id": "a"}, {"id": "b"}])
        page2 = _make_page([{"id": "c"}])
        fetch = MagicMock(side_effect=[page1, page2])
        result = fetch_all(fetch_page=fetch, items_per_page=2)
        assert len(result) == 3
