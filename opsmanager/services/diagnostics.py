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
Diagnostics service for MongoDB Ops Manager API.

Provides access to the diagnostic archive for a project — a gzip-compressed
bundle containing logs, configuration snapshots, and operational data useful
for root cause analysis and post-incident investigations.

See: https://www.mongodb.com/docs/ops-manager/current/reference/api/diagnostics/
"""

from typing import Optional

from opsmanager.services.base import BaseService


class DiagnosticsService(BaseService):
    """Service for downloading diagnostic archives.

    The diagnostic archive is a gzip-compressed file containing logs and
    configuration data for all processes in a project. It is the primary
    tool for deep incident investigation and post-incident reporting.

    The archive is returned as raw bytes. Write it to a ``.tar.gz`` file:

    Example::

        archive = client.diagnostics.get(project_id="abc123")
        with open("diagnostics.tar.gz", "wb") as f:
            f.write(archive)
    """

    def get(
        self,
        project_id: str,
        minutes: Optional[int] = None,
    ) -> bytes:
        """Download the diagnostic archive for a project.

        Returns a gzip-compressed archive containing logs and configuration
        snapshots for all MongoDB processes and agents in the project.

        Args:
            project_id: Project (group) ID.
            minutes: Number of minutes of log data to include (default: all
                available). Limiting this reduces archive size for large
                deployments.

        Returns:
            Raw gzip-compressed archive bytes. Write to a ``.tar.gz`` file.
        """
        params = {}
        if minutes is not None:
            params["minutes"] = minutes
        return self._download(
            f"groups/{project_id}/diagnostics",
            params=params or None,
        )
