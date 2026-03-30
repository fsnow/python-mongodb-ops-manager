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


@dataclass
class Agent:
    """A MongoDB Ops Manager agent (monitoring, backup, or automation)."""
    hostname: str
    state_name: str = ""
    type_name: str = ""
    last_ping: Optional[str] = None
    ping_count: int = 0
    conf_count: int = 0
    is_managed: bool = False
    links: List[Link] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Agent":
        return cls(
            hostname=data.get("hostname", ""),
            state_name=data.get("stateName", ""),
            type_name=data.get("typeName", ""),
            last_ping=data.get("lastPing"),
            ping_count=data.get("pingCount", 0),
            conf_count=data.get("confCount", 0),
            is_managed=data.get("isManaged", False),
            links=[Link.from_dict(link) for link in data.get("links", [])],
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SnapshotPart:
    """One replica set's portion of a backup snapshot."""
    cluster_id: str = ""
    compression_setting: str = ""
    data_size_bytes: int = 0
    encryption_enabled: bool = False
    file_size_bytes: int = 0
    mongod_version: str = ""
    replica_set_name: str = ""
    replica_state: str = ""
    storage_size_bytes: int = 0
    type_name: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SnapshotPart":
        return cls(
            cluster_id=data.get("clusterId", ""),
            compression_setting=data.get("compressionSetting", ""),
            data_size_bytes=data.get("dataSizeBytes", 0),
            encryption_enabled=data.get("encryptionEnabled", False),
            file_size_bytes=data.get("fileSizeBytes", 0),
            mongod_version=data.get("mongodVersion", ""),
            replica_set_name=data.get("replicaSetName", ""),
            replica_state=data.get("replicaState", ""),
            storage_size_bytes=data.get("storageSizeBytes", 0),
            type_name=data.get("typeName", ""),
        )


@dataclass
class Snapshot:
    """A backup snapshot."""
    id: str
    cluster_id: str
    complete: bool
    group_id: str
    do_not_delete: bool = False
    expires: Optional[str] = None
    created: Optional[Dict[str, Any]] = None
    last_oplog_applied_timestamp: Optional[Dict[str, Any]] = None
    parts: List[SnapshotPart] = field(default_factory=list)
    links: List[Link] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Snapshot":
        return cls(
            id=data.get("id", ""),
            cluster_id=data.get("clusterId", ""),
            complete=data.get("complete", False),
            group_id=data.get("groupId", ""),
            do_not_delete=data.get("doNotDelete", False),
            expires=data.get("expires"),
            created=data.get("created"),
            last_oplog_applied_timestamp=data.get("lastOplogAppliedTimestamp"),
            parts=[SnapshotPart.from_dict(p) for p in data.get("parts", [])],
            links=[Link.from_dict(link) for link in data.get("links", [])],
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Event:
    """An audit event from Ops Manager."""
    id: str
    created: str
    event_type_name: str
    group_id: Optional[str] = None
    org_id: Optional[str] = None
    user_id: Optional[str] = None
    username: Optional[str] = None
    public_key: Optional[str] = None
    remote_address: Optional[str] = None
    api_key_id: Optional[str] = None
    cluster_name: Optional[str] = None
    hostname: Optional[str] = None
    alert_id: Optional[str] = None
    alert_config_id: Optional[str] = None
    replica_set_name: Optional[str] = None
    shard_name: Optional[str] = None
    links: List[Link] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        return cls(
            id=data.get("id", ""),
            created=data.get("created", ""),
            event_type_name=data.get("eventTypeName", ""),
            group_id=data.get("groupId"),
            org_id=data.get("orgId"),
            user_id=data.get("userId"),
            username=data.get("username"),
            public_key=data.get("publicKey"),
            remote_address=data.get("remoteAddress"),
            api_key_id=data.get("apiKeyId"),
            cluster_name=data.get("clusterName"),
            hostname=data.get("hostname"),
            alert_id=data.get("alertId"),
            alert_config_id=data.get("alertConfigId"),
            replica_set_name=data.get("replicaSetName"),
            shard_name=data.get("shardName"),
            links=[Link.from_dict(l) for l in data.get("links", [])],
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AutomationAgentStatus:
    """Status of a single automation agent process."""
    hostname: str
    conf_count: int = 0
    goal_version: int = 0
    last_conf_sent: Optional[str] = None
    plan: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AutomationAgentStatus":
        return cls(
            hostname=data.get("hostname", ""),
            conf_count=data.get("confCount", 0),
            goal_version=data.get("goalVersion", 0),
            last_conf_sent=data.get("lastConf"),
            plan=data.get("plan", []),
        )


@dataclass
class AutomationStatus:
    """Automation status for a project — shows whether all agents are up-to-date."""
    goal_version: int
    processes: List[AutomationAgentStatus] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AutomationStatus":
        return cls(
            goal_version=data.get("goalVersion", 0),
            processes=[
                AutomationAgentStatus.from_dict(p)
                for p in data.get("processes", [])
            ],
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @property
    def is_in_goal_state(self) -> bool:
        """Return True if all agents have reached the goal version."""
        if not self.processes:
            return True
        return all(p.goal_version >= self.goal_version for p in self.processes)


@dataclass
class AlertNotification:
    """A notification channel for an alert configuration."""
    type_name: str
    interval_min: int = 0
    delay_min: int = 0
    email_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    username: Optional[str] = None
    team_id: Optional[str] = None
    email_address: Optional[str] = None
    mobile_number: Optional[str] = None
    notification_token: Optional[str] = None
    room_name: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AlertNotification":
        return cls(
            type_name=data.get("typeName", ""),
            interval_min=data.get("intervalMin", 0),
            delay_min=data.get("delayMin", 0),
            email_enabled=data.get("emailEnabled"),
            sms_enabled=data.get("smsEnabled"),
            username=data.get("username"),
            team_id=data.get("teamId"),
            email_address=data.get("emailAddress"),
            mobile_number=data.get("mobileNumber"),
            notification_token=data.get("notificationToken"),
            room_name=data.get("roomName"),
        )


@dataclass
class AlertMetricThreshold:
    """Metric threshold that triggers an alert."""
    metric_name: str
    operator: str
    threshold: float
    units: str
    mode: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AlertMetricThreshold":
        return cls(
            metric_name=data.get("metricName", ""),
            operator=data.get("operator", ""),
            threshold=data.get("threshold", 0.0),
            units=data.get("units", ""),
            mode=data.get("mode", ""),
        )


@dataclass
class AlertMatcher:
    """A matcher that scopes which resources an alert configuration applies to."""
    field_name: str
    operator: str
    value: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AlertMatcher":
        return cls(
            field_name=data.get("fieldName", ""),
            operator=data.get("operator", ""),
            value=data.get("value", ""),
        )


@dataclass
class AlertConfiguration:
    """An alert configuration rule in Ops Manager."""
    id: str
    group_id: str
    event_type_name: str
    enabled: bool = True
    matchers: List[AlertMatcher] = field(default_factory=list)
    notifications: List[AlertNotification] = field(default_factory=list)
    metric_threshold: Optional[AlertMetricThreshold] = None
    created: Optional[str] = None
    updated: Optional[str] = None
    links: List[Link] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AlertConfiguration":
        mt = data.get("metricThreshold")
        return cls(
            id=data.get("id", ""),
            group_id=data.get("groupId", ""),
            event_type_name=data.get("eventTypeName", ""),
            enabled=data.get("enabled", True),
            matchers=[AlertMatcher.from_dict(m) for m in data.get("matchers", [])],
            notifications=[
                AlertNotification.from_dict(n) for n in data.get("notifications", [])
            ],
            metric_threshold=AlertMetricThreshold.from_dict(mt) if mt else None,
            created=data.get("created"),
            updated=data.get("updated"),
            links=[Link.from_dict(l) for l in data.get("links", [])],
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MaintenanceWindow:
    """A scheduled maintenance window."""
    id: str
    group_id: str
    start_date: str
    end_date: str
    description: Optional[str] = None
    alert_type_names: List[str] = field(default_factory=list)
    links: List[Link] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MaintenanceWindow":
        return cls(
            id=data.get("id", ""),
            group_id=data.get("groupId", ""),
            start_date=data.get("startDate", ""),
            end_date=data.get("endDate", ""),
            description=data.get("description"),
            alert_type_names=data.get("alertTypeNames", []),
            links=[Link.from_dict(l) for l in data.get("links", [])],
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LogCollectionJob:
    """A log collection job."""
    id: str = ""
    group_id: str = ""
    user_id: str = ""
    resource_type: str = ""
    resource_name: str = ""
    root_resource_name: str = ""
    root_resource_type: str = ""
    size_requested_per_file_bytes: int = 0
    uncompressed_size_total_bytes: int = 0
    status: str = ""
    creation_date: Optional[str] = None
    expiration_date: Optional[str] = None
    log_collection_from_date: Optional[int] = None
    log_collection_to_date: Optional[int] = None
    redacted: Optional[bool] = None
    log_types: List[str] = field(default_factory=list)
    download_url: Optional[str] = None
    child_jobs: List[Dict[str, Any]] = field(default_factory=list)
    links: List[Link] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LogCollectionJob":
        return cls(
            id=data.get("id", ""),
            group_id=data.get("groupId", ""),
            user_id=data.get("userId", ""),
            resource_type=data.get("resourceType", ""),
            resource_name=data.get("resourceName", ""),
            root_resource_name=data.get("rootResourceName", ""),
            root_resource_type=data.get("rootResourceType", ""),
            size_requested_per_file_bytes=data.get("sizeRequestedPerFileBytes", 0),
            uncompressed_size_total_bytes=data.get("uncompressedSizeTotalBytes", 0),
            status=data.get("status", ""),
            creation_date=data.get("creationDate"),
            expiration_date=data.get("expirationDate"),
            log_collection_from_date=data.get("logCollectionFromDate"),
            log_collection_to_date=data.get("logCollectionToDate"),
            redacted=data.get("redacted"),
            log_types=data.get("logTypes", []),
            download_url=data.get("downloadUrl"),
            child_jobs=data.get("childJobs", []),
            links=[Link.from_dict(l) for l in data.get("links", [])],
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BackupConfig:
    """Backup configuration for a cluster."""
    cluster_id: str
    group_id: str
    status_name: str = ""
    storage_engine_name: str = ""
    auth_mechanism_name: str = ""
    encryption_enabled: bool = False
    ssl_enabled: bool = False
    excluded_namespaces: List[str] = field(default_factory=list)
    sync_source_cluster_id: Optional[str] = None
    links: List[Link] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BackupConfig":
        return cls(
            cluster_id=data.get("clusterId", ""),
            group_id=data.get("groupId", ""),
            status_name=data.get("statusName", ""),
            storage_engine_name=data.get("storageEngineName", ""),
            auth_mechanism_name=data.get("authMechanismName", ""),
            encryption_enabled=data.get("encryptionEnabled", False),
            ssl_enabled=data.get("sslEnabled", False),
            excluded_namespaces=data.get("excludedNamespaces", []),
            sync_source_cluster_id=data.get("syncSourceClusterId"),
            links=[Link.from_dict(l) for l in data.get("links", [])],
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SnapshotSchedule:
    """Snapshot retention schedule for a cluster."""
    cluster_id: str
    group_id: str
    reference_hour_of_day: int = 0
    reference_minute_of_hour: int = 0
    snapshot_interval_hours: int = 6
    snapshot_retention_days: int = 2
    daily_snapshot_retention_days: int = 7
    weekly_snapshot_retention_weeks: int = 4
    monthly_snapshot_retention_months: int = 13
    point_in_time_window_hours: int = 0
    reference_time_zone_offset: str = "+00:00"
    links: List[Link] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SnapshotSchedule":
        return cls(
            cluster_id=data.get("clusterId", ""),
            group_id=data.get("groupId", ""),
            reference_hour_of_day=data.get("referenceHourOfDay", 0),
            reference_minute_of_hour=data.get("referenceMinuteOfHour", 0),
            snapshot_interval_hours=data.get("snapshotIntervalHours", 6),
            snapshot_retention_days=data.get("snapshotRetentionDays", 2),
            daily_snapshot_retention_days=data.get("dailySnapshotRetentionDays", 7),
            weekly_snapshot_retention_weeks=data.get("weeklySnapshotRetentionWeeks", 4),
            monthly_snapshot_retention_months=data.get(
                "monthlySnapshotRetentionMonths", 13
            ),
            point_in_time_window_hours=data.get("pointInTimeWindowHours", 0),
            reference_time_zone_offset=data.get("referenceTimeZoneOffset", "+00:00"),
            links=[Link.from_dict(l) for l in data.get("links", [])],
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RestoreJob:
    """A continuous backup restore job."""
    id: str
    cluster_id: str
    cluster_name: str
    group_id: str
    status_name: str = ""
    delivery_type: str = ""
    delivery_url: Optional[str] = None
    snapshot_id: Optional[str] = None
    created: Optional[str] = None
    finished: Optional[str] = None
    point_in_time: Optional[int] = None
    timestamp: Optional[Dict[str, Any]] = None
    links: List[Link] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RestoreJob":
        return cls(
            id=data.get("id", ""),
            cluster_id=data.get("clusterId", ""),
            cluster_name=data.get("clusterName", ""),
            group_id=data.get("groupId", ""),
            status_name=data.get("statusName", ""),
            delivery_type=data.get("deliveryType", ""),
            delivery_url=data.get("deliveryUrl"),
            snapshot_id=data.get("snapshotId"),
            created=data.get("created"),
            finished=data.get("finished"),
            point_in_time=data.get("pointInTime"),
            timestamp=data.get("timestamp"),
            links=[Link.from_dict(l) for l in data.get("links", [])],
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Checkpoint:
    """A backup checkpoint for a sharded cluster."""
    id: str
    cluster_id: str
    group_id: str
    completed: Optional[str] = None
    created: Optional[str] = None
    timestamp: Optional[Dict[str, Any]] = None
    replica_set_checkpoints: List[Dict[str, Any]] = field(default_factory=list)
    links: List[Link] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Checkpoint":
        return cls(
            id=data.get("id", ""),
            cluster_id=data.get("clusterId", ""),
            group_id=data.get("groupId", ""),
            completed=data.get("completed"),
            created=data.get("created"),
            timestamp=data.get("timestamp"),
            replica_set_checkpoints=data.get("parts", []),
            links=[Link.from_dict(l) for l in data.get("links", [])],
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ServerType:
    """Server type classification for usage reporting."""
    name: str
    label: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ServerType":
        return cls(
            name=data.get("name", ""),
            label=data.get("label", ""),
        )


@dataclass
class HostAssignment:
    """A host assignment record for server usage reporting."""
    hostname: str = ""
    mem_size_mb: int = 0
    group_id: Optional[str] = None
    org_id: Optional[str] = None
    server_type: Optional[ServerType] = None
    links: List[Link] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HostAssignment":
        st = data.get("serverType")
        return cls(
            hostname=data.get("hostname", ""),
            mem_size_mb=data.get("memSizeMB", 0),
            group_id=data.get("groupId"),
            org_id=data.get("orgId"),
            server_type=ServerType.from_dict(st) if st else None,
            links=[Link.from_dict(l) for l in data.get("links", [])],
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Team:
    """An Ops Manager team within an organization."""
    id: str
    name: str
    org_id: Optional[str] = None
    usernames: List[str] = field(default_factory=list)
    links: List[Link] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Team":
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            org_id=data.get("orgId"),
            usernames=data.get("usernames", []),
            links=[Link.from_dict(l) for l in data.get("links", [])],
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class User:
    """An Ops Manager user."""
    id: str
    username: str
    email_address: str
    first_name: str = ""
    last_name: str = ""
    mobile_number: Optional[str] = None
    country: Optional[str] = None
    created: Optional[str] = None
    roles: List[Dict[str, Any]] = field(default_factory=list)
    team_ids: List[str] = field(default_factory=list)
    links: List[Link] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        return cls(
            id=data.get("id", ""),
            username=data.get("username", ""),
            email_address=data.get("emailAddress", ""),
            first_name=data.get("firstName", ""),
            last_name=data.get("lastName", ""),
            mobile_number=data.get("mobileNumber"),
            country=data.get("country"),
            created=data.get("created"),
            roles=data.get("roles", []),
            team_ids=data.get("teamIds", []),
            links=[Link.from_dict(l) for l in data.get("links", [])],
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @property
    def full_name(self) -> str:
        """Return first + last name."""
        return f"{self.first_name} {self.last_name}".strip()


@dataclass
class APIKey:
    """An Ops Manager API key."""
    id: str
    public_key: str
    desc: str = ""
    private_key: Optional[str] = None
    roles: List[Dict[str, Any]] = field(default_factory=list)
    links: List[Link] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "APIKey":
        return cls(
            id=data.get("id", ""),
            public_key=data.get("publicKey", ""),
            desc=data.get("desc", ""),
            private_key=data.get("privateKey"),
            roles=data.get("roles", []),
            links=[Link.from_dict(l) for l in data.get("links", [])],
        )

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d.pop("private_key", None)
        return d


@dataclass
class AgentAPIKey:
    """An agent API key for a project."""
    id: str
    agent_api_key: str
    desc: str = ""
    created_ip_addr: str = ""
    created_user_id: str = ""
    created_by: str = ""
    created: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentAPIKey":
        return cls(
            id=data.get("_id", data.get("id", "")),
            agent_api_key=data.get("agentApiKey", ""),
            desc=data.get("desc", ""),
            created_ip_addr=data.get("createdIpAddr", ""),
            created_user_id=data.get("createdUserId", ""),
            created_by=data.get("createdBy", ""),
            created=data.get("created"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AgentVersions:
    """Agent version information for a project."""
    count: int = 0
    is_any_agent_not_managed: bool = False
    is_any_agent_version_deprecated: bool = False
    is_any_agent_version_old: bool = False
    automation_agent_version: Optional[str] = None
    bi_connector_version: Optional[str] = None
    links: List[Link] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentVersions":
        return cls(
            count=data.get("count", 0),
            is_any_agent_not_managed=data.get("isAnyAgentNotManaged", False),
            is_any_agent_version_deprecated=data.get(
                "isAnyAgentVersionDeprecated", False
            ),
            is_any_agent_version_old=data.get("isAnyAgentVersionOld", False),
            automation_agent_version=data.get("automationAgentVersion"),
            bi_connector_version=data.get("biConnectorVersion"),
            links=[Link.from_dict(l) for l in data.get("links", [])],
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FeaturePolicy:
    """Feature control policy configuration for a project."""
    external_management_system: Optional[Dict[str, Any]] = None
    policies: List[Dict[str, Any]] = field(default_factory=list)
    links: List[Link] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FeaturePolicy":
        return cls(
            external_management_system=data.get("externalManagementSystem"),
            policies=data.get("policies", []),
            links=[Link.from_dict(l) for l in data.get("links", [])],
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ConnectionStatus:
    """Live data migration connection status for an organization."""
    status: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConnectionStatus":
        return cls(
            status=data.get("status", ""),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AdminBackupConfig:
    """Base configuration for admin backup stores."""
    id: str = ""
    uri: str = ""
    write_concern: str = ""
    labels: List[str] = field(default_factory=list)
    ssl: bool = False
    assignment_enabled: bool = False
    encrypted_credentials: bool = False
    used_size: int = 0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AdminBackupConfig":
        return cls(
            id=data.get("id", ""),
            uri=data.get("uri", ""),
            write_concern=data.get("writeConcern", ""),
            labels=data.get("labels", []),
            ssl=data.get("ssl", False),
            assignment_enabled=data.get("assignmentEnabled", False),
            encrypted_credentials=data.get("encryptedCredentials", False),
            used_size=data.get("usedSize", 0),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BackupStore:
    """MongoDB backup store (blockstore, oplog, or sync)."""
    id: str = ""
    uri: str = ""
    write_concern: str = ""
    labels: List[str] = field(default_factory=list)
    ssl: bool = False
    assignment_enabled: bool = False
    encrypted_credentials: bool = False
    used_size: int = 0
    load_factor: int = 0
    max_capacity_gb: int = 0
    provisioned: bool = False
    sync_source: str = ""
    username: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BackupStore":
        return cls(
            id=data.get("id", ""),
            uri=data.get("uri", ""),
            write_concern=data.get("writeConcern", ""),
            labels=data.get("labels", []),
            ssl=data.get("ssl", False),
            assignment_enabled=data.get("assignmentEnabled", False),
            encrypted_credentials=data.get("encryptedCredentials", False),
            used_size=data.get("usedSize", 0),
            load_factor=data.get("loadFactor", 0),
            max_capacity_gb=data.get("maxCapacityGB", 0),
            provisioned=data.get("provisioned", False),
            sync_source=data.get("syncSource", ""),
            username=data.get("username", ""),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class S3BlockstoreConfig:
    """S3-compatible backup blockstore configuration."""
    id: str = ""
    uri: str = ""
    write_concern: str = ""
    labels: List[str] = field(default_factory=list)
    ssl: bool = False
    assignment_enabled: bool = False
    encrypted_credentials: bool = False
    used_size: int = 0
    load_factor: int = 0
    max_capacity_gb: int = 0
    provisioned: bool = False
    sync_source: str = ""
    username: str = ""
    aws_access_key: str = ""
    s3_auth_method: str = ""
    s3_bucket_endpoint: str = ""
    s3_bucket_name: str = ""
    s3_max_connections: int = 0
    disable_proxy_s3: bool = False
    accepted_tos: bool = False
    sse_enabled: bool = False
    path_style_access_enabled: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "S3BlockstoreConfig":
        return cls(
            id=data.get("id", ""),
            uri=data.get("uri", ""),
            write_concern=data.get("writeConcern", ""),
            labels=data.get("labels", []),
            ssl=data.get("ssl", False),
            assignment_enabled=data.get("assignmentEnabled", False),
            encrypted_credentials=data.get("encryptedCredentials", False),
            used_size=data.get("usedSize", 0),
            load_factor=data.get("loadFactor", 0),
            max_capacity_gb=data.get("maxCapacityGB", 0),
            provisioned=data.get("provisioned", False),
            sync_source=data.get("syncSource", ""),
            username=data.get("username", ""),
            aws_access_key=data.get("awsAccessKey", ""),
            s3_auth_method=data.get("s3AuthMethod", ""),
            s3_bucket_endpoint=data.get("s3BucketEndpoint", ""),
            s3_bucket_name=data.get("s3BucketName", ""),
            s3_max_connections=data.get("s3MaxConnections", 0),
            disable_proxy_s3=data.get("disableProxyS3", False),
            accepted_tos=data.get("acceptedTos", False),
            sse_enabled=data.get("sseEnabled", False),
            path_style_access_enabled=data.get("pathStyleAccessEnabled", False),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FileSystemStoreConfig:
    """File system backup store configuration."""
    id: str = ""
    uri: str = ""
    write_concern: str = ""
    labels: List[str] = field(default_factory=list)
    ssl: bool = False
    assignment_enabled: bool = False
    encrypted_credentials: bool = False
    used_size: int = 0
    load_factor: int = 0
    max_capacity_gb: int = 0
    provisioned: bool = False
    sync_source: str = ""
    username: str = ""
    mmapv1_compression_setting: str = ""
    store_path: str = ""
    wt_compression_setting: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FileSystemStoreConfig":
        return cls(
            id=data.get("id", ""),
            uri=data.get("uri", ""),
            write_concern=data.get("writeConcern", ""),
            labels=data.get("labels", []),
            ssl=data.get("ssl", False),
            assignment_enabled=data.get("assignmentEnabled", False),
            encrypted_credentials=data.get("encryptedCredentials", False),
            used_size=data.get("usedSize", 0),
            load_factor=data.get("loadFactor", 0),
            max_capacity_gb=data.get("maxCapacityGB", 0),
            provisioned=data.get("provisioned", False),
            sync_source=data.get("syncSource", ""),
            username=data.get("username", ""),
            mmapv1_compression_setting=data.get("mmapv1CompressionSetting", ""),
            store_path=data.get("storePath", ""),
            wt_compression_setting=data.get("wtCompressionSetting", ""),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DaemonConfig:
    """Backup daemon configuration."""
    id: str = ""
    uri: str = ""
    write_concern: str = ""
    labels: List[str] = field(default_factory=list)
    ssl: bool = False
    assignment_enabled: bool = False
    encrypted_credentials: bool = False
    used_size: int = 0
    backup_jobs_enabled: bool = False
    configured: bool = False
    garbage_collection_enabled: bool = False
    resource_usage_enabled: bool = False
    restore_queryable_jobs_enabled: bool = False
    head_disk_type: str = ""
    num_workers: int = 0
    machine: str = ""
    head_root_directory: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DaemonConfig":
        machine_data = data.get("machine", {})
        return cls(
            id=data.get("id", ""),
            uri=data.get("uri", ""),
            write_concern=data.get("writeConcern", ""),
            labels=data.get("labels", []),
            ssl=data.get("ssl", False),
            assignment_enabled=data.get("assignmentEnabled", False),
            encrypted_credentials=data.get("encryptedCredentials", False),
            used_size=data.get("usedSize", 0),
            backup_jobs_enabled=data.get("backupJobsEnabled", False),
            configured=data.get("configured", False),
            garbage_collection_enabled=data.get("garbageCollectionEnabled", False),
            resource_usage_enabled=data.get("resourceUsageEnabled", False),
            restore_queryable_jobs_enabled=data.get("restoreQueryableJobsEnabled", False),
            head_disk_type=data.get("headDiskType", ""),
            num_workers=data.get("numWorkers", 0),
            machine=machine_data.get("machine", "") if isinstance(machine_data, dict) else str(machine_data),
            head_root_directory=machine_data.get("headRootDirectory", "") if isinstance(machine_data, dict) else "",
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ProjectJobConfig:
    """Admin backup project job configuration."""
    id: str = ""
    uri: str = ""
    write_concern: str = ""
    labels: List[str] = field(default_factory=list)
    ssl: bool = False
    assignment_enabled: bool = False
    encrypted_credentials: bool = False
    used_size: int = 0
    kmip_client_cert_path: str = ""
    label_filter: List[str] = field(default_factory=list)
    sync_store_filter: List[str] = field(default_factory=list)
    daemon_filter: List[str] = field(default_factory=list)
    oplog_store_filter: List[str] = field(default_factory=list)
    snapshot_store_filter: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectJobConfig":
        return cls(
            id=data.get("id", ""),
            uri=data.get("uri", ""),
            write_concern=data.get("writeConcern", ""),
            labels=data.get("labels", []),
            ssl=data.get("ssl", False),
            assignment_enabled=data.get("assignmentEnabled", False),
            encrypted_credentials=data.get("encryptedCredentials", False),
            used_size=data.get("usedSize", 0),
            kmip_client_cert_path=data.get("kmipClientCertPath", ""),
            label_filter=data.get("labelFilter", []),
            sync_store_filter=data.get("syncStoreFilter", []),
            daemon_filter=data.get("daemonFilter", []),
            oplog_store_filter=data.get("oplogStoreFilter", []),
            snapshot_store_filter=data.get("snapshotStoreFilter", []),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class GlobalWhitelistAPIKey:
    """Global API key whitelist entry (IP access list)."""
    id: str = ""
    cidr_block: str = ""
    created: str = ""
    description: str = ""
    type: str = ""
    updated: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GlobalWhitelistAPIKey":
        return cls(
            id=data.get("id", ""),
            cidr_block=data.get("cidrBlock", ""),
            created=data.get("created", ""),
            description=data.get("description", ""),
            type=data.get("type", ""),
            updated=data.get("updated", ""),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


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
