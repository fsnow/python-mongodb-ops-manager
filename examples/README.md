# Examples

Standalone consumers built on top of the `opsmanager` library. Each is meant to
be copied out and run on its own, so they depend on the single-file bundle
(`opsmanager_bundle.py`) rather than a `pip install`.

## om_health_summary.py — consolidated health summary for Grafana

Given one or more Ops Manager project IDs, produces a single JSON document with
the fleet-level metrics a dashboard needs:

- **totals** — `db_clusters`, `replica_sets`, `hosts`
- **cluster_health** — counts of `healthy` / `warning` / `degraded` clusters
- **clusters[]** — per-cluster drill-down for a table panel

### Setup

1. Build the bundle and drop it next to the script:

   ```bash
   python scripts/build_bundle.py          # writes dist-bundle/opsmanager_bundle.py
   cp dist-bundle/opsmanager_bundle.py examples/
   ```

   (For running inside this repo you can instead put the bundle on `PYTHONPATH`:
   `PYTHONPATH=dist-bundle python examples/om_health_summary.py ...`)

2. Provide credentials via environment variables — **never hard-code them**.
   A read-only key works, but it must also have **automation read** access
   (quorum is derived from the automation config — see "Voting membership"):

   ```bash
   export OM_BASE_URL="http://ops-manager.example.com:8081"
   export OM_PUBLIC_KEY="..."
   export OM_PRIVATE_KEY="..."
   ```

### Usage

```bash
# JSON to stdout (default)
python om_health_summary.py --project <PROJECT_ID> --project <PROJECT_ID>

# Human-readable table
python om_health_summary.py --project <PROJECT_ID> --pretty

# HTTP endpoint for Grafana (stdlib only, no web framework)
python om_health_summary.py --serve --port 8080 --project <PROJECT_ID> --project <PROJECT_ID>
#   GET http://localhost:8080/health                     -> the JSON summary
#   GET http://localhost:8080/health?projects=<id>,<id>  -> override projects per-request
```

Projects can also be supplied via `OM_PROJECT_IDS=<id>,<id>` instead of `--project`.

### Programmatic use (from another library)

The CLI is a thin wrapper over an importable core, so another Python project can
call it directly. The module is import-safe — all CLI/server code is guarded
behind `if __name__ == "__main__"`, so importing it has no side effects (its one
import-time requirement is that `opsmanager_bundle` is importable).

Two functions are meant for reuse:

- `health_summary(client, project_ids, now=None)` → returns the JSON-serializable
  summary `dict` (no printing, no `sys.exit`). This is the one to call.
- `client_from_env()` → convenience `OpsManagerClient` built from the `OM_*`
  environment variables.

```python
# Pattern A — caller owns the client (custom rate limit, reuse, callbacks, ...)
from opsmanager_bundle import OpsManagerClient
import om_health_summary as oh

client = OpsManagerClient(base_url=..., public_key=..., private_key=...)
summary = oh.health_summary(client, ["<project-id>", "<project-id>"])
client.close()

summary["totals"]                 # {'db_clusters': 2, 'replica_sets': 4, 'hosts': 18}
summary["cluster_health"]         # {'healthy': 2, 'warning': 0, 'degraded': 0}
summary["clusters"][0]["status"]  # 'HEALTHY'

# Pattern B — env-based convenience builder
import om_health_summary as oh
client = oh.client_from_env()     # OM_BASE_URL / OM_PUBLIC_KEY / OM_PRIVATE_KEY
summary = oh.health_summary(client, ["<project-id>"])
client.close()
```

The return value is a plain `dict`, so the caller can index into it, re-serialize
it, or merge it into a larger response.

Because this is an example file, it isn't on the import path by default. A
consuming project can either add `examples/` (and the bundle's directory) to
`PYTHONPATH`, or copy `om_health_summary.py` and `opsmanager_bundle.py` into its
own package. If it becomes a real dependency rather than a one-off, promote it
out of `examples/` into an installable module with a proper entry point.

### Grafana

Point the [Infinity](https://grafana.com/grafana/plugins/yesoreyeram-infinity-datasource/)
(or JSON) data source at `/health`. The KPI numbers live under `totals` and
`cluster_health`; the `clusters[]` array feeds a table panel. Responses are
cached for `CACHE_TTL_SECONDS` (default 30s) so frequent scrapes don't overload
Ops Manager — and the library's own rate limiter (2 req/s by default) caps the
call rate regardless.

### Example output

```json
{
  "generated_at": "2026-07-14T18:37:39Z",
  "project_ids": ["<rs-project>", "<sharded-project>"],
  "totals": { "db_clusters": 2, "replica_sets": 4, "hosts": 18 },
  "cluster_health": { "healthy": 2, "warning": 0, "degraded": 0, "unknown": 0 },
  "clusters": [
    {
      "project_id": "<rs-project>",
      "name": "example-replica-set",
      "type": "REPLICA_SET",
      "status": "HEALTHY",
      "nodes_total": 3, "nodes_up": 3, "nodes_down": 0,
      "replica_sets": [
        { "name": "example-replica-set", "type": "REPLICA_SET", "members_total": 3, "members_up": 3, "members_down": 0, "voting_total": 3, "voting_up": 3, "has_quorum": true, "down_members": [] }
      ]
    },
    {
      "project_id": "<sharded-project>",
      "name": "example-sharded-cluster",
      "type": "SHARDED_REPLICA_SET",
      "status": "HEALTHY",
      "nodes_total": 9, "nodes_up": 9, "nodes_down": 0,
      "replica_sets": [
        { "name": "shard0",  "type": "REPLICA_SET",                "members_total": 3, "members_up": 3, "members_down": 0, "voting_total": 3, "voting_up": 3, "has_quorum": true, "down_members": [] },
        { "name": "shard1",  "type": "REPLICA_SET",                "members_total": 3, "members_up": 3, "members_down": 0, "voting_total": 3, "voting_up": 3, "has_quorum": true, "down_members": [] },
        { "name": "configRS","type": "CONFIG_SERVER_REPLICA_SET",  "members_total": 3, "members_up": 3, "members_down": 0, "voting_total": 3, "voting_up": 3, "has_quorum": true, "down_members": [] }
      ]
    }
  ]
}
```

`members_*` count all replica-set members; `voting_*` count only voting members
(`votes >= 1`), which are what `has_quorum` is computed from. When vote data is
unavailable, `voting_total` / `voting_up` / `has_quorum` are `null` and the
cluster's `status` is `"UNKNOWN"`.

### How the metrics are defined

The Ops Manager `/clusters` endpoint returns a sharded cluster as several rows
sharing one `clusterName` — a `SHARDED_REPLICA_SET` umbrella plus one row per
shard and one for the config servers. The definitions below account for that.
All of them are **tunable constants at the top of the script**.

| Metric | Rule |
|--------|------|
| **DB Clusters** | distinct `clusterName` (a sharded cluster counts as 1) |
| **Replica Sets** | rows with typeName `REPLICA_SET` or `CONFIG_SERVER_REPLICA_SET` (`COUNT_CONFIG_SERVERS_AS_REPLICA_SETS`) |
| **Hosts** | monitored processes; mongos included by default (`COUNT_MONGOS_AS_HOSTS`), deactivated hosts excluded |

**Cluster health** is assessed per replica set, by quorum. Quorum — "does the
cluster remain operational" — is decided over **voting members only**
(`votes >= 1`):

- **Healthy** — every replica set has all its voting members up.
- **Warning** — a voting member is down, but every replica set retains majority
  (the cluster is still operational).
- **Degraded** — a replica set has lost voting majority (quorum), impacting the
  cluster.
- **Unknown** — vote data for a cluster couldn't be determined; the tool reports
  `UNKNOWN` rather than guess a quorum verdict.

A node counts as *up* when its `replicaStateName` is one of `UP_STATES`
(`PRIMARY`, `SECONDARY`, `ARBITER`) **and** its `lastPing` is newer than
`STALE_PING_SECONDS`. Tune these to match how quickly your Ops Manager surfaces
an outage.

#### Voting membership and why it matters

The Hosts API doesn't expose vote configuration, so voting membership is read
from the **automation config** (`replicaSets[].members[].votes`). This matters
for any cluster with non-voting members — for example, hidden non-voting
secondaries added ahead of a data-center migration. Counting those toward quorum
would misjudge whether the cluster is actually operational (e.g. call a
quorum-lost cluster merely "warning"). They are reported in `members_*` and in
`down_members`, but never counted in `voting_*` / `has_quorum`.

By default a non-voting member being down does **not** raise a cluster to
`WARNING` — so a migration node still doing initial sync doesn't create noise.
Set `WARN_ON_NONVOTING_DOWN = True` to flag any down member regardless of votes.

> **Permission requirement:** because quorum depends on the automation config,
> the API key must have **automation read** access in addition to cluster/host
> read. If that call fails, the tool errors out rather than emit an unreliable
> quorum verdict.

### Known limitation

`mongos` routers report `clusterId: null`, so they can't be attributed to a
specific cluster and are excluded from per-cluster health scoring (they still
count toward the host total). Health scoring is based on mongod replica-set
members.
