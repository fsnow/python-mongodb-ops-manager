#!/usr/bin/env python3
"""
om_check_permissions.py — does this Ops Manager API key have what the health
summary needs?

A deliberately minimal, dependency-light probe: plain `requests` + HTTP Digest
auth, no client library involved. It answers one question — is a failure caused
by TLS, by authentication, or by authorization (role/permissions)? — which are
easy to confuse because they can all surface as "401" or a wall of warnings.

The call that matters is:

    GET /api/public/v1.0/groups/{PROJECT}/automationConfig

om_health_summary.py needs it to read replica-set voting membership
(`replicaSets[].members[].votes`), which is the only source of truth for quorum
("does the cluster remain operational"). The Hosts API does not expose votes.

The other two calls are CONTROLS. They are what make the result conclusive: if
they succeed with the same key, over the same TLS connection, and only the
automation-config call is refused, then the problem is neither certificates nor
connectivity nor credentials — it is the key's role.

------------------------------------------------------------------------------
USAGE
------------------------------------------------------------------------------
    export OM_BASE_URL="https://opsmanager.example.net"
    export OM_PUBLIC_KEY="..."          # digest username
    export OM_PRIVATE_KEY="..."         # digest password
    python om_check_permissions.py --project <PROJECT_ID>

TLS options (prefer trusting the CA properly over disabling verification):
    # use the OS/Windows trust store, where a corporate root CA already lives:
    #   pip install truststore
    python om_check_permissions.py --project <ID> --use-os-truststore

    # or point at a CA bundle (equivalent to REQUESTS_CA_BUNDLE):
    python om_check_permissions.py --project <ID> --ca-bundle /path/ca.pem

    # last resort, to isolate permissions from TLS during triage:
    python om_check_permissions.py --project <ID> --insecure

Exit code 0 = key is sufficient, 1 = key is missing something, 2 = could not tell.
"""

import argparse
import json
import os
import sys

import requests
from requests.auth import HTTPDigestAuth

API = "/api/public/v1.0"

# (label, path template, why the health summary needs it, is_the_call_in_question)
ENDPOINTS = [
    ("clusters",         API + "/groups/{p}/clusters",
     "cluster inventory", False),
    ("hosts",            API + "/groups/{p}/hosts",
     "host inventory + replica state", False),
    ("automationConfig", API + "/groups/{p}/automationConfig",
     "replica-set voting membership (quorum)", True),
]


def probe(session, base_url, path, project, verify):
    """GET one endpoint. Returns (status, error_code, note)."""
    url = base_url.rstrip("/") + path.format(p=project)
    try:
        r = session.get(url, timeout=30, verify=verify)
    except requests.exceptions.SSLError as exc:
        return None, "TLS_ERROR", str(exc)[:120]
    except requests.exceptions.ConnectionError as exc:
        return None, "CONNECTION_ERROR", str(exc)[:120]
    except requests.exceptions.RequestException as exc:
        return None, type(exc).__name__, str(exc)[:120]

    error_code = ""
    if r.status_code >= 400:
        try:
            error_code = (r.json() or {}).get("errorCode", "") or ""
        except (ValueError, json.JSONDecodeError):
            error_code = ""
    return r.status_code, error_code, ""


def main(argv=None):
    ap = argparse.ArgumentParser(description="Check an Ops Manager API key's permissions.")
    ap.add_argument("--project", required=True, help="Ops Manager project (group) ID")
    ap.add_argument("--base-url", default=os.environ.get("OM_BASE_URL"))
    ap.add_argument("--public-key", default=os.environ.get("OM_PUBLIC_KEY"))
    ap.add_argument("--private-key", default=os.environ.get("OM_PRIVATE_KEY"))
    ap.add_argument("--ca-bundle", help="Path to a CA bundle (like REQUESTS_CA_BUNDLE)")
    ap.add_argument("--use-os-truststore", action="store_true",
                    help="Verify using the OS/Windows trust store (needs: pip install truststore)")
    ap.add_argument("--insecure", action="store_true",
                    help="Disable TLS verification (triage only — never in production)")
    args = ap.parse_args(argv)

    missing = [n for n, v in (("OM_BASE_URL", args.base_url),
                              ("OM_PUBLIC_KEY", args.public_key),
                              ("OM_PRIVATE_KEY", args.private_key)) if not v]
    if missing:
        sys.exit(f"Missing: {', '.join(missing)} (set env vars or pass flags)")

    if args.use_os_truststore:
        import truststore
        truststore.inject_into_ssl()

    verify = False if args.insecure else (args.ca_bundle or True)
    if args.insecure:
        requests.packages.urllib3.disable_warnings()  # we already know; keep output readable

    session = requests.Session()
    session.auth = HTTPDigestAuth(args.public_key, args.private_key)

    print("Ops Manager API key permission check")
    print(f"  host    : {args.base_url}")
    print(f"  project : {args.project}")
    print(f"  key     : {args.public_key} (public)")
    tls = ("DISABLED (--insecure)" if args.insecure else
           f"CA bundle {args.ca_bundle}" if args.ca_bundle else
           "OS trust store" if args.use_os_truststore else "default (certifi)")
    print(f"  TLS     : {tls}")
    print("-" * 78)

    results = {}
    for label, path, why, is_target in ENDPOINTS:
        status, code, note = probe(session, args.base_url, path, args.project, verify)
        if status is None:
            verdict = code                      # TLS_ERROR / CONNECTION_ERROR
        elif status < 300:
            verdict = "OK"
        elif code:
            verdict = f"{status} {code}"
        else:
            verdict = str(status)
        marker = "  <== the call in question" if is_target else ""
        print(f"  GET {label:<17} {verdict:<26} {why}{marker}")
        if note:
            print(f"      {note}")
        results[label] = (status, code)

    print("-" * 78)

    statuses = [s for s, _ in results.values()]
    codes = [c for _, c in results.values()]
    inventory_ok = all(results[k][0] is not None and results[k][0] < 300
                       for k in ("clusters", "hosts"))
    auto_status, auto_code = results["automationConfig"]

    if any(c == "TLS_ERROR" for c in codes):
        print("VERDICT: TLS/certificate problem — the CA signing Ops Manager's cert is not")
        print("  trusted. Fix by trusting the CA (--use-os-truststore, or --ca-bundle /")
        print("  REQUESTS_CA_BUNDLE). Note the CA cert is public info; you do NOT need the")
        print("  server's private key or access to the Ops Manager hosts.")
        return 2
    if any(c == "CONNECTION_ERROR" for c in codes):
        print("VERDICT: cannot reach the host — network/DNS/proxy, not permissions.")
        return 2
    if not inventory_ok and all(s == 401 for s in statuses if s is not None):
        print("VERDICT: authentication failed for every call — the key itself is bad or")
        print("  not entitled to this project. Not a certificate issue.")
        return 1

    if inventory_ok and auto_status is not None and auto_status < 300:
        print("VERDICT: key is SUFFICIENT — inventory and automation config all readable.")
        print("  om_health_summary.py will report true voting-based quorum.")
        return 0

    if inventory_ok and auto_code == "USER_UNAUTHORIZED":
        print("VERDICT: PERMISSIONS — and nothing else.")
        print("  TLS handshake succeeded, the key authenticated, and it is authorized for")
        print("  cluster + host inventory over the SAME connection. Only the automation")
        print("  config is refused, with USER_UNAUTHORIZED (authorization, not auth).")
        print()
        print("  => Not a certificate problem. Not connectivity. Not the client library.")
        print("     This key's ROLE lacks automation read access.")
        print()
        print("  Impact: quorum ('does the cluster remain operational') is derived from")
        print("  replicaSets[].members[].votes, which only the automation config exposes.")
        print("  Without it the tool reports UNKNOWN rather than guess a health verdict.")
        return 1

    print(f"VERDICT: inconclusive — automationConfig returned {auto_status} {auto_code}.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
