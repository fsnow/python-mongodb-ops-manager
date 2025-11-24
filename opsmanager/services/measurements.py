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
Measurements service for MongoDB Ops Manager API.

Provides access to time-series metrics for hosts, databases, and disks.
This is critical for health check reporting and performance analysis.

See: https://docs.opsmanager.mongodb.com/current/reference/api/measurements/
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from opsmanager.services.base import BaseService
from opsmanager.types import ProcessMeasurements, Measurement


@dataclass
class MeasurementOptions:
    """Options for measurement queries.

    Attributes:
        granularity: Duration that specifies the interval at which to report
            the metrics. Must be an ISO 8601 duration (e.g., "PT1M" for 1 minute,
            "PT1H" for 1 hour).
        period: Duration over which to report the metrics. Must be an ISO 8601
            duration (e.g., "P1D" for 1 day, "P7D" for 7 days).
        start: Start of the period (ISO 8601 timestamp). Mutually exclusive with period.
        end: End of the period (ISO 8601 timestamp). Mutually exclusive with period.
        metrics: List of metric names to retrieve.
    """
    granularity: str = "PT1M"  # 1 minute default
    period: Optional[str] = None  # e.g., "P1D" for 1 day
    start: Optional[str] = None
    end: Optional[str] = None
    metrics: Optional[List[str]] = None

    def to_params(self) -> Dict[str, Any]:
        """Convert to API query parameters."""
        params = {
            "granularity": self.granularity,
        }
        if self.period:
            params["period"] = self.period
        if self.start:
            params["start"] = self.start
        if self.end:
            params["end"] = self.end
        if self.metrics:
            params["m"] = self.metrics
        return params


class MeasurementsService(BaseService):
    """Service for retrieving measurement metrics.

    Provides access to time-series data for:
    - Host/process metrics (CPU, memory, connections, opcounters, etc.)
    - Database metrics (data size, index size, etc.)
    - Disk metrics (IOPS, latency, space usage, etc.)
    """

    # Common metric names for convenience
    # Host/Process metrics
    METRIC_OPCOUNTER_CMD = "OPCOUNTER_CMD"
    METRIC_OPCOUNTER_QUERY = "OPCOUNTER_QUERY"
    METRIC_OPCOUNTER_UPDATE = "OPCOUNTER_UPDATE"
    METRIC_OPCOUNTER_DELETE = "OPCOUNTER_DELETE"
    METRIC_OPCOUNTER_GETMORE = "OPCOUNTER_GETMORE"
    METRIC_OPCOUNTER_INSERT = "OPCOUNTER_INSERT"

    METRIC_CONNECTIONS = "CONNECTIONS"
    METRIC_CURSORS_TOTAL_OPEN = "CURSORS_TOTAL_OPEN"
    METRIC_NETWORK_BYTES_IN = "NETWORK_BYTES_IN"
    METRIC_NETWORK_BYTES_OUT = "NETWORK_BYTES_OUT"
    METRIC_NETWORK_NUM_REQUESTS = "NETWORK_NUM_REQUESTS"

    METRIC_OP_EXECUTION_TIME_READS = "OP_EXECUTION_TIME_READS"
    METRIC_OP_EXECUTION_TIME_WRITES = "OP_EXECUTION_TIME_WRITES"
    METRIC_OP_EXECUTION_TIME_COMMANDS = "OP_EXECUTION_TIME_COMMANDS"

    METRIC_QUERY_TARGETING_SCANNED_OBJECTS_PER_RETURNED = "QUERY_TARGETING_SCANNED_OBJECTS_PER_RETURNED"
    METRIC_QUERY_TARGETING_SCANNED_PER_RETURNED = "QUERY_TARGETING_SCANNED_PER_RETURNED"

    METRIC_TICKETS_AVAILABLE_READS = "TICKETS_AVAILABLE_READS"
    METRIC_TICKETS_AVAILABLE_WRITES = "TICKETS_AVAILABLE_WRITES"

    METRIC_OPLOG_MASTER_TIME = "OPLOG_MASTER_TIME"
    METRIC_OPLOG_SLAVE_LAG_MASTER_TIME = "OPLOG_SLAVE_LAG_MASTER_TIME"
    METRIC_OPLOG_MASTER_LAG_TIME_DIFF = "OPLOG_MASTER_LAG_TIME_DIFF"

    # System metrics (requires Automation Agent)
    METRIC_SYSTEM_CPU_USER = "SYSTEM_CPU_USER"
    METRIC_SYSTEM_CPU_KERNEL = "SYSTEM_CPU_KERNEL"
    METRIC_SYSTEM_CPU_NICE = "SYSTEM_CPU_NICE"
    METRIC_SYSTEM_CPU_IOWAIT = "SYSTEM_CPU_IOWAIT"
    METRIC_SYSTEM_CPU_STEAL = "SYSTEM_CPU_STEAL"
    METRIC_SYSTEM_NORMALIZED_CPU_USER = "SYSTEM_NORMALIZED_CPU_USER"
    METRIC_SYSTEM_NORMALIZED_CPU_KERNEL = "SYSTEM_NORMALIZED_CPU_KERNEL"

    METRIC_SYSTEM_MEMORY_AVAILABLE = "SYSTEM_MEMORY_AVAILABLE"
    METRIC_SYSTEM_MEMORY_FREE = "SYSTEM_MEMORY_FREE"
    METRIC_SYSTEM_MEMORY_USED = "SYSTEM_MEMORY_USED"

    # Process CPU metrics
    METRIC_PROCESS_CPU_USER = "PROCESS_CPU_USER"
    METRIC_PROCESS_CPU_KERNEL = "PROCESS_CPU_KERNEL"
    METRIC_PROCESS_NORMALIZED_CPU_USER = "PROCESS_NORMALIZED_CPU_USER"
    METRIC_PROCESS_NORMALIZED_CPU_KERNEL = "PROCESS_NORMALIZED_CPU_KERNEL"

    # Database metrics
    METRIC_DATABASE_DATA_SIZE = "DATABASE_DATA_SIZE"
    METRIC_DATABASE_STORAGE_SIZE = "DATABASE_STORAGE_SIZE"
    METRIC_DATABASE_INDEX_SIZE = "DATABASE_INDEX_SIZE"
    METRIC_DATABASE_AVERAGE_OBJECT_SIZE = "DATABASE_AVERAGE_OBJECT_SIZE"

    # Disk metrics
    METRIC_DISK_PARTITION_IOPS_READ = "DISK_PARTITION_IOPS_READ"
    METRIC_DISK_PARTITION_IOPS_WRITE = "DISK_PARTITION_IOPS_WRITE"
    METRIC_DISK_PARTITION_IOPS_TOTAL = "DISK_PARTITION_IOPS_TOTAL"
    METRIC_DISK_PARTITION_LATENCY_READ = "DISK_PARTITION_LATENCY_READ"
    METRIC_DISK_PARTITION_LATENCY_WRITE = "DISK_PARTITION_LATENCY_WRITE"
    METRIC_DISK_PARTITION_SPACE_FREE = "DISK_PARTITION_SPACE_FREE"
    METRIC_DISK_PARTITION_SPACE_USED = "DISK_PARTITION_SPACE_USED"
    METRIC_DISK_PARTITION_SPACE_PERCENT_FREE = "DISK_PARTITION_SPACE_PERCENT_FREE"
    METRIC_DISK_PARTITION_SPACE_PERCENT_USED = "DISK_PARTITION_SPACE_PERCENT_USED"

    def host(
        self,
        project_id: str,
        host_id: str,
        granularity: str = "PT1M",
        period: Optional[str] = "P1D",
        start: Optional[str] = None,
        end: Optional[str] = None,
        metrics: Optional[List[str]] = None,
        as_obj: bool = True,
    ) -> Union[ProcessMeasurements, Dict[str, Any]]:
        """Get measurements for a host.

        Args:
            project_id: Project (group) ID.
            host_id: Host ID.
            granularity: Interval for reporting metrics (ISO 8601 duration).
            period: Duration to report (ISO 8601 duration). Mutually exclusive
                with start/end.
            start: Start timestamp (ISO 8601). Requires end.
            end: End timestamp (ISO 8601). Requires start.
            metrics: List of metric names. If None, returns all available metrics.
            as_obj: Return ProcessMeasurements object if True, dict if False.

        Returns:
            Measurement data.

        Example:
            # Get opcounters for the last 24 hours at 1-minute granularity
            measurements = client.measurements.host(
                project_id="abc123",
                host_id="host123",
                granularity="PT1M",
                period="P1D",
                metrics=["OPCOUNTER_QUERY", "OPCOUNTER_INSERT"],
            )
        """
        params = {"granularity": granularity}

        if period:
            params["period"] = period
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        if metrics:
            # API accepts multiple m parameters
            params["m"] = metrics

        response = self._get(
            f"groups/{project_id}/hosts/{host_id}/measurements",
            params=params,
        )

        return ProcessMeasurements.from_dict(response) if as_obj else response

    def database(
        self,
        project_id: str,
        host_id: str,
        database_name: str,
        granularity: str = "PT1M",
        period: Optional[str] = "P1D",
        start: Optional[str] = None,
        end: Optional[str] = None,
        metrics: Optional[List[str]] = None,
        as_obj: bool = True,
    ) -> Union[ProcessMeasurements, Dict[str, Any]]:
        """Get measurements for a database.

        Args:
            project_id: Project (group) ID.
            host_id: Host ID.
            database_name: Database name.
            granularity: Interval for reporting metrics (ISO 8601 duration).
            period: Duration to report (ISO 8601 duration).
            start: Start timestamp (ISO 8601).
            end: End timestamp (ISO 8601).
            metrics: List of metric names.
            as_obj: Return ProcessMeasurements object if True, dict if False.

        Returns:
            Measurement data.
        """
        params = {"granularity": granularity}

        if period:
            params["period"] = period
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        if metrics:
            params["m"] = metrics

        response = self._get(
            f"groups/{project_id}/hosts/{host_id}/databases/{database_name}/measurements",
            params=params,
        )

        return ProcessMeasurements.from_dict(response) if as_obj else response

    def disk(
        self,
        project_id: str,
        host_id: str,
        partition_name: str,
        granularity: str = "PT1M",
        period: Optional[str] = "P1D",
        start: Optional[str] = None,
        end: Optional[str] = None,
        metrics: Optional[List[str]] = None,
        as_obj: bool = True,
    ) -> Union[ProcessMeasurements, Dict[str, Any]]:
        """Get measurements for a disk partition.

        Args:
            project_id: Project (group) ID.
            host_id: Host ID.
            partition_name: Disk partition name.
            granularity: Interval for reporting metrics (ISO 8601 duration).
            period: Duration to report (ISO 8601 duration).
            start: Start timestamp (ISO 8601).
            end: End timestamp (ISO 8601).
            metrics: List of metric names.
            as_obj: Return ProcessMeasurements object if True, dict if False.

        Returns:
            Measurement data.
        """
        params = {"granularity": granularity}

        if period:
            params["period"] = period
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        if metrics:
            params["m"] = metrics

        response = self._get(
            f"groups/{project_id}/hosts/{host_id}/disks/{partition_name}/measurements",
            params=params,
        )

        return ProcessMeasurements.from_dict(response) if as_obj else response

    # Convenience methods for common metric queries

    def get_opcounters(
        self,
        project_id: str,
        host_id: str,
        granularity: str = "PT1M",
        period: str = "P1D",
        as_obj: bool = True,
    ) -> Union[ProcessMeasurements, Dict[str, Any]]:
        """Get opcounter metrics for a host.

        Convenience method to fetch all operation counters.

        Args:
            project_id: Project (group) ID.
            host_id: Host ID.
            granularity: Interval for reporting metrics.
            period: Duration to report.
            as_obj: Return ProcessMeasurements object if True, dict if False.

        Returns:
            Opcounter measurements.
        """
        return self.host(
            project_id=project_id,
            host_id=host_id,
            granularity=granularity,
            period=period,
            metrics=[
                self.METRIC_OPCOUNTER_CMD,
                self.METRIC_OPCOUNTER_QUERY,
                self.METRIC_OPCOUNTER_UPDATE,
                self.METRIC_OPCOUNTER_DELETE,
                self.METRIC_OPCOUNTER_GETMORE,
                self.METRIC_OPCOUNTER_INSERT,
            ],
            as_obj=as_obj,
        )

    def get_query_targeting(
        self,
        project_id: str,
        host_id: str,
        granularity: str = "PT1M",
        period: str = "P1D",
        as_obj: bool = True,
    ) -> Union[ProcessMeasurements, Dict[str, Any]]:
        """Get query targeting metrics for a host.

        Query targeting metrics show the ratio of documents scanned to
        documents returned, indicating query efficiency.

        Args:
            project_id: Project (group) ID.
            host_id: Host ID.
            granularity: Interval for reporting metrics.
            period: Duration to report.
            as_obj: Return ProcessMeasurements object if True, dict if False.

        Returns:
            Query targeting measurements.
        """
        return self.host(
            project_id=project_id,
            host_id=host_id,
            granularity=granularity,
            period=period,
            metrics=[
                self.METRIC_QUERY_TARGETING_SCANNED_OBJECTS_PER_RETURNED,
                self.METRIC_QUERY_TARGETING_SCANNED_PER_RETURNED,
            ],
            as_obj=as_obj,
        )

    def get_replication_metrics(
        self,
        project_id: str,
        host_id: str,
        granularity: str = "PT1M",
        period: str = "P1D",
        as_obj: bool = True,
    ) -> Union[ProcessMeasurements, Dict[str, Any]]:
        """Get replication metrics for a host.

        Includes oplog window and replication lag metrics.

        Args:
            project_id: Project (group) ID.
            host_id: Host ID.
            granularity: Interval for reporting metrics.
            period: Duration to report.
            as_obj: Return ProcessMeasurements object if True, dict if False.

        Returns:
            Replication measurements.
        """
        return self.host(
            project_id=project_id,
            host_id=host_id,
            granularity=granularity,
            period=period,
            metrics=[
                self.METRIC_OPLOG_MASTER_TIME,
                self.METRIC_OPLOG_SLAVE_LAG_MASTER_TIME,
                self.METRIC_OPLOG_MASTER_LAG_TIME_DIFF,
            ],
            as_obj=as_obj,
        )
