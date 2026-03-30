#!/usr/bin/env python3
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
Extended live integration tests covering all services added in Tiers 1-3
plus log collection write operations.

The original test_live.py covers the 9 original services. This file covers
every service not yet tested there.

Usage:
    python tests/test_live_extended.py --verbose \\
        --base-url http://ops-manager:8081 \\
        --public-key xqjuwbve \\
        --private-key 7226793f-... \\
        --admin-public-key imvefyvt \\
        --admin-private-key 4d1df44f-... \\
        --org-id 69bac7e5ee8fcf25730c75ce \\
        --project-id 69bac7e5ee8fcf25730c75d2
"""

import argparse
import os
import sys
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from opsmanager import OpsManagerClient
from opsmanager.types import (
    AutomationStatus,
    AlertConfiguration,
    Event,
    MaintenanceWindow,
    LogCollectionJob,
    Team,
    User,
    APIKey,
    AgentVersions,
    AgentAPIKey,
    FeaturePolicy,
    BackupConfig,
)
from opsmanager.errors import (
    OpsManagerError,
    OpsManagerNotFoundError,
    OpsManagerForbiddenError,
)


class ExtendedLiveTestRunner:
    """Integration tests for Tier 1-3 services not covered by test_live.py."""

    def __init__(
        self,
        client: OpsManagerClient,
        admin_client: Optional[OpsManagerClient],
        org_id: str,
        project_id: str,
        verbose: bool = False,
    ):
        self.client = client
        self.admin_client = admin_client
        self.org_id = org_id
        self.project_id = project_id
        self.verbose = verbose
        self.results: dict = {}

        # Discovered during setup
        self.cluster_id: Optional[str] = None
        self.cluster_name: Optional[str] = None
        self.primary_host_id: Optional[str] = None
        self.first_user_id: Optional[str] = None
        self.first_username: Optional[str] = None
        self.created_log_job_id: Optional[str] = None

        self._setup()

    def _setup(self):
        """Discover cluster and host info once for all tests."""
        try:
            clusters = self.client.clusters.list(self.project_id)
            if clusters:
                self.cluster_id = clusters[0].id
                self.cluster_name = clusters[0].cluster_name
                self.log(f"  Setup: cluster={self.cluster_name} ({self.cluster_id})")
        except Exception as e:
            self.log(f"  Setup: could not discover cluster — {e}")

        try:
            hosts = self.client.deployments.list_hosts(self.project_id)
            for h in hosts:
                if h.replica_state_name == "PRIMARY":
                    self.primary_host_id = h.id
                    break
            if not self.primary_host_id and hosts:
                self.primary_host_id = hosts[0].id
        except Exception as e:
            self.log(f"  Setup: could not discover hosts — {e}")

    def log(self, msg: str) -> None:
        if self.verbose:
            print(msg)

    def run_test(self, name: str, func) -> bool:
        print(f"\n{'='*60}")
        print(f"TEST: {name}")
        print("=" * 60)
        try:
            func()
            print(f"✓ PASS: {name}")
            self.results[name] = True
            return True
        except Exception as e:
            print(f"✗ FAIL: {name}")
            print(f"  Error: {e}")
            import traceback
            if self.verbose:
                traceback.print_exc()
            self.results[name] = False
            return False

    # ------------------------------------------------------------------
    # Extended methods on existing services
    # ------------------------------------------------------------------

    def test_organizations_list_users(self) -> None:
        """organizations.list_users — new method not in original tests."""
        users = self.client.organizations.list_users(self.org_id)
        self.log(f"  Org users: {len(users)}")
        for u in users[:3]:
            assert isinstance(u, User), f"Expected User, got {type(u)}"
            assert u.id or u.username, "User has neither id nor username"
            self.log(f"    {u.username} ({u.id})")
            # Save for users service tests
            if not self.first_user_id and u.id:
                self.first_user_id = u.id
                self.first_username = u.username

    def test_projects_list_users(self) -> None:
        """projects.list_users — new method not in original tests."""
        users = self.client.projects.list_users(self.project_id)
        self.log(f"  Project users: {len(users)}")
        for u in users[:3]:
            assert isinstance(u, User), f"Expected User, got {type(u)}"
            self.log(f"    {u.username}")
            if not self.first_user_id and u.id:
                self.first_user_id = u.id
                self.first_username = u.username

    def test_projects_get_teams(self) -> None:
        """projects.get_teams — new method not in original tests."""
        teams = self.client.projects.get_teams(self.project_id)
        self.log(f"  Project teams: {len(teams)}")
        # May be empty — that's fine

    def test_agents_extended(self) -> None:
        """list_links, get_project_versions, get_global_versions, list_api_keys."""
        # Agent download links
        links = self.client.agents.list_links(self.project_id)
        assert isinstance(links, dict), f"Expected dict, got {type(links)}"
        self.log(f"  Agent links keys: {list(links.keys())[:5]}")

        # Project agent versions
        versions = self.client.agents.get_project_versions(self.project_id)
        assert isinstance(versions, AgentVersions), f"Expected AgentVersions, got {type(versions)}"
        self.log(f"  Project versions: automation={versions.automation_agent_version}")
        self.log(f"  Any deprecated: {versions.is_any_agent_version_deprecated}")

        # Global agent versions
        global_v = self.client.agents.get_global_versions()
        assert isinstance(global_v, dict), f"Expected dict, got {type(global_v)}"
        self.log(f"  Global versions keys: {list(global_v.keys())[:5]}")

        # Agent API keys (may be IP-restricted on some OM deployments)
        try:
            agent_keys = self.client.agents.list_api_keys(self.project_id)
            assert isinstance(agent_keys, list), f"Expected list, got {type(agent_keys)}"
            self.log(f"  Agent API keys: {len(agent_keys)}")
            for k in agent_keys[:2]:
                assert isinstance(k, AgentAPIKey), f"Expected AgentAPIKey, got {type(k)}"
        except OpsManagerForbiddenError as e:
            self.log(f"  (Agent API keys restricted: {e})")

    def test_backup_extended(self) -> None:
        """list_backup_configs, get_snapshot_schedule, list_restore_jobs, list_checkpoints."""
        if not self.cluster_id:
            self.log("  No cluster — skipping extended backup tests")
            return

        # List all backup configs for the project
        configs = self.client.backup.list_backup_configs(self.project_id)
        assert isinstance(configs, list), f"Expected list, got {type(configs)}"
        self.log(f"  Backup configs: {len(configs)}")
        for c in configs:
            assert isinstance(c, BackupConfig), f"Expected BackupConfig, got {type(c)}"
            self.log(f"    cluster_id={c.cluster_id} status={c.status_name}")

        # Snapshot schedule (may 404 if backup not configured)
        try:
            schedule = self.client.backup.get_snapshot_schedule(
                self.project_id, self.cluster_id
            )
            from opsmanager.types import SnapshotSchedule
            assert isinstance(schedule, SnapshotSchedule), f"Expected SnapshotSchedule, got {type(schedule)}"
            self.log(f"  Snapshot schedule: cluster_id={schedule.cluster_id} frequency_hours={schedule.snapshot_interval_hours}")
        except OpsManagerNotFoundError:
            self.log("  (No snapshot schedule — backup not configured)")
        except OpsManagerError as e:
            if "BACKUP" in str(e).upper():
                self.log(f"  (Snapshot schedule not available: {e})")
            else:
                raise

        # Restore jobs (may be empty)
        try:
            jobs = self.client.backup.list_restore_jobs(self.project_id, self.cluster_id)
            assert isinstance(jobs, list), f"Expected list, got {type(jobs)}"
            self.log(f"  Restore jobs: {len(jobs)}")
        except OpsManagerError as e:
            self.log(f"  (Restore jobs not available: {e})")

        # Checkpoints (only for sharded clusters; replica sets return empty or 404)
        try:
            checkpoints = self.client.backup.list_checkpoints(
                self.project_id, self.cluster_name
            )
            assert isinstance(checkpoints, list), f"Expected list, got {type(checkpoints)}"
            self.log(f"  Checkpoints: {len(checkpoints)}")
        except OpsManagerError as e:
            self.log(f"  (Checkpoints not available: {e})")

    # ------------------------------------------------------------------
    # New services — Tier 1
    # ------------------------------------------------------------------

    def test_events(self) -> None:
        """Events service: list_project_events, list_organization_events, get."""
        # Project events
        project_events = self.client.events.list_project_events(self.project_id)
        assert isinstance(project_events, list), f"Expected list, got {type(project_events)}"
        self.log(f"  Project events: {len(project_events)}")
        for ev in project_events[:3]:
            assert isinstance(ev, Event), f"Expected Event, got {type(ev)}"
            assert ev.id, "Event id is empty"
            self.log(f"    [{ev.created}] {ev.event_type_name}")

        # Get by ID if any exist
        if project_events:
            ev = self.client.events.get_project_event(self.project_id, project_events[0].id)
            assert ev.id == project_events[0].id, "Event ID mismatch on get"
            self.log(f"  Get project event by ID: OK")

        # Org events
        org_events = self.client.events.list_organization_events(self.org_id)
        assert isinstance(org_events, list), f"Expected list, got {type(org_events)}"
        self.log(f"  Org events: {len(org_events)}")

        if org_events:
            ev = self.client.events.get_organization_event(self.org_id, org_events[0].id)
            assert ev.id == org_events[0].id, "Org event ID mismatch on get"
            self.log(f"  Get org event by ID: OK")

    def test_automation(self) -> None:
        """Automation service: get_status, get_config, agent sub-configs."""
        # Convergence status
        status = self.client.automation.get_status(self.project_id)
        assert isinstance(status, AutomationStatus), f"Expected AutomationStatus, got {type(status)}"
        assert status.goal_version is not None, "goal_version is None"
        self.log(f"  Goal version: {status.goal_version}")
        self.log(f"  In goal state: {status.is_in_goal_state}")
        self.log(f"  Processes: {len(status.processes)}")

        # Full config (large doc — may be unauthorized for read-only keys)
        try:
            config = self.client.automation.get_config(self.project_id)
            assert isinstance(config, dict), f"Expected dict, got {type(config)}"
            assert "processes" in config or "replicaSets" in config or "mongoDbVersions" in config, \
                f"Automation config missing expected keys; got: {list(config.keys())[:10]}"
            self.log(f"  Config top-level keys: {list(config.keys())[:8]}")
        except OpsManagerError as e:
            self.log(f"  (Automation config not accessible: {e})")

        # Backup agent sub-config (may be unauthorized for read-only keys)
        try:
            ba_config = self.client.automation.get_backup_agent_config(self.project_id)
            assert isinstance(ba_config, dict), f"Expected dict, got {type(ba_config)}"
            self.log(f"  Backup agent config keys: {list(ba_config.keys())[:5]}")
        except OpsManagerError as e:
            self.log(f"  (Backup agent config not accessible: {e})")

        # Monitoring agent sub-config (may be unauthorized for read-only keys)
        try:
            ma_config = self.client.automation.get_monitoring_agent_config(self.project_id)
            assert isinstance(ma_config, dict), f"Expected dict, got {type(ma_config)}"
            self.log(f"  Monitoring agent config keys: {list(ma_config.keys())[:5]}")
        except OpsManagerError as e:
            self.log(f"  (Monitoring agent config not accessible: {e})")

    def test_alert_configurations(self) -> None:
        """Alert configurations: list, get, get_open_alerts, list_matcher_fields."""
        configs = self.client.alert_configurations.list(self.project_id)
        assert isinstance(configs, list), f"Expected list, got {type(configs)}"
        self.log(f"  Alert configurations: {len(configs)}")
        for cfg in configs[:3]:
            assert isinstance(cfg, AlertConfiguration), f"Expected AlertConfiguration, got {type(cfg)}"
            self.log(f"    [{cfg.id}] {cfg.event_type_name} enabled={cfg.enabled}")

        # Get by ID if any exist
        if configs:
            cfg_id = configs[0].id
            cfg = self.client.alert_configurations.get(self.project_id, cfg_id)
            assert cfg.id == cfg_id, "AlertConfiguration ID mismatch on get"
            self.log(f"  Get by ID: OK")

            # Open alerts for this config
            open_alerts = self.client.alert_configurations.get_open_alerts(
                self.project_id, cfg_id
            )
            assert isinstance(open_alerts, list), f"Expected list, got {type(open_alerts)}"
            self.log(f"  Open alerts for config: {len(open_alerts)}")

        # Matcher field names — always returns data
        fields = self.client.alert_configurations.list_matcher_fields()
        assert isinstance(fields, list), f"Expected list, got {type(fields)}"
        assert len(fields) > 0, "list_matcher_fields returned empty list"
        self.log(f"  Matcher fields ({len(fields)}): {fields[:5]}")

    def test_global_alerts(self) -> None:
        """Global alerts: list, list_open."""
        client = self.admin_client or self.client
        try:
            alerts = client.global_alerts.list()
            assert isinstance(alerts, list), f"Expected list, got {type(alerts)}"
            self.log(f"  Global alerts: {len(alerts)}")
            for a in alerts[:3]:
                assert "id" in a or hasattr(a, "id"), "Alert has no id"
                self.log(f"    {a}")

            open_alerts = client.global_alerts.list_open()
            assert isinstance(open_alerts, list), f"Expected list, got {type(open_alerts)}"
            self.log(f"  Open global alerts: {len(open_alerts)}")
        except (OpsManagerForbiddenError, OpsManagerError) as e:
            if "UNAUTHORIZED" in str(e) or "403" in str(e) or "Forbidden" in str(e):
                self.log(f"  (Global alerts restricted by permissions: {e})")
            else:
                raise

    def test_diagnostics(self) -> None:
        """Diagnostics: download archive (returns bytes)."""
        try:
            data = self.client.diagnostics.get(self.project_id)
            assert isinstance(data, bytes), f"Expected bytes, got {type(data)}"
            assert len(data) > 0, "Diagnostics archive is empty"
            # Check for gzip magic bytes
            is_gzip = data[:2] == b"\x1f\x8b"
            self.log(f"  Diagnostics archive: {len(data)} bytes, gzip={is_gzip}")
        except OpsManagerError as e:
            # Some OM versions return 406 Not Acceptable when Accept header is application/json
            self.log(f"  (Diagnostics not available on this instance: {e})")

    def test_maintenance_windows(self) -> None:
        """Maintenance windows: list (may be empty)."""
        windows = self.client.maintenance_windows.list(self.project_id)
        assert isinstance(windows, list), f"Expected list, got {type(windows)}"
        self.log(f"  Maintenance windows: {len(windows)}")
        for w in windows[:3]:
            assert isinstance(w, MaintenanceWindow), f"Expected MaintenanceWindow, got {type(w)}"
            self.log(f"    [{w.id}] {w.start_date} — {w.end_date}")

        # Get by ID if any exist
        if windows:
            w = self.client.maintenance_windows.get(self.project_id, windows[0].id)
            assert w.id == windows[0].id, "MaintenanceWindow ID mismatch on get"
            self.log(f"  Get by ID: OK")

    # ------------------------------------------------------------------
    # New services — Tier 2
    # ------------------------------------------------------------------

    def test_log_collection_read(self) -> None:
        """Log collection read: list, get (may be empty)."""
        jobs = self.client.log_collection.list(self.project_id)
        assert isinstance(jobs, list), f"Expected list, got {type(jobs)}"
        self.log(f"  Log collection jobs: {len(jobs)}")
        for j in jobs[:3]:
            assert isinstance(j, LogCollectionJob), f"Expected LogCollectionJob, got {type(j)}"
            self.log(f"    [{j.id}] status={j.status} resource={j.resource_name}")

        if jobs:
            j = self.client.log_collection.get(self.project_id, jobs[0].id)
            assert j.id == jobs[0].id, "LogCollectionJob ID mismatch on get"
            self.log(f"  Get by ID: OK")

    def test_log_collection_write(self) -> None:
        """Log collection write: create, get, extend, delete (requires write access)."""
        write_client = self.admin_client
        if not write_client:
            self.log("  (No admin client — skipping write tests)")
            # Still pass; caller should provide admin key for write ops
            return

        # Use the read client for host discovery (admin client may have IP restrictions)
        hosts = self.client.deployments.list_hosts(self.project_id)
        if not hosts:
            self.log("  (No hosts — skipping log collection write tests)")
            return

        host = hosts[0]
        self.log(f"  Creating log collection job for host: {host.hostname}")

        try:
            job = write_client.log_collection.create(
                project_id=self.project_id,
                resource_type="PROCESS",
                resource_name=host.hostname,
                log_types=["MONGODB"],
                size_requested_per_file_bytes=1_000_000,
                redacted=False,
            )
        except OpsManagerForbiddenError as e:
            self.log(f"  (Log collection create restricted by IP/permissions: {e})")
            return
        assert isinstance(job, LogCollectionJob), f"Expected LogCollectionJob, got {type(job)}"
        assert job.id, "Created job has no ID"
        self.created_log_job_id = job.id
        self.log(f"  Created job: {job.id} status={job.status}")

        # Get it back
        fetched = write_client.log_collection.get(self.project_id, job.id)
        assert fetched.id == job.id, "Job ID mismatch after create"
        self.log(f"  Get after create: OK (status={fetched.status})")

        # Extend expiration
        write_client.log_collection.extend(
            self.project_id,
            job.id,
            expiration_date="2026-12-31T23:59:59Z",
        )
        self.log(f"  Extend expiration: OK")

        # Delete
        write_client.log_collection.delete(self.project_id, job.id)
        self.log(f"  Delete: OK")
        self.created_log_job_id = None

        # Confirm deletion (should 404)
        try:
            write_client.log_collection.get(self.project_id, job.id)
            assert False, "Expected 404 after deletion but got a response"
        except OpsManagerNotFoundError:
            self.log(f"  Confirmed 404 after delete: OK")
        except OpsManagerError as e:
            # Some OM versions return a different error code for deleted resources
            self.log(f"  Post-delete error (acceptable): {e}")

    def test_server_usage(self) -> None:
        """Server usage: project and org host assignments."""
        client = self.admin_client or self.client

        # Project-level host assignments
        try:
            project_hosts = client.server_usage.get_project_host_assignments(self.project_id)
            assert isinstance(project_hosts, list), f"Expected list, got {type(project_hosts)}"
            self.log(f"  Project host assignments: {len(project_hosts)}")
            for h in project_hosts[:3]:
                self.log(f"    {h.hostname if hasattr(h, 'hostname') else h}")
        except OpsManagerForbiddenError:
            self.log("  (Project host assignments: forbidden — need higher privileges)")
        except OpsManagerError as e:
            self.log(f"  (Project host assignments: {e})")

        # Org-level host assignments
        try:
            org_hosts = client.server_usage.get_organization_host_assignments(self.org_id)
            assert isinstance(org_hosts, list), f"Expected list, got {type(org_hosts)}"
            self.log(f"  Org host assignments: {len(org_hosts)}")
        except (OpsManagerForbiddenError, OpsManagerError) as e:
            self.log(f"  (Org host assignments: {e})")

        # Global host assignments (admin)
        if self.admin_client:
            try:
                all_hosts = self.admin_client.server_usage.list_all_host_assignments()
                assert isinstance(all_hosts, list), f"Expected list, got {type(all_hosts)}"
                self.log(f"  All host assignments: {len(all_hosts)}")
            except OpsManagerError as e:
                self.log(f"  (All host assignments: {e})")

            # Project server type
            try:
                stype = self.admin_client.server_usage.get_project_server_type(self.project_id)
                self.log(f"  Project server type: {stype}")
            except OpsManagerError as e:
                self.log(f"  (Project server type: {e})")

    def test_feature_control(self) -> None:
        """Feature control: get policy, list supported policies."""
        policy = self.client.feature_control.get(self.project_id)
        assert isinstance(policy, FeaturePolicy), f"Expected FeaturePolicy, got {type(policy)}"
        self.log(f"  Feature policy: {len(policy.policies)} policies")
        for p in policy.policies[:3]:
            self.log(f"    {p}")

        supported = self.client.feature_control.list_supported_policies()
        assert isinstance(supported, list), f"Expected list, got {type(supported)}"
        self.log(f"  Supported policies: {len(supported)}")

    # ------------------------------------------------------------------
    # New services — Tier 3 (access control)
    # ------------------------------------------------------------------

    def test_teams(self) -> None:
        """Teams: list, get_by_name, list_users (may be empty)."""
        teams = self.client.teams.list(self.org_id)
        assert isinstance(teams, list), f"Expected list, got {type(teams)}"
        self.log(f"  Teams: {len(teams)}")
        for t in teams[:3]:
            assert isinstance(t, Team), f"Expected Team, got {type(t)}"
            self.log(f"    {t.name} ({t.id})")

        if teams:
            t = self.client.teams.get(self.org_id, teams[0].id)
            assert t.id == teams[0].id, "Team ID mismatch on get"
            self.log(f"  Get by ID: OK")

            t2 = self.client.teams.get_by_name(self.org_id, teams[0].name)
            assert t2.id == teams[0].id, "Team name lookup mismatch"
            self.log(f"  Get by name: OK")

            members = self.client.teams.list_users(self.org_id, teams[0].id)
            assert isinstance(members, list), f"Expected list, got {type(members)}"
            self.log(f"  Team members: {len(members)}")

    def test_users(self) -> None:
        """Users: get by ID and by name (uses user discovered from org/project)."""
        if not self.first_user_id:
            # Try to discover a user now
            try:
                users = self.client.organizations.list_users(self.org_id)
                if users:
                    self.first_user_id = users[0].id
                    self.first_username = users[0].username
            except Exception:
                pass

        if not self.first_user_id:
            self.log("  (No users found in org — skipping users service test)")
            return

        # Get by ID
        user = self.client.users.get(self.first_user_id)
        assert isinstance(user, User), f"Expected User, got {type(user)}"
        assert user.id == self.first_user_id, "User ID mismatch"
        self.log(f"  Get by ID: {user.username} ({user.id})")

        # Get by name
        if self.first_username:
            user2 = self.client.users.get_by_name(self.first_username)
            assert isinstance(user2, User), f"Expected User, got {type(user2)}"
            assert user2.id == self.first_user_id, "User name lookup ID mismatch"
            self.log(f"  Get by name: OK")

    def test_api_keys(self) -> None:
        """API keys: list org keys, get one, list project keys."""
        # Org keys
        org_keys = self.client.api_keys.list_organization_keys(self.org_id)
        assert isinstance(org_keys, list), f"Expected list, got {type(org_keys)}"
        assert len(org_keys) > 0, "No org API keys found (at minimum the test keys should appear)"
        self.log(f"  Org API keys: {len(org_keys)}")
        for k in org_keys[:3]:
            assert isinstance(k, APIKey), f"Expected APIKey, got {type(k)}"
            self.log(f"    {k.public_key}: {k.desc}")

        # Get single key by ID
        key = self.client.api_keys.get_organization_key(self.org_id, org_keys[0].id)
        assert isinstance(key, APIKey), f"Expected APIKey, got {type(key)}"
        assert key.id == org_keys[0].id, "APIKey ID mismatch on get"
        self.log(f"  Get org key by ID: OK")

        # Project keys (may require higher privileges)
        try:
            project_keys = self.client.api_keys.list_project_keys(self.project_id)
            assert isinstance(project_keys, list), f"Expected list, got {type(project_keys)}"
            self.log(f"  Project API keys: {len(project_keys)}")
        except OpsManagerError as e:
            self.log(f"  (Project API keys not accessible: {e})")

    # ------------------------------------------------------------------
    # New services — Tier 3 (version, migration, admin)
    # ------------------------------------------------------------------

    def test_version(self) -> None:
        """Version service: get_service_version, get_version_manifest."""
        # Service version (unauthenticated endpoint — may return 406 on some OM builds)
        try:
            version = self.client.version.get_service_version()
            assert isinstance(version, dict), f"Expected dict, got {type(version)}"
            assert "version" in version or "gitVersion" in version, \
                f"Service version response missing expected fields: {list(version.keys())}"
            self.log(f"  Service version: {version.get('version')} ({version.get('gitVersion', '')[:8]})")
        except OpsManagerError as e:
            self.log(f"  (Service version endpoint not available on this instance: {e})")

        # Version manifest for a well-known MongoDB version
        try:
            manifest = self.client.version.get_version_manifest("7.0")
            assert isinstance(manifest, dict), f"Expected dict, got {type(manifest)}"
            self.log(f"  Version manifest 7.0 keys: {list(manifest.keys())[:5]}")
        except OpsManagerError as e:
            self.log(f"  (Version manifest not available: {e})")

    def test_live_migration(self) -> None:
        """Live migration: get_connection_status (may return 404 if no link configured)."""
        try:
            status = self.client.live_migration.get_connection_status(self.org_id)
            from opsmanager.types import ConnectionStatus
            assert isinstance(status, ConnectionStatus), f"Expected ConnectionStatus, got {type(status)}"
            self.log(f"  Migration link status: {status.status}")
        except OpsManagerNotFoundError:
            self.log("  (No migration link configured — 404 expected)")
        except OpsManagerError as e:
            # Some OM versions may return a different error when no migration is active
            if "404" in str(e) or "NOT_FOUND" in str(e).upper():
                self.log(f"  (Migration link not found — acceptable)")
            else:
                self.log(f"  (Live migration error: {e})")

    def test_admin_backup_stores(self) -> None:
        """Admin backup store configs: all list endpoints (global owner key required)."""
        client = self.admin_client
        if not client:
            self.log("  (No admin client — skipping admin backup store tests)")
            return

        checks = [
            ("blockstores",       lambda: client.admin_backup_stores.list_blockstores()),
            ("S3 blockstores",    lambda: client.admin_backup_stores.list_s3_blockstores()),
            ("filesystem stores", lambda: client.admin_backup_stores.list_file_system_stores()),
            ("oplog stores",      lambda: client.admin_backup_stores.list_oplog_stores()),
            ("sync stores",       lambda: client.admin_backup_stores.list_sync_stores()),
            ("daemons",           lambda: client.admin_backup_stores.list_daemons()),
            ("project jobs",      lambda: client.admin_backup_stores.list_project_jobs()),
        ]
        for label, fn in checks:
            try:
                result = fn()
                assert isinstance(result, list), f"{label}: expected list, got {type(result)}"
                self.log(f"  {label}: {len(result)} item(s)")
            except OpsManagerError as e:
                self.log(f"  {label}: {e}")

    def test_global_admin(self) -> None:
        """Global admin: list API keys and whitelist (global owner key required)."""
        client = self.admin_client
        if not client:
            self.log("  (No admin client — skipping global admin tests)")
            return

        # Global API keys (may be IP-restricted)
        try:
            keys = client.global_admin.list_api_keys()
            assert isinstance(keys, list), f"Expected list, got {type(keys)}"
            self.log(f"  Global API keys: {len(keys)}")
            for k in keys[:3]:
                assert isinstance(k, APIKey), f"Expected APIKey, got {type(k)}"
                self.log(f"    {k.public_key}: {k.desc}")

            if keys:
                k = client.global_admin.get_api_key(keys[0].id)
                assert isinstance(k, APIKey), f"Expected APIKey, got {type(k)}"
                assert k.id == keys[0].id, "Global APIKey ID mismatch on get"
                self.log(f"  Get global API key by ID: OK")

            # Whitelist
            whitelist = client.global_admin.list_whitelist()
            assert isinstance(whitelist, list), f"Expected list, got {type(whitelist)}"
            self.log(f"  Global API key whitelist entries: {len(whitelist)}")
        except OpsManagerForbiddenError as e:
            self.log(f"  (Global admin restricted by IP/permissions: {e})")

    # ------------------------------------------------------------------
    # Run all
    # ------------------------------------------------------------------

    def run_all(self, specific_test: Optional[str] = None) -> bool:
        tests = [
            # Extended methods on original services
            ("organizations_list_users",    self.test_organizations_list_users),
            ("projects_list_users",         self.test_projects_list_users),
            ("projects_get_teams",          self.test_projects_get_teams),
            ("agents_extended",             self.test_agents_extended),
            ("backup_extended",             self.test_backup_extended),
            # Tier 1 — new services
            ("events",                      self.test_events),
            ("automation",                  self.test_automation),
            ("alert_configurations",        self.test_alert_configurations),
            ("global_alerts",               self.test_global_alerts),
            ("diagnostics",                 self.test_diagnostics),
            ("maintenance_windows",         self.test_maintenance_windows),
            # Tier 2 — new services
            ("log_collection_read",         self.test_log_collection_read),
            ("log_collection_write",        self.test_log_collection_write),
            ("server_usage",                self.test_server_usage),
            ("feature_control",             self.test_feature_control),
            # Tier 3 — access control
            ("teams",                       self.test_teams),
            ("users",                       self.test_users),
            ("api_keys",                    self.test_api_keys),
            # Tier 3 — version, migration, admin
            ("version",                     self.test_version),
            ("live_migration",              self.test_live_migration),
            ("admin_backup_stores",         self.test_admin_backup_stores),
            ("global_admin",                self.test_global_admin),
        ]

        if specific_test:
            tests = [(n, f) for n, f in tests if n == specific_test]
            if not tests:
                available = [n for n, _ in tests]
                print(f"Unknown test: {specific_test}. Available: {', '.join(available)}")
                return False

        for name, func in tests:
            self.run_test(name, func)

        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        passed = sum(1 for v in self.results.values() if v)
        failed = sum(1 for v in self.results.values() if not v)
        print(f"  Passed: {passed}")
        print(f"  Failed: {failed}")

        if failed:
            print("\nFailed tests:")
            for name, result in self.results.items():
                if not result:
                    print(f"  - {name}")

        return failed == 0


def main():
    parser = argparse.ArgumentParser(
        description="Extended live integration tests for Tier 1-3 services"
    )
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--test", "-t", help="Run a single named test")
    parser.add_argument("--base-url",         default=os.environ.get("OM_BASE_URL"))
    parser.add_argument("--public-key",       default=os.environ.get("OM_PUBLIC_KEY"))
    parser.add_argument("--private-key",      default=os.environ.get("OM_PRIVATE_KEY"))
    parser.add_argument("--admin-public-key", default=os.environ.get("OM_ADMIN_PUBLIC_KEY"))
    parser.add_argument("--admin-private-key",default=os.environ.get("OM_ADMIN_PRIVATE_KEY"))
    parser.add_argument("--org-id",           default=os.environ.get("OM_ORG_ID"))
    parser.add_argument("--project-id",       default=os.environ.get("OM_PROJECT_ID"))
    args = parser.parse_args()

    missing = [k for k, v in {
        "base-url": args.base_url,
        "public-key": args.public_key,
        "private-key": args.private_key,
        "org-id": args.org_id,
        "project-id": args.project_id,
    }.items() if not v]

    if missing:
        print(f"Error: Missing required arguments: {', '.join(missing)}")
        print("Set via environment variables or --flags:")
        print("  OM_BASE_URL, OM_PUBLIC_KEY, OM_PRIVATE_KEY, OM_ORG_ID, OM_PROJECT_ID")
        print("  OM_ADMIN_PUBLIC_KEY, OM_ADMIN_PRIVATE_KEY  (optional, for admin tests)")
        sys.exit(1)

    print(f"Connecting to: {args.base_url}")
    if args.admin_public_key:
        print(f"Admin key:     {args.admin_public_key} (admin tests enabled)")
    else:
        print("Admin key:     not provided (admin tests will be skipped)")

    client = OpsManagerClient(
        base_url=args.base_url,
        public_key=args.public_key,
        private_key=args.private_key,
        verify_ssl=False,
        rate_limit=5.0,
    )

    admin_client = None
    if args.admin_public_key and args.admin_private_key:
        admin_client = OpsManagerClient(
            base_url=args.base_url,
            public_key=args.admin_public_key,
            private_key=args.admin_private_key,
            verify_ssl=False,
            rate_limit=5.0,
        )

    try:
        runner = ExtendedLiveTestRunner(
            client=client,
            admin_client=admin_client,
            org_id=args.org_id,
            project_id=args.project_id,
            verbose=args.verbose,
        )
        success = runner.run_all(specific_test=args.test)
        sys.exit(0 if success else 1)
    finally:
        client.close()
        if admin_client:
            admin_client.close()


if __name__ == "__main__":
    main()
