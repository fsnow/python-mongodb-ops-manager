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
Live integration tests for the opsmanager library.

These tests require a running Ops Manager instance and valid credentials.
Set the following environment variables before running:

    export OM_BASE_URL="http://your-ops-manager:8081"
    export OM_PUBLIC_KEY="your-public-key"
    export OM_PRIVATE_KEY="your-private-key"

Run with:
    python tests/test_live.py
    python tests/test_live.py --verbose
    python tests/test_live.py --test measurements
"""

import argparse
import os
import sys
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from opsmanager import OpsManagerClient
from opsmanager.types import Host, Cluster, Organization, Project, Alert


class LiveTestRunner:
    """Runs live integration tests against Ops Manager."""

    def __init__(self, client: OpsManagerClient, verbose: bool = False):
        self.client = client
        self.verbose = verbose
        self.org_id: Optional[str] = None
        self.project_id: Optional[str] = None
        self.primary_host: Optional[Host] = None
        self.results: dict[str, bool] = {}

    def log(self, message: str, always: bool = False) -> None:
        """Print message if verbose or always."""
        if self.verbose or always:
            print(message)

    def run_test(self, name: str, test_func) -> bool:
        """Run a single test and track results."""
        print(f"\n{'='*60}")
        print(f"TEST: {name}")
        print('='*60)
        try:
            test_func()
            print(f"✓ PASS: {name}")
            self.results[name] = True
            return True
        except Exception as e:
            print(f"✗ FAIL: {name}")
            print(f"  Error: {e}")
            self.results[name] = False
            return False

    def test_organizations(self) -> None:
        """Test organizations endpoint."""
        orgs = self.client.organizations.list()
        assert len(orgs) > 0, "No organizations found"

        org = orgs[0]
        assert isinstance(org, Organization), f"Expected Organization, got {type(org)}"
        assert org.id, "Organization ID is empty"
        assert org.name, "Organization name is empty"

        self.org_id = org.id
        self.log(f"  Found {len(orgs)} organization(s)")
        self.log(f"  Using: {org.name} ({org.id})")

        # Test get by ID
        org_by_id = self.client.organizations.get(org.id)
        assert org_by_id.id == org.id, "Organization ID mismatch"
        self.log(f"  Get by ID: OK")

    def test_projects(self) -> None:
        """Test projects endpoint."""
        assert self.org_id, "Organization ID required (run organizations test first)"

        projects = self.client.organizations.list_projects(self.org_id)
        assert len(projects) > 0, "No projects found"

        project = projects[0]
        assert isinstance(project, Project), f"Expected Project, got {type(project)}"
        assert project.id, "Project ID is empty"
        assert project.name, "Project name is empty"

        self.project_id = project.id
        self.log(f"  Found {len(projects)} project(s)")
        self.log(f"  Using: {project.name} ({project.id})")

        # Test get by ID
        project_by_id = self.client.projects.get(project.id)
        assert project_by_id.id == project.id, "Project ID mismatch"
        self.log(f"  Get by ID: OK")

        # Test get by name
        project_by_name = self.client.projects.get_by_name(project.name)
        assert project_by_name.id == project.id, "Project name lookup mismatch"
        self.log(f"  Get by name: OK")

    def test_clusters(self) -> None:
        """Test clusters endpoint."""
        assert self.project_id, "Project ID required (run projects test first)"

        clusters = self.client.clusters.list(self.project_id)
        self.log(f"  Found {len(clusters)} cluster(s)")

        if clusters:
            cluster = clusters[0]
            assert isinstance(cluster, Cluster), f"Expected Cluster, got {type(cluster)}"
            assert cluster.id, "Cluster ID is empty"
            assert cluster.cluster_name, "Cluster name is empty"

            self.log(f"  Cluster: {cluster.cluster_name}")
            self.log(f"  Type: {cluster.type_name}")

            # Test get by ID
            cluster_by_id = self.client.clusters.get(self.project_id, cluster.id)
            assert cluster_by_id.id == cluster.id, "Cluster ID mismatch"
            self.log(f"  Get by ID: OK")
        else:
            self.log("  (No clusters deployed)")

    def test_hosts(self) -> None:
        """Test hosts/deployments endpoint."""
        assert self.project_id, "Project ID required (run projects test first)"

        hosts = self.client.deployments.list_hosts(self.project_id)
        assert len(hosts) > 0, "No hosts found"

        self.log(f"  Found {len(hosts)} host(s)")

        for host in hosts:
            assert isinstance(host, Host), f"Expected Host, got {type(host)}"
            assert host.id, "Host ID is empty"
            assert host.hostname, "Hostname is empty"

            self.log(f"  {host.hostname}:{host.port} - {host.type_name} ({host.replica_state_name})")

            if host.replica_state_name == "PRIMARY":
                self.primary_host = host

        # Test get by ID
        host = hosts[0]
        host_by_id = self.client.deployments.get_host(self.project_id, host.id)
        assert host_by_id.id == host.id, "Host ID mismatch"
        self.log(f"  Get by ID: OK")

    def test_measurements(self) -> None:
        """Test measurements endpoint."""
        assert self.project_id, "Project ID required (run projects test first)"

        # Get a host to query
        hosts = self.client.deployments.list_hosts(self.project_id)
        assert len(hosts) > 0, "No hosts found for measurements"

        host = self.primary_host or hosts[0]
        self.log(f"  Querying measurements for: {host.hostname}")

        # Get measurements - returns ProcessMeasurements object
        result = self.client.measurements.host(
            project_id=self.project_id,
            host_id=host.id,
            granularity="PT1M",
            period="PT1H",  # Last hour
        )

        # Access the measurements list from the ProcessMeasurements object
        measurements = result.measurements
        self.log(f"  Found {len(measurements)} measurement type(s)")
        self.log(f"  Time range: {result.start} to {result.end}")
        self.log(f"  Granularity: {result.granularity}")

        # Count measurements with data
        with_data = [m for m in measurements if m.data_points]
        self.log(f"  Measurements with data: {len(with_data)}")

        if with_data:
            # Show a few examples
            for m in with_data[:3]:
                latest = m.data_points[-1]
                self.log(f"    {m.name}: {latest.value} {m.units}")
        else:
            self.log("  (No data yet - monitoring may still be initializing)")

    def test_databases(self) -> None:
        """Test databases endpoint."""
        assert self.project_id, "Project ID required (run projects test first)"

        hosts = self.client.deployments.list_hosts(self.project_id)
        assert len(hosts) > 0, "No hosts found"

        host = self.primary_host or hosts[0]
        self.log(f"  Querying databases for: {host.hostname}")

        databases = self.client.deployments.list_databases(
            project_id=self.project_id,
            host_id=host.id,
        )

        self.log(f"  Found {len(databases)} database(s)")
        for db in databases:
            self.log(f"    {db.database_name}")

    def test_alerts(self) -> None:
        """Test alerts endpoint."""
        assert self.project_id, "Project ID required (run projects test first)"

        alerts = self.client.alerts.list(self.project_id)
        self.log(f"  Found {len(alerts)} alert(s)")

        for alert in alerts[:5]:  # Show first 5
            assert isinstance(alert, Alert), f"Expected Alert, got {type(alert)}"
            self.log(f"  [{alert.status}] {alert.event_type_name}")

    def test_performance_advisor(self) -> None:
        """Test performance advisor endpoint."""
        assert self.project_id, "Project ID required (run projects test first)"

        hosts = self.client.deployments.list_hosts(self.project_id)
        assert len(hosts) > 0, "No hosts found"

        host = self.primary_host or hosts[0]
        host_id = f"{host.hostname}:{host.port}"
        self.log(f"  Querying performance advisor for: {host_id}")

        try:
            namespaces = self.client.performance_advisor.get_namespaces(
                project_id=self.project_id,
                host_id=host_id,
            )
            self.log(f"  Found {len(namespaces)} namespace(s)")
        except Exception as e:
            # Performance advisor may not be available on all deployments
            if "UNEXPECTED_ERROR" in str(e):
                self.log("  (Performance Advisor not available - profiler may need to be enabled)")
            else:
                raise

    def test_raw_dict_response(self) -> None:
        """Test that as_obj=False returns raw dictionaries."""
        assert self.org_id, "Organization ID required (run organizations test first)"

        # Get projects as raw dicts
        projects = self.client.organizations.list_projects(self.org_id, as_obj=False)
        assert isinstance(projects, list), "Expected list"
        assert len(projects) > 0, "No projects found"
        assert isinstance(projects[0], dict), f"Expected dict, got {type(projects[0])}"

        self.log(f"  Raw dict keys: {list(projects[0].keys())[:5]}...")
        self.log("  as_obj=False: OK")

    def run_all(self, specific_test: Optional[str] = None) -> bool:
        """Run all tests or a specific test."""
        tests = [
            ("organizations", self.test_organizations),
            ("projects", self.test_projects),
            ("clusters", self.test_clusters),
            ("hosts", self.test_hosts),
            ("measurements", self.test_measurements),
            ("databases", self.test_databases),
            ("alerts", self.test_alerts),
            ("performance_advisor", self.test_performance_advisor),
            ("raw_dict_response", self.test_raw_dict_response),
        ]

        if specific_test:
            tests = [(name, func) for name, func in tests if name == specific_test]
            if not tests:
                print(f"Unknown test: {specific_test}")
                print(f"Available: {', '.join(name for name, _ in tests)}")
                return False

        for name, func in tests:
            self.run_test(name, func)

        # Summary
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
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
    parser = argparse.ArgumentParser(description="Live integration tests for opsmanager library")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--test", "-t", help="Run specific test (e.g., 'measurements')")
    parser.add_argument("--base-url", default=os.environ.get("OM_BASE_URL"),
                        help="Ops Manager base URL")
    parser.add_argument("--public-key", default=os.environ.get("OM_PUBLIC_KEY"),
                        help="API public key")
    parser.add_argument("--private-key", default=os.environ.get("OM_PRIVATE_KEY"),
                        help="API private key")
    args = parser.parse_args()

    # Validate required args
    if not all([args.base_url, args.public_key, args.private_key]):
        print("Error: Missing required configuration.")
        print("Set environment variables or use command-line arguments:")
        print("  OM_BASE_URL, OM_PUBLIC_KEY, OM_PRIVATE_KEY")
        print("\nExample:")
        print('  export OM_BASE_URL="http://ops-manager:8081"')
        print('  export OM_PUBLIC_KEY="your-public-key"')
        print('  export OM_PRIVATE_KEY="your-private-key"')
        sys.exit(1)

    print(f"Connecting to: {args.base_url}")

    # Create client
    client = OpsManagerClient(
        base_url=args.base_url,
        public_key=args.public_key,
        private_key=args.private_key,
        verify_ssl=False,  # Often needed for test instances
        rate_limit=5.0,
    )

    try:
        runner = LiveTestRunner(client, verbose=args.verbose)
        success = runner.run_all(specific_test=args.test)
        sys.exit(0 if success else 1)
    finally:
        client.close()


if __name__ == "__main__":
    main()
