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
Shared utilities for mongocli validation scripts.

Provides comparison helpers, key converters, and the mongocli runner
used by both read-only and admin validation scripts.
"""

import json
import os
import subprocess
from typing import Any, Dict, List, Optional, Set


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


def filter_differences(
    differences: List[str],
    expected_py_extras: Optional[Set[str]] = None,
    expected_cli_extras: Optional[Set[str]] = None,
) -> List[str]:
    """Filter out expected differences, returning only unexpected ones."""
    expected_py_extras = expected_py_extras or set()
    expected_cli_extras = expected_cli_extras or set()

    unexpected = []
    for diff in differences:
        field = diff_field(diff)
        if "Missing in CLI:" in diff and field in expected_py_extras:
            continue
        if "Missing in Python:" in diff and field in expected_cli_extras:
            continue
        unexpected.append(diff)
    return unexpected


def check_mongocli_available() -> None:
    """Check that mongocli is installed and exit if not."""
    try:
        subprocess.run(["mongocli", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: mongocli not found. Install from:")
        print("  https://www.mongodb.com/docs/mongocli/stable/install/")
        import sys
        sys.exit(1)


def make_mongocli_env(base_url: str, public_key: str, private_key: str, org_id: str) -> Dict[str, str]:
    """Build mongocli environment variables from Ops Manager credentials."""
    return {
        "MCLI_OPS_MANAGER_URL": base_url,
        "MCLI_PUBLIC_API_KEY": public_key,
        "MCLI_PRIVATE_API_KEY": private_key,
        "MCLI_ORG_ID": org_id,
    }


def print_summary(results: Dict[str, bool]) -> bool:
    """Print test summary and return True if all passed."""
    print("\n=== Summary ===")
    all_passed = True
    for endpoint, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {endpoint}: {status}")
        if not passed:
            all_passed = False
    return all_passed
