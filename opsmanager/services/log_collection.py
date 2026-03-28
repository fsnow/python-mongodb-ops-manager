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

Provides read access to log collection jobs and the ability to download
collected logs. Log collection jobs gather MongoDB process logs from
monitored hosts into a downloadable archive.

Critical for forensic investigation, compliance evidence, and incident
root cause analysis at regulated institutions.

See: https://www.mongodb.com/docs/ops-manager/current/reference/api/log-collection/
"""

from typing import Any, Dict, List, Optional

from opsmanager.services.base import BaseService
from opsmanager.types import LogCollectionJob
from opsmanager.pagination import PageIterator


class LogCollectionService(BaseService):
    """Service for reading log collection jobs and downloading collected logs.

    Log collection jobs are managed tasks that gather MongoDB process logs
    from all hosts in a project into a downloadable archive. Use this service
    to check job status, enumerate available log archives, and download them.

    Downloaded logs are returned as raw gzip-compressed bytes:

    Example::

        jobs = client.log_collection.list(project_id="abc123")
        for job in jobs:
            if job.status == "SUCCESS":
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
