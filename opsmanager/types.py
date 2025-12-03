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
Shared data types for MongoDB Ops Manager API.

These dataclasses represent the main resource types returned by the API.
They provide type safety and IDE autocompletion while remaining easy to
convert to/from dictionaries.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, TypeVar, Type
from enum import Enum


T = TypeVar("T")


class ClusterType(str, Enum):
    """Type of MongoDB cluster."""
    REPLICA_SET = "REPLICA_SET"
    SHARDED_REPLICA_SET = "SHARDED_REPLICA_SET"


class ProcessType(str, Enum):
    """Type of MongoDB process."""
    REPLICA_SET_PRIMARY = "REPLICA_PRIMARY"
    REPLICA_SET_SECONDARY = "REPLICA_SECONDARY"
    REPLICA_SET_ARBITER = "REPLICA_ARBITER"
    MONGOS = "SHARD_MONGOS"
    CONFIG_SERVER_PRIMARY = "SHARD_CONFIG_PRIMARY"
    CONFIG_SERVER_SECONDARY = "SHARD_CONFIG_SECONDARY"
    STANDALONE = "STANDALONE"


class ReplicaState(str, Enum):
    """Replica set member state."""
    PRIMARY = "PRIMARY"
    SECONDARY = "SECONDARY"
    ARBITER = "ARBITER"
    RECOVERING = "RECOVERING"
    STARTUP = "STARTUP"
    STARTUP2 = "STARTUP2"
    UNKNOWN = "UNKNOWN"
    DOWN = "DOWN"
    ROLLBACK = "ROLLBACK"
    REMOVED = "REMOVED"


@dataclass
class Link:
    """API link for pagination and related resources."""
    rel: str
    href: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Link":
        return cls(
            rel=data.get("rel", ""),
            href=data.get("href", ""),
        )


@dataclass
class Organization:
    """MongoDB Ops Manager Organization."""
    id: str
    name: str
    links: List[Link] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Organization":
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            links=[Link.from_dict(link) for link in data.get("links", [])],
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Project:
    """MongoDB Ops Manager Project (Group)."""
    id: str
    name: str
    org_id: str
    cluster_count: int = 0
    created: Optional[str] = None
    links: List[Link] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Project":
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            org_id=data.get("orgId", ""),
            cluster_count=data.get("clusterCount", 0),
            created=data.get("created"),
            links=[Link.from_dict(link) for link in data.get("links", [])],
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Cluster:
    """MongoDB cluster (replica set or sharded cluster)."""
    id: str
    cluster_name: str
    type_name: ClusterType
    replica_set_name: Optional[str] = None
    shard_name: Optional[str] = None
    last_heartbeat: Optional[str] = None
    links: List[Link] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Cluster":
        type_name = data.get("typeName", "REPLICA_SET")
        return cls(
            id=data.get("id", ""),
            cluster_name=data.get("clusterName", ""),
            type_name=ClusterType(type_name) if type_name in ClusterType.__members__.values() else ClusterType.REPLICA_SET,
            replica_set_name=data.get("replicaSetName"),
            shard_name=data.get("shardName"),
            last_heartbeat=data.get("lastHeartbeat"),
            links=[Link.from_dict(link) for link in data.get("links", [])],
        )

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["typeName"] = self.type_name.value
        return result

    @property
    def is_sharded(self) -> bool:
        """Return True if this is a sharded cluster."""
        return self.type_name == ClusterType.SHARDED_REPLICA_SET


@dataclass
class Host:
    """MongoDB host (mongod or mongos process)."""
    id: str
    hostname: str
    port: int
    type_name: str
    cluster_id: Optional[str] = None
    group_id: Optional[str] = None
    replica_set_name: Optional[str] = None
    replica_state_name: Optional[str] = None
    shard_name: Optional[str] = None
    version: Optional[str] = None
    ip_address: Optional[str] = None
    created: Optional[str] = None
    last_ping: Optional[str] = None
    last_restart: Optional[str] = None
    deactivated: bool = False
    host_enabled: bool = True
    alerts_enabled: Optional[bool] = None
    logs_enabled: Optional[bool] = None
    profiler_enabled: Optional[bool] = None
    ssl_enabled: Optional[bool] = None
    auth_mechanism_name: Optional[str] = None
    journaling_enabled: bool = True
    hidden: bool = False
    hidden_secondary: bool = False
    low_ulimit: bool = False
    last_data_size_bytes: float = 0.0
    last_index_size_bytes: float = 0.0
    uptime_msec: int = 0
    slave_delay_sec: int = 0
    links: List[Link] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Host":
        return cls(
            id=data.get("id", ""),
            hostname=data.get("hostname", ""),
            port=data.get("port", 27017),
            type_name=data.get("typeName", ""),
            cluster_id=data.get("clusterId"),
            group_id=data.get("groupId"),
            replica_set_name=data.get("replicaSetName"),
            replica_state_name=data.get("replicaStateName"),
            shard_name=data.get("shardName"),
            version=data.get("version"),
            ip_address=data.get("ipAddress"),
            created=data.get("created"),
            last_ping=data.get("lastPing"),
            last_restart=data.get("lastRestart"),
            deactivated=data.get("deactivated", False),
            host_enabled=data.get("hostEnabled", True),
            alerts_enabled=data.get("alertsEnabled"),
            logs_enabled=data.get("logsEnabled"),
            profiler_enabled=data.get("profilerEnabled"),
            ssl_enabled=data.get("sslEnabled"),
            auth_mechanism_name=data.get("authMechanismName"),
            journaling_enabled=data.get("journalingEnabled", True),
            hidden=data.get("hidden", False),
            hidden_secondary=data.get("hiddenSecondary", False),
            low_ulimit=data.get("lowUlimit", False),
            last_data_size_bytes=data.get("lastDataSizeBytes", 0.0),
            last_index_size_bytes=data.get("lastIndexSizeBytes", 0.0),
            uptime_msec=data.get("uptimeMsec", 0),
            slave_delay_sec=data.get("slaveDelaySec", 0),
            links=[Link.from_dict(link) for link in data.get("links", [])],
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @property
    def host_port(self) -> str:
        """Return hostname:port string."""
        return f"{self.hostname}:{self.port}"

    @property
    def is_primary(self) -> bool:
        """Return True if this host is a primary."""
        return self.replica_state_name == "PRIMARY"

    @property
    def is_secondary(self) -> bool:
        """Return True if this host is a secondary."""
        return self.replica_state_name == "SECONDARY"

    @property
    def is_arbiter(self) -> bool:
        """Return True if this host is an arbiter."""
        return self.replica_state_name == "ARBITER"

    @property
    def is_mongos(self) -> bool:
        """Return True if this host is a mongos."""
        return "MONGOS" in self.type_name.upper() if self.type_name else False


@dataclass
class Database:
    """MongoDB database on a host."""
    database_name: str
    links: List[Link] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Database":
        return cls(
            database_name=data.get("databaseName", ""),
            links=[Link.from_dict(link) for link in data.get("links", [])],
        )


@dataclass
class Disk:
    """Disk partition on a host."""
    partition_name: str
    links: List[Link] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Disk":
        return cls(
            partition_name=data.get("partitionName", ""),
            links=[Link.from_dict(link) for link in data.get("links", [])],
        )


@dataclass
class DataPoint:
    """A single data point in a measurement time series."""
    timestamp: str
    value: Optional[float] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DataPoint":
        return cls(
            timestamp=data.get("timestamp", ""),
            value=data.get("value"),
        )


@dataclass
class Measurement:
    """A measurement (metric) with its data points."""
    name: str
    units: str
    data_points: List[DataPoint] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Measurement":
        return cls(
            name=data.get("name", ""),
            units=data.get("units", ""),
            data_points=[DataPoint.from_dict(dp) for dp in data.get("dataPoints", [])],
        )


@dataclass
class ProcessMeasurements:
    """Collection of measurements for a process."""
    group_id: str
    host_id: str
    process_id: str
    granularity: str
    start: str
    end: str
    measurements: List[Measurement] = field(default_factory=list)
    links: List[Link] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProcessMeasurements":
        return cls(
            group_id=data.get("groupId", ""),
            host_id=data.get("hostId", ""),
            process_id=data.get("processId", ""),
            granularity=data.get("granularity", ""),
            start=data.get("start", ""),
            end=data.get("end", ""),
            measurements=[Measurement.from_dict(m) for m in data.get("measurements", [])],
            links=[Link.from_dict(link) for link in data.get("links", [])],
        )


@dataclass
class Namespace:
    """A namespace (database.collection) with slow queries."""
    namespace: str
    type: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Namespace":
        return cls(
            namespace=data.get("namespace", ""),
            type=data.get("type", ""),
        )


@dataclass
class SlowQuery:
    """A slow query from the Performance Advisor."""
    namespace: str
    line: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SlowQuery":
        return cls(
            namespace=data.get("namespace", ""),
            line=data.get("line", ""),
        )


@dataclass
class SuggestedIndex:
    """A suggested index from the Performance Advisor."""
    id: str
    namespace: str
    index: List[Dict[str, int]]
    weight: float = 0.0
    impact: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SuggestedIndex":
        return cls(
            id=data.get("id", ""),
            namespace=data.get("namespace", ""),
            index=data.get("index", []),
            weight=data.get("weight", 0.0),
            impact=data.get("impact", []),
        )


@dataclass
class QueryStats:
    """Statistics for a query shape."""
    ms: float = 0.0
    n_returned: int = 0
    n_scanned: int = 0
    ts: int = 0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QueryStats":
        return cls(
            ms=data.get("ms", 0.0),
            n_returned=data.get("nReturned", 0),
            n_scanned=data.get("nScanned", 0),
            ts=data.get("ts", 0),
        )


@dataclass
class QueryOperation:
    """A specific query operation."""
    raw: str
    stats: QueryStats
    predicates: List[Dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QueryOperation":
        return cls(
            raw=data.get("raw", ""),
            stats=QueryStats.from_dict(data.get("stats", {})),
            predicates=data.get("predicates", []),
        )


@dataclass
class QueryShape:
    """A query shape from the Performance Advisor."""
    id: str
    namespace: str
    avg_ms: float = 0.0
    count: int = 0
    inefficiency_score: int = 0
    operations: List[QueryOperation] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QueryShape":
        return cls(
            id=data.get("id", ""),
            namespace=data.get("namespace", ""),
            avg_ms=data.get("avgMs", 0.0),
            count=data.get("count", 0),
            inefficiency_score=data.get("inefficiencyScore", 0),
            operations=[QueryOperation.from_dict(op) for op in data.get("operations", [])],
        )


@dataclass
class Alert:
    """An alert from Ops Manager."""
    id: str
    group_id: str
    alert_config_id: str
    event_type_name: str
    status: str
    created: str
    updated: str
    resolved: Optional[str] = None
    acknowledged_until: Optional[str] = None
    acknowledgement_comment: Optional[str] = None
    acknowledging_username: Optional[str] = None
    cluster_name: Optional[str] = None
    replica_set_name: Optional[str] = None
    host_id: Optional[str] = None
    hostname_and_port: Optional[str] = None
    metric_name: Optional[str] = None
    current_value: Optional[Dict[str, Any]] = None
    links: List[Link] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Alert":
        return cls(
            id=data.get("id", ""),
            group_id=data.get("groupId", ""),
            alert_config_id=data.get("alertConfigId", ""),
            event_type_name=data.get("eventTypeName", ""),
            status=data.get("status", ""),
            created=data.get("created", ""),
            updated=data.get("updated", ""),
            resolved=data.get("resolved"),
            acknowledged_until=data.get("acknowledgedUntil"),
            acknowledgement_comment=data.get("acknowledgementComment"),
            acknowledging_username=data.get("acknowledgingUsername"),
            cluster_name=data.get("clusterName"),
            replica_set_name=data.get("replicaSetName"),
            host_id=data.get("hostId"),
            hostname_and_port=data.get("hostnameAndPort"),
            metric_name=data.get("metricName"),
            current_value=data.get("currentValue"),
            links=[Link.from_dict(link) for link in data.get("links", [])],
        )


# Type alias for paginated results
@dataclass
class PaginatedResult:
    """Generic paginated result from API."""
    results: List[Any]
    total_count: int
    links: List[Link] = field(default_factory=list)

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
        item_type: Optional[Type[T]] = None,
    ) -> "PaginatedResult":
        results = data.get("results", [])
        if item_type and hasattr(item_type, "from_dict"):
            results = [item_type.from_dict(item) for item in results]
        return cls(
            results=results,
            total_count=data.get("totalCount", len(results)),
            links=[Link.from_dict(link) for link in data.get("links", [])],
        )

    def has_next(self) -> bool:
        """Return True if there are more pages."""
        for link in self.links:
            if link.rel == "next":
                return True
        return False

    def get_next_link(self) -> Optional[str]:
        """Return the URL for the next page, if available."""
        for link in self.links:
            if link.rel == "next":
                return link.href
        return None
