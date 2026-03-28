A Python client library for the MongoDB Ops Manager API, for automating health checks, metrics collection, and reporting across MongoDB deployments.

**Status:** Beta — tested against live Ops Manager for read operations

## Features

- **Rate limiting** — built-in, enabled by default (2 req/s) to avoid overloading Ops Manager
- **Retries** — exponential backoff on transient failures
- **Type hints** — full annotations with dataclass models for API responses
- **Pagination** — automatic multi-page traversal with both eager and lazy (iterator) APIs
- **Flexible output** — typed dataclass objects or raw dicts, per call

## Installation

```bash
pip install opsmanager
```

Or install from source:

```bash
git clone https://github.com/fsnow/python-mongodb-ops-manager.git
cd python-mongodb-ops-manager
pip install -e .
```

## Quick Start

```python
from opsmanager import OpsManagerClient

client = OpsManagerClient(
    base_url="https://ops-manager.example.com",
    public_key="your-public-key",
    private_key="your-private-key",
)

# List all projects
projects = client.projects.list()
for project in projects:
    print(f"{project.name} ({project.id})")

# List hosts in a project
hosts = client.deployments.list_hosts(project_id="your-project-id")
for host in hosts:
    print(f"{host.hostname}:{host.port} — {host.replica_state_name}")

# Host metrics — last 24 hours at 1-minute granularity
metrics = client.measurements.host(
    project_id="your-project-id",
    host_id="host-id",
    granularity="PT1M",
    period="P1D",
    metrics=["OPCOUNTER_QUERY", "OPCOUNTER_INSERT", "CONNECTIONS"],
)

# Audit event log — project events in a date range
events = client.events.list_project_events(
    project_id="your-project-id",
    min_date="2026-01-01T00:00:00Z",
    max_date="2026-03-31T23:59:59Z",
)

# Automation convergence status
status = client.automation.get_status(project_id="your-project-id")
print(f"In goal state: {status.is_in_goal_state}")

# Active alerts
alerts = client.alerts.list(project_id="your-project-id", status="OPEN")

# Performance Advisor index suggestions
suggestions = client.performance_advisor.get_suggested_indexes(
    project_id="your-project-id",
    host_id="hostname:27017",
    duration=86400000,  # 24 hours in milliseconds
)

client.close()
```

### Context manager

```python
with OpsManagerClient(
    base_url="https://ops-manager.example.com",
    public_key="your-public-key",
    private_key="your-private-key",
) as client:
    projects = client.projects.list()
```

## API Coverage

All 25 services are read-only (GET) operations. Write operations are not implemented.

### Infrastructure & Topology

| Service | Methods | Description |
|---------|---------|-------------|
| `organizations` | `list`, `get`, `list_projects`, `list_users` | Organizations and their members |
| `projects` | `list`, `get`, `get_by_name`, `list_users`, `get_teams` | Projects (groups) |
| `clusters` | `list`, `get` | Cluster topology |
| `deployments` | `list_hosts`, `get_host`, `list_databases`, `list_disks` + iter variants | Hosts, databases, and disk partitions |

### Metrics & Performance

| Service | Methods | Description |
|---------|---------|-------------|
| `measurements` | `host`, `database`, `disk` | Time-series metrics for hosts, databases, and disks |
| `performance_advisor` | `get_namespaces`, `get_slow_queries`, `get_suggested_indexes` | Slow query analysis and index recommendations |

### Alerts

| Service | Methods | Description |
|---------|---------|-------------|
| `alerts` | `list`, `get` | Active and resolved alert instances |
| `alert_configurations` | `list`, `get`, `get_open_alerts`, `list_matcher_fields` + iter | Alert configuration rules |
| `global_alerts` | `list`, `get`, `list_open` + iter | Cross-project global alerts |

### Automation & Agents

| Service | Methods | Description |
|---------|---------|-------------|
| `automation` | `get_config`, `get_status`, `get_backup_agent_config`, `get_monitoring_agent_config` | Automation configuration and convergence status |
| `agents` | `list_by_type`, `list_links`, `get_project_versions`, `get_global_versions`, `list_api_keys` + iter | Agent inventory and versions |

### Backup

| Service | Methods | Description |
|---------|---------|-------------|
| `backup` | `list_snapshots`, `get_snapshot`, `list_backup_configs`, `get_backup_config`, `get_snapshot_schedule`, `list_restore_jobs`, `get_restore_job`, `list_checkpoints`, `get_checkpoint` + iter | Snapshots, configs, restore jobs, and checkpoints |

### Events & Audit

| Service | Methods | Description |
|---------|---------|-------------|
| `events` | `list_organization_events`, `get_organization_event`, `list_project_events`, `get_project_event` + iter | Audit event log (org and project level) |

### Diagnostics & Logs

| Service | Methods | Description |
|---------|---------|-------------|
| `diagnostics` | `get` → `bytes` | Diagnostic archive download (gzip) |
| `log_collection` | `list`, `get`, `download` → `bytes` + iter | Log collection jobs and log downloads |

### Maintenance

| Service | Methods | Description |
|---------|---------|-------------|
| `maintenance_windows` | `list`, `get` | Scheduled maintenance windows |

### Capacity & Licensing

| Service | Methods | Description |
|---------|---------|-------------|
| `server_usage` | `list_all_host_assignments`, `get_project_host_assignments`, `get_organization_host_assignments`, `get_project_server_type`, `get_organization_server_type`, `download_report` → `bytes` | Host assignments and capacity reporting |

### Feature Control

| Service | Methods | Description |
|---------|---------|-------------|
| `feature_control` | `get`, `list_supported_policies` | Project feature control policies |

### Access Control

| Service | Methods | Description |
|---------|---------|-------------|
| `teams` | `list`, `get`, `get_by_name`, `list_users` + iter | Organization teams |
| `users` | `get`, `get_by_name` | User lookup by ID or username |
| `api_keys` | `list_organization_keys`, `get_organization_key`, `list_project_keys` + iter | API key inventory (org and project level) |

### Admin (global owner role required)

| Service | Methods | Description |
|---------|---------|-------------|
| `admin_backup_stores` | `list_blockstores`, `get_blockstore`, `list_s3_blockstores`, `get_s3_blockstore`, `list_file_system_stores`, `get_file_system_store`, `list_oplog_stores`, `get_oplog_store`, `list_sync_stores`, `get_sync_store`, `list_daemons`, `get_daemon`, `list_project_jobs`, `get_project_job` + iter variants | Backup infrastructure configuration |
| `global_admin` | `list_api_keys`, `get_api_key`, `list_whitelist`, `get_whitelist_entry` + iter | Global API keys and IP whitelist |

### Version & Migration

| Service | Methods | Description |
|---------|---------|-------------|
| `version` | `get_service_version`, `get_version_manifest` | Ops Manager version (health check) and MongoDB release metadata |
| `live_migration` | `get_connection_status` | Live data migration link status |

## Configuration

```python
client = OpsManagerClient(
    base_url="https://ops-manager.example.com",
    public_key="your-public-key",
    private_key="your-private-key",
    timeout=30.0,        # Request timeout in seconds (default 30)
    rate_limit=2.0,      # Max requests per second (default 2)
    rate_burst=1,        # Burst size: 1 = strict spacing, >1 = token bucket
    retry_count=3,       # Retries on transient failures (default 3)
    retry_backoff=1.0,   # Base backoff between retries in seconds
    verify_ssl=True,     # SSL certificate verification (default True)
    user_agent=None,     # Custom User-Agent string (optional)
)
```

## Rate Limiting

Rate limiting is enabled by default at 2 requests per second. With `rate_burst=1` (the default), requests are strictly spaced — no bursting. This keeps the load on Ops Manager predictable.

```python
# Increase if your Ops Manager instance can handle it
client.set_rate_limit(5.0)
```

## Pagination

List methods come in two forms:

```python
# Fetch all pages into a list
all_hosts = client.deployments.list_hosts(project_id="abc123")

# Iterate page by page (lazy — avoids loading everything into memory)
for host in client.deployments.list_hosts_iter(project_id="abc123"):
    print(host.hostname)
```

## Return Types

Every method accepts `as_obj=True` (default) or `as_obj=False`:

```python
# Typed dataclass objects — IDE autocomplete works
hosts = client.deployments.list_hosts(project_id="abc123")
print(hosts[0].hostname)

# Raw dicts — useful for direct serialization
hosts = client.deployments.list_hosts(project_id="abc123", as_obj=False)
print(hosts[0]["hostname"])
```

## Request Callbacks

Attach callbacks for logging or tracing:

```python
client.on_request(lambda method, url, kwargs: print(f"→ {method} {url}"))
client.on_response(lambda resp: print(f"← {resp.status_code}"))
```

## Testing

### Unit Tests

```bash
PYTHONPATH=. pytest tests/unit/ -v
```

Covers: rate limiter, pagination edge cases, HTTP error mapping (401/404/429/500), retries, and measurement parameter validation.

### Live Integration Tests

```bash
export OM_BASE_URL="http://ops-manager.example.com:8081"
export OM_PUBLIC_KEY="your-public-key"
export OM_PRIVATE_KEY="your-private-key"

python tests/test_live.py --verbose
```

### Validation Against mongocli

Compare output against the official MongoDB CLI (Go SDK):

```bash
export OM_ORG_ID="your-org-id"
export OM_PROJECT_ID="your-project-id"

python tests/validate_against_mongocli.py
```

## Design Notes

Modeled after the official [MongoDB Go SDK](https://github.com/mongodb/go-client-mongodb-ops-manager):

- **Service-oriented** — each API section is a separate service class
- **Explicit project IDs** — passed per call rather than stored on the client
- **Consistent signatures** — `list_*` / `get_*` naming, `as_obj` toggle, `items_per_page` on paginators
- **Binary downloads** — `diagnostics.get()`, `log_collection.download()`, and `server_usage.download_report()` return `bytes` directly

## Use Cases

Primarily used with read-only API keys for monitoring and reporting:

- Health check reporting across MongoDB fleets
- Metrics collection and analysis
- Audit log querying for compliance reporting
- Backup inventory and restore job tracking
- Access control audits (API keys, teams, users)
- Capacity and license reporting

## Requirements

- Python 3.9+
- `requests`

## License

Apache License 2.0 — see [LICENSE](LICENSE) for details.

## Contributing

Contributions welcome. Please open an issue or pull request.

## Disclaimer

This is an independent project and is not officially affiliated with or endorsed by MongoDB, Inc.
