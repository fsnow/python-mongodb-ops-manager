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
MongoDB Ops Manager Python Client

A production-quality Python client library for the MongoDB Ops Manager API.

Example usage:
    from opsmanager import OpsManagerClient

    client = OpsManagerClient(
        base_url="https://ops-manager.example.com",
        public_key="your-public-key",
        private_key="your-private-key",
    )

    # List all hosts in a project
    hosts = client.deployments.list_hosts(project_id="your-project-id")

    # Get metrics for a host
    metrics = client.measurements.host(
        project_id="your-project-id",
        host_id="host-id",
        granularity="PT1M",
        period="P1D",
    )
"""

__version__ = "0.2.0"
__author__ = "Frank Snow"

from opsmanager.client import OpsManagerClient
from opsmanager.errors import (
    OpsManagerError,
    OpsManagerAuthenticationError,
    OpsManagerNotFoundError,
    OpsManagerBadRequestError,
    OpsManagerForbiddenError,
    OpsManagerConflictError,
    OpsManagerServerError,
    OpsManagerRateLimitError,
)

__all__ = [
    "OpsManagerClient",
    "OpsManagerError",
    "OpsManagerAuthenticationError",
    "OpsManagerNotFoundError",
    "OpsManagerBadRequestError",
    "OpsManagerForbiddenError",
    "OpsManagerConflictError",
    "OpsManagerServerError",
    "OpsManagerRateLimitError",
    "__version__",
]
