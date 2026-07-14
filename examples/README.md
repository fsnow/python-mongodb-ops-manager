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
   A read-only key is sufficient:

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
  "cluster_health": { "healthy": 2, "warning": 0, "degraded": 0 },
  "clusters": [
    {
      "project_id": "<sharded-project>",
      "name": "example-sharded-cluster",
      "type": "SHARDED_REPLICA_SET",
      "status": "HEALTHY",
      "nodes_total": 9, "nodes_up": 9, "nodes_down": 0,
      "replica_sets": [
        { "name": "shard0",  "type": "REPLICA_SET",                "members_total": 3, "members_up": 3, "members_down": 0, "has_quorum": true, "down_members": [] },
        { "name": "shard1",  "type": "REPLICA_SET",                "members_total": 3, "members_up": 3, "members_down": 0, "has_quorum": true, "down_members": [] },
        { "name": "configRS","type": "CONFIG_SERVER_REPLICA_SET",  "members_total": 3, "members_up": 3, "members_down": 0, "has_quorum": true, "down_members": [] }
      ]
    }
  ]
}
```

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

**Cluster health** is assessed per replica set, by quorum:

- **Healthy** — every replica set has all members up.
- **Warning** — one or more members down, but every replica set retains majority
  (the cluster is still operational).
- **Degraded** — a replica set has lost majority (quorum), impacting the cluster.

A node counts as *up* when its `replicaStateName` is one of `UP_STATES`
(`PRIMARY`, `SECONDARY`, `ARBITER`) **and** its `lastPing` is newer than
`STALE_PING_SECONDS`. Tune these to match how quickly your Ops Manager surfaces
an outage.

### Known limitation

`mongos` routers report `clusterId: null`, so they can't be attributed to a
specific cluster and are excluded from per-cluster health scoring (they still
count toward the host total). Health scoring is based on mongod replica-set
members.
