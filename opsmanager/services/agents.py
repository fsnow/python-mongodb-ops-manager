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
Agents service for MongoDB Ops Manager API.

Provides access to monitoring, backup, and automation agent status.

See: https://docs.opsmanager.mongodb.com/current/reference/api/agents/
"""

from typing import Any, Dict, List, Optional

from opsmanager.services.base import BaseService
from opsmanager.types import Agent
from opsmanager.pagination import PageIterator


class AgentsService(BaseService):
    """Service for querying agent status.

    Provides access to the state of monitoring, backup, and automation
    agents registered in a project.
    """

    # Agent type values
    TYPE_MONITORING = "MONITORING"
    TYPE_BACKUP = "BACKUP"
    TYPE_AUTOMATION = "AUTOMATION"

    # Agent state values
    STATE_ACTIVE = "ACTIVE"
    STATE_STANDBY = "STANDBY"
    STATE_NO_PROCESSES = "NO_PROCESSES"

    def list(
        self,
        project_id: str,
        agent_type: str,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> List[Agent]:
        """Get all agents of a given type in a project.

        Args:
            project_id: Project (group) ID.
            agent_type: Agent type (MONITORING, BACKUP, or AUTOMATION).
            items_per_page: Number of items per page.
            as_obj: Return Agent objects if True, dicts if False.

        Returns:
            List of agents.
        """
        return self._fetch_all(
            path=f"groups/{project_id}/agents/{agent_type}",
            item_type=Agent if as_obj else None,
            items_per_page=items_per_page,
        )

    def list_iter(
        self,
        project_id: str,
        agent_type: str,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> PageIterator[Agent]:
        """Iterate over agents of a given type in a project.

        Args:
            project_id: Project (group) ID.
            agent_type: Agent type (MONITORING, BACKUP, or AUTOMATION).
            items_per_page: Number of items per page.
            as_obj: Return Agent objects if True, dicts if False.

        Returns:
            Iterator over agents.
        """
        return self._paginate(
            path=f"groups/{project_id}/agents/{agent_type}",
            item_type=Agent if as_obj else None,
            items_per_page=items_per_page,
        )

    def list_monitoring(
        self,
        project_id: str,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> List[Agent]:
        """Get all monitoring agents in a project.

        Convenience method for health checks — monitoring agents must be
        ACTIVE for Ops Manager to collect metrics.

        Args:
            project_id: Project (group) ID.
            items_per_page: Number of items per page.
            as_obj: Return Agent objects if True, dicts if False.

        Returns:
            List of monitoring agents.
        """
        return self.list(
            project_id=project_id,
            agent_type=self.TYPE_MONITORING,
            items_per_page=items_per_page,
            as_obj=as_obj,
        )

    def list_backup(
        self,
        project_id: str,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> List[Agent]:
        """Get all backup agents in a project.

        Args:
            project_id: Project (group) ID.
            items_per_page: Number of items per page.
            as_obj: Return Agent objects if True, dicts if False.

        Returns:
            List of backup agents.
        """
        return self.list(
            project_id=project_id,
            agent_type=self.TYPE_BACKUP,
            items_per_page=items_per_page,
            as_obj=as_obj,
        )
