# Code Review: python-mongodb-ops-manager

**Reviewed:** 2026-03-28
**Reviewer:** Claude (claude-sonnet-4-6)
**Scope:** Full codebase — 21 Python files, ~3,500 lines

---

## Overall Assessment

**Grade: A- (Excellent)**

Production-ready, professional quality codebase. No critical bugs found. The main weaknesses are missing input validation, dead code, a potential API parameter bug, and the absence of unit tests.

---

## What's Good

- Consistent PEP 8, type hints, and Google-style docstrings throughout
- Well-designed exception hierarchy with proper HTTP status code mapping
- Thread-safe rate limiter with retry/backoff logic
- Lazy service initialization and memory-efficient pagination iterator
- API keys masked from logging; SSL verification enabled by default
- Comprehensive README and live integration tests

---

## Bugs

| Severity | File | Line | Issue |
|---|---|---|---|
| **High** | `services/performance_advisor.py` | 184 | Param key `"NExamples"` — if the API expects `"nExamples"`, requests will silently send the wrong parameter |
| **Medium** | `services/measurements.py` | 219, 266, 312 | `period` and `start`/`end` are documented as mutually exclusive but not enforced in code; if both are supplied, API behavior is undefined |
| **Medium** | `pagination.py` | 121 | Last-page detection via `len(results) < items_per_page` causes one extra unnecessary API fetch when the final page happens to be exactly full |

### Bug Details

**`performance_advisor.py:184` — NExamples param key**

The parameter is passed as `"NExamples"` (capital N). Verify against the Ops Manager API docs. If the API expects `"nExamples"`, this is a silent functional bug where the parameter is simply ignored by the server.

**`measurements.py` — Missing mutual exclusivity validation**

`period` and `start`/`end` are mutually exclusive per the docstrings, but nothing enforces this. Add at the start of each affected method:

```python
if period and (start or end):
    raise ValueError("period and start/end are mutually exclusive")
if bool(start) != bool(end):
    raise ValueError("start and end must both be provided")
```

**`pagination.py:121` — Last-page detection**

```python
if len(results) < self._items_per_page:
    self._exhausted = True
```

If the last page contains exactly `items_per_page` items, this condition is false and the iterator makes one extra fetch before hitting the empty-result guard on line 108. A more efficient approach is to compare the running count of fetched items against `total_count` (already available from the response at line 106).

---

## Code Quality Issues

| Severity | File | Line | Issue |
|---|---|---|---|
| Low | `types.py` | 138 | Enum membership check via `__members__.values()` is not idiomatic; use `try/except ValueError` |
| Low | `network.py` | 320 | `except ValueError` for JSON parse failures should be `except json.JSONDecodeError` |
| Low | `network.py` | 197 | User-Agent hardcoded as `"0.1.0"` but package is at `0.3.1`; should reference `__version__` |
| Low | `services/measurements.py` | 31–65 | `MeasurementOptions` dataclass defined but never used — dead code |
| Low | `services/base.py` | 40 | API path `"api/public/v1.0"` is hardcoded and not configurable for future versions |

### Code Quality Details

**`types.py:138` — Enum check**

Current:
```python
type_name=ClusterType(type_name) if type_name in ClusterType.__members__.values() else ClusterType.REPLICA_SET,
```

Preferred:
```python
try:
    type_name = ClusterType(type_name)
except ValueError:
    type_name = ClusterType.REPLICA_SET
```

**`network.py:197` — User-Agent version**

Current:
```python
"User-Agent": user_agent or "python-opsmanager/0.1.0",
```

Should be:
```python
from opsmanager import __version__
"User-Agent": user_agent or f"python-opsmanager/{__version__}",
```

**`measurements.py:31-65` — Dead code**

`MeasurementOptions` is a dataclass with a `to_params()` method, but all measurement service methods build their params manually instead of using it. Either refactor the service methods to accept a `MeasurementOptions` instance, or remove the class entirely.

---

## Error Handling Issues

| Severity | File | Line | Issue |
|---|---|---|---|
| Medium | `services/performance_advisor.py` | 248–250 | Bare `except Exception` silently absorbs all errors into the result dict; should catch `OpsManagerError` specifically |
| Low | `auth.py` | 87–90 | Whitespace-only strings (e.g. `"   "`) pass key validation; add `.strip()` check |
| Low | `network.py` | 320 | Use `json.JSONDecodeError` instead of `ValueError` for JSON parse failures |

### Error Handling Details

**`performance_advisor.py:248` — Broad exception catch**

```python
except Exception as e:
    # Log but continue with other hosts
    results[host_id] = {"error": str(e)}
```

This swallows all exceptions silently, including programming errors. Change to `except OpsManagerError as e:` so unexpected exceptions propagate normally.

**`auth.py:87-90` — Whitespace validation**

```python
if not public_key:
    raise ValueError("public_key is required")
```

A string like `"   "` passes this check. Should be:

```python
if not public_key or not public_key.strip():
    raise ValueError("public_key is required")
```

---

## Security Issues

| Severity | File | Line | Issue |
|---|---|---|---|
| Low | `client.py` | 119 | `base_url` is not validated to be HTTPS; no warning if a plain HTTP URL is used in production |

### Security Details

**`client.py:119` — No HTTPS enforcement**

`base_url` is accepted as-is with no validation. Consider emitting a warning for non-HTTPS, non-localhost URLs:

```python
import warnings
if not base_url.startswith("https://") and "localhost" not in base_url and "127.0.0.1" not in base_url:
    warnings.warn(
        "base_url is not HTTPS. API credentials may be transmitted in plaintext.",
        SecurityWarning,
        stacklevel=2,
    )
```

**Note on error responses:** Full API responses are stored in exception objects (`errors.py:49`). This is useful for debugging but be cautious when logging exceptions in production environments, as responses could contain sensitive data.

---

## Testing Gaps

The test suite consists entirely of live integration tests against a real Ops Manager instance. There are no unit tests with mocks.

**Untested paths:**
- Rate limiter edge cases (burst=1, window boundary, timeout)
- Pagination transitions (empty results, single item, exactly-full last page)
- All exception handling paths (404, 401, 429 responses)
- `auth.py` validation logic
- Enum handling in `types.py`
- The `MeasurementOptions.to_params()` method (also dead code)

**Recommendation:** Add a `tests/unit/` directory using `pytest` with `responses` or `unittest.mock` to mock HTTP calls. Prioritize tests for the rate limiter, pagination, and error handling since these have the most complex logic.

---

## Top 5 Actionable Fixes

1. **Verify `"NExamples"` vs `"nExamples"`** in `performance_advisor.py:184` against the Ops Manager API docs — this could be a silent functional bug affecting every performance advisor call that uses this parameter.

2. **Add mutual exclusivity validation** for `period` vs `start`/`end` in `measurements.py` at lines 219, 266, and 312 — prevents undefined API behavior when both are supplied.

3. **Add unit tests with mocks** for rate limiter, pagination, and error handling — the biggest gap in long-term maintainability.

4. **Delete `MeasurementOptions`** (or refactor measurement methods to actually use it) — dead code creates confusion about the intended API.

5. **Fix User-Agent version** in `network.py:197` to pull from `__version__` dynamically so it stays accurate across releases.
