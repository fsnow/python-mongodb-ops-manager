#!/usr/bin/env python3
"""
Build a single-file distribution of the opsmanager package.

Concatenates all opsmanager source files into one importable .py file
that can be sent into restricted environments where pip / wheel files
are not allowed (e.g. air-gapped banks that accept plain-text scripts
through email/ticketing review).

Output: dist-bundle/opsmanager_bundle.py

Usage:
    python scripts/build_bundle.py

The bundle has the same public surface as the regular package:

    from opsmanager_bundle import OpsManagerClient, OpsManagerError

…instead of `from opsmanager import …`.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List

REPO_ROOT = Path(__file__).resolve().parent.parent
PKG = REPO_ROOT / "opsmanager"
OUTPUT_DIR = REPO_ROOT / "dist-bundle"
OUTPUT_FILE = OUTPUT_DIR / "opsmanager_bundle.py"

# Files in dependency order. Skipping __init__.py files — their re-exports
# happen implicitly because everything ends up in one namespace.
FILES_IN_ORDER: List[Path] = [
    PKG / "errors.py",
    PKG / "auth.py",
    PKG / "pagination.py",
    PKG / "types.py",
    PKG / "network.py",
    PKG / "services" / "base.py",
    # All services depend only on base + types + pagination.
    # Order within the group doesn't matter.
    PKG / "services" / "organizations.py",
    PKG / "services" / "projects.py",
    PKG / "services" / "clusters.py",
    PKG / "services" / "deployments.py",
    PKG / "services" / "measurements.py",
    PKG / "services" / "performance_advisor.py",
    PKG / "services" / "alerts.py",
    PKG / "services" / "alert_configurations.py",
    PKG / "services" / "global_alerts.py",
    PKG / "services" / "automation.py",
    PKG / "services" / "agents.py",
    PKG / "services" / "backup.py",
    PKG / "services" / "events.py",
    PKG / "services" / "diagnostics.py",
    PKG / "services" / "maintenance_windows.py",
    PKG / "services" / "log_collection.py",
    PKG / "services" / "server_usage.py",
    PKG / "services" / "feature_control.py",
    PKG / "services" / "teams.py",
    PKG / "services" / "users.py",
    PKG / "services" / "api_keys.py",
    PKG / "services" / "version.py",
    PKG / "services" / "live_migration.py",
    PKG / "services" / "admin_backup_stores.py",
    PKG / "services" / "global_admin.py",
    PKG / "client.py",
]

# Match any `import opsmanager…` or `from opsmanager…` line, including
# multi-line parenthesized forms.
INTERNAL_IMPORT_RE = re.compile(
    r"^(from opsmanager(?:\.[\w.]+)?\s+import\s+\([^)]*\)|"
    r"from opsmanager(?:\.[\w.]+)?\s+import\s+[^\n]+|"
    r"import opsmanager(?:\.[\w.]+)?[^\n]*)$",
    re.MULTILINE,
)

# Strip license headers — keep only the first one in the bundle header.
LICENSE_HEADER_RE = re.compile(
    r"^# Copyright \d+ Frank Snow\n(?:#[^\n]*\n)*\n",
    re.MULTILINE,
)

# Strip the deferred `from opsmanager import __version__` inside network.py.
# A module-level __version__ is defined in the bundle header, so this is
# unnecessary in the flattened form.
DEFERRED_VERSION_IMPORT_RE = re.compile(
    r"^[ \t]*from opsmanager import __version__\s*#[^\n]*\n",
    re.MULTILINE,
)


def read_version() -> str:
    """Read __version__ from opsmanager/__init__.py."""
    text = (PKG / "__init__.py").read_text()
    m = re.search(r'__version__\s*=\s*"([^"]+)"', text)
    if not m:
        raise SystemExit("Could not find __version__ in opsmanager/__init__.py")
    return m.group(1)


def collect_external_imports(files: List[Path]) -> List[str]:
    """Collect distinct external (non-opsmanager) imports across all files."""
    imports = set()
    for path in files:
        text = path.read_text()
        # Match standalone import lines (not inside try/except, not inside funcs)
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if not (stripped.startswith("import ") or stripped.startswith("from ")):
                continue
            if "opsmanager" in stripped:
                continue
            # Skip indented imports (inside functions / TYPE_CHECKING blocks)
            if line[0] in (" ", "\t"):
                continue
            imports.add(stripped)
    return sorted(imports, key=_import_sort_key)


def _import_sort_key(line: str) -> tuple:
    """Sort: stdlib `import X` first, then stdlib `from X`, then third-party."""
    third_party_roots = {"requests"}
    root = line.split()[1].split(".")[0]
    is_third_party = root in third_party_roots
    is_from = line.startswith("from ")
    return (is_third_party, is_from, line)


def process_file(path: Path) -> str:
    """Return the body of a source file with imports and license stripped."""
    text = path.read_text()
    text = LICENSE_HEADER_RE.sub("", text, count=1)
    text = DEFERRED_VERSION_IMPORT_RE.sub("", text)
    text = INTERNAL_IMPORT_RE.sub("", text)
    # Remove the standalone import lines we already hoisted to the top
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith("from "):
            # Only strip top-level (column 0) imports — leave indented ones
            if line and line[0] not in (" ", "\t") and "opsmanager" not in stripped:
                continue
        lines.append(line)
    return "\n".join(lines)


def build_bundle() -> str:
    version = read_version()
    external_imports = collect_external_imports(FILES_IN_ORDER)

    header = f'''"""
opsmanager — single-file bundle of the opsmanager Python package.

Generated from the upstream package by scripts/build_bundle.py.
Source: https://github.com/fsnow/python-mongodb-ops-manager
PyPI:   https://pypi.org/project/opsmanager/

Use this when pip / wheel installs are not available. The public API is
identical to `import opsmanager`; just use `import opsmanager_bundle` (or
rename the file) instead.

Copyright 2024 Frank Snow
Licensed under the Apache License, Version 2.0 (the "License").
You may obtain a copy at http://www.apache.org/licenses/LICENSE-2.0.

Bundled version: {version}
"""

__version__ = "{version}"
__author__ = "Frank Snow"

'''

    parts: List[str] = [header]
    parts.append("\n".join(external_imports))
    parts.append("\n\n")

    for path in FILES_IN_ORDER:
        rel = path.relative_to(REPO_ROOT)
        parts.append(f"\n# {'=' * 70}\n# {rel}\n# {'=' * 70}\n")
        parts.append(process_file(path))
        parts.append("\n")

    # Public __all__ — same surface as opsmanager/__init__.py
    parts.append("""
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
    "OpsManagerTimeoutError",
    "OpsManagerConnectionError",
    "OpsManagerValidationError",
    "__version__",
]
""")
    return "".join(parts)


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    bundle = build_bundle()
    OUTPUT_FILE.write_text(bundle)
    line_count = bundle.count("\n")
    print(f"Wrote {OUTPUT_FILE} ({line_count} lines, {len(bundle):,} bytes)")


if __name__ == "__main__":
    main()
