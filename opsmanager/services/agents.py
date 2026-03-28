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
from opsmanager.types import Agent, AgentAPIKey, AgentVersions
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

    def list_links(
        self,
        project_id: str,
    ) -> Dict[str, Any]:
        """Get all agent links (download URLs) for a project.

        Returns the agent download links — URLs for downloading monitoring,
        backup, and automation agent installers for this project.

        Args:
            project_id: Project (group) ID.

        Returns:
            Agent links as a raw dict (API response).
        """
        return self._get(f"groups/{project_id}/agents")

    def get_project_versions(
        self,
        project_id: str,
        as_obj: bool = True,
    ) -> AgentVersions:
        """Get agent version information for a project.

        Returns the current versions of all agents in the project and flags
        indicating whether any agents are out of date or deprecated.
        Useful for security patch compliance reporting.

        Args:
            project_id: Project (group) ID.
            as_obj: Return AgentVersions object if True, dict if False.

        Returns:
            Agent version summary for the project.
        """
        response = self._get(f"groups/{project_id}/agents/versions")
        return AgentVersions.from_dict(response) if as_obj else response

    def get_global_versions(self) -> Dict[str, Any]:
        """Get the latest available agent versions across the Ops Manager deployment.

        Returns the current globally-available versions of the automation,
        monitoring, and backup agents. Compare against project versions to
        identify which projects have outdated agents.

        Returns:
            Global software versions as a raw dict (API response).
        """
        return self._get("softwareComponents/versions")

    def list_api_keys(
        self,
        project_id: str,
        as_obj: bool = True,
    ) -> List[AgentAPIKey]:
        """Get all agent API keys for a project.

        Args:
            project_id: Project (group) ID.
            as_obj: Return AgentAPIKey objects if True, dicts if False.

        Returns:
            List of agent API keys.
        """
        response = self._get(f"groups/{project_id}/agentapikeys")
        results = response if isinstance(response, list) else response.get("results", [])
        if as_obj:
            return [AgentAPIKey.from_dict(item) for item in results]
        return results
