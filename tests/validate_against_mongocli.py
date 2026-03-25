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

This script compares the raw JSON responses from our Python library
against mongocli (which uses the official Go SDK) to validate correctness.

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

    # Run validation
    python tests/validate_against_mongocli.py

    # Or validate specific endpoints
    python tests/validate_against_mongocli.py --endpoint hosts
    python tests/validate_against_mongocli.py --endpoint alerts
    python tests/validate_against_mongocli.py --endpoint agents
    python tests/validate_against_mongocli.py --endpoint backup
    python tests/validate_against_mongocli.py --endpoint backup --cluster-id <clusterId>

Note:
    mongocli environment variables (MCLI_*) are set automatically from OM_* vars.
    The clusters endpoint is not validated because mongocli uses a different API
    (automationConfig) that requires additional permissions.
"""

import argparse
import json
import os
import subprocess
import sys
from typing import Any, Dict, List, Optional, Set

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from opsmanager import OpsManagerClient


# camelCase to snake_case conversion for comparison
def camel_to_snake(name: str) -> str:
    """Convert camelCase to snake_case."""
    import re
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def snake_to_camel(name: str) -> str:
    """Convert snake_case to camelCase."""
    components = name.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


def normalize_keys(obj: Any, to_snake: bool = True) -> Any:
    """Recursively convert dict keys between camelCase and snake_case."""
    if isinstance(obj, dict):
        converter = camel_to_snake if to_snake else snake_to_camel
        return {converter(k): normalize_keys(v, to_snake) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [normalize_keys(item, to_snake) for item in obj]
    return obj


def run_mongocli(args: List[str], env: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Run mongocli command and return JSON output.

    Args:
        args: Command arguments for mongocli ops-manager.
        env: Environment variables to pass to mongocli.
    """
    cmd = ["mongocli", "ops-manager"] + args + ["-o", "json"]
    print(f"Running: {' '.join(cmd)}")

    # Merge provided env with current environment
    run_env = os.environ.copy()
    if env:
        run_env.update(env)

    result = subprocess.run(cmd, capture_output=True, text=True, env=run_env)

    if result.returncode != 0:
        print(f"mongocli error: {result.stderr}")
        raise RuntimeError(f"mongocli failed: {result.stderr}")

    return json.loads(result.stdout)


def diff_field(diff: str) -> str:
    """Extract the leaf field name from a difference string like 'Missing in CLI: foo.bar.baz'."""
    path = diff.split(": ", 1)[-1]  # everything after the prefix
    return path.split(".")[-1]      # last component (handles nested and top-level)


def compare_results(
    py_result: Any,
    cli_result: Any,
    path: str = "",
    ignore_fields: Optional[Set[str]] = None,
) -> List[str]:
    """Compare Python and CLI results, returning list of differences.

    Both inputs are expected to be in camelCase (raw API response format).
    """
    differences = []
    ignore_fields = ignore_fields or {"links", "Links"}  # Ignore pagination links

    if isinstance(py_result, dict) and isinstance(cli_result, dict):
        all_keys = set(py_result.keys()) | set(cli_result.keys())
        for key in all_keys:
            if key in ignore_fields:
                continue

            key_path = f"{path}.{key}" if path else key

            if key not in py_result:
                differences.append(f"Missing in Python: {key_path}")
            elif key not in cli_result:
                differences.append(f"Missing in CLI: {key_path}")
            else:
                differences.extend(
                    compare_results(py_result[key], cli_result[key], key_path, ignore_fields)
                )

    elif isinstance(py_result, list) and isinstance(cli_result, list):
        if len(py_result) != len(cli_result):
            differences.append(f"{path}: list length mismatch (py={len(py_result)}, cli={len(cli_result)})")
        else:
            for i, (py_item, cli_item) in enumerate(zip(py_result, cli_result)):
                differences.extend(
                    compare_results(py_item, cli_item, f"{path}[{i}]", ignore_fields)
                )

    elif py_result != cli_result:
        # Allow for minor type differences (int vs float, etc.)
        if not (isinstance(py_result, (int, float)) and isinstance(cli_result, (int, float)) and py_result == cli_result):
            differences.append(f"{path}: value mismatch (py={py_result!r}, cli={cli_result!r})")

    return differences


def validate_hosts(client: OpsManagerClient, project_id: str, mongocli_env: Dict[str, str]) -> bool:
    """Validate hosts endpoint."""
    print("\n=== Validating Hosts ===")

    # Get from Python library (raw dict)
    py_hosts = client.deployments.list_hosts(project_id=project_id, as_obj=False)

    # Get from mongocli
    cli_result = run_mongocli(["processes", "list", "--projectId", project_id], env=mongocli_env)
    cli_hosts = cli_result.get("results", cli_result)

    print(f"Python returned {len(py_hosts)} hosts")
    print(f"mongocli returned {len(cli_hosts)} hosts")

    # Fields our library returns that mongocli omits (our library is more complete)
    expected_py_extras = {
        "lastIndexSizeBytes", "hidden", "lowUlimit", "systemInfo",
        "lastDataSizeBytes", "slaveDelaySec", "hiddenSecondary",
        "hasStartupWarnings", "journalingEnabled",
    }
    # Fields mongocli adds as Go struct zero-values not present in the actual API response
    expected_cli_extras = set()

    # Compare
    differences = compare_results(py_hosts, cli_hosts)

    # Filter out expected differences
    unexpected_differences = []
    for diff in differences:
        field = diff_field(diff)
        if "Missing in CLI:" in diff and field in expected_py_extras:
            continue
        if "Missing in Python:" in diff and field in expected_cli_extras:
            continue
        unexpected_differences.append(diff)

    if unexpected_differences:
        print("Unexpected differences found:")
        for diff in unexpected_differences[:20]:
            print(f"  - {diff}")
        if len(unexpected_differences) > 20:
            print(f"  ... and {len(unexpected_differences) - 20} more")
        return False

    if differences:
        extra_count = len(differences) - len(unexpected_differences)
        print(f"  Note: Python library returns {extra_count} additional fields not in mongocli output")

    print("PASS: Hosts match!")
    return True


def validate_alerts(client: OpsManagerClient, project_id: str, mongocli_env: Dict[str, str]) -> bool:
    """Validate alerts endpoint."""
    print("\n=== Validating Alerts ===")

    # Get from Python library (raw dict)
    py_alerts = client.alerts.list(project_id=project_id, as_obj=False)

    # Get from mongocli
    cli_result = run_mongocli(["alerts", "list", "--projectId", project_id], env=mongocli_env)
    cli_alerts = cli_result.get("results", cli_result)

    print(f"Python returned {len(py_alerts)} alerts")
    print(f"mongocli returned {len(cli_alerts)} alerts")

    expected_py_extras = {"orgId", "hostId"}
    expected_cli_extras: Set[str] = set()

    # Compare
    differences = compare_results(py_alerts, cli_alerts)

    # Filter out expected differences
    unexpected_differences = []
    for diff in differences:
        field = diff_field(diff)
        if "Missing in CLI:" in diff and field in expected_py_extras:
            continue
        if "Missing in Python:" in diff and field in expected_cli_extras:
            continue
        unexpected_differences.append(diff)

    if unexpected_differences:
        print("Unexpected differences found:")
        for diff in unexpected_differences[:20]:
            print(f"  - {diff}")
        return False

    if differences:
        extra_count = len(differences) - len(unexpected_differences)
        print(f"  Note: Python library returns {extra_count} additional fields not in mongocli output")

    print("PASS: Alerts match!")
    return True


def validate_agents(client: OpsManagerClient, project_id: str, mongocli_env: Dict[str, str]) -> bool:
    """Validate agents endpoint."""
    print("\n=== Validating Agents ===")
    all_passed = True

    # Fields mongocli adds as Go struct zero-values not present in the actual API response
    expected_cli_extras = {"tag", "pingCount", "isManaged", "lastPing"}

    for agent_type in ("MONITORING", "BACKUP", "AUTOMATION"):
        py_agents = client.agents.list(project_id=project_id, agent_type=agent_type, as_obj=False)

        cli_result = run_mongocli(
            ["agents", "list", agent_type, "--projectId", project_id], env=mongocli_env
        )
        cli_agents = cli_result.get("results", [])

        print(f"  {agent_type}: Python={len(py_agents)}, mongocli={len(cli_agents)}")

        differences = compare_results(py_agents, cli_agents)
        unexpected = [
            d for d in differences
            if not ("Missing in Python:" in d and diff_field(d) in expected_cli_extras)
        ]
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

    # Resolve cluster ID if not provided
    if not cluster_id:
        clusters = client.clusters.list(project_id=project_id)
        if not clusters:
            print("  No clusters found — skipping backup validation")
            return True
        cluster_id = clusters[0].id
        print(f"  Using cluster: {clusters[0].cluster_name} ({cluster_id})")

    all_passed = True

    # Validate backup config
    try:
        py_config = client.backup.get_backup_config(project_id, cluster_id)
        cli_config = run_mongocli(
            ["backups", "config", "describe", cluster_id, "--projectId", project_id],
            env=mongocli_env,
        )

        # Fields our library returns that mongocli omits from backup config
        expected_config_py_extras = {
            "excludedNamespaces", "multiRegionMisconfigured", "multiRegionBackupEnabled"
        }
        differences = compare_results(py_config, cli_config)
        unexpected = [
            d for d in differences
            if not ("Missing in CLI:" in d and diff_field(d) in expected_config_py_extras)
        ]
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

    # Validate snapshots
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


def main():
    parser = argparse.ArgumentParser(description="Validate Python library against mongocli")
    parser.add_argument("--endpoint", choices=["hosts", "alerts", "agents", "backup", "all"],
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

    # Validate required args
    if not all([args.base_url, args.public_key, args.private_key, args.org_id, args.project_id]):
        print("Error: Missing required configuration.")
        print("Set environment variables or use command-line arguments:")
        print("  OM_BASE_URL, OM_PUBLIC_KEY, OM_PRIVATE_KEY, OM_ORG_ID, OM_PROJECT_ID")
        sys.exit(1)

    # Check mongocli is available
    try:
        subprocess.run(["mongocli", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: mongocli not found. Install from:")
        print("  https://www.mongodb.com/docs/mongocli/stable/install/")
        sys.exit(1)

    # Set up mongocli environment variables
    mongocli_env = {
        "MCLI_OPS_MANAGER_URL": args.base_url,
        "MCLI_PUBLIC_API_KEY": args.public_key,
        "MCLI_PRIVATE_API_KEY": args.private_key,
        "MCLI_ORG_ID": args.org_id,
    }

    print(f"Connecting to: {args.base_url}")
    print(f"Project ID: {args.project_id}")

    # Create Python client
    client = OpsManagerClient(
        base_url=args.base_url,
        public_key=args.public_key,
        private_key=args.private_key,
        verify_ssl=False,  # Often needed for test instances
        rate_limit=5.0,  # Faster for testing
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

    finally:
        client.close()

    # Summary
    print("\n=== Summary ===")
    all_passed = True
    for endpoint, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {endpoint}: {status}")
        if not passed:
            all_passed = False

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
