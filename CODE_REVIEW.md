# Code Review — Outstanding Issues

**Consolidated:** 2026-04-16
**Status:** Issues verified against current codebase. Fixed items removed.

---

## Resolved Since Reviews

The following issues from the original reviews have been fixed:
- Mutual exclusivity validation for `period` vs `start/end` in `measurements.py` (added)
- User-Agent version in `network.py` now reads from `__version__` dynamically
- `MeasurementOptions` dead code removed from `measurements.py`
- `except Exception` narrowed to `except OpsManagerError` in `performance_advisor.py`
- Whitespace-only string validation added to `auth.py` with `.strip()`
- BUG-1: `get_open_alerts()` fallback fixed from `[response]` to `[]`
- SEC-1: `APIKey.to_dict()` no longer exposes `private_key`
- `json` parameter shadowing `json` module in `network.py` `except` clause (catch `ValueError`)
- BUG-2/3/4: Verified correct against Go SDK (`NExamples`, `Checkpoint.parts`, `DaemonConfig.machine`)
- PAG-1: `maintenance_windows.list()` now uses `_fetch_all` with pagination
- PAG-2: `server_usage` three host assignment methods now use `_fetch_all`
- PAG-3: `teams.list_users()` now uses `_fetch_all` with pagination
- PAG-4: `alert_configurations.get_open_alerts()` now uses `_fetch_all`
- TYPE-2: `__exit__` signatures fixed to `(self, exc_type, exc_val, exc_tb)`
- TYPE-4: `ClusterType` membership check refactored to idiomatic try/except via `_safe_enum()`
- DUP-2: Time validation extracted to `_validate_time_params()` in `measurements.py`
- DEAD-5: Unused imports (`Iterator`, `Dict`, `Any`) removed from `organizations.py`
- DEAD-6: Redundant `BASE_PATH` override removed from `version.py`
- DOC-2: `OpsManagerTimeoutError`, `OpsManagerConnectionError`, `OpsManagerValidationError` added to `__init__.py` exports
- INCON-4: Cross-reference comment added to `backup.py` `get_checkpoint()` re: cluster_id vs cluster_name
- INCON-5: Stale "existing/new services" comments removed from `client.py`
- STYLE-1: Single-char `l` variable renamed to `link` in `types.py` comprehensions
- DOC-1: CLAUDE.md status section updated to reflect all implemented services
- Weak `test_burst_throttles_after_burst` fixed in v0.4.2 with real timing assertions

---

## Remaining Issues

### Type Annotations

| ID | Severity | File | Issue |
|----|----------|------|-------|
| TYPE-1 | Medium | All services | `as_obj=False` return types are wrong — annotated as typed object but returns `Dict`. Needs `@overload` with `Literal[True]`/`Literal[False]` |
| TYPE-3 | Low | `types.py:39-46` | `ProcessType` enum name/value mismatch: `REPLICA_SET_PRIMARY = "REPLICA_PRIMARY"` |

### Dead Code

| ID | File | Item |
|----|------|------|
| DEAD-1 | `types.py:1215` | `AdminBackupConfig` — not imported by any service |
| DEAD-2 | `types.py:1500` | `PaginatedResult` — not used anywhere |
| DEAD-3 | `pagination.py:28-44` | `ListOptions` — not used by any service |
| DEAD-4 | `performance_advisor.py:32-67` | `PerformanceAdvisorOptions` — defined but no service method uses it |

### API Path Issues

| ID | File | Issue |
|----|------|-------|
| API-1 | `global_admin.py:117` | **CONFIRMED BUG**: `admin/whitelist` is wrong — Go SDK uses `orgs/{orgID}/apiKeys/{apiKeyID}/accessList` |
| API-2 | `version.py:71` | `static/version_manifest/{version}` bypasses API base path — verify this works |
| API-3 | `live_migration.py:54` | `orgs/{id}/liveExport/migrationLink/status` — docs show `liveMigrations/linkTokens` |

### Security

| ID | Severity | File | Issue |
|----|----------|------|-------|
| SEC-2 | Low | `client.py` | No HTTPS enforcement or warning for non-localhost HTTP URLs |

### Code Duplication

| ID | File | Issue |
|----|------|-------|
| DUP-1 | `network.py:420-530` | `download()` duplicates ~80 lines of retry/rate-limit logic from `request()` — extract shared `_execute_request()` |

### Inconsistencies

| ID | File | Issue |
|----|------|-------|
| INCON-1 | Various | `params or None` vs passing `params` directly — inconsistent across services |

### Infrastructure

| ID | File | Issue |
|----|------|-------|
| INFRA-1 | `pagination.py:121` | Last-page detection via `len(results) < items_per_page` causes one extra fetch when final page is exactly full |
