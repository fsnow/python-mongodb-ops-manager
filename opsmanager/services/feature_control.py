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
Feature control policies service for MongoDB Ops Manager API.

Provides read access to the feature control policies for a project.
Feature control policies restrict which MongoDB features can be used,
which is important for security hardening evidence — e.g., confirming
that certain features are disabled as required by policy.

See: https://www.mongodb.com/docs/ops-manager/current/reference/api/feature-control-policies/
"""

from typing import Any, Dict, List

from opsmanager.services.base import BaseService
from opsmanager.types import FeaturePolicy


class FeatureControlService(BaseService):
    """Service for reading feature control policies.

    Feature control policies document which MongoDB features are enabled or
    restricted in each project. Use this to produce security hardening evidence
    showing that specific features are disabled per organizational policy.
    """

    def get(
        self,
        project_id: str,
        as_obj: bool = True,
    ) -> FeaturePolicy:
        """Get the feature control policies for a project.

        Returns the current feature policy including which external management
        system owns the policy and the list of restricted features.

        Args:
            project_id: Project (group) ID.
            as_obj: Return FeaturePolicy object if True, dict if False.

        Returns:
            Feature control policy for the project.
        """
        response = self._get(f"groups/{project_id}/controlledFeature")
        return FeaturePolicy.from_dict(response) if as_obj else response

    def list_supported_policies(self) -> List[Dict[str, Any]]:
        """Get all supported feature control policy names.

        Returns the list of feature names that can be restricted via the
        feature control API. Use to enumerate available policy options.

        Returns:
            List of supported policy dicts.
        """
        response = self._get("groups/availablePolicies")
        if isinstance(response, list):
            return response
        return response.get("policies", response.get("results", []))
