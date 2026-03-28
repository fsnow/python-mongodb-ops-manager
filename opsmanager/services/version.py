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
Version service for MongoDB Ops Manager API.

Provides access to the Ops Manager service version (useful as a health check
and for including the Ops Manager version in diagnostic reports) and to the
MongoDB version manifest (maps version strings to release metadata).

See: https://www.mongodb.com/docs/ops-manager/current/reference/api/
"""

from typing import Any, Dict

from opsmanager.services.base import BaseService


class VersionService(BaseService):
    """Service for Ops Manager and MongoDB version information.

    Provides two endpoints:
    - ``get_service_version``: Returns the running Ops Manager version.
      Useful as a health check or for including the OM version in reports.
    - ``get_version_manifest``: Returns MongoDB release metadata for a
      specific version string. Useful for enriching version compliance
      reports with release dates and EOL status.
    """

    # Override base path: service version uses private/unauth path
    BASE_PATH = "api/public/v1.0"

    def get_service_version(self) -> Dict[str, Any]:
        """Get the running Ops Manager service version.

        This is an unauthenticated endpoint — no API key is required.
        Returns the Ops Manager version string and git hash.

        Returns:
            Service version info as a raw dict, e.g.
            ``{"version": "5.0.12", "gitVersion": "abc123..."}``.
        """
        # This endpoint uses a different base path
        full_path = "api/private/unauth/version"
        return self._session.get(full_path)

    def get_version_manifest(self, version: str) -> Dict[str, Any]:
        """Get the MongoDB version manifest for a specific version.

        Returns release metadata for the given MongoDB version string,
        including available builds, release dates, and platform support.
        Useful for enriching version compliance reports.

        Args:
            version: MongoDB version string (e.g. ``"7.0"``).

        Returns:
            Version manifest as a raw dict.
        """
        full_path = f"static/version_manifest/{version}"
        return self._session.get(full_path)
