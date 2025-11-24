# Research Notes

This document tracks our research into the MongoDB Ops Manager API and official Go SDK implementation.

## Goals

1. Understand complete API endpoint coverage
2. Learn authentication patterns (Digest auth)
3. Study rate limiting and best practices
4. Document pagination patterns
5. Identify all resource types and their operations

## Official Go SDK Reference

**Repository**: https://github.com/mongodb/go-client-mongodb-ops-manager

**Package**: `go.mongodb.org/ops-manager/opsmngr`

**API Documentation**:
- Ops Manager: https://docs.opsmanager.mongodb.com/master/reference/api/
- Cloud Manager: https://docs.cloudmanager.mongodb.com/master/reference/api/

## Key Findings

### Authentication
- Uses HTTP Digest authentication
- Requires public API key and private API key
- Org-level or project-level permissions

### Rate Limiting
- TBD - Need to research from Go SDK

### Pagination
- TBD - Need to research from Go SDK

### Resource Types
- TBD - Document as we discover

## API Endpoints Needed for Health Checks

Based on AUTOMATION_PLAN.md requirements:

1. **Organizations** - Get org info
2. **Projects (Groups)** - List projects, get project details
3. **Clusters** - List clusters, get cluster config, detect sharded vs replica set
4. **Processes** - List all hosts/processes in a cluster
5. **Metrics** - Time-series metrics (opcounters, CPU, disk, etc.)
6. **Performance Advisor** - Suggested indexes (host-level and shard-level)
7. **Database Stats** - Database sizes, collection counts
8. **Profiler / Slow Queries** - ⚠️ Need to verify if API endpoint exists

## Next Steps

- [ ] Clone and study go-client-mongodb-ops-manager
- [ ] Document authentication implementation
- [ ] Map out all endpoint categories
- [ ] Identify rate limiting patterns
- [ ] Document pagination implementation
- [ ] Create endpoint reference document
