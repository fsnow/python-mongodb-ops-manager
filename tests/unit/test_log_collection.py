# Copyright 2024 Frank Snow
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Unit tests for LogCollectionService and LogCollectionJob."""

import pytest
from unittest.mock import MagicMock, call

from opsmanager.services.log_collection import LogCollectionService
from opsmanager.types import LogCollectionJob
from opsmanager.errors import (
    OpsManagerNotFoundError,
    OpsManagerBadRequestError,
    OpsManagerConflictError,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROJECT_ID = "proj123"
JOB_ID = "job456"
_BASE = "api/public/v1.0"
_JOBS = f"{_BASE}/groups/{PROJECT_ID}/logCollectionJobs"
_JOB = f"{_JOBS}/{JOB_ID}"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_service():
    """Return (LogCollectionService, mock_session)."""
    session = MagicMock()
    # download returns bytes; everything else returns dicts
    session.download.return_value = b""
    return LogCollectionService(session), session


def _job_dict(**overrides):
    """Full job dict with every field populated."""
    data = {
        "id": JOB_ID,
        "groupId": PROJECT_ID,
        "userId": "user001",
        "status": "SUCCESS",
        "resourceType": "REPLICASET",
        "resourceName": "rs0",
        "rootResourceName": "cluster0",
        "rootResourceType": "CLUSTER",
        "sizeRequestedPerFileBytes": 1_000_000,
        "uncompressedSizeTotalBytes": 512_000,
        "creationDate": "2026-01-01T00:00:00Z",
        "expirationDate": "2026-02-01T00:00:00Z",
        "logCollectionFromDate": 1_700_000_000_000,
        "logCollectionToDate": 1_700_086_400_000,
        "redacted": True,
        "logTypes": ["MONGODB", "AUTOMATION_AGENT"],
        "downloadUrl": "https://om.example.com/download/job456",
        "childJobs": [],
        "links": [],
    }
    data.update(overrides)
    return data


def _page(items, total=None):
    return {
        "results": items,
        "totalCount": total if total is not None else len(items),
    }


# ---------------------------------------------------------------------------
# LogCollectionJob dataclass
# ---------------------------------------------------------------------------

class TestLogCollectionJobFromDict:
    """from_dict() with full and partial data."""

    def test_all_fields_populated(self):
        job = LogCollectionJob.from_dict(_job_dict())
        assert job.id == JOB_ID
        assert job.group_id == PROJECT_ID
        assert job.user_id == "user001"
        assert job.status == "SUCCESS"
        assert job.resource_type == "REPLICASET"
        assert job.resource_name == "rs0"
        assert job.root_resource_name == "cluster0"
        assert job.root_resource_type == "CLUSTER"
        assert job.size_requested_per_file_bytes == 1_000_000
        assert job.uncompressed_size_total_bytes == 512_000
        assert job.creation_date == "2026-01-01T00:00:00Z"
        assert job.expiration_date == "2026-02-01T00:00:00Z"
        assert job.log_collection_from_date == 1_700_000_000_000
        assert job.log_collection_to_date == 1_700_086_400_000
        assert job.redacted is True
        assert job.log_types == ["MONGODB", "AUTOMATION_AGENT"]
        assert job.download_url == "https://om.example.com/download/job456"
        assert job.child_jobs == []

    def test_redacted_false_is_preserved(self):
        """redacted=False must round-trip correctly (not confused with None)."""
        job = LogCollectionJob.from_dict(_job_dict(redacted=False))
        assert job.redacted is False

    def test_redacted_absent_is_none(self):
        data = _job_dict()
        data.pop("redacted")
        job = LogCollectionJob.from_dict(data)
        assert job.redacted is None

    def test_optional_fields_default_when_absent(self):
        job = LogCollectionJob.from_dict({})
        assert job.id == ""
        assert job.group_id == ""
        assert job.user_id == ""
        assert job.resource_type == ""
        assert job.resource_name == ""
        assert job.root_resource_name == ""
        assert job.root_resource_type == ""
        assert job.size_requested_per_file_bytes == 0
        assert job.uncompressed_size_total_bytes == 0
        assert job.status == ""
        assert job.creation_date is None
        assert job.expiration_date is None
        assert job.log_collection_from_date is None
        assert job.log_collection_to_date is None
        assert job.redacted is None
        assert job.log_types == []
        assert job.download_url is None
        assert job.child_jobs == []
        assert job.links == []

    def test_partial_dict_does_not_raise(self):
        job = LogCollectionJob.from_dict({"id": "x", "status": "IN_PROGRESS"})
        assert job.id == "x"
        assert job.status == "IN_PROGRESS"
        assert job.user_id == ""
        assert job.root_resource_name == ""

    def test_log_collection_dates_are_integers(self):
        job = LogCollectionJob.from_dict(_job_dict())
        assert isinstance(job.log_collection_from_date, int)
        assert isinstance(job.log_collection_to_date, int)

    def test_to_dict_round_trips(self):
        original = _job_dict()
        job = LogCollectionJob.from_dict(original)
        d = job.to_dict()
        assert d["id"] == JOB_ID
        assert d["uncompressed_size_total_bytes"] == 512_000
        assert d["root_resource_name"] == "cluster0"


# ---------------------------------------------------------------------------
# Read operations
# ---------------------------------------------------------------------------

class TestLogCollectionList:
    """list() — GET with pagination params."""

    def test_list_calls_correct_path(self):
        svc, session = _make_service()
        session.get.return_value = _page([_job_dict()])
        svc.list(PROJECT_ID)
        session.get.assert_called_once()
        path = session.get.call_args[0][0]
        assert path == _JOBS

    def test_list_returns_typed_objects_by_default(self):
        svc, session = _make_service()
        session.get.return_value = _page([_job_dict()])
        jobs = svc.list(PROJECT_ID)
        assert len(jobs) == 1
        assert isinstance(jobs[0], LogCollectionJob)
        assert jobs[0].id == JOB_ID

    def test_list_as_obj_false_returns_dicts(self):
        svc, session = _make_service()
        session.get.return_value = _page([_job_dict()])
        jobs = svc.list(PROJECT_ID, as_obj=False)
        assert isinstance(jobs[0], dict)

    def test_list_verbose_sends_param(self):
        svc, session = _make_service()
        session.get.return_value = _page([])
        svc.list(PROJECT_ID, verbose=True)
        _, kwargs = session.get.call_args
        params = kwargs.get("params", {})
        assert params.get("verbose") == "true"

    def test_list_no_verbose_omits_param(self):
        svc, session = _make_service()
        session.get.return_value = _page([])
        svc.list(PROJECT_ID)
        _, kwargs = session.get.call_args
        params = kwargs.get("params") or {}
        assert "verbose" not in params

    def test_list_empty_returns_empty_list(self):
        svc, session = _make_service()
        session.get.side_effect = [_page([]), _page([])]
        jobs = svc.list(PROJECT_ID)
        assert jobs == []


class TestLogCollectionGet:
    """get() — single job fetch."""

    def test_get_calls_correct_path(self):
        svc, session = _make_service()
        session.get.return_value = _job_dict()
        svc.get(PROJECT_ID, JOB_ID)
        path = session.get.call_args[0][0]
        assert path == _JOB

    def test_get_returns_typed_object(self):
        svc, session = _make_service()
        session.get.return_value = _job_dict()
        job = svc.get(PROJECT_ID, JOB_ID)
        assert isinstance(job, LogCollectionJob)
        assert job.id == JOB_ID
        assert job.user_id == "user001"
        assert job.root_resource_name == "cluster0"
        assert job.uncompressed_size_total_bytes == 512_000

    def test_get_as_obj_false_returns_dict(self):
        svc, session = _make_service()
        session.get.return_value = _job_dict()
        result = svc.get(PROJECT_ID, JOB_ID, as_obj=False)
        assert isinstance(result, dict)
        assert result["id"] == JOB_ID

    def test_get_verbose_sends_param(self):
        svc, session = _make_service()
        session.get.return_value = _job_dict()
        svc.get(PROJECT_ID, JOB_ID, verbose=True)
        _, kwargs = session.get.call_args
        params = kwargs.get("params", {})
        assert params.get("verbose") == "true"


class TestLogCollectionDownload:
    """download() — binary gzip response."""

    def test_download_calls_correct_path(self):
        svc, session = _make_service()
        session.download.return_value = b"\x1f\x8b fake gzip"
        svc.download(PROJECT_ID, JOB_ID)
        path = session.download.call_args[0][0]
        assert path == f"{_JOB}/download"

    def test_download_returns_bytes(self):
        svc, session = _make_service()
        raw = b"\x1f\x8b fake gzip content"
        session.download.return_value = raw
        result = svc.download(PROJECT_ID, JOB_ID)
        assert result == raw

    def test_download_returns_bytes_type(self):
        svc, session = _make_service()
        session.download.return_value = b"data"
        result = svc.download(PROJECT_ID, JOB_ID)
        assert isinstance(result, bytes)


# ---------------------------------------------------------------------------
# Write operations
# ---------------------------------------------------------------------------

class TestLogCollectionCreate:
    """create() — POST with request body."""

    def test_create_calls_post_on_jobs_path(self):
        svc, session = _make_service()
        session.post.return_value = _job_dict(status="IN_PROGRESS")
        svc.create(PROJECT_ID, resource_type="REPLICASET", resource_name="rs0")
        path = session.post.call_args[0][0]
        assert path == _JOBS

    def test_create_returns_typed_object(self):
        svc, session = _make_service()
        session.post.return_value = _job_dict(status="IN_PROGRESS")
        job = svc.create(PROJECT_ID, resource_type="REPLICASET", resource_name="rs0")
        assert isinstance(job, LogCollectionJob)
        assert job.status == "IN_PROGRESS"

    def test_create_as_obj_false_returns_dict(self):
        svc, session = _make_service()
        session.post.return_value = _job_dict()
        result = svc.create(
            PROJECT_ID, resource_type="REPLICASET", resource_name="rs0", as_obj=False
        )
        assert isinstance(result, dict)

    def test_create_minimal_body_shape(self):
        """Only resource_type and resource_name are required in the body."""
        svc, session = _make_service()
        session.post.return_value = _job_dict()
        svc.create(PROJECT_ID, resource_type="REPLICASET", resource_name="rs0")
        _, kwargs = session.post.call_args
        body = kwargs["json"]
        assert body["resourceType"] == "REPLICASET"
        assert body["resourceName"] == "rs0"
        # Optional fields not passed — must not be in body
        assert "logTypes" not in body
        assert "sizeRequestedPerFileBytes" not in body
        assert "redacted" not in body
        assert "logCollectionFromDate" not in body
        assert "logCollectionToDate" not in body

    def test_create_full_body_shape(self):
        """All optional fields appear in body when provided."""
        svc, session = _make_service()
        session.post.return_value = _job_dict()
        svc.create(
            PROJECT_ID,
            resource_type="CLUSTER",
            resource_name="cluster0",
            log_types=["MONGODB"],
            size_requested_per_file_bytes=2_000_000,
            log_collection_from_date=1_700_000_000_000,
            log_collection_to_date=1_700_086_400_000,
            redacted=True,
        )
        _, kwargs = session.post.call_args
        body = kwargs["json"]
        assert body["resourceType"] == "CLUSTER"
        assert body["resourceName"] == "cluster0"
        assert body["logTypes"] == ["MONGODB"]
        assert body["sizeRequestedPerFileBytes"] == 2_000_000
        assert body["logCollectionFromDate"] == 1_700_000_000_000
        assert body["logCollectionToDate"] == 1_700_086_400_000
        assert body["redacted"] is True

    def test_create_redacted_false_included_in_body(self):
        """redacted=False must be sent (not silently dropped like None)."""
        svc, session = _make_service()
        session.post.return_value = _job_dict()
        svc.create(PROJECT_ID, resource_type="REPLICASET", resource_name="rs0", redacted=False)
        _, kwargs = session.post.call_args
        assert "redacted" in kwargs["json"]
        assert kwargs["json"]["redacted"] is False

    def test_create_uses_http_post(self):
        """Verify POST is used, not GET/PATCH/etc."""
        svc, session = _make_service()
        session.post.return_value = _job_dict()
        svc.create(PROJECT_ID, resource_type="REPLICASET", resource_name="rs0")
        session.post.assert_called_once()
        session.get.assert_not_called()


class TestLogCollectionExtend:
    """extend() — PATCH with expirationDate."""

    def test_extend_calls_patch_on_job_path(self):
        svc, session = _make_service()
        session.patch.return_value = {}
        svc.extend(PROJECT_ID, JOB_ID, expiration_date="2026-06-01T00:00:00Z")
        path = session.patch.call_args[0][0]
        assert path == _JOB

    def test_extend_sends_expiration_date(self):
        svc, session = _make_service()
        session.patch.return_value = {}
        svc.extend(PROJECT_ID, JOB_ID, expiration_date="2026-06-01T00:00:00Z")
        _, kwargs = session.patch.call_args
        assert kwargs["json"] == {"expirationDate": "2026-06-01T00:00:00Z"}

    def test_extend_returns_none(self):
        svc, session = _make_service()
        session.patch.return_value = {}
        result = svc.extend(PROJECT_ID, JOB_ID, expiration_date="2026-06-01T00:00:00Z")
        assert result is None

    def test_extend_uses_http_patch(self):
        svc, session = _make_service()
        session.patch.return_value = {}
        svc.extend(PROJECT_ID, JOB_ID, expiration_date="2026-06-01T00:00:00Z")
        session.patch.assert_called_once()
        session.post.assert_not_called()


class TestLogCollectionRetry:
    """retry() — PUT with no body."""

    def test_retry_calls_put_on_retry_path(self):
        svc, session = _make_service()
        session.put.return_value = {}
        svc.retry(PROJECT_ID, JOB_ID)
        path = session.put.call_args[0][0]
        assert path == f"{_JOB}/retry"

    def test_retry_returns_none(self):
        svc, session = _make_service()
        session.put.return_value = {}
        result = svc.retry(PROJECT_ID, JOB_ID)
        assert result is None

    def test_retry_uses_http_put(self):
        svc, session = _make_service()
        session.put.return_value = {}
        svc.retry(PROJECT_ID, JOB_ID)
        session.put.assert_called_once()
        session.post.assert_not_called()
        session.patch.assert_not_called()


class TestLogCollectionDelete:
    """delete() — DELETE with no body."""

    def test_delete_calls_delete_on_job_path(self):
        svc, session = _make_service()
        session.delete.return_value = {}
        svc.delete(PROJECT_ID, JOB_ID)
        path = session.delete.call_args[0][0]
        assert path == _JOB

    def test_delete_returns_none(self):
        svc, session = _make_service()
        session.delete.return_value = {}
        result = svc.delete(PROJECT_ID, JOB_ID)
        assert result is None

    def test_delete_uses_http_delete(self):
        svc, session = _make_service()
        session.delete.return_value = {}
        svc.delete(PROJECT_ID, JOB_ID)
        session.delete.assert_called_once()
        session.post.assert_not_called()


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

class TestLogCollectionErrors:
    """Service methods propagate errors raised by the session."""

    def test_get_404_propagates(self):
        svc, session = _make_service()
        session.get.side_effect = OpsManagerNotFoundError(
            message="Job not found", error_code="JOB_NOT_FOUND"
        )
        with pytest.raises(OpsManagerNotFoundError) as exc_info:
            svc.get(PROJECT_ID, "nonexistent-job")
        assert exc_info.value.status_code == 404

    def test_delete_404_propagates(self):
        svc, session = _make_service()
        session.delete.side_effect = OpsManagerNotFoundError(
            message="Job not found", error_code="JOB_NOT_FOUND"
        )
        with pytest.raises(OpsManagerNotFoundError):
            svc.delete(PROJECT_ID, "nonexistent-job")

    def test_create_409_conflict_propagates(self):
        """409 when a job already exists for the same resource."""
        svc, session = _make_service()
        session.post.side_effect = OpsManagerConflictError(
            message="Conflict", error_code="JOB_ALREADY_EXISTS"
        )
        with pytest.raises(OpsManagerConflictError) as exc_info:
            svc.create(PROJECT_ID, resource_type="REPLICASET", resource_name="rs0")
        assert exc_info.value.status_code == 409

    def test_create_400_bad_request_propagates(self):
        """400 for invalid payload (e.g. unknown resourceType)."""
        svc, session = _make_service()
        session.post.side_effect = OpsManagerBadRequestError(
            message="Bad request", error_code="INVALID_RESOURCE_TYPE"
        )
        with pytest.raises(OpsManagerBadRequestError) as exc_info:
            svc.create(PROJECT_ID, resource_type="INVALID", resource_name="rs0")
        assert exc_info.value.status_code == 400

    def test_extend_404_propagates(self):
        svc, session = _make_service()
        session.patch.side_effect = OpsManagerNotFoundError(message="Not found")
        with pytest.raises(OpsManagerNotFoundError):
            svc.extend(PROJECT_ID, "bad-job-id", expiration_date="2026-06-01T00:00:00Z")

    def test_retry_404_propagates(self):
        svc, session = _make_service()
        session.put.side_effect = OpsManagerNotFoundError(message="Not found")
        with pytest.raises(OpsManagerNotFoundError):
            svc.retry(PROJECT_ID, "bad-job-id")

    def test_list_propagates_errors(self):
        svc, session = _make_service()
        from opsmanager.errors import OpsManagerAuthenticationError
        session.get.side_effect = OpsManagerAuthenticationError()
        with pytest.raises(OpsManagerAuthenticationError):
            svc.list(PROJECT_ID)


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------

class TestLogCollectionPagination:
    """list_iter() paginates through multiple pages."""

    def test_list_iter_single_page(self):
        svc, session = _make_service()
        session.get.return_value = _page([_job_dict()])
        jobs = list(svc.list_iter(PROJECT_ID))
        assert len(jobs) == 1
        assert isinstance(jobs[0], LogCollectionJob)

    def test_list_iter_multiple_pages(self):
        """Two full pages (2 items each) + one empty page signals end."""
        svc, session = _make_service()
        page1 = _page([_job_dict(id="j1"), _job_dict(id="j2")])
        page2 = _page([_job_dict(id="j3"), _job_dict(id="j4")])
        page3 = _page([])
        session.get.side_effect = [page1, page2, page3]
        jobs = list(svc.list_iter(PROJECT_ID, items_per_page=2))
        assert len(jobs) == 4
        assert [j.id for j in jobs] == ["j1", "j2", "j3", "j4"]

    def test_list_iter_partial_last_page(self):
        """Partial last page (fewer items than items_per_page) stops without extra fetch."""
        svc, session = _make_service()
        page1 = _page([_job_dict(id="j1"), _job_dict(id="j2")])
        page2 = _page([_job_dict(id="j3")])  # partial — stops here
        session.get.side_effect = [page1, page2]
        jobs = list(svc.list_iter(PROJECT_ID, items_per_page=2))
        assert len(jobs) == 3
        assert session.get.call_count == 2

    def test_list_iter_sends_pagination_params(self):
        """Each page request includes pageNum, itemsPerPage, includeCount."""
        svc, session = _make_service()
        session.get.return_value = _page([])
        list(svc.list_iter(PROJECT_ID, items_per_page=50))
        _, kwargs = session.get.call_args
        params = kwargs.get("params", {})
        assert params["pageNum"] == 1
        assert params["itemsPerPage"] == 50
        assert params["includeCount"] == "true"

    def test_list_iter_verbose_forwarded_to_each_page(self):
        svc, session = _make_service()
        session.get.return_value = _page([])
        list(svc.list_iter(PROJECT_ID, verbose=True))
        _, kwargs = session.get.call_args
        params = kwargs.get("params", {})
        assert params.get("verbose") == "true"

    def test_list_iter_returns_page_iterator(self):
        from opsmanager.pagination import PageIterator
        svc, session = _make_service()
        session.get.return_value = _page([])
        it = svc.list_iter(PROJECT_ID)
        assert isinstance(it, PageIterator)

    def test_list_iter_empty_project(self):
        svc, session = _make_service()
        session.get.return_value = _page([])
        jobs = list(svc.list_iter(PROJECT_ID))
        assert jobs == []
