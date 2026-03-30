# Code Review 2 — python-mongodb-ops-manager

**Date**: 2026-03-28
**Reviewer**: Code review pass on full codebase post-implementation
**Version reviewed**: 0.3.1
**Scope**: Complete codebase including all 26 services, types, network layer, pagination, auth, tests

---

## Executive Summary

This is a well-designed, production-quality Python client library with strong architectural bones — consistent service patterns, good documentation, a real network layer, and meaningful test coverage of the critical infrastructure (network, pagination, rate limiting). The core abstractions are sound.

This review found **no critical security vulnerabilities** and **no data-loss bugs**. The issues identified fall into: pagination correctness gaps in a handful of services, dead code, type annotation inaccuracies, minor API inconsistencies, and test coverage gaps for service classes. All are fixable.

---

## 1. Architecture & Design

### Strengths

- **BaseService mixin** cleanly centralises all HTTP plumbing. Every service inherits `_get`, `_post`, `_put`, `_patch`, `_delete`, `_paginate`, `_fetch_all`, `_download`. Zero duplication across 26 service files.
- **NetworkSession** correctly separates concerns: rate limiting, retry, logging, error mapping.
- **RateLimiter** is thread-safe (Lock), supports both strict-spacing and token-bucket modes, and is tested.
- **PageIterator[T]** is lazy, generic, and correct. The "full last page fetches an extra empty page" behaviour is tested and documented.
- **Exception hierarchy** is clean: all errors inherit from `OpsManagerError`, specific subclasses map 1:1 to HTTP status codes, and `raise_for_status()` is a single dispatch function.
- **as_obj parameter** is consistent across all services, giving callers a choice between typed dataclasses and raw dicts.
- **Compliance context** in docstrings (SOX, PCI-DSS, banking regulators) is domain-appropriate and valuable.

### Design Decisions That Are Fine

- Project ID passed per-call (not stored) — matches Go SDK, explicit.
- Deferred `from opsmanager import __version__` inside `NetworkSession.__init__` to avoid circular import — works, but see note below.
- Automation config returned as raw dict — correct choice given its complex, version-dependent schema.

---

## 2. Bugs

### BUG-1: `alert_configurations.py` — `get_open_alerts()` wrong fallback

**File**: `opsmanager/services/alert_configurations.py`, line 128
**Severity**: Medium

```python
results = response.get("results", [response]) if isinstance(response, dict) else [response]
```

When `response` is a dict but has no `"results"` key, this wraps the entire response dict in a list and tries to call `Alert.from_dict(response_dict)` — which will produce an `Alert` object with every field empty/default, silently discarding the real response content. The fallback should be an empty list:

```python
results = response.get("results", [])
```

### BUG-2: `Checkpoint.from_dict()` — wrong field name

**File**: `opsmanager/types.py`, line 974
**Severity**: Low

```python
replica_set_checkpoints=data.get("parts", []),
```

The field is named `replica_set_checkpoints` but is populated from `"parts"` in the API response. The Go SDK calls this field `parts` in the response, while the checkpoint's replica set sub-documents are in `parts`. If the actual API key is `replicaSetCheckpoints` (as the field name implies), this silently returns empty. Verify against the actual API response shape.

### BUG-3: `PerformanceAdvisorOptions.to_params()` — wrong casing for `nExamples`

**File**: `opsmanager/services/performance_advisor.py`, line 66
**Severity**: Low (only affects `PerformanceAdvisorOptions` users, not the service methods)

```python
params["NExamples"] = self.n_examples
```

All other params use lowercase-first camelCase (`nLogs`, `nIndexes`). This should be `"nExamples"`. The API will likely ignore the incorrectly-cased parameter, silently returning the default number of examples.

### BUG-4: `DaemonConfig.from_dict()` — fragile `machine` field parsing

**File**: `opsmanager/types.py`, lines 1393–1411
**Severity**: Low

```python
machine_data = data.get("machine", {})
...
machine=machine_data.get("machine", "") if isinstance(machine_data, dict) else str(machine_data),
head_root_directory=machine_data.get("headRootDirectory", "") if isinstance(machine_data, dict) else "",
```

This does `machine_data.get("machine", "")` — so it's accessing `data["machine"]["machine"]`, a nested key with the same name as its parent. If the API structure is `{"machine": {"machine": "hostname", "headRootDirectory": "/data"}}`, this is correct but extremely unusual. If `data["machine"]` is a plain string (the machine hostname), this silently sets `machine = ""`. The defensive `isinstance` check suggests uncertainty about the actual API shape. Should be verified against live API response.

---

## 3. Pagination Correctness Gaps

Several services bypass `_fetch_all`/`_paginate` and use a direct `_get` + manual `results` extraction. This means only the first page (up to `itemsPerPage`, default 100) is ever returned. For deployments with more than 100 entries, results are silently truncated.

### PAG-1: `maintenance_windows.py` — `list()` not paginated

**File**: `opsmanager/services/maintenance_windows.py`, line 54

```python
response = self._get(f"groups/{project_id}/maintenanceWindows")
results = response.get("results", [])
```

Maintenance windows are rarely >100, but this should use `_fetch_all` for consistency and correctness.

### PAG-2: `server_usage.py` — three methods not paginated

**File**: `opsmanager/services/server_usage.py`, lines 60–118

`list_all_host_assignments()`, `get_project_host_assignments()`, and `get_organization_host_assignments()` all do:

```python
response = self._get("usage/assignments", params=params or None)
results = response.get("results", [])
```

For large fleets this silently truncates. These should use `_fetch_all` with the result type.

### PAG-3: `teams.py` — `list_users()` not paginated

**File**: `opsmanager/services/teams.py`, line 137

```python
response = self._get(f"orgs/{org_id}/teams/{team_id}/users")
results = response.get("results", [])
```

Teams with >100 users will silently truncate.

### PAG-4: `alert_configurations.py` — `get_open_alerts()` not paginated

**File**: `opsmanager/services/alert_configurations.py`, line 125

This endpoint could return many alert instances. Should use `_fetch_all` instead of direct `_get`.

---

## 4. Type Annotation Issues

### TYPE-1: `as_obj=False` return types are incorrect

**Files**: All service files
**Severity**: Medium

```python
def get(self, org_id: str, as_obj: bool = True) -> Organization:
    response = self._get(f"orgs/{org_id}")
    return Organization.from_dict(response) if as_obj else response
```

When `as_obj=False`, the function returns `Dict[str, Any]` but the annotation says `Organization`. This misleads callers and static type checkers. The correct annotation would use an overload:

```python
@overload
def get(self, org_id: str, as_obj: Literal[True] = ...) -> Organization: ...
@overload
def get(self, org_id: str, as_obj: Literal[False]) -> Dict[str, Any]: ...
```

This affects every `get()`, `list()`, and `list_iter()` method across all 26 services. It's a pervasive type annotation inaccuracy — callers who use `as_obj=False` get a dict but mypy thinks they got a typed object.

### TYPE-2: `__exit__` signature is non-standard

**Files**: `opsmanager/network.py:539`, `opsmanager/client.py:358`

```python
def __exit__(self, *args) -> None:
```

Should be:

```python
def __exit__(self, exc_type: Optional[type], exc_val: Optional[BaseException], exc_tb: Optional[object]) -> None:
```

The `*args` form works at runtime but fails mypy's strict mode and is non-idiomatic.

### TYPE-3: `ProcessType` enum names/values mismatch

**File**: `opsmanager/types.py`, lines 39–46

```python
class ProcessType(str, Enum):
    REPLICA_SET_PRIMARY = "REPLICA_PRIMARY"    # name: REPLICA_SET_PRIMARY, value: REPLICA_PRIMARY
    REPLICA_SET_SECONDARY = "REPLICA_SECONDARY"
    REPLICA_SET_ARBITER = "REPLICA_ARBITER"
```

The names include `_SET_` but the values don't. If someone writes `ProcessType.REPLICA_SET_PRIMARY.value` they get `"REPLICA_PRIMARY"`. This inconsistency will confuse users. Either rename the enum members to match the values (e.g. `REPLICA_PRIMARY = "REPLICA_PRIMARY"`) or document the discrepancy clearly.

### TYPE-4: `Cluster.from_dict()` enum membership check is non-idiomatic

**File**: `opsmanager/types.py`, line 138

```python
type_name=ClusterType(type_name) if type_name in ClusterType.__members__.values() else ClusterType.REPLICA_SET,
```

`ClusterType.__members__` maps names to members, so `.values()` gives members (not strings). This works because `ClusterType` inherits from `str`, but it's fragile. The idiomatic pattern is:

```python
try:
    type_name=ClusterType(type_name)
except ValueError:
    type_name=ClusterType.REPLICA_SET
```

---

## 5. Dead Code

### DEAD-1: `AdminBackupConfig` is unused

**File**: `opsmanager/types.py`, lines 1200–1227

`AdminBackupConfig` is defined but never imported or used by any service. `AdminBackupStoresService` imports `BackupStore`, `S3BlockstoreConfig`, `FileSystemStoreConfig`, `DaemonConfig`, `ProjectJobConfig` — but not `AdminBackupConfig`. Can be removed.

### DEAD-2: `PaginatedResult` is unused

**File**: `opsmanager/types.py`, lines 1485–1519

`PaginatedResult` with `has_next()` and `get_next_link()` is a complete implementation but is never used. All pagination goes through `PageIterator`. Can be removed, or its `has_next()`/`get_next_link()` logic could inform a future enhancement to `PageIterator`.

### DEAD-3: `ListOptions` is unused

**File**: `opsmanager/pagination.py`, lines 28–44

`ListOptions` dataclass with `to_params()` is defined but no service uses it. `BaseService._paginate()` builds params inline. Can be removed or documented as a public helper for callers who want to build params manually.

### DEAD-4: `PerformanceAdvisorOptions` is unused internally

**File**: `opsmanager/services/performance_advisor.py`, lines 32–67

`PerformanceAdvisorOptions` is a dataclass with a `to_params()` method, but none of the service methods (`get_namespaces`, `get_slow_queries`, `get_suggested_indexes`, `get_query_shapes`) actually accept or use it — they all take individual keyword arguments. The class is public API but the service methods bypass it entirely. Either wire it up so methods accept `options: Optional[PerformanceAdvisorOptions] = None` or remove it.

### DEAD-5: Unused import in `organizations.py`

**File**: `opsmanager/services/organizations.py`, line 21

```python
from typing import Any, Dict, Iterator, List, Optional
```

`Iterator` is imported but unused. `Dict` and `Any` are also imported but not used in type hints after the `_fetch_all` delegation.

### DEAD-6: `VersionService.BASE_PATH` redundant override

**File**: `opsmanager/services/version.py`, lines 41–42

```python
# Override base path: service version uses private/unauth path
BASE_PATH = "api/public/v1.0"
```

This override sets `BASE_PATH` to exactly the same value as `BaseService.BASE_PATH`. The comment says it overrides to "private/unauth path" but it does no such thing. The two methods with special paths call `self._session.get()` directly, completely bypassing `BASE_PATH`. The override and comment are misleading — remove both.

---

## 6. Inconsistency Issues

### INCON-1: `params or None` used inconsistently

Some services pass `params or None` to avoid sending an empty dict:

```python
# diagnostics.py:70
return self._download(f"groups/{project_id}/diagnostics", params=params or None)

# log_collection.py:82
params=params or None,
```

Others just pass `params` directly (which can be `{}`). `BaseService._paginate()` accepts `{}` fine and merges it with pagination params. The inconsistency is harmless but visually noisy. Pick one pattern and use it throughout.

### INCON-2: `list()` methods with no `items_per_page` parameter

`MaintenanceWindowsService.list()` does not expose `items_per_page` as a parameter (it uses `_get` directly, not `_fetch_all`). Most other list methods do. See also PAG-1.

### INCON-3: `TeamsService.list_users()` lacks `items_per_page`

`TeamsService.list_users()` has no `items_per_page` parameter, unlike `OrganizationsService.list_users()` which does. If wiring up pagination properly (see PAG-3), add `items_per_page: int = 100`.

### INCON-4: `backup.py` — `list_checkpoints()` takes `cluster_name`, `get_checkpoint()` takes `cluster_id`

**File**: `opsmanager/services/backup.py`, lines 230–278

```python
def list_checkpoints(self, project_id: str, cluster_name: str, ...) -> List[Checkpoint]:
def get_checkpoint(self, project_id: str, cluster_id: str, ...) -> Checkpoint:
```

This is documented in the docstring but is a usability trap. Users must know that checkpoints-list takes a name but checkpoint-get takes an ID. This reflects the actual Ops Manager API inconsistency; a comment cross-referencing this in `get_checkpoint` would help.

### INCON-5: `client.py` has stale "existing/new services" comments

**File**: `opsmanager/client.py`, lines 162–164, 173–174

```python
# Initialize services — existing
...
# Initialize services — new
```

These are temporary scaffolding comments from the implementation phase. The distinction is no longer meaningful — all services are "existing". Remove them.

---

## 7. Code Duplication

### DUP-1: `network.py` — `download()` is near-duplicate of `request()`

**File**: `opsmanager/network.py`, lines 420–530

`download()` (~110 lines) duplicates the entire retry loop, rate limiter acquisition, pre/post callbacks, timeout handling, connection error handling, and logging from `request()` (~135 lines). Only the response handling differs (returning `response.content` instead of `response.json()`).

This is the largest code duplication in the codebase. Extract a private `_execute_request()` method that handles the common retry/rate-limit/logging loop and is called by both `request()` and `download()`. A ~30-line refactor would eliminate ~80 lines of duplication.

### DUP-2: Measurements time validation is repeated three times

**File**: `opsmanager/services/measurements.py`, lines 182–185, 234–237, 285–288

```python
if period and (start or end):
    raise ValueError("period and start/end are mutually exclusive")
if bool(start) != bool(end):
    raise ValueError("start and end must both be provided")
```

Identical validation block in `host()`, `database()`, and `disk()`. Extract to `_validate_time_params(period, start, end)`.

---

## 8. API Contract Notes

### API-1: `global_admin.py` — likely incorrect API path for whitelist

**File**: `opsmanager/services/global_admin.py`, lines 115–156

```python
path="admin/whitelist",
```

The Ops Manager API endpoint for global API key access lists is `admin/apiKeys/{API_KEY_ID}/accessList` (not a separate `/admin/whitelist` endpoint). Verify against the actual Ops Manager API docs; this path may return 404 in production.

### API-2: `version.py` — `get_version_manifest()` path is unverified

**File**: `opsmanager/services/version.py`, line 71

```python
full_path = f"static/version_manifest/{version}"
```

This path bypasses `api/public/v1.0/`. Whether Ops Manager serves a version manifest at this static path should be verified. The live test suite doesn't appear to cover this endpoint.

### API-3: `live_migration.py` — API path needs verification

**File**: `opsmanager/services/live_migration.py`, line 54

```python
response = self._get(f"orgs/{org_id}/liveExport/migrationLink/status")
```

`liveExport/migrationLink/status` is a less common endpoint. Ops Manager live migration docs show `orgs/{ORG-ID}/liveMigrations/linkTokens`. Verify the correct path against current Ops Manager API documentation.

---

## 9. Security

### SEC-1: `APIKey.to_dict()` exposes `private_key` if present

**File**: `opsmanager/types.py`, line 1106

```python
def to_dict(self) -> Dict[str, Any]:
    return asdict(self)
```

`APIKey` has a `private_key: Optional[str]` field. The API only returns the private key once, at creation time. But if a caller serialises a populated `APIKey` object (e.g. to JSON for logging), the private key would be included. `OpsManagerAuth.__repr__` correctly masks `private_key='***'` — `APIKey` should do the same, either by overriding `to_dict()` to mask private key, or by providing a `__repr__` that masks it.

### SEC-2: `create_auth()` validation is good

`create_auth()` validates that keys are non-empty and non-whitespace-only. This is appropriate. No concerns.

### SEC-3: `verify_ssl=True` default is correct

The `verify_ssl=True` default and the fact that callers must explicitly set `verify_ssl=False` is the right security posture. No concerns.

### SEC-4: Private key masking in `OpsManagerAuth.__repr__` is good

`private_key='***'` in repr is correct. No concerns.

---

## 10. Test Coverage Gaps

The four unit test files cover the infrastructure layer well:

| Covered | File |
|---------|------|
| ✅ | NetworkSession error mapping (404, 401, 429, 500, timeouts, retries, callbacks) |
| ✅ | PageIterator (empty, single item, full pages, multi-page, max_items) |
| ✅ | RateLimiter (strict mode, burst mode, timeout, set_rate) |
| ✅ | MeasurementsService parameter validation |

**Not covered by unit tests:**

| Gap | Impact |
|-----|--------|
| No tests for any service class HTTP calls | High — services tested only via live tests |
| No tests for `auth.py` / `create_auth()` validation | Low |
| No tests for `errors.py` `raise_for_status()` directly | Low (covered indirectly via NetworkSession tests) |
| No tests for `types.py` `from_dict()` round-trips | Medium — silent default values on missing fields |
| No tests for `client.py` initialization | Low |
| No tests for new services (events, automation, backup, etc.) | Medium |
| No tests for `backup.py` cluster_name vs cluster_id inconsistency | Low |
| No tests for `alert_configurations.py` `get_open_alerts()` fallback | Medium (bug BUG-1 above) |
| `test_burst_throttles_after_burst` asserts `result in (True, False)` | Weak — this test never fails |

**Recommendation**: Add service-level unit tests that mock `BaseService._session` and assert the correct API paths and parameters are sent. Even a handful of tests per service would catch path regressions (e.g. the whitelist path issue in API-1).

---

## 11. Documentation & Docstrings

### DOC-1: `CLAUDE.md` status section is stale

**File**: `CLAUDE.md`

The "Not Yet Implemented" section still lists:
- `[ ] Automation service`
- `[ ] Backup services`
- `[ ] Events service`
- `[ ] Log collection service`

All of these are now fully implemented. Update the status section to reflect the actual implementation state, or remove the checklist entirely.

### DOC-2: `__init__.py` missing exports

**File**: `opsmanager/__init__.py`

`OpsManagerTimeoutError`, `OpsManagerConnectionError`, and `OpsManagerValidationError` are not exported from the package `__all__`. Users who want to catch these specifically must import from `opsmanager.errors` directly, which is not discoverable. Add them to `__all__` and the import list.

### DOC-3: `PerformanceAdvisorOptions.namespaces` documents as "comma-separated" but API may accept list

**File**: `opsmanager/services/performance_advisor.py`, line 42

The attribute is typed as `Optional[str]` and documented as "Comma-separated list". Verify the API — if it accepts `namespaces=db.collection` (single value) or must be `namespaces=db.col1,db.col2`, the `get_slow_queries` `namespaces` parameter should be the same type. The `get_namespaces` and `get_slow_queries` methods take `namespaces: Optional[str]` inline, which is consistent with this.

### DOC-4: `AutomationStatus.is_in_goal_state` property may have off-by-one

**File**: `opsmanager/types.py`, line 671

```python
return all(p.goal_version >= self.goal_version for p in self.processes)
```

The per-process `goal_version` (confusingly) is actually the current `conf_count` applied by the agent — it's compared against the top-level `goalVersion` which is the target. The semantics are: an agent is converged when `p.conf_count >= goal_version`. Using `p.goal_version` (field name) here matches the API's `AutomationAgentStatus.goalVersion` response field which actually does hold the agent's reported version. This is correct but the field naming is confusing due to the API's own terminology.

---

## 12. Minor Style Issues

- **Single-char loop variable `l`**: Used in dozens of list comprehensions (`[Link.from_dict(l) for l in data.get("links", [])]`). Single-char variable names are flagged by ruff's E741 rule. Use `link` as the variable name throughout.

- **`network.py` deferred import**: `from opsmanager import __version__` inside `__init__` is non-standard. Move `__version__` to a standalone `opsmanager/_version.py` file, or simply hardcode the user agent as a string constant in `NetworkSession`. This avoids the circular import concern entirely.

- **`DEFAULT_BASE_URL` in `client.py`**: `OpsManagerClient.DEFAULT_BASE_URL = "https://cloud.mongodb.com"` is defined but never used (the constructor requires `base_url` as a positional argument). If it's not a fallback, remove it.

---

## 13. Summary: Issues by Priority

### High Priority (correctness)
| ID | Description | File |
|----|-------------|------|
| BUG-1 | `get_open_alerts()` fallback wraps entire response in list | `alert_configurations.py:128` |
| PAG-2 | `server_usage.py` three methods silently truncate at 100 items | `server_usage.py:60-118` |
| PAG-3 | `teams.py` `list_users()` silently truncates at 100 | `teams.py:137` |
| PAG-4 | `get_open_alerts()` not paginated | `alert_configurations.py:125` |

### Medium Priority (quality, discoverability)
| ID | Description | File |
|----|-------------|------|
| TYPE-1 | `as_obj=False` return types are incorrect throughout all services | All services |
| DUP-1 | `download()` is ~80 lines duplicated from `request()` | `network.py` |
| PAG-1 | `maintenance_windows.list()` not paginated | `maintenance_windows.py:54` |
| API-1 | Global whitelist path likely incorrect | `global_admin.py` |
| SEC-1 | `APIKey.to_dict()` exposes private_key | `types.py:1106` |
| DOC-2 | `OpsManagerTimeoutError` et al. not exported from package | `__init__.py` |
| TEST | No unit tests for service classes | `tests/unit/` |

### Low Priority (cleanup, polish)
| ID | Description | File |
|----|-------------|------|
| BUG-2 | `Checkpoint.from_dict()` field name ambiguity | `types.py:974` |
| BUG-3 | `NExamples` casing wrong in `PerformanceAdvisorOptions` | `performance_advisor.py:66` |
| BUG-4 | `DaemonConfig.from_dict()` fragile `machine` parsing | `types.py:1393-1411` |
| DEAD-1..6 | Dead code: `AdminBackupConfig`, `PaginatedResult`, `ListOptions`, `PerformanceAdvisorOptions`, unused imports, `VersionService.BASE_PATH` | Various |
| INCON-1..5 | Inconsistencies in `params or None`, missing `items_per_page`, stale comments | Various |
| DUP-2 | Measurements time validation duplicated 3× | `measurements.py` |
| TYPE-2 | `__exit__` signature non-standard | `network.py`, `client.py` |
| TYPE-3 | `ProcessType` enum name/value mismatch | `types.py:39-46` |
| TYPE-4 | `Cluster.from_dict()` non-idiomatic enum check | `types.py:138` |
| DOC-1 | `CLAUDE.md` stale status | `CLAUDE.md` |
| STYLE | Single-char `l` variable in comprehensions | `types.py` throughout |
| API-2 | `version.py` manifest path unverified | `version.py:71` |
| API-3 | `live_migration.py` API path needs verification | `live_migration.py:54` |

---

## 14. What's Working Well (Don't Change)

- The **BaseService → Service → OpsManagerClient** three-layer architecture is clean and should be maintained as-is.
- The **PageIterator** implementation is correct, well-tested, and handles edge cases properly.
- The **RateLimiter** is correctly implemented and well-tested.
- The **error hierarchy** and `raise_for_status()` dispatch function are excellent.
- **Docstring quality** across services is consistently high — the compliance context notes are valuable.
- The **test infrastructure** (mocking pattern, `_make_session()`, `_make_response()` helpers) is clean and should be extended for service-level tests.
- **`pyproject.toml`** tooling configuration (black, isort, ruff, mypy) is complete and appropriate.
- The `as_obj` pattern (despite the type annotation issue) is a good design choice for library flexibility.
