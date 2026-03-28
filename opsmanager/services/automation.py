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
Automation service for MongoDB Ops Manager API.

Provides read access to the automation configuration and status for a project.
The automation config is the source of truth for cluster topology, MongoDB versions,
TLS settings, authentication configuration, and agent settings.

See: https://www.mongodb.com/docs/ops-manager/current/reference/api/automation-config/
"""

from typing import Any, Dict

from opsmanager.services.base import BaseService
from opsmanager.types import AutomationStatus


class AutomationService(BaseService):
    """Service for reading automation configuration and status.

    The automation config (``get_config``) is a complex document that describes
    the full desired state of all MongoDB processes in a project. It is returned
    as a raw dict because its schema is large and version-dependent.

    The automation status (``get_status``) shows whether all agents have applied
    the current goal version — useful for confirming that configuration changes
    (e.g. TLS enforcement, auth changes) are fully rolled out across the fleet.
    """

    def get_config(self, project_id: str) -> Dict[str, Any]:
        """Get the automation configuration for a project.

        Returns the full desired-state document covering all MongoDB processes,
        replica sets, sharding config, authentication settings, TLS config,
        and agent configuration.

        The config is returned as a raw dict because its schema is large and
        varies by MongoDB and Ops Manager version. Key top-level fields include:
        ``processes``, ``replicaSets``, ``sharding``, ``auth``, ``ssl``,
        ``mongoDbVersions``, ``backupVersions``, ``monitoringVersions``.

        Args:
            project_id: Project (group) ID.

        Returns:
            Automation config as a raw dict (full API response).
        """
        return self._get(f"groups/{project_id}/automationConfig")

    def get_status(
        self,
        project_id: str,
        as_obj: bool = True,
    ) -> AutomationStatus:
        """Get the automation status for a project.

        Shows the current goal version and the conf version reported by each
        agent. When all agents report a ``goalVersion`` equal to or greater than
        the top-level ``goalVersion``, the deployment is fully converged.

        Args:
            project_id: Project (group) ID.
            as_obj: Return AutomationStatus object if True, dict if False.

        Returns:
            Automation status including per-agent convergence state.
        """
        response = self._get(f"groups/{project_id}/automationStatus")
        return AutomationStatus.from_dict(response) if as_obj else response

    def get_backup_agent_config(self, project_id: str) -> Dict[str, Any]:
        """Get the backup agent configuration for a project.

        Returns the configuration section that controls backup agent behavior,
        including log paths, SSL settings, and Kerberos configuration.

        Args:
            project_id: Project (group) ID.

        Returns:
            Backup agent configuration as a raw dict.
        """
        return self._get(f"groups/{project_id}/automationConfig/backupAgentConfig")

    def get_monitoring_agent_config(self, project_id: str) -> Dict[str, Any]:
        """Get the monitoring agent configuration for a project.

        Returns the configuration section that controls monitoring agent
        behavior, including log paths, SSL settings, and collection intervals.

        Args:
            project_id: Project (group) ID.

        Returns:
            Monitoring agent configuration as a raw dict.
        """
        return self._get(f"groups/{project_id}/automationConfig/monitoringAgentConfig")
