#!/usr/bin/env python3
"""
om_health_summary.py — Consolidated Ops Manager health summary for Grafana.

Given one or more Ops Manager project IDs, this produces a single JSON document
with the fleet-level metrics a dashboard needs:

    totals:
        db_clusters    - number of top-level deployments (a sharded cluster = 1)
        replica_sets   - number of replica sets (shards + config servers count)
        hosts          - number of monitored processes (mongod + mongos)

    cluster_health:
        healthy        - every replica set fully up
        warning        - some members down, but every replica set keeps quorum
        degraded       - a replica set has lost quorum (majority unreachable)

    clusters[]         - per-cluster drill-down for a Grafana table panel

It is built on the `opsmanager` client library, distributed here as the
single-file bundle `opsmanager_bundle.py`. Drop that file next to this one.

------------------------------------------------------------------------------
USAGE
------------------------------------------------------------------------------
Credentials come from the environment (never hard-code them):

    export OM_BASE_URL="http://ops-manager.example.com:8081"
    export OM_PUBLIC_KEY="..."
    export OM_PRIVATE_KEY="..."

Print the summary as JSON:

    python om_health_summary.py --project 6a2c... --project 6a2c...

Human-readable table:

    python om_health_summary.py --project 6a2c... --pretty

Serve it as an HTTP endpoint for Grafana (stdlib only, no web framework):

    python om_health_summary.py --serve --port 8080 --project 6a2c... --project 6a2c...
    # then GET http://localhost:8080/health   -> the JSON above
    # override projects per-request: GET /health?projects=<id>,<id>

Grafana: point the Infinity (or JSON) data source at /health. Responses are
cached for CACHE_TTL_SECONDS so frequent scrapes don't hammer Ops Manager.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# The consumer is built on the single-file bundle. Keep opsmanager_bundle.py
# in the same directory (or on PYTHONPATH).
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
# Tunable policy — adjust to taste, all counting/health knobs live here.
# =============================================================================

# Replica-set member states that count as "operational and reachable".
UP_STATES = {"PRIMARY", "SECONDARY", "ARBITER"}

# A node whose monitoring ping is older than this is treated as unreachable,
# even if its last-known replica state looked healthy. Set to 0 to rely on
# replica state alone (disable ping-freshness checking).
STALE_PING_SECONDS = 600  # 10 minutes

# Count config-server replica sets toward the "replica_sets" total. They are
# genuine replica sets; set False to count only data-bearing shards / RSes.
COUNT_CONFIG_SERVERS_AS_REPLICA_SETS = True

# Count mongos routers toward the "hosts" total. They are monitored processes
# but carry no data; set False to count only mongod processes.
COUNT_MONGOS_AS_HOSTS = True

# HTTP server response cache (see --serve). Protects Ops Manager from frequent
# Grafana scrapes. Set to 0 to disable caching.
CACHE_TTL_SECONDS = 30

# Cluster typeName values as returned by the Ops Manager /clusters endpoint.
_TYPE_SHARDED = "SHARDED_REPLICA_SET"
_TYPE_REPLICA_SET = "REPLICA_SET"
_TYPE_CONFIG_RS = "CONFIG_SERVER_REPLICA_SET"

# typeName values that represent an actual replica set (not the sharded umbrella).
_REPLICA_SET_TYPES = {_TYPE_REPLICA_SET, _TYPE_CONFIG_RS}


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


def _quorum_size(member_count: int) -> int:
    """Voting majority for a replica set of the given size."""
    return member_count // 2 + 1


# =============================================================================
# Core: build the consolidated summary
# =============================================================================

def _is_mongos(host: Dict[str, Any]) -> bool:
    return "MONGOS" in (host.get("typeName") or "").upper()


def _is_active(host: Dict[str, Any]) -> bool:
    """A host Ops Manager is actively monitoring (not deactivated / disabled)."""
    if host.get("deactivated"):
        return False
    if host.get("hostEnabled") is False:
        return False
    return True


def _summarize_project(
    client: OpsManagerClient,
    project_id: str,
    now: datetime,
) -> Dict[str, Any]:
    """Compute clusters + host inventory for a single project."""
    # Raw dicts: we need fields (parent hierarchy, ids) the dataclass drops,
    # and want to be robust to unknown typeName values.
    clusters = client.clusters.list(project_id=project_id, as_obj=False)
    hosts = client.deployments.list_hosts(project_id=project_id, as_obj=False)

    active_hosts = [h for h in hosts if _is_active(h)]

    # Map cluster_id -> list of member hosts (mongod). mongos have clusterId=None.
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
            members = hosts_by_cluster_id.get(rs.get("id"), [])
            up = [m for m in members if _node_is_up(m, now)]
            down = [m for m in members if m not in up]
            total = len(members)
            has_quorum = len(up) >= _quorum_size(total) if total else True

            nodes_total += total
            nodes_up += len(up)

            # Escalate cluster status: any RS that lost quorum -> DEGRADED;
            # otherwise any down member -> at least WARNING.
            if not has_quorum:
                cluster_status = "DEGRADED"
            elif down and cluster_status == "HEALTHY":
                cluster_status = "WARNING"

            rs_summaries.append({
                "name": rs.get("replicaSetName") or rs.get("shardName") or name,
                "type": rs.get("typeName"),
                "members_total": total,
                "members_up": len(up),
                "members_down": len(down),
                "has_quorum": has_quorum,
                "down_members": [f"{m.get('hostname')}:{m.get('port')}" for m in down],
            })

        cluster_summaries.append({
            "project_id": project_id,
            "name": name,
            "type": _TYPE_SHARDED if is_sharded else _TYPE_REPLICA_SET,
            "status": cluster_status,
            "nodes_total": nodes_total,
            "nodes_up": nodes_up,
            "nodes_down": nodes_total - nodes_up,
            "replica_sets": rs_summaries,
        })

    # Host total (policy-controlled).
    if COUNT_MONGOS_AS_HOSTS:
        host_count = len(active_hosts)
    else:
        host_count = sum(1 for h in active_hosts if not _is_mongos(h))

    # Replica-set total (policy-controlled).
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

    Returns a JSON-serializable dict (see module docstring for the shape).
    """
    now = now or datetime.now(timezone.utc)

    all_clusters: List[Dict[str, Any]] = []
    totals = {"db_clusters": 0, "replica_sets": 0, "hosts": 0}

    for pid in project_ids:
        proj = _summarize_project(client, pid, now)
        all_clusters.extend(proj["clusters"])
        totals["db_clusters"] += proj["db_cluster_count"]
        totals["replica_sets"] += proj["replica_set_count"]
        totals["hosts"] += proj["host_count"]

    health = {"healthy": 0, "warning": 0, "degraded": 0}
    for c in all_clusters:
        health[c["status"].lower()] += 1

    return {
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "project_ids": list(project_ids),
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
            "No projects given. Use --project <id> (repeatable) "
            "or set OM_PROJECT_IDS=<id>,<id>."
        )
    return ids


# =============================================================================
# Pretty printer (for --pretty / CLI humans)
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
          f"{h['degraded']} degraded")
    print("-" * 60)
    for c in summary["clusters"]:
        print(f"  [{c['status']:>8}] {c['name']}  ({c['type']}, "
              f"{c['nodes_up']}/{c['nodes_total']} nodes up)")
        for rs in c["replica_sets"]:
            flag = "" if rs["has_quorum"] else "  !! NO QUORUM"
            down = f"  down: {', '.join(rs['down_members'])}" if rs["down_members"] else ""
            print(f"        - {rs['name']} ({rs['type']}): "
                  f"{rs['members_up']}/{rs['members_total']} up{down}{flag}")


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
            except Exception as exc:  # surface errors as JSON, keep server up
                body = json.dumps({"error": str(exc)}).encode()
                self.send_response(502)
            else:
                self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):  # quiet default logging
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
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument(
        "--project", action="append", default=[], metavar="PROJECT_ID",
        help="Ops Manager project ID (repeatable). "
             "Defaults to OM_PROJECT_IDS env var.",
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
