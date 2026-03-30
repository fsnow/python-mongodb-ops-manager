# Code Review — Outstanding Issues

**Consolidated:** 2026-03-27
**Source:** CODE_REVIEW_1.md, CODE_REVIEW_2.md
**Status:** Issues verified against current codebase. Fixed items removed.

---

## Resolved Since Reviews

The following issues from the original reviews have been fixed:
- Mutual exclusivity validation for `period` vs `start/end` in `measurements.py` (added)
- User-Agent version in `network.py` now reads from `__version__` dynamically
- `MeasurementOptions` dead code removed from `measurements.py`
- `except Exception` narrowed to `except OpsManagerError` in `performance_advisor.py`
- Whitespace-only string validation added to `auth.py` with `.strip()`

---

## Bugs

| ID | Severity | File | Issue |
|----|----------|------|-------|
| BUG-1 | **High** | `alert_configurations.py:128` | `get_open_alerts()` fallback `[response]` wraps entire response dict in list when `"results"` key missing; should be `[]` |
| BUG-2 | **Medium** | `performance_advisor.py:66,185` | Param key `"NExamples"` — should be `"nExamples"` (lowercase n). API silently ignores the miscased parameter |
| BUG-3 | Low | `types.py:988` | `Checkpoint.from_dict()` uses `data.get("parts", [])` for field `replica_set_checkpoints` — verify actual API key name |
| BUG-4 | Low | `types.py:1406` | `DaemonConfig.from_dict()` accesses `data["machine"]["machine"]` (nested same-name key) — fragile, verify API shape |

---

## Pagination Gaps

These methods use a single `_get` instead of `_fetch_all`, silently truncating results beyond 100 items:

| ID | Severity | File | Method |
|----|----------|------|--------|
| PAG-1 | Medium | `maintenance_windows.py:54` | `list()` |
| PAG-2 | **High** | `server_usage.py:60-118` | `list_all_host_assignments()`, `get_project_host_assignments()`, `get_organization_host_assignments()` |
| PAG-3 | Medium | `teams.py:137` | `list_users()` |
| PAG-4 | Medium | `alert_configurations.py:125` | `get_open_alerts()` |

---

## Type Annotation Issues

| ID | Severity | File | Issue |
|----|----------|------|-------|
| TYPE-1 | Medium | All services | `as_obj=False` return types are wrong — annotated as typed object but returns `Dict`. Needs `@overload` with `Literal[True]`/`Literal[False]` |
| TYPE-2 | Low | `network.py:539`, `client.py:358` | `__exit__(self, *args)` — should use `(self, exc_type, exc_val, exc_tb)` |
| TYPE-3 | Low | `types.py:39-46` | `ProcessType` enum name/value mismatch: `REPLICA_SET_PRIMARY = "REPLICA_PRIMARY"` |
| TYPE-4 | Low | `types.py:138` | `ClusterType` membership check via `__members__.values()` — use try/except instead |

---

## Dead Code

| ID | File | Item |
|----|------|------|
| DEAD-1 | `types.py:1215` | `AdminBackupConfig` — not imported by any service |
| DEAD-2 | `types.py:1500` | `PaginatedResult` — not used anywhere |
| DEAD-3 | `pagination.py:28-44` | `ListOptions` — not used by any service |
| DEAD-4 | `performance_advisor.py:32-67` | `PerformanceAdvisorOptions` — defined but no service method uses it |
| DEAD-5 | `organizations.py:21` | Unused imports: `Iterator`, `Dict`, `Any` |
| DEAD-6 | `version.py:42` | `BASE_PATH` override identical to parent class, never used by either method |

---

## API Path Issues (Unverified)

| ID | File | Issue |
|----|------|-------|
| API-1 | `global_admin.py:117` | `admin/whitelist` may be wrong — current API uses `admin/apiKeys/{id}/accessList` |
| API-2 | `version.py:71` | `static/version_manifest/{version}` bypasses API base path — verify this works |
| API-3 | `live_migration.py:54` | `orgs/{id}/liveExport/migrationLink/status` — docs show `liveMigrations/linkTokens` |

---

## Security

| ID | Severity | File | Issue |
|----|----------|------|-------|
| SEC-1 | Medium | `types.py:1120` | `APIKey.to_dict()` uses `asdict(self)` which exposes `private_key` if populated |
| SEC-2 | Low | `client.py` | No HTTPS enforcement or warning for non-localhost HTTP URLs |

---

## Code Duplication

| ID | File | Issue |
|----|------|-------|
| DUP-1 | `network.py:420-530` | `download()` duplicates ~80 lines of retry/rate-limit logic from `request()` — extract shared `_execute_request()` |
| DUP-2 | `measurements.py` | Time validation block duplicated identically in `host()`, `database()`, `disk()` — extract to `_validate_time_params()` |

---

## Inconsistencies

| ID | File | Issue |
|----|------|-------|
| INCON-1 | Various | `params or None` vs passing `params` directly — inconsistent across services |
| INCON-4 | `backup.py:233,260` | `list_checkpoints()` takes `cluster_name`, `get_checkpoint()` takes `cluster_id` — add cross-reference comment |
| INCON-5 | `client.py:162-238` | Stale `"existing/new services"` section comments from implementation — remove |

---

## Documentation

| ID | File | Issue |
|----|------|-------|
| DOC-1 | `CLAUDE.md` | "Not Yet Implemented" list is stale — automation, backup, events, log collection are all implemented |
| DOC-2 | `__init__.py` | `OpsManagerTimeoutError`, `OpsManagerConnectionError`, `OpsManagerValidationError` not exported in `__all__` |

---

## Style

| ID | File | Issue |
|----|------|-------|
| STYLE-1 | `types.py` | 14 occurrences of single-char `l` variable in `[Link.from_dict(l) for l in ...]` — use `link` |

---

## Infrastructure

| ID | File | Issue |
|----|------|-------|
| INFRA-1 | `pagination.py:121` | Last-page detection via `len(results) < items_per_page` causes one extra fetch when final page is exactly full |
| INFRA-2 | `network.py:322` | `except ValueError` catches JSON parse errors (intentional — `json` module shadowed by `json` parameter in method signature). Correct but worth noting. |

---

## Test Gaps

- No unit tests for any service class HTTP calls (only live integration tests)
- No unit tests for `types.py` `from_dict()` round-trips
- No tests for `alert_configurations.py` `get_open_alerts()` fallback (BUG-1)
- `test_burst_throttles_after_burst` asserts `result in (True, False)` — never fails
