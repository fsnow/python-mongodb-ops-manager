A production-quality Python client library for the MongoDB Ops Manager API, designed to enable automated health checks, metrics collection, and fleet management for MongoDB deployments.

**Status:** Beta - Core functionality implemented and tested against live Ops Manager

## Features

- **Production-ready** - Built-in rate limiting, error handling, retry logic with exponential backoff
- **Type-safe** - Full type hints throughout with dataclass models
- **Pythonic** - Clean, idiomatic Python API design
- **Safe by default** - Conservative rate limiting to protect production Ops Manager instances
- **Tested** - Validated against live Ops Manager and cross-checked with mongocli (Go SDK)

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

# Create client
client = OpsManagerClient(
    base_url="https://ops-manager.example.com",
    public_key="your-public-key",
    private_key="your-private-key",
)

# List all projects
projects = client.projects.list()
for project in projects:
    print(f"Project: {project.name} ({project.id})")

# Get hosts in a project
hosts = client.deployments.list_hosts(project_id="your-project-id")
for host in hosts:
    print(f"Host: {host.hostname}:{host.port} - {host.replica_state_name}")

# Get metrics for a host (last 24 hours, 1-minute granularity)
metrics = client.measurements.host(
    project_id="your-project-id",
    host_id="host-id",
    granularity="PT1M",
    period="P1D",
    metrics=["OPCOUNTER_QUERY", "OPCOUNTER_INSERT", "CONNECTIONS"],
)

# Get Performance Advisor suggestions
suggestions = client.performance_advisor.get_suggested_indexes(
    project_id="your-project-id",
    host_id="hostname:27017",
    duration=86400000,  # 24 hours in milliseconds
)

# Clean up
client.close()
```

### Using as Context Manager

```python
with OpsManagerClient(
    base_url="https://ops-manager.example.com",
    public_key="your-public-key",
    private_key="your-private-key",
) as client:
    projects = client.projects.list()
```

## API Coverage

### Currently Implemented

| Service | Description |
|---------|-------------|
| `organizations` | List organizations, get org details, list projects in org |
| `projects` | List projects, get project by ID or name |
| `clusters` | List clusters, get cluster details |
| `deployments` | List hosts, databases, disks; get by ID or name |
| `measurements` | Host, database, and disk metrics with time-series data |
| `performance_advisor` | Namespaces, slow queries, suggested indexes |
| `alerts` | List alerts, acknowledge alerts |

### Configuration Options

```python
client = OpsManagerClient(
    base_url="https://ops-manager.example.com",
    public_key="your-public-key",
    private_key="your-private-key",
    timeout=30.0,           # Request timeout in seconds
    rate_limit=2.0,         # Max requests per second (conservative default)
    retry_count=3,          # Number of retries for failed requests
    retry_backoff=1.0,      # Base backoff time between retries
    verify_ssl=True,        # Verify SSL certificates
)
```

### Rate Limiting

Rate limiting is **built-in and enabled by default** to protect production Ops Manager instances. The default is 2 requests per second, which is conservative but safe.

```python
# Adjust rate limit if needed (be careful with production systems!)
client.set_rate_limit(5.0)  # 5 requests per second
```

### Pagination

All list methods support pagination automatically:

```python
# Fetch all results (handles pagination internally)
all_hosts = client.deployments.list_hosts(project_id="abc123")

# Or iterate with automatic pagination
for host in client.deployments.list_hosts_iter(project_id="abc123"):
    print(host.hostname)
```

### Return Types

All methods support returning either typed objects or raw dictionaries:

```python
# Return typed objects (default)
hosts = client.deployments.list_hosts(project_id="abc123", as_obj=True)
print(hosts[0].hostname)  # IDE autocomplete works

# Return raw dictionaries
hosts = client.deployments.list_hosts(project_id="abc123", as_obj=False)
print(hosts[0]["hostname"])
```

## Testing

### Live Integration Tests

Run the integration test suite against a live Ops Manager instance:

```bash
export OM_BASE_URL="http://ops-manager.example.com:8081"
export OM_PUBLIC_KEY="your-public-key"
export OM_PRIVATE_KEY="your-private-key"

python tests/test_live.py --verbose
```

### Validation Against mongocli

Compare output against the official MongoDB CLI (uses the Go SDK):

```bash
export OM_ORG_ID="your-org-id"
export OM_PROJECT_ID="your-project-id"

python tests/validate_against_mongocli.py
```

## Design Principles

This library is modeled after the official [MongoDB Go SDK](https://github.com/mongodb/go-client-mongodb-ops-manager) with Pythonic adaptations:

1. **Service-oriented architecture** - Logical grouping of API endpoints
2. **Explicit over implicit** - Project ID passed per-call, not stored globally
3. **Safe defaults** - Rate limiting and SSL verification enabled by default
4. **Flexible output** - Choose between typed objects or raw dictionaries

## Use Cases

This library has been tested primarily with **read-only API keys** for monitoring and reporting use cases:

- Automated health check reporting for large MongoDB fleets
- Metrics collection and statistical analysis
- Performance advisor recommendations aggregation
- Cluster topology documentation

Write operations (automation config, backup management, etc.) are not yet fully implemented or tested.

## Inspiration

- **Go SDK**: [go-client-mongodb-ops-manager](https://github.com/mongodb/go-client-mongodb-ops-manager) - Official MongoDB Go client
- **Python**: [atlasapi](https://pypi.org/project/atlasapi/) - Community Atlas API library

## Requirements

- Python 3.9+
- `requests` library

## License

Apache License 2.0 - See [LICENSE](LICENSE) for details.

## Contributing

Contributions welcome! Please open an issue or pull request.

## Disclaimer

This is an independent project and is not officially affiliated with or endorsed by MongoDB, Inc.
