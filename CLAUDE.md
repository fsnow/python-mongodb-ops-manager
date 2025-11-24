# CLAUDE.md - Project Context for Claude Code

## Project Overview

**python-mongodb-ops-manager** (`opsmanager`) is a Python client library for the MongoDB Ops Manager API.

### Purpose
Enable automated health checks, metrics collection, and fleet management for MongoDB deployments managed by Ops Manager. This supports the automation plan defined in `~/Projects/WFRCE/AUTOMATION_PLAN.md`.

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
    └── alerts.py            # Alerts API
```

## Current Status

### Implemented
- [x] Core client with rate limiting and retries
- [x] HTTP Digest authentication
- [x] Exception hierarchy mapping HTTP status codes
- [x] Pagination (automatic and iterator-based)
- [x] Services: organizations, projects, clusters, deployments, measurements, performance_advisor, alerts
- [x] Typed dataclasses for all major API types
- [x] Validation script against mongocli

### Not Yet Implemented
- [ ] Automation service (automationConfig)
- [ ] Backup services (snapshots, restore jobs)
- [ ] Events service
- [ ] Log collection service
- [ ] Additional services from Go SDK (see `opsmngr.go` lines 88-129)

### Testing
- No live Ops Manager currently available for testing
- Validation approach: `tests/validate_against_mongocli.py` compares output against mongocli (Go SDK)
- All Python files pass syntax check (`python -m py_compile`)

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
# Install in development mode
pip install -e .

# Install with dev dependencies
pip install -e ".[dev]"

# Syntax check all files
python -m py_compile opsmanager/*.py opsmanager/services/*.py

# Run validation against mongocli (requires Ops Manager access)
export OM_BASE_URL="https://ops-manager.example.com"
export OM_PUBLIC_KEY="your-key"
export OM_PRIVATE_KEY="your-key"
export OM_PROJECT_ID="your-project"
python tests/validate_against_mongocli.py
```

## Related Projects

- **AUTOMATION_PLAN.md**: `~/Projects/WFRCE/AUTOMATION_PLAN.md` - defines export scripts that will use this library
- **Export scripts**: To be built in this repo or separately, using this library

## Notes

- Copyright: Frank Snow (independent project, not MongoDB)
- License: Apache 2.0
- Python: 3.9+
- Dependencies: `requests` only
