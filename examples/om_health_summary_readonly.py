#!/usr/bin/env python3
"""
om_health_summary_readonly.py — consolidated Ops Manager health summary for
Grafana, using ONLY read-only permissions.

Same output as om_health_summary.py, but it never calls the automation config,
so it works with an ordinary read-only API key (Project Read Only / Org Read
Only). Use this version unless the dashboard key has GROUP_AUTOMATION_ADMIN.

    totals:
        db_clusters    - number of top-level deployments (a sharded cluster = 1)
        replica_sets   - number of replica sets (shards + config servers count)
        hosts          - number of monitored processes (mongod + mongos)

    cluster_health:
        healthy        - replica set has a PRIMARY and all members are up
        warning        - replica set has a PRIMARY (still operational) but a
                         member is down
        degraded       - replica set has NO PRIMARY: quorum lost, not operational
        unknown        - a replica set has no monitored members (cannot assess)

    projects[]         - {id, name} for each project queried
    clusters[]         - per-cluster drill-down for a Grafana table panel, each
                         carrying project_id / project_name and the cluster
                         `name`, so panels can label rows without a second lookup

------------------------------------------------------------------------------
HOW OPERABILITY IS DETERMINED (and why this needs no extra permission)
------------------------------------------------------------------------------
"Does the cluster remain operational" is equivalent to "does the replica set
have quorum". Rather than *infer* quorum by counting votes — which requires the
automation config, and therefore an automation-admin-grade key — this version
*observes* it directly:

    A replica set has an elected PRIMARY if and only if it has quorum.

MongoDB guarantees this: a primary that cannot reach a majority of voting
members steps down within electionTimeoutMillis (~10s). So the presence of a
PRIMARY is a direct measurement of operability, and `replicaStateName` is
already in the Hosts API, which any read-only key can read.

This is also immune to non-voting members. Hidden non-voting secondaries — for
example nodes added ahead of a data-center migration — cannot affect whether a
primary exists, so they can never skew the operability verdict. (Counting all
members toward a majority *would* skew it; that is precisely the bug this
approach sidesteps.)

Trade-off: during a brief election (~10s) there is genuinely no primary, so a
scrape landing in that window reports DEGRADED. That is accurate at that instant
— no writes are possible — but it can look like a blip on a dashboard.

------------------------------------------------------------------------------
USAGE  (identical to om_health_summary.py)
------------------------------------------------------------------------------
    export OM_BASE_URL="https://ops-manager.example.com:8081"
    export OM_PUBLIC_KEY="..."
    export OM_PRIVATE_KEY="..."

    # --project accepts a project ID *or* a project name
    python om_health_summary_readonly.py --project <ID-or-NAME> --project <ID-or-NAME>
    python om_health_summary_readonly.py --project "My Project" --pretty
    python om_health_summary_readonly.py --serve --port 8080 --project <ID-or-NAME>
        # GET /health  ->  the JSON summary

Verify a key first with:  python om_check_permissions.py --project <ID>
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

try:
    from opsmanager_bundle import OpsManagerClient
except ImportError:  # pragma: no cover
    sys.stderr.write(
        "ERROR: could not import 'opsmanager_bundle'. "
        "Place opsmanager_bundle.py next to this script "
        "(build it with: python scripts/build_bundle.py).\n"
    )
    raise

# =============================================================================
# Tunable policy
# =============================================================================

# Replica-set member states that count as "operational and reachable".
UP_STATES = {"PRIMARY", "SECONDARY", "ARBITER"}

# A node whose monitoring ping is older than this is treated as unreachable,
# even if its last-known replica state looked healthy. Set to 0 to rely on
# replica state alone.
STALE_PING_SECONDS = 600  # 10 minutes

# Count config-server replica sets toward the "replica_sets" total.
COUNT_CONFIG_SERVERS_AS_REPLICA_SETS = True

# Count mongos routers toward the "hosts" total.
COUNT_MONGOS_AS_HOSTS = True

# Hidden members are frequently non-voting extras (analytics nodes, or nodes
# added ahead of a data-center migration that are still doing initial sync).
# Set True to stop a down *hidden* member from raising a cluster to WARNING.
#
# This is a heuristic — `hidden` does not strictly imply non-voting — but it is
# a SAFE one here: it only ever affects HEALTHY vs WARNING. It can never change
# the DEGRADED verdict, because that is decided solely by whether a PRIMARY
# exists. A wrong guess therefore cannot misreport whether the cluster is
# operational.
IGNORE_HIDDEN_MEMBERS_FOR_WARNING = False

# HTTP server response cache (see --serve).
CACHE_TTL_SECONDS = 30

_TYPE_SHARDED = "SHARDED_REPLICA_SET"
_TYPE_REPLICA_SET = "REPLICA_SET"
_TYPE_CONFIG_RS = "CONFIG_SERVER_REPLICA_SET"
_REPLICA_SET_TYPES = {_TYPE_REPLICA_SET, _TYPE_CONFIG_RS}

_STATUS_RANK = {"HEALTHY": 0, "WARNING": 1, "UNKNOWN": 2, "DEGRADED": 3}


def _escalate(current: str, new: str) -> str:
    """Return the more severe status (DEGRADED > UNKNOWN > WARNING > HEALTHY)."""
    return new if _STATUS_RANK[new] > _STATUS_RANK[current] else current


# =============================================================================
# Health primitives
# =============================================================================

def _parse_om_timestamp(value: Optional[str]) -> Optional[datetime]:
    """Parse an Ops Manager ISO-8601 timestamp (e.g. '2026-07-14T18:33:18Z')."""
    if not value:
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        try:
            dt = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=timezone.utc
            )
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _node_is_up(host: Dict[str, Any], now: datetime) -> bool:
    """Return True if a mongod host is operational and reachable."""
    if host.get("replicaStateName") not in UP_STATES:
        return False
    if STALE_PING_SECONDS > 0:
        last_ping = _parse_om_timestamp(host.get("lastPing"))
        if last_ping is None:
            return False
        if (now - last_ping).total_seconds() > STALE_PING_SECONDS:
            return False
    return True


def _is_mongos(host: Dict[str, Any]) -> bool:
    return "MONGOS" in (host.get("typeName") or "").upper()


def _is_active(host: Dict[str, Any]) -> bool:
    """A host Ops Manager is actively monitoring (not deactivated / disabled)."""
    if host.get("deactivated"):
        return False
    if host.get("hostEnabled") is False:
        return False
    return True


def _is_hidden(host: Dict[str, Any]) -> bool:
    return bool(host.get("hidden") or host.get("hiddenSecondary"))


def _host_port(host: Dict[str, Any]) -> str:
    return f"{host.get('hostname')}:{host.get('port')}"


def _assess_replica_set(
    rs_name: str,
    rs_type: str,
    members: List[Dict[str, Any]],
    now: datetime,
) -> Dict[str, Any]:
    """Assess one replica set's operability by PRIMARY presence.

    Returns the per-RS summary; the private "_status" key is popped by the
    caller to escalate the parent cluster's status.
    """
    up = [m for m in members if _node_is_up(m, now)]
    down = [m for m in members if m not in up]

    # A PRIMARY exists iff the replica set holds quorum. Require it to be
    # reachable too, so a stale "PRIMARY" reading can't imply operability.
    primaries = [
        m for m in members
        if m.get("replicaStateName") == "PRIMARY" and _node_is_up(m, now)
    ]
    has_primary = bool(primaries)

    if not members:
        status = "UNKNOWN"                       # nothing monitored; cannot assess
    elif not has_primary:
        status = "DEGRADED"                      # no primary => quorum lost
    else:
        blocking = down
        if IGNORE_HIDDEN_MEMBERS_FOR_WARNING:
            blocking = [m for m in down if not _is_hidden(m)]
        status = "WARNING" if blocking else "HEALTHY"

    return {
        "name": rs_name,
        "type": rs_type,
        "members_total": len(members),
        "members_up": len(up),
        "members_down": len(down),
        "has_primary": has_primary,
        "primary": _host_port(primaries[0]) if primaries else None,
        "down_members": [_host_port(m) for m in down],
        "_status": status,
    }


# =============================================================================
# Core: build the consolidated summary
# =============================================================================

_OBJECT_ID_RE = re.compile(r"^[0-9a-f]{24}$", re.IGNORECASE)


def _resolve_project(client: OpsManagerClient, reference: str) -> Tuple[str, str]:
    """Resolve a project reference to (id, name).

    Accepts EITHER a 24-character project ID or a project name, so callers can
    use whichever they have to hand. Passing a name where Ops Manager wants an
    ID otherwise fails with a confusing "INVALID_GROUP_ID" error.
    """
    ref = reference.strip()
    try:
        if _OBJECT_ID_RE.match(ref):
            project = client.projects.get(project_id=ref)
        else:
            project = client.projects.get_by_name(project_name=ref)
    except Exception as exc:  # noqa: BLE001 — re-raise with actionable guidance
        raise RuntimeError(
            f"Could not resolve project {ref!r}: {exc}. Pass either the "
            "24-character project ID or the exact project name."
        ) from exc
    return project.id, project.name


def _summarize_project(
    client: OpsManagerClient,
    project_id: str,
    project_name: str,
    now: datetime,
) -> Dict[str, Any]:
    """Compute clusters + host inventory for a single project (read-only calls)."""
    clusters = client.clusters.list(project_id=project_id, as_obj=False)
    hosts = client.deployments.list_hosts(project_id=project_id, as_obj=False)

    active_hosts = [h for h in hosts if _is_active(h)]

    # Map cluster_id -> member hosts (mongod). mongos have clusterId=None.
    hosts_by_cluster_id: Dict[str, List[Dict[str, Any]]] = {}
    for h in active_hosts:
        cid = h.get("clusterId")
        if cid and not _is_mongos(h):
            hosts_by_cluster_id.setdefault(cid, []).append(h)

    # Group cluster entries by clusterName. Each group is one "DB cluster".
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for c in clusters:
        groups.setdefault(c.get("clusterName", ""), []).append(c)

    cluster_summaries: List[Dict[str, Any]] = []
    for name, entries in groups.items():
        is_sharded = any(e.get("typeName") == _TYPE_SHARDED for e in entries)
        rs_entries = [e for e in entries if e.get("typeName") in _REPLICA_SET_TYPES]

        rs_summaries: List[Dict[str, Any]] = []
        cluster_status = "HEALTHY"
        nodes_total = nodes_up = 0

        for rs in rs_entries:
            rs_name = rs.get("replicaSetName") or rs.get("shardName") or name
            members = hosts_by_cluster_id.get(rs.get("id"), [])

            rs_summary = _assess_replica_set(rs_name, rs.get("typeName"), members, now)
            nodes_total += rs_summary["members_total"]
            nodes_up += rs_summary["members_up"]
            cluster_status = _escalate(cluster_status, rs_summary.pop("_status"))
            rs_summaries.append(rs_summary)

        cluster_summaries.append({
            "project_id": project_id,
            "project_name": project_name,
            "name": name,
            "type": _TYPE_SHARDED if is_sharded else _TYPE_REPLICA_SET,
            "status": cluster_status,
            "nodes_total": nodes_total,
            "nodes_up": nodes_up,
            "nodes_down": nodes_total - nodes_up,
            "replica_sets": rs_summaries,
        })

    if COUNT_MONGOS_AS_HOSTS:
        host_count = len(active_hosts)
    else:
        host_count = sum(1 for h in active_hosts if not _is_mongos(h))

    rs_total = 0
    for c in clusters:
        t = c.get("typeName")
        if t == _TYPE_REPLICA_SET:
            rs_total += 1
        elif t == _TYPE_CONFIG_RS and COUNT_CONFIG_SERVERS_AS_REPLICA_SETS:
            rs_total += 1

    return {
        "clusters": cluster_summaries,
        "db_cluster_count": len(groups),
        "replica_set_count": rs_total,
        "host_count": host_count,
    }


def health_summary(
    client: OpsManagerClient,
    project_ids: List[str],
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Build the consolidated health summary across the given projects.

    Each entry in `project_ids` may be a project ID *or* a project name.
    Returns a JSON-serializable dict (see module docstring for the shape).
    Uses only read-only endpoints.
    """
    now = now or datetime.now(timezone.utc)

    all_clusters: List[Dict[str, Any]] = []
    projects: List[Dict[str, Any]] = []
    resolved_ids: List[str] = []
    totals = {"db_clusters": 0, "replica_sets": 0, "hosts": 0}

    for reference in project_ids:
        pid, pname = _resolve_project(client, reference)
        proj = _summarize_project(client, pid, pname, now)
        all_clusters.extend(proj["clusters"])
        projects.append({"id": pid, "name": pname})
        resolved_ids.append(pid)
        totals["db_clusters"] += proj["db_cluster_count"]
        totals["replica_sets"] += proj["replica_set_count"]
        totals["hosts"] += proj["host_count"]

    health = {"healthy": 0, "warning": 0, "degraded": 0, "unknown": 0}
    for c in all_clusters:
        health[c["status"].lower()] += 1

    return {
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "project_ids": resolved_ids,          # always IDs, even if names were given
        "projects": projects,
        "totals": totals,
        "cluster_health": health,
        "clusters": all_clusters,
    }


# =============================================================================
# Client construction
# =============================================================================

def client_from_env() -> OpsManagerClient:
    """Build an OpsManagerClient from OM_BASE_URL / OM_PUBLIC_KEY / OM_PRIVATE_KEY."""
    missing = [
        v for v in ("OM_BASE_URL", "OM_PUBLIC_KEY", "OM_PRIVATE_KEY")
        if not os.environ.get(v)
    ]
    if missing:
        raise SystemExit(f"Missing required environment variables: {', '.join(missing)}")
    return OpsManagerClient(
        base_url=os.environ["OM_BASE_URL"],
        public_key=os.environ["OM_PUBLIC_KEY"],
        private_key=os.environ["OM_PRIVATE_KEY"],
    )


def _projects_from_args(cli_projects: List[str]) -> List[str]:
    """Resolve project IDs from --project flags or the OM_PROJECT_IDS env var."""
    if cli_projects:
        return cli_projects
    env = os.environ.get("OM_PROJECT_IDS", "")
    ids = [p.strip() for p in env.split(",") if p.strip()]
    if not ids:
        raise SystemExit(
            "No projects given. Use --project <id-or-name> (repeatable) "
            "or set OM_PROJECT_IDS=<id-or-name>,<id-or-name>."
        )
    return ids


# =============================================================================
# Pretty printer
# =============================================================================

def _print_pretty(summary: Dict[str, Any]) -> None:
    t = summary["totals"]
    h = summary["cluster_health"]
    print(f"Ops Manager health summary  ({summary['generated_at']})")
    print("-" * 60)
    print(f"  DB clusters : {t['db_clusters']}")
    print(f"  Replica sets: {t['replica_sets']}")
    print(f"  Hosts       : {t['hosts']}")
    print(f"  Health      : {h['healthy']} healthy / {h['warning']} warning / "
          f"{h['degraded']} degraded / {h['unknown']} unknown")
    print("-" * 60)
    for c in summary["clusters"]:
        print(f"  [{c['status']:>8}] {c['project_name']} / {c['name']}  ({c['type']}, "
              f"{c['nodes_up']}/{c['nodes_total']} nodes up)")
        for rs in c["replica_sets"]:
            if rs["has_primary"]:
                prim = f"primary {rs['primary']}"
            else:
                prim = "NO PRIMARY — quorum lost"
            down = f"  down: {', '.join(rs['down_members'])}" if rs["down_members"] else ""
            print(f"        - {rs['name']} ({rs['type']}): "
                  f"{rs['members_up']}/{rs['members_total']} up, {prim}{down}")


# =============================================================================
# Optional HTTP server for Grafana (stdlib only)
# =============================================================================

def serve(project_ids: List[str], port: int) -> None:
    """Run a tiny HTTP server exposing GET /health for Grafana."""
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from urllib.parse import urlparse, parse_qs
    import threading

    client = client_from_env()
    cache: Dict[str, Any] = {"at": None, "body": None, "key": None}
    lock = threading.Lock()

    def get_summary(pids: List[str]) -> bytes:
        key = ",".join(pids)
        now = datetime.now(timezone.utc)
        with lock:
            fresh = (
                cache["body"] is not None
                and cache["key"] == key
                and cache["at"] is not None
                and (now - cache["at"]).total_seconds() < CACHE_TTL_SECONDS
            )
            if fresh:
                return cache["body"]
            body = json.dumps(health_summary(client, pids, now=now)).encode()
            cache.update(at=now, body=body, key=key)
            return body

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path != "/health":
                self.send_error(404, "Not found (try /health)")
                return
            q = parse_qs(parsed.query).get("projects", [])
            pids = [p for chunk in q for p in chunk.split(",") if p] or project_ids
            try:
                body = get_summary(pids)
            except Exception as exc:
                body = json.dumps({"error": str(exc)}).encode()
                self.send_response(502)
            else:
                self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("", port), Handler)
    print(f"Serving Ops Manager health summary on http://0.0.0.0:{port}/health")
    print(f"  default projects: {', '.join(project_ids) or '(none — pass ?projects=)'}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
        client.close()


# =============================================================================
# CLI
# =============================================================================

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Ops Manager health summary using read-only permissions."
    )
    parser.add_argument(
        "--project", action="append", default=[], metavar="PROJECT",
        help="Ops Manager project ID or project name (repeatable). "
             "Defaults to OM_PROJECT_IDS.",
    )
    parser.add_argument("--pretty", action="store_true",
                        help="Human-readable table instead of JSON.")
    parser.add_argument("--serve", action="store_true",
                        help="Run an HTTP endpoint (GET /health) for Grafana.")
    parser.add_argument("--port", type=int, default=8080,
                        help="Port for --serve (default 8080).")
    args = parser.parse_args(argv)

    project_ids = _projects_from_args(args.project)

    if args.serve:
        serve(project_ids, args.port)
        return 0

    client = client_from_env()
    try:
        summary = health_summary(client, project_ids)
    finally:
        client.close()

    if args.pretty:
        _print_pretty(summary)
    else:
        print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
