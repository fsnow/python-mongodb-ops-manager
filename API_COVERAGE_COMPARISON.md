# API Coverage Comparison: Python vs Go Client Libraries

**Compared:** 2026-03-28
- **Python:** `fsnow/python-mongodb-ops-manager`
- **Go:** `mongodb/go-client-mongodb-ops-manager`

---

## Executive Summary

The Python library covers approximately **18% of the Go library's API surface**. Of 33 Go services and ~175 methods, Python implements 9 services with ~32 equivalent methods. Four services have full coverage; five have partial coverage; **24 services are entirely absent** from Python.

| Metric | Count |
|---|---|
| Total Go services | 33 |
| Total Python services | 9 |
| Go services fully covered in Python | 4 |
| Go services partially covered in Python | 5 |
| Go services entirely missing from Python | **24** |
| Total Go methods | ~175 |
| Go methods with Python equivalent | ~32 |
| Go methods missing from Python | **~143** |
| **Python coverage of Go API** | **~18%** |

---

## Coverage Summary by Service

| Service Area | Go Methods | Python Coverage | Status |
|---|---|---|---|
| Clusters | 3 | 3 | ✅ Full |
| Measurements | 3 | 3 | ✅ Full |
| Alerts | 3 | 3 | ✅ Full |
| Performance Advisor | 3 | 3 | ✅ Full |
| Organizations | 12 | 3 | ⚠️ Partial |
| Projects | 15 | 3 | ⚠️ Partial |
| Deployments | 10 | 7 | ⚠️ Partial |
| Agents | 7 | 1 | ⚠️ Partial |
| Backup Configs / Snapshots | 6 | 2 | ⚠️ Partial |
| Alert Configurations | 8 | 0 | ❌ Missing |
| Automation | 6 | 0 | ❌ Missing |
| Org API Keys | 5 | 0 | ❌ Missing |
| Project API Keys | 4 | 0 | ❌ Missing |
| Access List API Keys | 4 | 0 | ❌ Missing |
| Global API Keys | 5 | 0 | ❌ Missing |
| Global API Key Whitelists | 4 | 0 | ❌ Missing |
| Teams | 11 | 0 | ❌ Missing |
| Users | 4 | 0 | ❌ Missing |
| Events | 4 | 0 | ❌ Missing |
| Continuous Restore Jobs | 3 | 0 | ❌ Missing |
| Checkpoints | 2 | 0 | ❌ Missing |
| Snapshot Schedule | 2 | 0 | ❌ Missing |
| Maintenance Windows | 5 | 0 | ❌ Missing |
| Log Download | 1 | 0 | ❌ Missing |
| Log Collection Jobs | 6 | 0 | ❌ Missing |
| Diagnostics | 1 | 0 | ❌ Missing |
| Feature Control Policies | 3 | 0 | ❌ Missing |
| Version Manifest | 2 | 0 | ❌ Missing |
| Blockstore Config (Admin) | 5 | 0 | ❌ Missing |
| File System Store Config (Admin) | 5 | 0 | ❌ Missing |
| S3 Blockstore Config (Admin) | 5 | 0 | ❌ Missing |
| Oplog Store Config (Admin) | 5 | 0 | ❌ Missing |
| Sync Store Config (Admin) | 5 | 0 | ❌ Missing |
| Daemon Config (Admin) | 4 | 0 | ❌ Missing |
| Project Job Config (Admin) | 3 | 0 | ❌ Missing |
| Server Usage | 9 | 0 | ❌ Missing |
| Live Data Migration | 3 | 0 | ❌ Missing |
| Unauth Users | 1 | 0 | ❌ Missing |
| Global Alerts | 3 | 0 | ❌ Missing |
| Service Version | 1 | 0 | ❌ Missing |

---

## Fully Covered Services (4)

These Go services have complete Python equivalents.

### Clusters
| Go Method | Python Method | Path |
|---|---|---|
| `List` | `clusters.list` | GET `groups/{id}/clusters` |
| `Get` | `clusters.get` | GET `groups/{id}/clusters/{id}` |
| `ListAll` | `clusters.list_all` | GET `clusters` |

### Measurements
| Go Method | Python Method | Path |
|---|---|---|
| `Host` | `measurements.host` | GET `groups/{id}/hosts/{id}/measurements` |
| `Disk` | `measurements.disk` | GET `groups/{id}/hosts/{id}/disks/{name}/measurements` |
| `Database` | `measurements.database` | GET `groups/{id}/hosts/{id}/databases/{name}/measurements` |

> Python also has convenience methods not in Go: `get_opcounters`, `get_query_targeting`, `get_replication_metrics`.

### Alerts
| Go Method | Python Method | Path |
|---|---|---|
| `List` | `alerts.list` | GET `groups/{id}/alerts` |
| `Get` | `alerts.get` | GET `groups/{id}/alerts/{id}` |
| `Acknowledge` | `alerts.acknowledge` | PATCH `groups/{id}/alerts/{id}` |

> Python also has `list_open` convenience method not in Go.

### Performance Advisor
| Go Method | Python Method | Path |
|---|---|---|
| `GetNamespaces` | `performance_advisor.get_namespaces` | GET `.../performanceAdvisor/namespaces` |
| `GetSlowQueries` | `performance_advisor.get_slow_queries` | GET `.../performanceAdvisor/slowQueryLogs` |
| `GetSuggestedIndexes` | `performance_advisor.get_suggested_indexes` | GET `.../performanceAdvisor/suggestedIndexes` |

> Python also has `get_all_suggestions_for_cluster` convenience method not in Go.

---

## Partially Covered Services (5)

### Organizations

| Go Method | Python Equivalent | Status |
|---|---|---|
| `List` | `organizations.list` | ✅ |
| `Get` | `organizations.get` | ✅ |
| `Projects` | `organizations.list_projects` | ✅ |
| `ListUsers` | — | ❌ GET `orgs/{id}/users` |
| `Create` | — | ❌ POST `orgs` |
| `Delete` | — | ❌ DELETE `orgs/{id}` |
| `Invitations` | — | ❌ GET `orgs/{id}/invitations` |
| `Invitation` | — | ❌ GET `orgs/{id}/invitations/{id}` |
| `InviteUser` | — | ❌ POST `orgs/{id}/invitations` |
| `UpdateInvitation` | — | ❌ PATCH `orgs/{id}/invitations` |
| `UpdateInvitationByID` | — | ❌ PATCH `orgs/{id}/invitations/{id}` |
| `DeleteInvitation` | — | ❌ DELETE `orgs/{id}/invitations/{id}` |

### Projects

| Go Method | Python Equivalent | Status |
|---|---|---|
| `List` | `projects.list` | ✅ |
| `Get` | `projects.get` | ✅ |
| `GetByName` | `projects.get_by_name` | ✅ |
| `ListUsers` | — | ❌ GET `groups/{id}/users` |
| `Create` | — | ❌ POST `groups` |
| `Delete` | — | ❌ DELETE `groups/{id}` |
| `RemoveUser` | — | ❌ DELETE `groups/{id}/users/{id}` |
| `AddTeamsToProject` | — | ❌ POST `groups/{id}/teams` |
| `GetTeams` | — | ❌ GET `groups/{id}/teams` |
| `Invitations` | — | ❌ GET `groups/{id}/invitations` |
| `Invitation` | — | ❌ GET `groups/{id}/invitations/{id}` |
| `InviteUser` | — | ❌ POST `groups/{id}/invitations` |
| `UpdateInvitation` | — | ❌ PATCH `groups/{id}/invitations` |
| `UpdateInvitationByID` | — | ❌ PATCH `groups/{id}/invitations/{id}` |
| `DeleteInvitation` | — | ❌ DELETE `groups/{id}/invitations/{id}` |

### Deployments (Hosts, Databases, Disks)

| Go Method | Python Equivalent | Status |
|---|---|---|
| `ListHosts` | `deployments.list_hosts` | ✅ |
| `GetHost` | `deployments.get_host` | ✅ |
| `GetHostByHostname` | `deployments.get_host_by_name` | ✅ |
| `ListPartitions` | `deployments.list_disks` | ✅ |
| `GetPartition` | `deployments.get_disk` | ✅ |
| `ListDatabases` | `deployments.list_databases` | ✅ |
| `GetDatabase` | `deployments.get_database` | ✅ |
| `StartMonitoring` | — | ❌ POST `groups/{id}/hosts` |
| `UpdateMonitoring` | — | ❌ PATCH `groups/{id}/hosts/{id}` |
| `StopMonitoring` | — | ❌ DELETE `groups/{id}/hosts/{id}` |

### Agents

| Go Method | Python Equivalent | Status |
|---|---|---|
| `ListAgentsByType` | `agents.list` | ✅ |
| `ListAgentLinks` | — | ❌ GET `groups/{id}/agents` |
| `CreateAgentAPIKey` | — | ❌ POST `groups/{id}/agentapikeys` |
| `ListAgentAPIKeys` | — | ❌ GET `groups/{id}/agentapikeys` |
| `DeleteAgentAPIKey` | — | ❌ DELETE `groups/{id}/agentapikeys/{id}` |
| `GlobalVersions` | — | ❌ GET `agents/versions` |
| `ProjectVersions` | — | ❌ GET `groups/{id}/agents/versions` |

### Backup Configs & Continuous Snapshots

| Go Method | Python Equivalent | Status |
|---|---|---|
| `ContinuousSnapshots.List` | `backup.list_snapshots` | ✅ |
| `ContinuousSnapshots.Get` | `backup.get_snapshot` | ✅ |
| `BackupConfigs.Get` | `backup.get_backup_config` | ✅ |
| `ContinuousSnapshots.ChangeExpiry` | — | ❌ PATCH `groups/{id}/clusters/{id}/snapshots/{id}` |
| `ContinuousSnapshots.Delete` | — | ❌ DELETE `groups/{id}/clusters/{id}/snapshots/{id}` |
| `BackupConfigs.List` | — | ❌ GET `groups/{id}/backupConfigs` |
| `BackupConfigs.Update` | — | ❌ PATCH `groups/{id}/backupConfigs/{id}` |

---

## Entirely Missing Services (24)

### Alert Configurations
Full CRUD for alert configuration rules — entirely absent from Python.

| Method | Verb | Path |
|---|---|---|
| `List` | GET | `groups/{id}/alertConfigs` |
| `GetAnAlertConfig` | GET | `groups/{id}/alertConfigs/{id}` |
| `Create` | POST | `groups/{id}/alertConfigs` |
| `Update` | PUT | `groups/{id}/alertConfigs/{id}` |
| `EnableAnAlertConfig` | PATCH | `groups/{id}/alertConfigs/{id}` |
| `Delete` | DELETE | `groups/{id}/alertConfigs/{id}` |
| `GetOpenAlertsConfig` | GET | `groups/{id}/alertConfigs/{id}/alerts` |
| `ListMatcherFields` | GET | `alertConfigs/matchers/fieldNames` |

### Automation
Core Ops Manager feature for cluster deployment management — entirely absent from Python.

| Method | Verb | Path |
|---|---|---|
| `GetConfig` | GET | `groups/{id}/automationConfig` |
| `UpdateConfig` | PUT | `groups/{id}/automationConfig` |
| `UpdateAgentVersion` | POST | `groups/{id}/automationConfig/updateAgentVersion` |
| `GetBackupAgentConfig` | GET | `groups/{id}/backupAgentConfig` |
| `GetMonitoringAgentConfig` | GET | `groups/{id}/monitoringAgentConfig` |
| `GetStatus` | GET | `groups/{id}/automationStatus` |

### Teams
Full team management — entirely absent from Python.

| Method | Verb | Path |
|---|---|---|
| `List` | GET | `orgs/{id}/teams` |
| `Get` | GET | `orgs/{id}/teams/{id}` |
| `GetOneTeamByName` | GET | `orgs/{id}/teams/byName/{name}` |
| `GetTeamUsersAssigned` | GET | `orgs/{id}/teams/{id}/users` |
| `Create` | POST | `orgs/{id}/teams` |
| `Rename` | PATCH | `orgs/{id}/teams/{id}` |
| `UpdateTeamRoles` | PATCH | `groups/{id}/teams/{id}` |
| `AddUsersToTeam` | POST | `orgs/{id}/teams/{id}/users` |
| `RemoveUserToTeam` | DELETE | `orgs/{id}/teams/{id}/users/{id}` |
| `RemoveTeamFromOrganization` | DELETE | `orgs/{id}/teams/{id}` |
| `RemoveTeamFromProject` | DELETE | `groups/{id}/teams/{id}` |

### Users
User management — entirely absent from Python.

| Method | Verb | Path |
|---|---|---|
| `Get` | GET | `users/{id}` |
| `GetByName` | GET | `users/byName/{username}` |
| `Create` | POST | `users` |
| `Delete` | DELETE | `users/{id}` |

### Events
Org and project event log access — entirely absent from Python.

| Method | Verb | Path |
|---|---|---|
| `ListOrganizationEvents` | GET | `orgs/{id}/events` |
| `GetOrganizationEvent` | GET | `orgs/{id}/events/{id}` |
| `ListProjectEvents` | GET | `groups/{id}/events` |
| `GetProjectEvent` | GET | `groups/{id}/events/{id}` |

### Continuous Restore Jobs
Restore job management — entirely absent from Python.

| Method | Verb | Path |
|---|---|---|
| `List` | GET | `groups/{id}/clusters/{id}/restoreJobs` |
| `Get` | GET | `groups/{id}/clusters/{id}/restoreJobs/{id}` |
| `Create` | POST | `groups/{id}/clusters/{id}/restoreJobs` |

### Checkpoints
Backup checkpoints — entirely absent from Python.

| Method | Verb | Path |
|---|---|---|
| `List` | GET | `groups/{id}/clusters/{id}/checkpoints` |
| `Get` | GET | `groups/{id}/clusters/{id}/checkpoints/{id}` |

### Snapshot Schedule
Snapshot retention scheduling — entirely absent from Python.

| Method | Verb | Path |
|---|---|---|
| `Get` | GET | `groups/{id}/backupConfigs/{id}/snapshotSchedule` |
| `Update` | PATCH | `groups/{id}/backupConfigs/{id}/snapshotSchedule` |

### Maintenance Windows

| Method | Verb | Path |
|---|---|---|
| `List` | GET | `groups/{id}/maintenanceWindows` |
| `Get` | GET | `groups/{id}/maintenanceWindows/{id}` |
| `Create` | POST | `groups/{id}/maintenanceWindows` |
| `Update` | PATCH | `groups/{id}/maintenanceWindows/{id}` |
| `Delete` | DELETE | `groups/{id}/maintenanceWindows/{id}` |

### Log Download

| Method | Verb | Path |
|---|---|---|
| `Download` | GET | `groups/{id}/clusters/{hostname}/logs/{logName}` |

### Log Collection Jobs

| Method | Verb | Path |
|---|---|---|
| `List` | GET | `groups/{id}/logCollectionJobs` |
| `Get` | GET | `groups/{id}/logCollectionJobs/{id}` |
| `Create` | POST | `groups/{id}/logCollectionJobs` |
| `Extend` | PATCH | `groups/{id}/logCollectionJobs/{id}` |
| `Retry` | PUT | `groups/{id}/logCollectionJobs/{id}/retry` |
| `Delete` | DELETE | `groups/{id}/logCollectionJobs/{id}` |

### Diagnostics

| Method | Verb | Path |
|---|---|---|
| `Get` | GET | `groups/{id}/diagnostics` (returns gzip archive) |

### Feature Control Policies

| Method | Verb | Path |
|---|---|---|
| `List` | GET | `groups/{id}/controlledFeature` |
| `Update` | PUT | `groups/{id}/controlledFeature` |
| `ListSupportedPolicies` | GET | `groups/{id}/controlledFeature/externalManagementSystem/config` |

### Version Manifest

| Method | Verb | Path |
|---|---|---|
| `Get` | GET | `static/version_manifest/{version}` |
| `Update` | PUT | `versionManifest` |

### Org API Keys

| Method | Verb | Path |
|---|---|---|
| `List` | GET | `orgs/{id}/apiKeys` |
| `Get` | GET | `orgs/{id}/apiKeys/{id}` |
| `Create` | POST | `orgs/{id}/apiKeys` |
| `Update` | PATCH | `orgs/{id}/apiKeys/{id}` |
| `Delete` | DELETE | `orgs/{id}/apiKeys/{id}` |

### Project API Keys

| Method | Verb | Path |
|---|---|---|
| `List` | GET | `groups/{id}/apiKeys` |
| `Create` | POST | `groups/{id}/apiKeys` |
| `Assign` | PATCH | `groups/{id}/apiKeys/{id}` |
| `Unassign` | DELETE | `groups/{id}/apiKeys/{id}` |

### Access List API Keys (Org)

| Method | Verb | Path |
|---|---|---|
| `List` | GET | `orgs/{id}/apiKeys/{id}/accessList` |
| `Get` | GET | `orgs/{id}/apiKeys/{id}/accessList/{ip}` |
| `Create` | POST | `orgs/{id}/apiKeys/{id}/accessList` |
| `Delete` | DELETE | `orgs/{id}/apiKeys/{id}/accessList/{ip}` |

### Global API Keys (Admin)

| Method | Verb | Path |
|---|---|---|
| `List` | GET | `admin/apiKeys` |
| `Get` | GET | `admin/apiKeys/{id}` |
| `Create` | POST | `admin/apiKeys` |
| `Update` | PATCH | `admin/apiKeys/{id}` |
| `Delete` | DELETE | `admin/apiKeys/{id}` |

### Global API Key Whitelists (Admin)

| Method | Verb | Path |
|---|---|---|
| `List` | GET | `admin/whitelist` |
| `Get` | GET | `admin/whitelist/{ip}` |
| `Create` | POST | `admin/whitelist` |
| `Delete` | DELETE | `admin/whitelist/{ip}` |

### Global Alerts

| Method | Verb | Path |
|---|---|---|
| `List` | GET | `globalAlerts` |
| `Get` | GET | `globalAlerts/{id}` |
| `Acknowledge` | PATCH | `globalAlerts/{id}` |

### Admin Backup Store Configs
Five separate admin services for configuring backup storage backends — all entirely absent from Python.

| Service | Base Path |
|---|---|
| BlockstoreConfigService | `admin/backup/snapshot/mongoConfigs` |
| FileSystemStoreConfigService | `admin/backup/snapshot/fileSystemConfigs` |
| S3BlockstoreConfigService | `admin/backup/snapshot/s3Configs` |
| OplogStoreConfigService | `admin/backup/oplog/mongoConfigs` |
| SyncStoreConfigService | `admin/backup/sync/mongoConfigs` |
| DaemonConfigService | `admin/backup/daemon/configs` |

Each supports: List, Get, Create, Update, Delete.

### Project Job Config (Admin)

| Method | Verb | Path |
|---|---|---|
| `List` | GET | `admin/backup/configs` |
| `Get` | GET | `admin/backup/configs/{groupID}` |
| `Update` | PUT | `admin/backup/configs/{groupID}` |

### Server Usage

| Method | Verb | Path |
|---|---|---|
| `GenerateDailyUsageSnapshot` | POST | `usage/dailyCapture` |
| `ListAllHostAssignment` | GET | `usage/assignments` |
| `ProjectHostAssignments` | GET | `usage/assignments/groups/{id}` |
| `OrganizationHostAssignments` | GET | `usage/assignments/orgs/{id}` |
| `GetServerTypeProject` | GET | `usage/groups/{id}/serverType` |
| `GetServerTypeOrganization` | GET | `usage/orgs/{id}/serverType` |
| `UpdateProjectServerType` | PUT | `usage/groups/{id}/serverType` |
| `UpdateOrganizationServerType` | PUT | `usage/orgs/{id}/serverType` |
| `Download` (report) | GET | `usage/report/download` |

### Live Data Migration

| Method | Verb | Path |
|---|---|---|
| `ConnectOrganizations` | POST | `orgs/{id}/liveExport/migrationLink` |
| `DeleteConnection` | DELETE | `orgs/{id}/liveExport/migrationLink` |
| `ConnectionStatus` | GET | `orgs/{id}/liveExport/migrationLink` |

### Unauth Users

| Method | Verb | Path |
|---|---|---|
| `CreateFirstUser` | POST | `unauth/users` |

### Service Version

| Method | Verb | Path |
|---|---|---|
| `Get` | GET | `api/private/unauth/version` |

---

## Python-Only Methods (Not in Go)

The Python library adds convenience/iterator methods beyond the Go API:

| Python Method | Service | Notes |
|---|---|---|
| `list_iter` (8 variants) | organizations, projects, clusters, deployments, alerts, agents, backup | Lazy pagination iterators |
| `list_all_iter` | clusters | Paginated iterator for global cluster list |
| `list_open` | alerts | `list` filtered to `status=OPEN` |
| `list_monitoring` | agents | `list` with `agent_type="MONITORING"` |
| `list_backup` | agents | `list` with `agent_type="BACKUP"` |
| `get_opcounters` | measurements | `host` filtered to opcounter metrics |
| `get_query_targeting` | measurements | `host` filtered to query targeting metrics |
| `get_replication_metrics` | measurements | `host` filtered to replication metrics |
| `get_primaries` | deployments | `list_hosts` filtered to `REPLICA_PRIMARY` |
| `get_mongos_hosts` | deployments | `list_hosts` filtered to `SHARD_MONGOS` |
| `get_all_suggestions_for_cluster` | performance_advisor | Aggregates `get_suggested_indexes` across all hosts |

---

## Recommended Implementation Priority

Based on importance and usage frequency:

### Priority 1 — Core Functionality Gaps
1. **Automation** (`automationConfig`, `automationStatus`) — This is Ops Manager's primary feature; its absence is the largest functional gap
2. **Alert Configurations** — Complements the existing Alerts service; full CRUD for alert rules
3. **Continuous Restore Jobs** — Completes the backup story alongside existing snapshot support
4. **Snapshot Schedule** — Completes the backup story (expiry/retention config)

### Priority 2 — User & Access Management
5. **Users** — Basic user CRUD
6. **Teams** — Org team management
7. **Org Invitations** — Already partially stubbed in Organizations
8. **Org API Keys / Project API Keys** — Programmatic API key management
9. **Access List API Keys** — IP allowlisting for API keys

### Priority 3 — Observability & Operations
10. **Events** — Audit log / event stream for orgs and projects
11. **Maintenance Windows** — Operational scheduling
12. **Log Download** — Single log file download
13. **Log Collection Jobs** — Managed log collection
14. **Diagnostics** — Diagnostic archive download
15. **Monitoring write operations** (`StartMonitoring`, `UpdateMonitoring`, `StopMonitoring`)

### Priority 4 — Admin / Infrastructure
16. **Admin Backup Store Configs** (Blockstore, S3, FileSystem, Oplog, Sync, Daemon)
17. **Global Alerts**
18. **Global API Keys / Whitelists**
19. **Server Usage**
20. **Feature Control Policies**
21. **Live Data Migration**
22. **Version Manifest**
