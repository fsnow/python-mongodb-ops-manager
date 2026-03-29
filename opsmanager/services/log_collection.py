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

"""
Log collection service for MongoDB Ops Manager API.

Provides access to log collection jobs: creating, extending, retrying,
and deleting jobs, as well as listing, getting, and downloading collected
log archives.

See: https://www.mongodb.com/docs/ops-manager/current/reference/api/log-collection/
"""

from typing import Any, Dict, List, Optional

from opsmanager.services.base import BaseService
from opsmanager.types import LogCollectionJob
from opsmanager.pagination import PageIterator


class LogCollectionService(BaseService):
    """Service for managing log collection jobs and downloading collected logs.

    Log collection jobs gather MongoDB process logs from all hosts in a
    project into a downloadable gzip archive.

    Example::

        # Create a job, wait for completion, then download
        job = client.log_collection.create(
            project_id="abc123",
            resource_type="REPLICASET",
            resource_name="rs0",
            log_types=["MONGODB"],
            size_requested_per_file_bytes=1000000,
        )
        # ... poll job.status until "SUCCESS" ...
        log_bytes = client.log_collection.download(
            project_id="abc123",
            job_id=job.id,
        )
        with open(f"logs_{job.id}.gz", "wb") as f:
            f.write(log_bytes)
    """

    def list(
        self,
        project_id: str,
        verbose: bool = False,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> List[LogCollectionJob]:
        """Get all log collection jobs for a project.

        Args:
            project_id: Project (group) ID.
            verbose: Include child job details if True.
            items_per_page: Number of items per page.
            as_obj: Return LogCollectionJob objects if True, dicts if False.

        Returns:
            List of log collection jobs.
        """
        params: Dict[str, Any] = {}
        if verbose:
            params["verbose"] = "true"
        return self._fetch_all(
            path=f"groups/{project_id}/logCollectionJobs",
            item_type=LogCollectionJob if as_obj else None,
            params=params or None,
            items_per_page=items_per_page,
        )

    def list_iter(
        self,
        project_id: str,
        verbose: bool = False,
        items_per_page: int = 100,
        as_obj: bool = True,
    ) -> PageIterator[LogCollectionJob]:
        """Iterate over log collection jobs for a project.

        Args:
            project_id: Project (group) ID.
            verbose: Include child job details if True.
            items_per_page: Number of items per page.
            as_obj: Return LogCollectionJob objects if True, dicts if False.

        Returns:
            Iterator over log collection jobs.
        """
        params: Dict[str, Any] = {}
        if verbose:
            params["verbose"] = "true"
        return self._paginate(
            path=f"groups/{project_id}/logCollectionJobs",
            item_type=LogCollectionJob if as_obj else None,
            params=params or None,
            items_per_page=items_per_page,
        )

    def get(
        self,
        project_id: str,
        job_id: str,
        verbose: bool = False,
        as_obj: bool = True,
    ) -> LogCollectionJob:
        """Get a single log collection job by ID.

        Args:
            project_id: Project (group) ID.
            job_id: Log collection job ID.
            verbose: Include child job details if True.
            as_obj: Return LogCollectionJob object if True, dict if False.

        Returns:
            Log collection job details.
        """
        params: Dict[str, Any] = {}
        if verbose:
            params["verbose"] = "true"
        response = self._get(
            f"groups/{project_id}/logCollectionJobs/{job_id}",
            params=params or None,
        )
        return LogCollectionJob.from_dict(response) if as_obj else response

    def download(
        self,
        project_id: str,
        job_id: str,
    ) -> bytes:
        """Download the log archive for a completed log collection job.

        Returns the gzip-compressed log archive for the specified job.
        The job must have ``status == "SUCCESS"`` before download is available.

        Args:
            project_id: Project (group) ID.
            job_id: Log collection job ID.

        Returns:
            Raw gzip-compressed log archive bytes. Write to a ``.gz`` file.
        """
        return self._download(
            f"groups/{project_id}/logCollectionJobs/{job_id}/download"
        )

    def create(
        self,
        project_id: str,
        resource_type: str,
        resource_name: str,
        log_types: Optional[List[str]] = None,
        size_requested_per_file_bytes: Optional[int] = None,
        log_collection_from_date: Optional[int] = None,
        log_collection_to_date: Optional[int] = None,
        redacted: Optional[bool] = None,
        as_obj: bool = True,
    ) -> LogCollectionJob:
        """Create a new log collection job.

        Submits a request to collect MongoDB process logs from the specified
        resource (cluster, replica set, or host). Poll the returned job's
        ``status`` field until it reaches ``"SUCCESS"`` before downloading.

        Args:
            project_id: Project (group) ID.
            resource_type: Type of resource — ``"REPLICASET"``, ``"CLUSTER"``,
                or ``"PROCESS"``.
            resource_name: Name of the resource to collect logs from.
            log_types: Log types to collect (e.g. ``["MONGODB", "AUTOMATION_AGENT"]``).
                Defaults to all available types if omitted.
            size_requested_per_file_bytes: Maximum bytes per log file.
            log_collection_from_date: Start of log collection window
                (milliseconds since Unix epoch).
            log_collection_to_date: End of log collection window
                (milliseconds since Unix epoch).
            redacted: If True, redact IP addresses and hostnames in logs.
            as_obj: Return LogCollectionJob object if True, dict if False.

        Returns:
            The created log collection job.
        """
        body: Dict[str, Any] = {
            "resourceType": resource_type,
            "resourceName": resource_name,
        }
        if log_types is not None:
            body["logTypes"] = log_types
        if size_requested_per_file_bytes is not None:
            body["sizeRequestedPerFileBytes"] = size_requested_per_file_bytes
        if log_collection_from_date is not None:
            body["logCollectionFromDate"] = log_collection_from_date
        if log_collection_to_date is not None:
            body["logCollectionToDate"] = log_collection_to_date
        if redacted is not None:
            body["redacted"] = redacted

        response = self._post(f"groups/{project_id}/logCollectionJobs", json=body)
        return LogCollectionJob.from_dict(response) if as_obj else response

    def extend(
        self,
        project_id: str,
        job_id: str,
        expiration_date: str,
    ) -> None:
        """Extend the expiration date of a log collection job.

        Pushes the expiration date forward so the collected log archive
        remains available for download beyond its original retention window.

        Args:
            project_id: Project (group) ID.
            job_id: Log collection job ID.
            expiration_date: New expiration date (ISO 8601 timestamp,
                e.g. ``"2026-04-30T00:00:00Z"``).
        """
        self._patch(
            f"groups/{project_id}/logCollectionJobs/{job_id}",
            json={"expirationDate": expiration_date},
        )

    def retry(
        self,
        project_id: str,
        job_id: str,
    ) -> None:
        """Retry a failed log collection job.

        Re-submits a job that reached ``status == "FAILED"`` so that log
        collection is attempted again without creating a new job.

        Args:
            project_id: Project (group) ID.
            job_id: Log collection job ID.
        """
        self._put(f"groups/{project_id}/logCollectionJobs/{job_id}/retry")

    def delete(
        self,
        project_id: str,
        job_id: str,
    ) -> None:
        """Delete a log collection job.

        Removes the job and its associated log archive. Downloads are no
        longer available after deletion.

        Args:
            project_id: Project (group) ID.
            job_id: Log collection job ID.
        """
        self._delete(f"groups/{project_id}/logCollectionJobs/{job_id}")
