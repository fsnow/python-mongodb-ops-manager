# Ops Manager API Endpoints Reference

This document catalogs all Ops Manager API endpoints we'll support, organized by category.

## Base URL Pattern

```
https://<ops-manager-host>/api/public/v1.0
```

## Authentication

All endpoints require HTTP Digest authentication using public/private API key pair.

## Endpoint Categories

### Organizations

TBD - Document endpoints from Go SDK research

### Projects (Groups)

TBD - Document endpoints from Go SDK research

### Clusters

TBD - Document endpoints from Go SDK research

### Processes (Hosts)

TBD - Document endpoints from Go SDK research

### Metrics

TBD - Document endpoints from Go SDK research

### Performance Advisor

TBD - Document endpoints from Go SDK research

### Database Stats

TBD - Document endpoints from Go SDK research

### Alerts

TBD - Document endpoints from Go SDK research

### Backup

TBD - Document endpoints from Go SDK research

## Endpoint Priority for Health Checks

Based on our automation requirements, prioritize these endpoints:

1. **Critical** (needed for basic health check):
   - List projects
   - List clusters
   - Get cluster config
   - List processes
   - Get database metrics

2. **High priority** (needed for comprehensive health check):
   - Performance Advisor (host-level)
   - Performance Advisor (shard-level - if exists)
   - Metrics (opcounters, CPU, disk, queues)
   - Query targeting metrics

3. **Medium priority** (nice to have):
   - Profiler / slow queries
   - Alerts
   - Backup status

## Research Tasks

- [ ] Map all endpoints from go-client-mongodb-ops-manager
- [ ] Document request/response schemas
- [ ] Identify pagination patterns
- [ ] Note rate limiting recommendations
- [ ] Test endpoint availability in our Ops Manager version
