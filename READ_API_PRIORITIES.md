# Read API Implementation Priorities

**Context:** Read-only (GET) operations only. Prioritized for a banking client using the library for diagnostics and reporting — not administration.

**Methodology:** Sourced directly from the Go client source files in `mongodb/go-client-mongodb-ops-manager/opsmngr/`. Each entry includes the exact Go method name, receiver type, and URL path as found in the source.

---

## Already Implemented (Reference)

The following read operations are already in the Python library and require no action:

| Service | Python Method | API Path |
|---|---|---|
| Organizations | `list`, `get`, `list_projects` | `orgs`, `orgs/{id}`, `orgs/{id}/groups` |
| Projects | `list`, `get`, `get_by_name` | `groups`, `groups/{id}`, `groups/byName/{name}` |
| Clusters | `list`, `get`, `list_all` | `groups/{id}/clusters`, `clusters` |
| Deployments | `list_hosts`, `get_host`, `get_host_by_name` | `groups/{id}/hosts/...` |
| Deployments | `list_disks`, `get_disk`, `list_databases`, `get_database` | `groups/{id}/hosts/{id}/disks/...`, `.../databases/...` |
| Measurements | `host`, `disk`, `database` | `groups/{id}/hosts/{id}/measurements`, etc. |
| Alerts | `list`, `get` | `groups/{id}/alerts`, `groups/{id}/alerts/{id}` |
| Performance Advisor | `get_namespaces`, `get_slow_queries`, `get_suggested_indexes` | `groups/{id}/hosts/{id}/performanceAdvisor/...` |
| Agents | `list` (by type) | `groups/{id}/agents/{agentType}` |
| Backup | `list_snapshots`, `get_snapshot`, `get_backup_config` | `groups/{id}/clusters/{id}/snapshots/...`, `groups/{id}/backupConfigs/{id}` |

---

## Tier 1 — Critical for Banking Diagnostics & Reporting

These endpoints are directly required for compliance reporting, audit trails, incident investigation, and governance documentation — all high-priority concerns for a financial institution.

---

### 1. Events (Audit Log)
**Why:** The audit log is the most critical missing feature for a bank. Events capture every action taken in Ops Manager — configuration changes, user logins, alert triggers, backup events, etc. Essential for SOX, PCI-DSS, and internal audit requirements.

| Go Method | Receiver | API Path |
|---|---|---|
| `ListOrganizationEvents` | `*EventsServiceOp` | GET `api/public/v1.0/orgs/{orgID}/events` |
| `GetOrganizationEvent` | `*EventsServiceOp` | GET `api/public/v1.0/orgs/{orgID}/events/{eventID}` |
| `ListProjectEvents` | `*EventsServiceOp` | GET `api/public/v1.0/groups/{groupID}/events` |
| `GetProjectEvent` | `*EventsServiceOp` | GET `api/public/v1.0/groups/{groupID}/events/{eventID}` |

**Note:** Go's `ListOrganizationEvents` and `ListProjectEvents` accept an `*EventListOptions` struct that supports date range filtering — important for time-scoped compliance queries.

---

### 2. Automation Status
**Why:** Shows whether every agent in every project has applied the current automation configuration. Critical for confirming that security and configuration policies are actually in effect across the fleet — not just defined.

| Go Method | Receiver | API Path |
|---|---|---|
| `GetStatus` | `*AutomationServiceOp` | GET `api/public/v1.0/groups/{groupID}/automationStatus` |

---

### 3. Automation Config (Read)
**Why:** The automation config is the complete source of truth for cluster topology, MongoDB versions, TLS settings, authentication configuration, and more. Essential for configuration compliance reporting ("what version is this cluster running?", "is auth enabled?", "what TLS mode?").

| Go Method | Receiver | API Path |
|---|---|---|
| `GetConfig` | `*AutomationServiceOp` | GET `api/public/v1.0/groups/{groupID}/automationConfig` |
| `GetBackupAgentConfig` | `*AutomationServiceOp` | GET `api/public/v1.0/groups/{groupID}/automationConfig/backupAgentConfig` |
| `GetMonitoringAgentConfig` | `*AutomationServiceOp` | GET `api/public/v1.0/groups/{groupID}/automationConfig/monitoringAgentConfig` |

---

### 4. Alert Configurations (Reads)
**Why:** Answers "what are our alerting thresholds and rules?" — a governance and compliance question. Also powers reporting on alert coverage gaps ("which clusters have no alert configured for X?"). Complements the existing Alerts service.

| Go Method | Receiver | API Path |
|---|---|---|
| `List` | `*AlertConfigurationsServiceOp` | GET `api/public/v1.0/groups/{groupID}/alertConfigs` |
| `GetAnAlertConfig` | `*AlertConfigurationsServiceOp` | GET `api/public/v1.0/groups/{groupID}/alertConfigs/{alertConfigID}` |
| `GetOpenAlertsConfig` | `*AlertConfigurationsServiceOp` | GET `api/public/v1.0/groups/{groupID}/alertConfigs/{alertConfigID}/alerts` |
| `ListMatcherFields` | `*AlertConfigurationsServiceOp` | GET `api/public/v1.0/alertConfigs/matchers/fieldNames` |

---

### 5. Global Alerts (Reads)
**Why:** Global alerts span all projects — important for enterprise-wide monitoring dashboards and reporting. Complements the existing project-scoped alerts.

| Go Method | Receiver | API Path |
|---|---|---|
| `List` | `*GlobalAlertsServiceOp` | GET `api/public/v1.0/globalAlerts` |
| `Get` | `*GlobalAlertsServiceOp` | GET `api/public/v1.0/globalAlerts/{alertID}` |

---

### 6. Diagnostics
**Why:** Returns a full diagnostic archive (gzip) for a project. The primary tool for deep incident investigation. Banks need this for post-incident reporting and root cause analysis. Implemented as a streaming download in Go.

| Go Method | Receiver | API Path |
|---|---|---|
| `Get` | `*DiagnosticsServiceOp` | GET `api/public/v1.0/groups/{groupID}/diagnostics` |

**Note:** Returns a gzip stream via `io.Writer` parameter. Python implementation will need to handle streaming binary response, similar to how Go uses `NewGZipRequest`.

---

### 7. Maintenance Windows (Reads)
**Why:** Change management documentation. A bank must be able to report on scheduled maintenance windows for DR planning, change advisory board (CAB) submissions, and audit evidence. Currently 100% missing from Python.

| Go Method | Receiver | API Path |
|---|---|---|
| `List` | `*MaintenanceWindowsServiceOp` | GET `api/public/v1.0/groups/{groupID}/maintenanceWindows` |
| `Get` | `*MaintenanceWindowsServiceOp` | GET `api/public/v1.0/groups/{groupID}/maintenanceWindows/{maintenanceWindowID}` |

---

### 8. Log Collection Jobs (Reads)
**Why:** Log collection jobs are the mechanism for gathering logs from MongoDB processes. A bank needs to verify that log collection is running, check job status, and download logs for forensic/compliance purposes.

| Go Method | Receiver | API Path |
|---|---|---|
| `List` | `*LogCollectionServiceOp` | GET `api/public/v1.0/groups/{groupID}/logCollectionJobs` |
| `Get` | `*LogCollectionServiceOp` | GET `api/public/v1.0/groups/{groupID}/logCollectionJobs/{jobID}` |
| `Download` | `*LogsServiceOp` | GET `api/public/v1.0/groups/{groupID}/logCollectionJobs/{jobID}/download` |

**Note:** `Download` returns a gzip stream via `io.Writer`. Requires streaming binary response handling.

---

## Tier 2 — Useful for Diagnostics & Reporting

These endpoints add meaningful depth to reporting capabilities — particularly around backup health, access control, capacity, and version compliance.

---

### 9. Backup Configs — List (Missing)
**Why:** `get_backup_config` is already in Python but `list` is not. Listing all backup configurations across all clusters in a project is essential for backup coverage reporting ("which clusters are not backed up?").

| Go Method | Receiver | API Path |
|---|---|---|
| `List` | `*BackupConfigsServiceOp` | GET `api/public/v1.0/groups/{groupID}/backupConfigs` |

---

### 10. Snapshot Schedule
**Why:** Documents the backup retention policy in force for each cluster. A bank's audit may require evidence of backup retention periods. Currently missing from Python.

| Go Method | Receiver | API Path |
|---|---|---|
| `Get` | `*SnapshotScheduleServiceOp` | GET `api/public/v1.0/groups/{groupID}/backupConfigs/{clusterID}/snapshotSchedule` |

---

### 11. Continuous Restore Jobs (Reads)
**Why:** Tracking restore job history is part of DR testing documentation. A bank must demonstrate it can restore from backups — restore job records are audit evidence.

| Go Method | Receiver | API Path |
|---|---|---|
| `List` | `*ContinuousRestoreJobsServiceOp` | GET `api/public/v1.0/groups/{groupID}/clusters/{clusterID}/restoreJobs` |
| `Get` | `*ContinuousRestoreJobsServiceOp` | GET `api/public/v1.0/groups/{groupID}/clusters/{clusterID}/restoreJobs/{jobID}` |

---

### 12. Checkpoints (Reads)
**Why:** Backup checkpoints for sharded clusters. Required for complete backup coverage reporting on sharded deployments.

| Go Method | Receiver | API Path |
|---|---|---|
| `List` | `*CheckpointsServiceOp` | GET `api/public/v1.0/groups/{groupID}/clusters/{clusterName}/checkpoints` |
| `Get` | `*CheckpointsServiceOp` | GET `api/public/v1.0/groups/{groupID}/clusters/{clusterID}/checkpoints/{checkpointID}` |

---

### 13. Server Usage (Reads)
**Why:** License and capacity reporting. Banks often have strict software licensing obligations and need to report server counts, types, and assignments for compliance with licensing agreements.

| Go Method | Receiver | API Path |
|---|---|---|
| `ListAllHostAssignment` | `*ServerUsageServiceOp` | GET `api/public/v1.0/usage/assignments` |
| `ProjectHostAssignments` | `*ServerUsageServiceOp` | GET `api/public/v1.0/usage/groups/{groupID}/hosts` |
| `OrganizationHostAssignments` | `*ServerUsageServiceOp` | GET `api/public/v1.0/usage/organizations/{orgID}/hosts` |
| `GetServerTypeProject` | `*ServerUsageServiceOp` | GET `api/public/v1.0/usage/groups/{groupID}/defaultServerType` |
| `GetServerTypeOrganization` | `*ServerUsageServiceOp` | GET `api/public/v1.0/usage/organizations/{orgID}/defaultServerType` |
| `Download` | `*ServerUsageReportServiceOp` | GET `api/public/v1.0/usage/report` |

---

### 14. Agent Versions
**Why:** Version compliance reporting — confirms that all monitoring and backup agents are running approved/current versions. Important for security patch compliance.

| Go Method | Receiver | API Path |
|---|---|---|
| `GlobalVersions` | `*AgentsServiceOp` | GET `api/public/v1.0/softwareComponents/versions` |
| `ProjectVersions` | `*AgentsServiceOp` | GET `api/public/v1.0/groups/{groupID}/agents/versions` |
| `ListAgentLinks` | `*AgentsServiceOp` | GET `api/public/v1.0/groups/{groupID}/agents` |

---

### 15. Organization Users (Read)
**Why:** Access control reporting — who has access to which organizations. Essential for periodic access reviews required by banking regulators.

| Go Method | Receiver | API Path |
|---|---|---|
| `ListUsers` | `*OrganizationsServiceOp` | GET `api/public/v1.0/orgs/{orgID}/users` |

---

### 16. Project Users (Read)
**Why:** Project-level access control reporting. Complements org-level user listing for granular access reviews.

| Go Method | Receiver | API Path |
|---|---|---|
| `ListUsers` | `*ProjectsServiceOp` | GET `api/public/v1.0/groups/{projectID}/users` |

---

### 17. Feature Control Policies (Reads)
**Why:** Documents which MongoDB features are enabled or restricted in each project. Important for security hardening evidence ("is X feature disabled as required by policy?").

| Go Method | Receiver | API Path |
|---|---|---|
| `List` | `*FeatureControlPoliciesServiceOp` | GET `api/public/v1.0/groups/{groupID}/controlledFeature` |
| `ListSupportedPolicies` | `*FeatureControlPoliciesServiceOp` | GET `api/public/v1.0/groups/availablePolicies` |

---

## Tier 3 — Nice to Have

These endpoints add completeness but are lower priority for a diagnostics/reporting use case.

---

### 18. Teams (Reads)
**Why:** Organizational structure reporting. Useful for understanding team-based access but less critical than user-level access reporting.

| Go Method | Receiver | API Path |
|---|---|---|
| `List` | `*TeamsServiceOp` | GET `api/public/v1.0/orgs/{orgID}/teams` |
| `Get` | `*TeamsServiceOp` | GET `api/public/v1.0/orgs/{orgID}/teams/{teamID}` |
| `GetOneTeamByName` | `*TeamsServiceOp` | GET `api/public/v1.0/orgs/{orgID}/teams/byName/{teamName}` |
| `GetTeamUsersAssigned` | `*TeamsServiceOp` | GET `api/public/v1.0/orgs/{orgID}/teams/{teamID}/users` |
| `GetTeams` (project) | `*ProjectsServiceOp` | GET `api/public/v1.0/groups/{projectID}/teams` |

---

### 19. Users (Reads)
**Why:** User lookup by ID or username. Useful for resolving user IDs in event logs to human-readable names during audit reporting.

| Go Method | Receiver | API Path |
|---|---|---|
| `Get` | `*UsersServiceOp` | GET `api/public/v1.0/users/{userID}` |
| `GetByName` | `*UsersServiceOp` | GET `api/public/v1.0/users/byName/{username}` |

---

### 20. API Key Inventory (Reads)
**Why:** Useful for an access control audit ("what API keys exist?"), but less urgent than user and event reporting.

| Go Method | Receiver | API Path |
|---|---|---|
| `List` (org keys) | `*APIKeysServiceOp` | GET `api/public/v1.0/orgs/{orgID}/apiKeys` |
| `Get` (org key) | `*APIKeysServiceOp` | GET `api/public/v1.0/orgs/{orgID}/apiKeys/{apiKeyID}` |
| `List` (project keys) | `*ProjectAPIKeysOp` | GET `api/public/v1.0/groups/{groupID}/apiKeys` |
| `ListAgentAPIKeys` | `*AgentsServiceOp` | GET `api/public/v1.0/groups/{projectID}/agentapikeys` |

---

### 21. Version Manifest
**Why:** Maps MongoDB version strings to full release metadata. Useful for enriching version compliance reports with release dates and EOL status.

| Go Method | Receiver | API Path |
|---|---|---|
| `Get` | `*VersionManifestServiceOp` | GET `static/version_manifest/{version}` |

---

### 22. Service Version
**Why:** Returns the Ops Manager server version. Useful as a health check and for including the Ops Manager version in diagnostic reports.

| Go Method | Receiver | API Path |
|---|---|---|
| `Get` | `*ServiceVersionServiceOp` | GET `api/private/unauth/version` |

**Note:** Uses `api/private/unauth/version` — unauthenticated endpoint.

---

### 23. Live Data Migration — Connection Status
**Why:** If the bank is running a live migration, this shows the link status. Low priority unless migrations are in scope.

| Go Method | Receiver | API Path |
|---|---|---|
| `ConnectionStatus` | `*LiveDataMigrationServiceOp` | GET `api/public/v1.0/orgs/{orgID}/liveExport/migrationLink/status` |

---

### 24. Admin Backup Store Config (Reads)
**Why:** Documents the backup infrastructure configuration. Relevant only if the bank also manages the Ops Manager installation itself (as opposed to using Cloud Manager). Low priority for a typical diagnostics client.

| Go Method | Receiver | API Path |
|---|---|---|
| `List`, `Get` | `*BlockstoreConfigServiceOp` | GET `api/public/v1.0/admin/backup/snapshot/mongoConfigs[/{id}]` |
| `List`, `Get` | `*FileSystemStoreConfigServiceOp` | GET `api/public/v1.0/admin/backup/snapshot/fileSystemConfigs[/{id}]` |
| `List`, `Get` | `*S3BlockstoreConfigServiceOp` | GET `api/public/v1.0/admin/backup/snapshot/s3Configs[/{id}]` |
| `List`, `Get` | `*OplogStoreConfigServiceOp` | GET `api/public/v1.0/admin/backup/oplog/mongoConfigs[/{id}]` |
| `List`, `Get` | `*SyncStoreConfigServiceOp` | GET `api/public/v1.0/admin/backup/sync/mongoConfigs[/{id}]` |
| `List`, `Get` | `*DaemonConfigServiceOp` | GET `api/public/v1.0/admin/backup/daemon/configs[/{id}]` |
| `List`, `Get` | `*ProjectJobConfigServiceOp` | GET `api/public/v1.0/admin/backup/groups[/{id}]` |

---

### 25. Global Admin API Keys (Reads)
**Why:** Useful only if the client also manages the global Ops Manager admin API key inventory. Not relevant for a diagnostics-only use case.

| Go Method | Receiver | API Path |
|---|---|---|
| `List` | `*GlobalAPIKeysServiceOp` | GET `api/public/v1.0/admin/apiKeys` |
| `Get` | `*GlobalAPIKeysServiceOp` | GET `api/public/v1.0/admin/apiKeys/{apiKeyID}` |
| `List` | `*GlobalAPIKeyWhitelistsServiceOp` | GET `api/public/v1.0/admin/whitelist` |
| `Get` | `*GlobalAPIKeyWhitelistsServiceOp` | GET `api/public/v1.0/admin/whitelist/{id}` |

---

## Summary Table

| # | Service / Endpoint Group | Tier | Endpoints | Banking Rationale |
|---|---|---|---|---|
| 1 | Events (org + project) | **1** | 4 | Audit log — SOX/PCI compliance |
| 2 | Automation Status | **1** | 1 | Config enforcement verification |
| 3 | Automation Config reads | **1** | 3 | Configuration compliance reporting |
| 4 | Alert Configurations reads | **1** | 4 | Governance / alerting policy reporting |
| 5 | Global Alerts reads | **1** | 2 | Enterprise-wide alert monitoring |
| 6 | Diagnostics | **1** | 1 | Incident investigation / root cause |
| 7 | Maintenance Windows reads | **1** | 2 | Change management documentation |
| 8 | Log Collection Jobs reads | **1** | 3 | Log audit trail + forensics |
| 9 | Backup Configs — List | **2** | 1 | Backup coverage reporting |
| 10 | Snapshot Schedule | **2** | 1 | Backup retention policy evidence |
| 11 | Continuous Restore Jobs reads | **2** | 2 | DR testing documentation |
| 12 | Checkpoints reads | **2** | 2 | Backup coverage (sharded clusters) |
| 13 | Server Usage reads | **2** | 6 | License/capacity compliance |
| 14 | Agent versions | **2** | 3 | Security patch compliance |
| 15 | Organization Users | **2** | 1 | Access control reviews |
| 16 | Project Users | **2** | 1 | Granular access reviews |
| 17 | Feature Control Policies reads | **2** | 2 | Security hardening evidence |
| 18 | Teams reads | **3** | 5 | Org structure reporting |
| 19 | Users reads | **3** | 2 | User ID resolution in event logs |
| 20 | API Key inventory reads | **3** | 4 | Access control audit |
| 21 | Version Manifest | **3** | 1 | Enriched version reporting |
| 22 | Service Version | **3** | 1 | Health check / diagnostic header |
| 23 | Live Migration status | **3** | 1 | Migration tracking (if applicable) |
| 24 | Admin Backup Store Config reads | **3** | 14 | Backup infra config (self-managed OM only) |
| 25 | Global Admin API Keys reads | **3** | 4 | Admin key inventory (if applicable) |
| | **Total missing read endpoints** | | **~72** | |
