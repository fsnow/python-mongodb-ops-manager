# CLAUDE.md - Project Context for Claude Code

## Project Overview

**python-mongodb-ops-manager** (`opsmanager`) is a Python client library for the MongoDB Ops Manager API.

### Purpose

Enable automated health checks, metrics collection, and fleet management for MongoDB deployments managed by Ops Manager.

### Design Decisions
- **Architecture**: Service-oriented, modeled after the official [Go SDK](https://github.com/mongodb/go-client-mongodb-ops-manager)
- **Naming**: snake_case (Pythonic) vs Go SDK's camelCase
- **Project ID**: Passed per-call (explicit) rather than stored globally
- **Rate limiting**: Built-in, default 2 req/sec to protect production Ops Manager
- **Return types**: Support both typed dataclasses (`as_obj=True`) and raw dicts

### Key References
- **Go SDK**: `~/github/mongodb/go-client-mongodb-ops-manager/opsmngr/` - authoritative for API coverage
- **atlasapi**: `~/github/mgmonteleone/python-atlasapi/atlasapi/` - Python style reference
- **Ops Manager API docs**: https://www.mongodb.com/docs/ops-manager/current/reference/api/

## Package Structure

```
opsmanager/
├── __init__.py              # Exports OpsManagerClient, exceptions
├── auth.py                  # HTTP Digest authentication
├── client.py                # Main OpsManagerClient class
├── errors.py                # Exception hierarchy
├── network.py               # HTTP layer with rate limiting, retries
├── pagination.py            # Automatic pagination helpers
├── types.py                 # Dataclass models for API responses
└── services/
    ├── base.py              # BaseService with _get, _post, _paginate
    ├── organizations.py     # Organizations API
    ├── projects.py          # Projects (Groups) API
    ├── clusters.py          # Clusters API
    ├── deployments.py       # Hosts, databases, disks
    ├── measurements.py      # Time-series metrics
    ├── performance_advisor.py  # Slow queries, index suggestions
    ├── alerts.py            # Alerts API
    ├── alert_configurations.py  # Alert rules/policies
    ├── agents.py            # Monitoring, backup, automation agents
    ├── backup.py            # Snapshots, restore jobs, checkpoints, configs
    ├── automation.py        # Automation config and status
    ├── events.py            # Project and organization events
    ├── global_alerts.py     # Global alerts (admin)
    ├── diagnostics.py       # Diagnostic archives
    ├── maintenance_windows.py  # Scheduled maintenance
    ├── log_collection.py    # Log collection jobs (read + write)
    ├── server_usage.py      # Host assignments, server types
    ├── feature_control.py   # Feature policies
    ├── teams.py             # Team management
    ├── users.py             # User management
    ├── api_keys.py          # API key management
    ├── version.py           # Ops Manager version info
    ├── live_migration.py    # Live migration status
    ├── admin_backup_stores.py  # Backup store admin
    └── global_admin.py      # Global admin operations
```

## Current Status

**Published to PyPI**: <https://pypi.org/project/opsmanager/>

**v0.4.0** — 100% coverage of read-only Ops Manager APIs (25 services).

### Implemented

- [x] Core client with rate limiting and retries
- [x] HTTP Digest authentication
- [x] Exception hierarchy mapping HTTP status codes
- [x] Pagination (automatic and iterator-based)
- [x] 25 services covering all read-only Ops Manager API endpoints
- [x] Typed dataclasses for all major API types
- [x] Log collection write operations (create, extend, retry, delete)
- [x] Validation scripts against mongocli (10 read-only + 4 admin endpoints)

### Not Yet Implemented

- [ ] Write operations for most services (automation config updates, backup enable/disable, etc.)
- [ ] Additional admin-only write endpoints

### Testing

- **Live tests**: `tests/test_live.py` — 11 core integration tests
- **Extended live tests**: `tests/test_live_extended.py` — 22 tests covering all Tier 1-3 services
- **mongocli validation (read-only)**: `tests/validate_against_mongocli.py` — 10 endpoints
- **mongocli validation (admin)**: `tests/validate_against_mongocli_admin.py` — 4 endpoints
- **Unit tests**: `tests/unit/` — 108 tests (error handling, pagination, rate limiter, measurements, log collection, service bugs)
- All Python files pass syntax check (`python -m py_compile`)

**Last tested**: 2026-03-30 against Ops Manager at `http://54.81.135.16:8081`

## Usage Example

```python
from opsmanager import OpsManagerClient

client = OpsManagerClient(
    base_url="https://ops-manager.example.com",
    public_key="your-public-key",
    private_key="your-private-key",
)

# List hosts
hosts = client.deployments.list_hosts(project_id="abc123")

# Get metrics
metrics = client.measurements.host(
    project_id="abc123",
    host_id="host-id",
    granularity="PT1M",
    period="P1D",
)

client.close()
```

## Development Commands

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install in development mode
pip install -e .

# Install with dev dependencies
pip install -e ".[dev]"

# Syntax check all files
python -m py_compile opsmanager/*.py opsmanager/services/*.py

# Run live integration tests (requires Ops Manager access)
export OM_BASE_URL="http://ops-manager:8081"
export OM_PUBLIC_KEY="your-key"
export OM_PRIVATE_KEY="your-key"
python tests/test_live.py --verbose

# Run validation against mongocli (requires mongocli installed)
export OM_ORG_ID="your-org-id"
export OM_PROJECT_ID="your-project"
python tests/validate_against_mongocli.py
```

> **Required for every change**: Both `test_live.py` and `validate_against_mongocli.py` must pass before
> committing or publishing. The mongocli validation step was skipped in v0.3.0 and should not be skipped again.

## Related Projects

- **AUTOMATION_PLAN.md**: Defined elsewhere - describes health check export scripts that use this library

## Publishing a New Version to PyPI

### Steps

1. **Update version** in `opsmanager/__init__.py` and `pyproject.toml`
   ```python
   __version__ = "0.2.0"  # in __init__.py
   ```
   ```toml
   version = "0.2.0"  # in pyproject.toml
   ```

2. **Test the changes**
   ```bash
   source .venv/bin/activate
   python tests/test_live.py --verbose
   ```

3. **Build the package**
   ```bash
   pip install build twine
   rm -rf dist/ build/ *.egg-info
   python -m build
   twine check dist/*
   ```

4. **Upload to PyPI**
   ```bash
   twine upload dist/*
   ```
   - Username: `__token__`
   - Password: PyPI API token (get from https://pypi.org/manage/account/token/)

5. **Tag and push**
   ```bash
   git add -A
   git commit -m "Release vX.Y.Z"
   git tag -a vX.Y.Z -m "Release vX.Y.Z"
   git push && git push --tags
   ```

### Version Numbering

- **Patch** (0.1.1): Bug fixes, no API changes
- **Minor** (0.2.0): New features, backward compatible
- **Major** (1.0.0): Breaking API changes

### TestPyPI (Optional)

To test before real release:
```bash
twine upload --repository testpypi dist/*
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ opsmanager
```

## Notes

- Copyright: Frank Snow (independent project, not MongoDB)
- License: Apache 2.0
- Python: 3.9 - 3.14
- Dependencies: `requests` only
- PyPI: https://pypi.org/project/opsmanager/
