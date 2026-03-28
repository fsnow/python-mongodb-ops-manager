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
Events service for MongoDB Ops Manager API.

Provides access to the audit event log at both the organization and project level.
Events capture every significant action in Ops Manager — configuration changes,
user logins, alert triggers, backup events, etc.

Critical for compliance reporting (SOX, PCI-DSS) and incident investigation.

See: https://www.mongodb.com/docs/ops-manager/current/reference/api/events/
"""

from typing import Any, Dict, List, Optional

from opsmanager.services.base import BaseService
from opsmanager.types import Event
from opsmanager.pagination import PageIterator


class EventsService(BaseService):
    """Service for accessing the Ops Manager audit event log.

    Events are immutable records of actions taken in Ops Manager.
    Both organization-level and project-level events are supported.

    Use ``min_date`` / ``max_date`` parameters to scope queries to a time range,
    which is essential for compliance reports covering a specific audit period.
    """

    def list_organization_events(
        self,
        org_id: str,
        event_type: Optional[str] = None,
        min_date: Optional[str] = None,
        max_date: Optional[str] = None,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> List[Event]:
        """Get all events for an organization.

        Args:
            org_id: Organization ID.
            event_type: Filter by event type name (e.g. ``"USER_CREATED"``).
            min_date: ISO 8601 start of date range (inclusive).
            max_date: ISO 8601 end of date range (inclusive).
            items_per_page: Number of items per page.
            as_obj: Return Event objects if True, dicts if False.

        Returns:
            List of events, most recent first.
        """
        params = self._build_params(event_type=event_type, min_date=min_date, max_date=max_date)
        return self._fetch_all(
            path=f"orgs/{org_id}/events",
            item_type=Event if as_obj else None,
            params=params,
            items_per_page=items_per_page,
        )

    def list_organization_events_iter(
        self,
        org_id: str,
        event_type: Optional[str] = None,
        min_date: Optional[str] = None,
        max_date: Optional[str] = None,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> PageIterator[Event]:
        """Iterate over events for an organization.

        Args:
            org_id: Organization ID.
            event_type: Filter by event type name.
            min_date: ISO 8601 start of date range (inclusive).
            max_date: ISO 8601 end of date range (inclusive).
            items_per_page: Number of items per page.
            as_obj: Return Event objects if True, dicts if False.

        Returns:
            Iterator over events.
        """
        params = self._build_params(event_type=event_type, min_date=min_date, max_date=max_date)
        return self._paginate(
            path=f"orgs/{org_id}/events",
            item_type=Event if as_obj else None,
            params=params,
            items_per_page=items_per_page,
        )

    def get_organization_event(
        self,
        org_id: str,
        event_id: str,
        as_obj: bool = True,
    ) -> Event:
        """Get a single organization event by ID.

        Args:
            org_id: Organization ID.
            event_id: Event ID.
            as_obj: Return Event object if True, dict if False.

        Returns:
            Event details.
        """
        response = self._get(f"orgs/{org_id}/events/{event_id}")
        return Event.from_dict(response) if as_obj else response

    def list_project_events(
        self,
        project_id: str,
        event_type: Optional[str] = None,
        min_date: Optional[str] = None,
        max_date: Optional[str] = None,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> List[Event]:
        """Get all events for a project.

        Args:
            project_id: Project (group) ID.
            event_type: Filter by event type name (e.g. ``"HOST_DOWN"``).
            min_date: ISO 8601 start of date range (inclusive).
            max_date: ISO 8601 end of date range (inclusive).
            items_per_page: Number of items per page.
            as_obj: Return Event objects if True, dicts if False.

        Returns:
            List of events, most recent first.
        """
        params = self._build_params(event_type=event_type, min_date=min_date, max_date=max_date)
        return self._fetch_all(
            path=f"groups/{project_id}/events",
            item_type=Event if as_obj else None,
            params=params,
            items_per_page=items_per_page,
        )

    def list_project_events_iter(
        self,
        project_id: str,
        event_type: Optional[str] = None,
        min_date: Optional[str] = None,
        max_date: Optional[str] = None,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> PageIterator[Event]:
        """Iterate over events for a project.

        Args:
            project_id: Project (group) ID.
            event_type: Filter by event type name.
            min_date: ISO 8601 start of date range (inclusive).
            max_date: ISO 8601 end of date range (inclusive).
            items_per_page: Number of items per page.
            as_obj: Return Event objects if True, dicts if False.

        Returns:
            Iterator over events.
        """
        params = self._build_params(event_type=event_type, min_date=min_date, max_date=max_date)
        return self._paginate(
            path=f"groups/{project_id}/events",
            item_type=Event if as_obj else None,
            params=params,
            items_per_page=items_per_page,
        )

    def get_project_event(
        self,
        project_id: str,
        event_id: str,
        as_obj: bool = True,
    ) -> Event:
        """Get a single project event by ID.

        Args:
            project_id: Project (group) ID.
            event_id: Event ID.
            as_obj: Return Event object if True, dict if False.

        Returns:
            Event details.
        """
        response = self._get(f"groups/{project_id}/events/{event_id}")
        return Event.from_dict(response) if as_obj else response

    @staticmethod
    def _build_params(
        event_type: Optional[str],
        min_date: Optional[str],
        max_date: Optional[str],
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if event_type:
            params["eventType"] = event_type
        if min_date:
            params["minDate"] = min_date
        if max_date:
            params["maxDate"] = max_date
        return params
