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
Main client for MongoDB Ops Manager API.

This is the primary entry point for interacting with the Ops Manager API.
"""

from typing import Callable, Optional

from opsmanager.auth import OpsManagerAuth
from opsmanager.network import NetworkSession
from opsmanager.services.organizations import OrganizationsService
from opsmanager.services.projects import ProjectsService
from opsmanager.services.clusters import ClustersService
from opsmanager.services.deployments import DeploymentsService
from opsmanager.services.measurements import MeasurementsService
from opsmanager.services.performance_advisor import PerformanceAdvisorService
from opsmanager.services.alerts import AlertsService


class OpsManagerClient:
    """Client for MongoDB Ops Manager API.

    This is the main entry point for interacting with Ops Manager.
    It provides access to all API services through properties.

    Example:
        from opsmanager import OpsManagerClient

        # Create client
        client = OpsManagerClient(
            base_url="https://ops-manager.example.com",
            public_key="your-public-key",
            private_key="your-private-key",
        )

        # Use services
        projects = client.projects.list()
        hosts = client.deployments.list_hosts(project_id="abc123")
        metrics = client.measurements.host(
            project_id="abc123",
            host_id="host123",
            period="P1D",
        )

        # Close when done
        client.close()

        # Or use as context manager
        with OpsManagerClient(...) as client:
            projects = client.projects.list()

    Attributes:
        organizations: Service for managing organizations.
        projects: Service for managing projects (groups).
        clusters: Service for managing clusters.
        deployments: Service for hosts, databases, and disks.
        measurements: Service for time-series metrics.
        performance_advisor: Service for slow query analysis and index suggestions.
        alerts: Service for alert management.
    """

    # Default base URL for Cloud Manager (Ops Manager URL must be provided)
    DEFAULT_BASE_URL = "https://cloud.mongodb.com"

    def __init__(
        self,
        base_url: str,
        public_key: str,
        private_key: str,
        timeout: float = 30.0,
        rate_limit: float = 2.0,
        rate_burst: int = 1,
        retry_count: int = 3,
        retry_backoff: float = 1.0,
        verify_ssl: bool = True,
        user_agent: Optional[str] = None,
    ):
        """Initialize the Ops Manager client.

        Args:
            base_url: Base URL for the Ops Manager instance
                (e.g., "https://ops-manager.example.com").
            public_key: API public key.
            private_key: API private key.
            timeout: Request timeout in seconds (default 30).
            rate_limit: Maximum requests per second (default 2).
                Set conservatively to protect production Ops Manager.
            rate_burst: Maximum burst size (default 1 = no bursting).
                With burst=1, requests are strictly spaced by rate_limit.
                Higher values allow short bursts before throttling.
            retry_count: Number of retries for failed requests (default 3).
            retry_backoff: Base backoff time between retries in seconds.
            verify_ssl: Whether to verify SSL certificates (default True).
            user_agent: Custom User-Agent string.
        """
        # Create authentication handler
        auth = OpsManagerAuth(public_key=public_key, private_key=private_key)

        # Create network session with rate limiting
        self._session = NetworkSession(
            base_url=base_url.rstrip("/"),
            auth=auth,
            timeout=timeout,
            rate_limit=rate_limit,
            rate_burst=rate_burst,
            retry_count=retry_count,
            retry_backoff=retry_backoff,
            verify_ssl=verify_ssl,
            user_agent=user_agent,
        )

        # Initialize services
        self._organizations = OrganizationsService(self._session)
        self._projects = ProjectsService(self._session)
        self._clusters = ClustersService(self._session)
        self._deployments = DeploymentsService(self._session)
        self._measurements = MeasurementsService(self._session)
        self._performance_advisor = PerformanceAdvisorService(self._session)
        self._alerts = AlertsService(self._session)

    @property
    def organizations(self) -> OrganizationsService:
        """Service for managing organizations."""
        return self._organizations

    @property
    def projects(self) -> ProjectsService:
        """Service for managing projects (groups)."""
        return self._projects

    @property
    def clusters(self) -> ClustersService:
        """Service for managing clusters."""
        return self._clusters

    @property
    def deployments(self) -> DeploymentsService:
        """Service for hosts, databases, and disks."""
        return self._deployments

    @property
    def measurements(self) -> MeasurementsService:
        """Service for time-series metrics."""
        return self._measurements

    @property
    def performance_advisor(self) -> PerformanceAdvisorService:
        """Service for slow query analysis and index suggestions."""
        return self._performance_advisor

    @property
    def alerts(self) -> AlertsService:
        """Service for alert management."""
        return self._alerts

    def set_rate_limit(self, rate: float) -> None:
        """Update the rate limit for API requests.

        Args:
            rate: Maximum requests per second.
        """
        self._session.set_rate_limit(rate)

    def on_request(self, callback: Callable) -> None:
        """Set a callback to be invoked before each request.

        Useful for logging or debugging.

        Args:
            callback: Function(method, url, kwargs) called before each request.
        """
        self._session.on_request(callback)

    def on_response(self, callback: Callable) -> None:
        """Set a callback to be invoked after each response.

        Useful for logging or debugging.

        Args:
            callback: Function(response) called after each response.
        """
        self._session.on_response(callback)

    def close(self) -> None:
        """Close the client and release resources."""
        self._session.close()

    def __enter__(self) -> "OpsManagerClient":
        """Enter context manager."""
        return self

    def __exit__(self, *args) -> None:
        """Exit context manager."""
        self.close()

    def __repr__(self) -> str:
        return f"OpsManagerClient(base_url={self._session.base_url!r})"
