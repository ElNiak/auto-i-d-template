# Database Wire Protocols Collection

## Overview

This directory contains detailed documentation for three major database wire protocols, extracted from official company/project documentation. These protocols serve as reference examples for RFC-style application profile documentation.

## Contents

### Protocol Documentation Files

1. **[postgresql-wire-protocol.md](postgresql-wire-protocol.md)** (507 lines, 16KB)
   - PostgreSQL Frontend/Backend Protocol v3.2
   - Message-based binary protocol
   - Comprehensive coverage of connection, authentication, query execution, and replication
   
2. **[mysql-wire-protocol.md](mysql-wire-protocol.md)** (817 lines, 24KB)
   - MySQL Client/Server Protocol v10
   - Packet-based protocol with multiple transport options
   - Detailed command phase, prepared statements, and replication protocol
   
3. **[redis-wire-protocol.md](redis-wire-protocol.md)** (1,117 lines, 21KB)
   - Redis Serialization Protocol (RESP2 and RESP3)
   - Human-readable ASCII protocol
   - Extensive coverage of data types, pipelining, Pub/Sub, and cluster extensions

4. **[summary.md](summary.md)** (583 lines, 17KB)
   - Comprehensive index and comparison matrix
   - Protocol selection guidelines
   - Implementation considerations
   - Testing and debugging resources

## Quick Reference

### Protocol Characteristics

| Protocol | Type | Port | Key Strength |
|----------|------|------|--------------|
| PostgreSQL | Binary message-based | 5432 | Rich features, ACID |
| MySQL | Packet-based | 3306 | Wide adoption, replication |
| Redis | ASCII text-based | 6379 | Performance, simplicity |

### Use Case Recommendations

- **PostgreSQL:** Complex relational data, ACID transactions, rich data types
- **MySQL:** Web applications, e-commerce, read-heavy workloads
- **Redis:** Caching, sessions, real-time analytics, Pub/Sub

## Documentation Sources

All documentation is derived from official sources:

- **PostgreSQL:** https://www.postgresql.org/docs/current/protocol.html
- **MySQL:** https://dev.mysql.com/doc/dev/mysql-server/9.3.0/PAGE_PROTOCOL.html
- **Redis:** https://redis.io/docs/latest/develop/reference/protocol-spec/

## Collection Date

**Created:** 2025-10-13

## Usage

These documents are intended as:

1. Reference examples for RFC-style protocol documentation
2. Implementation guides for client libraries
3. Debugging resources for protocol-level issues
4. Educational material for understanding wire protocol design

## Related Resources

- See `summary.md` for comprehensive comparison matrix
- Each protocol file includes implementation examples
- Official documentation links provided throughout
