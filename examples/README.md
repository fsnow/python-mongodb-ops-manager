# Examples

Standalone consumers built on top of the `opsmanager` library. Each is meant to
be copied out and run on its own, so they depend on the single-file bundle
(`opsmanager_bundle.py`) rather than a `pip install`.

| Script | Purpose | Permissions needed |
|--------|---------|--------------------|
| **`om_health_summary_readonly.py`** | Health summary for Grafana — **start here** | read-only (Project/Org Read Only) |
| `om_health_summary.py` | Same, but derives quorum from vote configuration | **automation read** (`GROUP_AUTOMATION_ADMIN`) |
| `om_check_permissions.py` | Does a given API key have what the summary needs? | any key (it's a probe) |

## Which health summary should I use?

Both emit the same JSON. They differ only in how they decide whether a cluster
**remains operational** (the `warning` vs `degraded` line):

- **`om_health_summary_readonly.py` — recommended.** Observes operability
  directly: *a replica set has an elected PRIMARY if and only if it has quorum.*
  `replicaStateName` is in the Hosts API, so this needs **no special
  permissions**. It is also immune to non-voting members — hidden non-voting
  secondaries cannot affect whether a primary exists.
- **`om_health_summary.py`** — infers quorum by counting **voting** members
  (`votes >= 1`) from the automation config. Equally correct, but the automation
  config is readable only by `GROUP_AUTOMATION_ADMIN` or `GROUP_OWNER` — roles
  that can also **rewrite** the automation config (i.e. reconfigure or destroy
  clusters). Ops Manager has no read-only automation role. Granting that to a
  dashboard key is usually not acceptable; prefer the read-only version.

Use `om_check_permissions.py` to find out which one a given key can run.

## om_health_summary.py — consolidated health summary for Grafana

Given one or more Ops Manager project IDs, produces a single JSON document with
the fleet-level metrics a dashboard needs:

- **totals** — `db_clusters`, `replica_sets`, `hosts`
- **cluster_health** — counts of `healthy` / `warning` / `degraded` clusters
- **projects[]** — `{id, name}` for each project queried
- **clusters[]** — per-cluster drill-down for a table panel, each carrying
  `project_id` / `project_name` and the cluster `name`

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

`--project` accepts a **project name or a project ID**, so you can use whichever
you have to hand:

```bash
python om_health_summary.py --project "My Project" --project 5f1a...c3
```

Names are resolved via `GET /groups/byName/{name}` (readable by a read-only key);
IDs are detected by their 24-hex-character form. `project_ids` in the output is
always resolved to real IDs. Passing a name where Ops Manager wants an ID would
otherwise fail with a confusing `INVALID_GROUP_ID`.

Projects can also be supplied via `OM_PROJECT_IDS=<id-or-name>,<id-or-name>`
instead of `--project`.

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
  "projects": [
    { "id": "<rs-project>", "name": "Example Project" },
    { "id": "<sharded-project>", "name": "Example Sharded Project" }
  ],
  "totals": { "db_clusters": 2, "replica_sets": 4, "hosts": 18 },
  "cluster_health": { "healthy": 2, "warning": 0, "degraded": 0, "unknown": 0 },
  "clusters": [
    {
      "project_id": "<rs-project>",
      "project_name": "Example Project",
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
      "project_name": "Example Sharded Project",
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

---

## om_health_summary_readonly.py — same summary, read-only permissions

Identical output and CLI to `om_health_summary.py` (`--pretty`, `--serve`,
`health_summary()` for programmatic use), but it never calls the automation
config, so an ordinary read-only key works.

### How operability is determined

> A replica set has an elected **PRIMARY if and only if it has quorum.**

MongoDB guarantees this: a primary that cannot reach a majority of voting
members steps down within `electionTimeoutMillis` (~10s). So rather than
*infer* quorum by counting votes (which needs the automation config), this
version *observes* it via `replicaStateName` from the Hosts API:

| Status | Rule |
|--------|------|
| **Healthy** | replica set has a PRIMARY and all members are up |
| **Warning** | replica set has a PRIMARY (still operational) but a member is down |
| **Degraded** | replica set has **no PRIMARY** — quorum lost, not operational |
| **Unknown** | replica set has no monitored members (cannot assess) |

A PRIMARY is only trusted if it is itself reachable (`lastPing` fresh), so a
stale reading can't imply operability. Per-RS output carries `has_primary` and
`primary` (the `hostname:port`) instead of `has_quorum` / `voting_*`.

**Immune to non-voting members.** Hidden non-voting secondaries — e.g. nodes
added ahead of a data-center migration — cannot affect whether a primary exists.
A replica set with 3 voters (2 down) plus 2 healthy hidden members reports
`DEGRADED` even though 3 of 5 members are up, with no vote data required.

**Trade-off.** During a brief election (~10s) there is genuinely no primary, so
a scrape landing in that window reports `DEGRADED`. That is accurate at that
instant (no writes are possible) but can look like a blip on a dashboard.

**Migration noise.** Without vote data, a down *hidden* member can't be
distinguished from a down voter, so a hidden node doing initial sync reports
`WARNING`. Set `IGNORE_HIDDEN_MEMBERS_FOR_WARNING = True` to suppress that. This
is a heuristic (`hidden` does not strictly imply non-voting) but a safe one: it
only ever affects `HEALTHY` vs `WARNING` and can **never** change the `DEGRADED`
verdict, which depends solely on PRIMARY presence.

---

## om_check_permissions.py — what can this API key actually do?

A minimal probe (plain `requests` + digest auth, no client library) that
separates the three failure modes that all look alike: **TLS/CA trust**,
**authentication**, and **authorization**.

```bash
export OM_BASE_URL="https://ops-manager.example.com"
export OM_PUBLIC_KEY="..." ; export OM_PRIVATE_KEY="..."
python om_check_permissions.py --project <PROJECT_ID>

# TLS options — prefer trusting the CA over disabling verification:
python om_check_permissions.py --project <ID> --use-os-truststore  # pip install truststore
python om_check_permissions.py --project <ID> --ca-bundle /path/ca.pem
python om_check_permissions.py --project <ID> --insecure           # triage only
```

It checks `clusters` and `hosts` (which the summary needs, and which act as
controls) plus `automationConfig` (the call that requires elevated permission).
If the controls succeed over the same connection and only `automationConfig` is
refused with `USER_UNAUTHORIZED`, the cause is the key's role — not
certificates, connectivity, or the library.

Exit codes: `0` key is sufficient for either version, `1` key can't read the
automation config (use `om_health_summary_readonly.py`), `2` inconclusive
(TLS/network).

### Role matrix (verified against Ops Manager)

| Role | clusters / hosts | automationConfig |
|------|------------------|------------------|
| `ORG_READ_ONLY` | OK | DENIED |
| `GROUP_READ_ONLY` | OK | DENIED |
| `GROUP_DATA_ACCESS_READ_ONLY` | OK | DENIED |
| `GROUP_READ_ONLY` + `GROUP_BACKUP_ADMIN` | OK | DENIED |
| `GROUP_MONITORING_ADMIN` | OK | DENIED |
| `GROUP_AUTOMATION_ADMIN` | OK | **ALLOWED** (least privilege) |
| `GROUP_OWNER` | OK | ALLOWED (broader) |

Every role that can *read* the automation config can also *write* it — there is
no read-only automation role. That is the reason `om_health_summary_readonly.py`
exists and is the default recommendation.

### TLS note

A corporate CA certificate is **public** information — you do not need the Ops
Manager server's private key or access to its hosts to verify its certificate.
On a domain-joined Windows machine the corporate root is usually already in the
Windows trust store; Python just doesn't look there by default. `pip install
truststore` and `truststore.inject_into_ssl()` fixes it with no PEM file.
Otherwise export the CA chain and point `REQUESTS_CA_BUNDLE` at it. Don't
disable verification.
