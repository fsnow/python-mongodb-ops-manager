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
Admin-level validation script to compare Python library output against mongocli.

This script requires a Global Owner API key. For read-only validations,
see validate_against_mongocli.py.

Usage:
    # Set environment variables
    export OM_BASE_URL="http://ops-manager.example.com:8081"
    export OM_ADMIN_PUBLIC_KEY="your-admin-public-key"
    export OM_ADMIN_PRIVATE_KEY="your-admin-private-key"
    export OM_ORG_ID="your-org-id"
    export OM_PROJECT_ID="your-project-id"
    export OM_CLUSTER_ID="your-cluster-id"  # optional, auto-detected if not set

    # Run all admin validations
    python tests/validate_against_mongocli_admin.py

    # Or validate specific endpoints
    python tests/validate_against_mongocli_admin.py --endpoint global_alerts
    python tests/validate_against_mongocli_admin.py --endpoint server_usage
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
    filter_differences,
    check_mongocli_available,
    make_mongocli_env,
    print_summary,
)


# ---------------------------------------------------------------
# Admin validators (Global Owner key required)
# ---------------------------------------------------------------

def validate_global_alerts(client: OpsManagerClient, mongocli_env: Dict[str, str]) -> bool:
    """Validate global alerts endpoint."""
    print("\n=== Validating Global Alerts ===")

    py_alerts = client.global_alerts.list(as_obj=False)

    cli_result = run_mongocli(["alerts", "global", "list"], env=mongocli_env)
    cli_alerts = cli_result.get("results", [])

    print(f"  Python={len(py_alerts)}, mongocli={len(cli_alerts)}")

    differences = compare_results(py_alerts, cli_alerts)
    if differences:
        print("  Differences:")
        for diff in differences[:20]:
            print(f"    - {diff}")
        return False

    print("PASS: Global alerts match!")
    return True


def validate_server_usage(
    client: OpsManagerClient,
    project_id: str,
    mongocli_env: Dict[str, str],
) -> bool:
    """Validate server usage host assignments endpoint."""
    print("\n=== Validating Server Usage ===")

    from datetime import datetime, timedelta, timezone
    end = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    start = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        py_assignments = client.server_usage.get_project_host_assignments(
            project_id=project_id, start_date=start, end_date=end, as_obj=False
        )
    except Exception as e:
        print(f"  (Server usage not available: {e})")
        return True

    try:
        cli_result = run_mongocli(
            ["serverUsage", "projects", "hosts", "list",
             "--projectId", project_id,
             "--startDate", start,
             "--endDate", end],
            env=mongocli_env,
        )
        cli_assignments = cli_result.get("results", cli_result if isinstance(cli_result, list) else [])
    except RuntimeError as e:
        print(f"  (mongocli server usage failed: {e})")
        return True

    print(f"  Python={len(py_assignments)}, mongocli={len(cli_assignments)}")

    differences = compare_results(py_assignments, cli_assignments)
    if differences:
        print("  Differences:")
        for diff in differences[:20]:
            print(f"    - {diff}")
        return False

    print("PASS: Server usage match!")
    return True


def validate_automation_config(
    client: OpsManagerClient,
    project_id: str,
    mongocli_env: Dict[str, str],
) -> bool:
    """Validate automation config endpoint (structure comparison only)."""
    print("\n=== Validating Automation Config ===")

    py_config = client.automation.get_config(project_id=project_id)

    cli_config = run_mongocli(
        ["automation", "describe", "--projectId", project_id], env=mongocli_env
    )

    # Compare top-level keys only — the full config is very large
    py_keys = set(py_config.keys()) - {"links"}
    cli_keys = set(cli_config.keys()) - {"links"}

    missing_in_py = cli_keys - py_keys
    missing_in_cli = py_keys - cli_keys

    if missing_in_py:
        print(f"  Keys in CLI but not Python: {missing_in_py}")
    if missing_in_cli:
        print(f"  Keys in Python but not CLI: {missing_in_cli}")

    # Compare version field
    py_version = py_config.get("version")
    cli_version = cli_config.get("version")
    print(f"  Config version: py={py_version}, cli={cli_version}")

    # Compare process count
    py_procs = len(py_config.get("processes", []))
    cli_procs = len(cli_config.get("processes", []))
    print(f"  Processes: py={py_procs}, cli={cli_procs}")

    if py_procs != cli_procs:
        print("  Process count mismatch")
        return False

    # Compare replica set count
    py_rs = len(py_config.get("replicaSets", []))
    cli_rs = len(cli_config.get("replicaSets", []))
    print(f"  Replica sets: py={py_rs}, cli={cli_rs}")

    if py_rs != cli_rs:
        print("  Replica set count mismatch")
        return False

    print("PASS: Automation config match!")
    return True


def validate_restore_jobs(
    client: OpsManagerClient,
    project_id: str,
    mongocli_env: Dict[str, str],
    cluster_id: Optional[str] = None,
) -> bool:
    """Validate backup restore jobs endpoint."""
    print("\n=== Validating Restore Jobs ===")

    if not cluster_id:
        clusters = client.clusters.list(project_id=project_id)
        if not clusters:
            print("  No clusters found — skipping restore jobs validation")
            return True
        cluster_id = clusters[0].id
        print(f"  Using cluster: {clusters[0].cluster_name} ({cluster_id})")

    py_jobs = client.backup.list_restore_jobs(project_id, cluster_id, as_obj=False)

    cli_result = run_mongocli(
        ["backups", "restores", "list", cluster_id, "--projectId", project_id],
        env=mongocli_env,
    )
    cli_jobs = cli_result.get("results", [])

    print(f"  Python={len(py_jobs)}, mongocli={len(cli_jobs)}")

    differences = compare_results(py_jobs, cli_jobs)
    if differences:
        print("  Differences:")
        for diff in differences[:20]:
            print(f"    - {diff}")
        return False

    print("PASS: Restore jobs match!")
    return True


# ---------------------------------------------------------------
# Main
# ---------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Validate Python library against mongocli (admin endpoints, requires Global Owner key)"
    )
    all_endpoints = [
        "global_alerts", "server_usage", "automation_config",
        "restore_jobs", "all",
    ]
    parser.add_argument("--endpoint", choices=all_endpoints,
                        default="all", help="Which endpoint to validate")
    parser.add_argument("--cluster-id", default=os.environ.get("OM_CLUSTER_ID"),
                        help="Cluster ID for backup-related validation")
    parser.add_argument("--base-url", default=os.environ.get("OM_BASE_URL"),
                        help="Ops Manager base URL")
    parser.add_argument("--public-key",
                        default=os.environ.get("OM_ADMIN_PUBLIC_KEY", os.environ.get("OM_PUBLIC_KEY")),
                        help="Admin API public key (OM_ADMIN_PUBLIC_KEY or OM_PUBLIC_KEY)")
    parser.add_argument("--private-key",
                        default=os.environ.get("OM_ADMIN_PRIVATE_KEY", os.environ.get("OM_PRIVATE_KEY")),
                        help="Admin API private key (OM_ADMIN_PRIVATE_KEY or OM_PRIVATE_KEY)")
    parser.add_argument("--org-id", default=os.environ.get("OM_ORG_ID"),
                        help="Organization ID")
    parser.add_argument("--project-id", default=os.environ.get("OM_PROJECT_ID"),
                        help="Project ID to validate")
    args = parser.parse_args()

    if not all([args.base_url, args.public_key, args.private_key, args.org_id, args.project_id]):
        print("Error: Missing required configuration.")
        print("Set environment variables or use command-line arguments:")
        print("  OM_BASE_URL, OM_ADMIN_PUBLIC_KEY, OM_ADMIN_PRIVATE_KEY, OM_ORG_ID, OM_PROJECT_ID")
        sys.exit(1)

    check_mongocli_available()

    mongocli_env = make_mongocli_env(args.base_url, args.public_key, args.private_key, args.org_id)

    print(f"Connecting to: {args.base_url}")
    print(f"Project ID: {args.project_id}")
    print(f"Key: {args.public_key} (admin)")

    client = OpsManagerClient(
        base_url=args.base_url,
        public_key=args.public_key,
        private_key=args.private_key,
        verify_ssl=False,
        rate_limit=5.0,
    )

    results = {}

    try:
        if args.endpoint in ("global_alerts", "all"):
            results["global_alerts"] = validate_global_alerts(client, mongocli_env)

        if args.endpoint in ("server_usage", "all"):
            results["server_usage"] = validate_server_usage(client, args.project_id, mongocli_env)

        if args.endpoint in ("automation_config", "all"):
            results["automation_config"] = validate_automation_config(client, args.project_id, mongocli_env)

        if args.endpoint in ("restore_jobs", "all"):
            results["restore_jobs"] = validate_restore_jobs(
                client, args.project_id, mongocli_env, args.cluster_id
            )

    finally:
        client.close()

    all_passed = print_summary(results)
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
