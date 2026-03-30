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
from opsmanager.services.alert_configurations import AlertConfigurationsService
from opsmanager.services.global_alerts import GlobalAlertsService
from opsmanager.services.agents import AgentsService
from opsmanager.services.backup import BackupService
from opsmanager.services.automation import AutomationService
from opsmanager.services.events import EventsService
from opsmanager.services.diagnostics import DiagnosticsService
from opsmanager.services.maintenance_windows import MaintenanceWindowsService
from opsmanager.services.log_collection import LogCollectionService
from opsmanager.services.server_usage import ServerUsageService
from opsmanager.services.feature_control import FeatureControlService
from opsmanager.services.teams import TeamsService
from opsmanager.services.users import UsersService
from opsmanager.services.api_keys import APIKeysService
from opsmanager.services.version import VersionService
from opsmanager.services.live_migration import LiveMigrationService
from opsmanager.services.admin_backup_stores import AdminBackupStoresService
from opsmanager.services.global_admin import GlobalAdminService


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
        events = client.events.list_project_events(
            project_id="abc123",
            min_date="2026-01-01T00:00:00Z",
            max_date="2026-03-31T23:59:59Z",
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
        alerts: Service for alert instances.
        alert_configurations: Service for alert configuration rules.
        global_alerts: Service for global (cross-project) alerts.
        agents: Service for monitoring, backup, and automation agent status.
        backup: Service for backup snapshots, configs, restore jobs, and checkpoints.
        automation: Service for automation config and status.
        events: Service for the audit event log.
        diagnostics: Service for diagnostic archive downloads.
        maintenance_windows: Service for scheduled maintenance windows.
        log_collection: Service for log collection jobs and downloads.
        server_usage: Service for license/capacity reporting.
        feature_control: Service for feature control policies.
        teams: Service for organization teams.
        users: Service for user lookup.
        api_keys: Service for API key inventory.
        version: Service for Ops Manager and MongoDB version information.
        live_migration: Service for live data migration connection status.
        admin_backup_stores: Service for admin backup store configurations.
        global_admin: Service for global admin API keys and IP whitelist.
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
        self._agents = AgentsService(self._session)
        self._backup = BackupService(self._session)

        self._alert_configurations = AlertConfigurationsService(self._session)
        self._global_alerts = GlobalAlertsService(self._session)
        self._automation = AutomationService(self._session)
        self._events = EventsService(self._session)
        self._diagnostics = DiagnosticsService(self._session)
        self._maintenance_windows = MaintenanceWindowsService(self._session)
        self._log_collection = LogCollectionService(self._session)
        self._server_usage = ServerUsageService(self._session)
        self._feature_control = FeatureControlService(self._session)
        self._teams = TeamsService(self._session)
        self._users = UsersService(self._session)
        self._api_keys = APIKeysService(self._session)
        self._version = VersionService(self._session)
        self._live_migration = LiveMigrationService(self._session)
        self._admin_backup_stores = AdminBackupStoresService(self._session)
        self._global_admin = GlobalAdminService(self._session)

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
        """Service for alert instances."""
        return self._alerts

    @property
    def agents(self) -> AgentsService:
        """Service for monitoring, backup, and automation agent status."""
        return self._agents

    @property
    def backup(self) -> BackupService:
        """Service for backup snapshots, configs, restore jobs, and checkpoints."""
        return self._backup

    @property
    def alert_configurations(self) -> AlertConfigurationsService:
        """Service for alert configuration rules (policies that define when alerts fire)."""
        return self._alert_configurations

    @property
    def global_alerts(self) -> GlobalAlertsService:
        """Service for global alerts spanning all projects."""
        return self._global_alerts

    @property
    def automation(self) -> AutomationService:
        """Service for automation config and convergence status."""
        return self._automation

    @property
    def events(self) -> EventsService:
        """Service for the audit event log (org and project level)."""
        return self._events

    @property
    def diagnostics(self) -> DiagnosticsService:
        """Service for downloading diagnostic archives."""
        return self._diagnostics

    @property
    def maintenance_windows(self) -> MaintenanceWindowsService:
        """Service for scheduled maintenance windows."""
        return self._maintenance_windows

    @property
    def log_collection(self) -> LogCollectionService:
        """Service for log collection jobs and log downloads."""
        return self._log_collection

    @property
    def server_usage(self) -> ServerUsageService:
        """Service for license and capacity reporting."""
        return self._server_usage

    @property
    def feature_control(self) -> FeatureControlService:
        """Service for feature control policies."""
        return self._feature_control

    @property
    def teams(self) -> TeamsService:
        """Service for organization teams."""
        return self._teams

    @property
    def users(self) -> UsersService:
        """Service for user lookup by ID or username."""
        return self._users

    @property
    def api_keys(self) -> APIKeysService:
        """Service for API key inventory (org and project level)."""
        return self._api_keys

    @property
    def version(self) -> VersionService:
        """Service for Ops Manager and MongoDB version information."""
        return self._version

    @property
    def live_migration(self) -> LiveMigrationService:
        """Service for live data migration connection status."""
        return self._live_migration

    @property
    def admin_backup_stores(self) -> AdminBackupStoresService:
        """Service for admin backup store configurations (blockstore, S3, filesystem, oplog, sync, daemon, project jobs)."""
        return self._admin_backup_stores

    @property
    def global_admin(self) -> GlobalAdminService:
        """Service for global admin API keys and IP whitelist."""
        return self._global_admin

    # --- Client utilities ---

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

    def __exit__(self, exc_type: type = None, exc_val: BaseException = None, exc_tb: object = None) -> None:
        """Exit context manager."""
        self.close()

    def __repr__(self) -> str:
        return f"OpsManagerClient(base_url={self._session.base_url!r})"
