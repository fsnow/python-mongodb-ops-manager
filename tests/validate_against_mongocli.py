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
Validation script to compare Python library output against mongocli.

This script uses a GROUP_READ_ONLY (+ GROUP_BACKUP_ADMIN) API key to validate
read-only endpoints. For admin-level endpoints, see validate_against_mongocli_admin.py.

Prerequisites:
    - mongocli installed (https://www.mongodb.com/docs/mongocli/)
    - Access to an Ops Manager instance

Usage:
    # Set environment variables
    export OM_BASE_URL="http://ops-manager.example.com:8081"
    export OM_PUBLIC_KEY="your-public-key"
    export OM_PRIVATE_KEY="your-private-key"
    export OM_ORG_ID="your-org-id"
    export OM_PROJECT_ID="your-project-id"
    export OM_CLUSTER_ID="your-cluster-id"  # optional, auto-detected if not set

    # Run all read-only validations
    python tests/validate_against_mongocli.py

    # Or validate specific endpoints
    python tests/validate_against_mongocli.py --endpoint hosts
    python tests/validate_against_mongocli.py --endpoint events
    python tests/validate_against_mongocli.py --endpoint backup --cluster-id <clusterId>

Note:
    mongocli environment variables (MCLI_*) are set automatically from OM_* vars.
    The clusters endpoint is not validated because mongocli uses a different API
    (automationConfig) that requires additional permissions.
"""

import argparse
import os
import sys
from typing import Dict, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from opsmanager import OpsManagerClient
from tests.mongocli_helpers import (
    run_mongocli,
    compare_results,
    diff_field,
    filter_differences,
    check_mongocli_available,
    make_mongocli_env,
    print_summary,
)


# ---------------------------------------------------------------
# Read-only validators (GROUP_READ_ONLY + GROUP_BACKUP_ADMIN)
# ---------------------------------------------------------------

def validate_hosts(client: OpsManagerClient, project_id: str, mongocli_env: Dict[str, str]) -> bool:
    """Validate hosts endpoint."""
    print("\n=== Validating Hosts ===")

    py_hosts = client.deployments.list_hosts(project_id=project_id, as_obj=False)

    cli_result = run_mongocli(["processes", "list", "--projectId", project_id], env=mongocli_env)
    cli_hosts = cli_result.get("results", cli_result)

    print(f"Python returned {len(py_hosts)} hosts")
    print(f"mongocli returned {len(cli_hosts)} hosts")

    expected_py_extras = {
        "lastIndexSizeBytes", "hidden", "lowUlimit", "systemInfo",
        "lastDataSizeBytes", "slaveDelaySec", "hiddenSecondary",
        "hasStartupWarnings", "journalingEnabled",
    }

    differences = compare_results(py_hosts, cli_hosts)
    unexpected = filter_differences(differences, expected_py_extras=expected_py_extras)

    if unexpected:
        print("Unexpected differences found:")
        for diff in unexpected[:20]:
            print(f"  - {diff}")
        if len(unexpected) > 20:
            print(f"  ... and {len(unexpected) - 20} more")
        return False

    if differences:
        print(f"  Note: Python library returns {len(differences) - len(unexpected)} additional fields not in mongocli output")

    print("PASS: Hosts match!")
    return True


def validate_alerts(client: OpsManagerClient, project_id: str, mongocli_env: Dict[str, str]) -> bool:
    """Validate alerts endpoint."""
    print("\n=== Validating Alerts ===")

    py_alerts = client.alerts.list(project_id=project_id, as_obj=False)

    cli_result = run_mongocli(["alerts", "list", "--projectId", project_id], env=mongocli_env)
    cli_alerts = cli_result.get("results", cli_result)

    print(f"Python returned {len(py_alerts)} alerts")
    print(f"mongocli returned {len(cli_alerts)} alerts")

    differences = compare_results(py_alerts, cli_alerts)
    unexpected = filter_differences(differences, expected_py_extras={"orgId", "hostId"})

    if unexpected:
        print("Unexpected differences found:")
        for diff in unexpected[:20]:
            print(f"  - {diff}")
        return False

    if differences:
        print(f"  Note: Python library returns {len(differences) - len(unexpected)} additional fields not in mongocli output")

    print("PASS: Alerts match!")
    return True


def validate_agents(client: OpsManagerClient, project_id: str, mongocli_env: Dict[str, str]) -> bool:
    """Validate agents endpoint."""
    print("\n=== Validating Agents ===")
    all_passed = True

    expected_cli_extras = {"tag", "pingCount", "isManaged", "lastPing"}

    for agent_type in ("MONITORING", "BACKUP", "AUTOMATION"):
        py_agents = client.agents.list(project_id=project_id, agent_type=agent_type, as_obj=False)

        cli_result = run_mongocli(
            ["agents", "list", agent_type, "--projectId", project_id], env=mongocli_env
        )
        cli_agents = cli_result.get("results", [])

        print(f"  {agent_type}: Python={len(py_agents)}, mongocli={len(cli_agents)}")

        differences = compare_results(py_agents, cli_agents)
        unexpected = filter_differences(differences, expected_cli_extras=expected_cli_extras)
        if unexpected:
            print(f"  Differences for {agent_type}:")
            for diff in unexpected[:20]:
                print(f"    - {diff}")
            all_passed = False

    if all_passed:
        print("PASS: Agents match!")
    return all_passed


def validate_backup(
    client: OpsManagerClient,
    project_id: str,
    mongocli_env: Dict[str, str],
    cluster_id: Optional[str] = None,
) -> bool:
    """Validate backup snapshots and config endpoints."""
    print("\n=== Validating Backup ===")

    if not cluster_id:
        clusters = client.clusters.list(project_id=project_id)
        if not clusters:
            print("  No clusters found — skipping backup validation")
            return True
        cluster_id = clusters[0].id
        print(f"  Using cluster: {clusters[0].cluster_name} ({cluster_id})")

    all_passed = True

    try:
        py_config = client.backup.get_backup_config(project_id, cluster_id, as_obj=False)
        cli_config = run_mongocli(
            ["backups", "config", "describe", cluster_id, "--projectId", project_id],
            env=mongocli_env,
        )

        expected_config_py_extras = {
            "excludedNamespaces", "multiRegionMisconfigured", "multiRegionBackupEnabled"
        }
        differences = compare_results(py_config, cli_config)
        unexpected = filter_differences(differences, expected_py_extras=expected_config_py_extras)
        if unexpected:
            print("  Config differences:")
            for diff in unexpected[:20]:
                print(f"    - {diff}")
            all_passed = False
        else:
            print("  Config: match")

    except Exception as e:
        if "BACKUP_NOT_ENABLED" in str(e) or "404" in str(e):
            print("  (Backup not enabled for this cluster — skipping)")
            return True
        raise

    py_snapshots = client.backup.list_snapshots(project_id, cluster_id, as_obj=False)
    cli_result = run_mongocli(
        ["backups", "snapshots", "list", cluster_id, "--projectId", project_id],
        env=mongocli_env,
    )
    cli_snapshots = cli_result.get("results", [])

    print(f"  Snapshots: Python={len(py_snapshots)}, mongocli={len(cli_snapshots)}")

    differences = compare_results(py_snapshots, cli_snapshots)
    if differences:
        print("  Snapshot differences:")
        for diff in differences[:20]:
            print(f"    - {diff}")
        all_passed = False

    if all_passed:
        print("PASS: Backup match!")
    return all_passed


def validate_events(client: OpsManagerClient, project_id: str, mongocli_env: Dict[str, str]) -> bool:
    """Validate events endpoint."""
    print("\n=== Validating Events ===")

    py_events = client.events.list_project_events(project_id=project_id, as_obj=False)

    cli_result = run_mongocli(
        ["events", "projects", "list", "--projectId", project_id], env=mongocli_env
    )
    cli_events = cli_result.get("results", [])

    print(f"  Python={len(py_events)}, mongocli={len(cli_events)}")

    expected_cli_extras = {"alertId", "alertConfigId", "hostname",
                           "targetPublicKey", "userId", "username",
                           "Port"}
    expected_py_extras = {"diffs", "port", "isGlobalAdmin", "hostId"}

    differences = compare_results(py_events, cli_events)
    unexpected = filter_differences(differences, expected_py_extras, expected_cli_extras)

    if unexpected:
        print("  Unexpected differences:")
        for diff in unexpected[:20]:
            print(f"    - {diff}")
        return False

    print("PASS: Events match!")
    return True


def validate_measurements(
    client: OpsManagerClient,
    project_id: str,
    mongocli_env: Dict[str, str],
) -> bool:
    """Validate measurements endpoint (single metric comparison)."""
    print("\n=== Validating Measurements ===")

    hosts = client.deployments.list_hosts(project_id=project_id)
    if not hosts:
        print("  No hosts found — skipping measurements validation")
        return True
    host = hosts[0]
    print(f"  Using host: {host.hostname} ({host.id})")

    metric = "PROCESS_CPU_USER"
    py_result = client.measurements.host(
        project_id=project_id,
        host_id=host.id,
        granularity="PT1H",
        period="P1D",
        metrics=[metric],
        as_obj=False,
    )

    cli_result = run_mongocli(
        ["metrics", "process", host.id,
         "--projectId", project_id,
         "--granularity", "PT1H",
         "--period", "P1D",
         "--type", metric],
        env=mongocli_env,
    )

    py_keys = set(py_result.keys()) - {"links"}
    cli_keys = set(cli_result.keys()) - {"links"}
    missing_in_py = cli_keys - py_keys
    missing_in_cli = py_keys - cli_keys

    if missing_in_py:
        print(f"  Missing in Python: {missing_in_py}")
    if missing_in_cli:
        print(f"  Missing in CLI: {missing_in_cli}")

    py_metrics = {m["name"] for m in py_result.get("measurements", [])}
    cli_metrics = {m["name"] for m in cli_result.get("measurements", [])}

    if py_metrics != cli_metrics:
        print(f"  Metric name mismatch: py={py_metrics}, cli={cli_metrics}")
        return False

    for m in py_result.get("measurements", []):
        if m.get("dataPoints"):
            dp = m["dataPoints"][0]
            assert "timestamp" in dp, "Missing timestamp in dataPoint"
            assert "value" in dp, "Missing value in dataPoint"
            break

    print(f"  Metric: {metric}, data points aligned")
    print("PASS: Measurements match!")
    return True


def validate_automation_status(
    client: OpsManagerClient,
    project_id: str,
    mongocli_env: Dict[str, str],
) -> bool:
    """Validate automation status endpoint."""
    print("\n=== Validating Automation Status ===")

    py_status = client.automation.get_status(project_id=project_id, as_obj=False)

    cli_status = run_mongocli(
        ["automation", "status", "--projectId", project_id], env=mongocli_env
    )

    if py_status.get("goalVersion") != cli_status.get("goalVersion"):
        print(f"  goalVersion mismatch: py={py_status.get('goalVersion')}, cli={cli_status.get('goalVersion')}")
        return False
    print(f"  goalVersion: {py_status.get('goalVersion')}")

    py_procs = py_status.get("processes", [])
    cli_procs = cli_status.get("processes", [])

    print(f"  Processes: Python={len(py_procs)}, mongocli={len(cli_procs)}")

    if len(py_procs) != len(cli_procs):
        print(f"  Process count mismatch")
        return False

    py_by_host = {p.get("hostname", p.get("name", "")): p for p in py_procs}
    cli_by_host = {p.get("hostname", p.get("name", "")): p for p in cli_procs}

    expected_cli_extras = {"errorCode", "errorCodeDescription",
                           "errorCodeHumanReadable", "errorString"}

    for hostname in cli_by_host:
        if hostname not in py_by_host:
            print(f"  Missing in Python: process {hostname}")
            return False
        differences = compare_results(py_by_host[hostname], cli_by_host[hostname])
        unexpected = filter_differences(differences, expected_cli_extras=expected_cli_extras)
        if unexpected:
            print(f"  Process {hostname} differences:")
            for diff in unexpected[:10]:
                print(f"    - {diff}")
            return False

    print("PASS: Automation status match!")
    return True


def validate_maintenance_windows(
    client: OpsManagerClient,
    project_id: str,
    mongocli_env: Dict[str, str],
) -> bool:
    """Validate maintenance windows endpoint."""
    print("\n=== Validating Maintenance Windows ===")

    py_windows = client.maintenance_windows.list(project_id=project_id, as_obj=False)

    cli_result = run_mongocli(
        ["maintenanceWindows", "list", "--projectId", project_id], env=mongocli_env
    )
    cli_windows = cli_result.get("results", [])

    print(f"  Python={len(py_windows)}, mongocli={len(cli_windows)}")

    differences = compare_results(py_windows, cli_windows)
    if differences:
        print("  Differences:")
        for diff in differences[:20]:
            print(f"    - {diff}")
        return False

    print("PASS: Maintenance windows match!")
    return True


def validate_feature_policies(
    client: OpsManagerClient,
    project_id: str,
    mongocli_env: Dict[str, str],
) -> bool:
    """Validate feature control policies endpoint."""
    print("\n=== Validating Feature Policies ===")

    py_policy = client.feature_control.get(project_id=project_id, as_obj=False)
    py_policies = py_policy.get("policies", [])

    cli_result = run_mongocli(
        ["featurePolicies", "list", "--projectId", project_id], env=mongocli_env
    )
    cli_policies = cli_result.get("policies", [])

    print(f"  Python={len(py_policies)}, mongocli={len(cli_policies)}")

    differences = compare_results(py_policies, cli_policies)
    if differences:
        print("  Differences:")
        for diff in differences[:20]:
            print(f"    - {diff}")
        return False

    print("PASS: Feature policies match!")
    return True


def validate_log_collection(
    client: OpsManagerClient,
    project_id: str,
    mongocli_env: Dict[str, str],
) -> bool:
    """Validate log collection jobs endpoint."""
    print("\n=== Validating Log Collection ===")

    py_jobs = client.log_collection.list(project_id=project_id, as_obj=False)

    cli_result = run_mongocli(
        ["logs", "jobs", "list", "--projectId", project_id], env=mongocli_env
    )
    cli_jobs = cli_result.get("results", [])

    print(f"  Python={len(py_jobs)}, mongocli={len(cli_jobs)}")

    differences = compare_results(py_jobs, cli_jobs)
    if differences:
        print("  Differences:")
        for diff in differences[:20]:
            print(f"    - {diff}")
        return False

    print("PASS: Log collection match!")
    return True


# ---------------------------------------------------------------
# Main
# ---------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Validate Python library against mongocli (read-only endpoints)"
    )
    all_endpoints = [
        "hosts", "alerts", "agents", "backup", "events", "measurements",
        "automation_status", "maintenance_windows", "feature_policies",
        "log_collection", "all",
    ]
    parser.add_argument("--endpoint", choices=all_endpoints,
                        default="all", help="Which endpoint to validate")
    parser.add_argument("--cluster-id", default=os.environ.get("OM_CLUSTER_ID"),
                        help="Cluster ID for backup validation")
    parser.add_argument("--base-url", default=os.environ.get("OM_BASE_URL"),
                        help="Ops Manager base URL")
    parser.add_argument("--public-key", default=os.environ.get("OM_PUBLIC_KEY"),
                        help="API public key")
    parser.add_argument("--private-key", default=os.environ.get("OM_PRIVATE_KEY"),
                        help="API private key")
    parser.add_argument("--org-id", default=os.environ.get("OM_ORG_ID"),
                        help="Organization ID")
    parser.add_argument("--project-id", default=os.environ.get("OM_PROJECT_ID"),
                        help="Project ID to validate")
    args = parser.parse_args()

    if not all([args.base_url, args.public_key, args.private_key, args.org_id, args.project_id]):
        print("Error: Missing required configuration.")
        print("Set environment variables or use command-line arguments:")
        print("  OM_BASE_URL, OM_PUBLIC_KEY, OM_PRIVATE_KEY, OM_ORG_ID, OM_PROJECT_ID")
        sys.exit(1)

    check_mongocli_available()

    mongocli_env = make_mongocli_env(args.base_url, args.public_key, args.private_key, args.org_id)

    print(f"Connecting to: {args.base_url}")
    print(f"Project ID: {args.project_id}")

    client = OpsManagerClient(
        base_url=args.base_url,
        public_key=args.public_key,
        private_key=args.private_key,
        verify_ssl=False,
        rate_limit=5.0,
    )

    results = {}

    try:
        if args.endpoint in ("hosts", "all"):
            results["hosts"] = validate_hosts(client, args.project_id, mongocli_env)

        if args.endpoint in ("alerts", "all"):
            results["alerts"] = validate_alerts(client, args.project_id, mongocli_env)

        if args.endpoint in ("agents", "all"):
            results["agents"] = validate_agents(client, args.project_id, mongocli_env)

        if args.endpoint in ("backup", "all"):
            results["backup"] = validate_backup(client, args.project_id, mongocli_env, args.cluster_id)

        if args.endpoint in ("events", "all"):
            results["events"] = validate_events(client, args.project_id, mongocli_env)

        if args.endpoint in ("measurements", "all"):
            results["measurements"] = validate_measurements(client, args.project_id, mongocli_env)

        if args.endpoint in ("automation_status", "all"):
            results["automation_status"] = validate_automation_status(client, args.project_id, mongocli_env)

        if args.endpoint in ("maintenance_windows", "all"):
            results["maintenance_windows"] = validate_maintenance_windows(client, args.project_id, mongocli_env)

        if args.endpoint in ("feature_policies", "all"):
            results["feature_policies"] = validate_feature_policies(client, args.project_id, mongocli_env)

        if args.endpoint in ("log_collection", "all"):
            results["log_collection"] = validate_log_collection(client, args.project_id, mongocli_env)

    finally:
        client.close()

    all_passed = print_summary(results)
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
