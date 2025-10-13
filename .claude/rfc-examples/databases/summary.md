# Database Wire Protocols - Summary Index

## Overview

This directory contains comprehensive documentation for three major database wire protocols:

1. **PostgreSQL Frontend/Backend Protocol**
2. **MySQL Client/Server Protocol**
3. **Redis Serialization Protocol (RESP)**

These are company-defined protocols (not IETF RFCs) that specify how clients communicate with their respective database servers. All documentation is sourced from official project documentation.

## Collection Metadata

- **Date Collected:** 2025-10-13
- **Purpose:** Reference examples for RFC-style application profile documentation
- **Source Type:** Official company/project documentation
- **Format:** Markdown with detailed specifications

## Protocol Summaries

### 1. PostgreSQL Wire Protocol

**File:** [`postgresql-wire-protocol.md`](postgresql-wire-protocol.md)

**Protocol Version:** 3.2 (PostgreSQL 18+), backward compatible to 3.0 (PostgreSQL 7.4+)

**Key Characteristics:**
- Message-based binary protocol
- TCP/IP and Unix domain sockets
- Separate backend process per connection
- Supports text and binary data formats
- Multiple query execution modes (Simple, Extended, Pipelining)
- Strong authentication (SCRAM-SHA-256, GSSAPI, OAuth)
- SSL/TLS and GSSAPI encryption support

**Main Protocol Features:**
- **Connection Phase:** StartupMessage, authentication negotiation, backend key
- **Query Modes:**
  - Simple Query: Single SQL statement as text
  - Extended Query: Parse, Bind, Execute with parameters
  - Pipelining: Multiple requests without waiting for responses
- **COPY Protocol:** High-performance bulk data transfer
- **Asynchronous Operations:** Server-initiated notifications (LISTEN/NOTIFY)
- **Streaming Replication:** WAL streaming for replicas
- **Function Calls:** Direct server-side function invocation

**Message Types:** 40+ distinct message types (Query, Parse, Bind, Execute, DataRow, etc.)

**Data Encoding:**
- Text format: ASCII representation
- Binary format: Network byte order (big-endian), type-specific encoding
- NULL handling: -1 length field

**Authentication Methods:**
- SCRAM-SHA-256 (recommended)
- SASL framework
- MD5 (legacy)
- GSSAPI/Kerberos
- OAUTHBEARER
- Cleartext (not recommended)

**Official Documentation:**
- Main: https://www.postgresql.org/docs/current/protocol.html
- Message Formats: https://www.postgresql.org/docs/current/protocol-message-formats.html
- Protocol Flow: https://www.postgresql.org/docs/current/protocol-flow.html

**Use Cases:**
- Relational database operations
- ACID transaction support
- Complex queries with JOINs
- Stored procedures
- Full-text search
- JSON/JSONB operations

**Performance Features:**
- Prepared statements with query plan caching
- Binary protocol for reduced parsing overhead
- Pipelining for latency reduction
- COPY for bulk loading (much faster than INSERT)
- Connection pooling support

---

### 2. MySQL Wire Protocol

**File:** [`mysql-wire-protocol.md`](mysql-wire-protocol.md)

**Protocol Version:** 10 (MySQL 8.x+)

**Key Characteristics:**
- Packet-based protocol with sequence numbering
- Two-phase: Connection Phase and Command Phase
- Multiple transport options (TCP/IP, Unix socket, Named pipe, Shared memory)
- Supports compression and SSL/TLS encryption
- Prepared statements with binary protocol

**Main Protocol Features:**
- **Transport Layers:**
  - TCP/IP (most common, port 3306)
  - Unix socket (local, fast, secure by default)
  - Named pipe (Windows, local)
  - Shared memory (Windows, fastest local)
- **Packet Structure:**
  - 3-byte payload length (max 16MB-1 per packet)
  - 1-byte sequence ID
  - Variable payload
- **Connection Phase:**
  - Initial handshake with capability negotiation
  - Authentication with pluggable methods
  - SSL/TLS negotiation
- **Command Phase:**
  - 30+ command types (COM_QUERY, COM_STMT_PREPARE, etc.)
  - Text protocol for simple queries
  - Binary protocol for prepared statements

**Command Types:** 32 commands including:
- COM_QUERY (0x03): Execute SQL
- COM_QUIT (0x01): Close connection
- COM_PING (0x0E): Keep-alive
- COM_STMT_PREPARE (0x16): Prepare statement
- COM_STMT_EXECUTE (0x17): Execute prepared statement
- COM_BINLOG_DUMP (0x12): Replication

**Response Packets:**
- OK Packet: Successful command execution
- Error Packet: Command failure with error code and SQLSTATE
- Result Set: Column definitions + data rows + EOF/OK
- EOF Packet: Deprecated in favor of OK with CLIENT_DEPRECATE_EOF

**Authentication Methods:**
- caching_sha2_password (MySQL 8.0+ default)
- mysql_native_password (legacy, SHA1-based)
- sha256_password
- PAM, LDAP, Kerberos plugins

**Data Types:** 25+ column types (INT, VARCHAR, BLOB, DATETIME, etc.)

**Official Documentation:**
- Main: https://dev.mysql.com/doc/dev/mysql-server/9.3.0/PAGE_PROTOCOL.html
- Protocol Basics: https://dev.mysql.com/doc/dev/mysql-server/9.3.0/page_protocol_basics.html
- Transport: https://dev.mysql.com/doc/refman/8.1/en/transport-protocols.html

**Use Cases:**
- Web application databases
- E-commerce platforms
- Content management systems
- Data warehousing
- Replication for high availability

**Performance Features:**
- Binary protocol for efficient data encoding
- Prepared statement caching
- Compression for bandwidth reduction
- Connection pooling
- Multi-statement execution
- Pipelining support

**MariaDB Compatibility:**
- Uses same core protocol
- Minor extensions for enhanced features
- Protocol documentation: https://mariadb.com/kb/en/clientserver-protocol/

---

### 3. Redis Wire Protocol (RESP)

**File:** [`redis-wire-protocol.md`](redis-wire-protocol.md)

**Protocol Versions:**
- RESP2: Standard since Redis 2.0 (2010)
- RESP3: Enhanced protocol since Redis 6.0 (2020)

**Key Characteristics:**
- Human-readable ASCII protocol
- Binary-safe with length-prefixed encoding
- Simple to implement and debug
- Request-response model with Pub/Sub exceptions
- Excellent pipelining support

**Main Protocol Features:**
- **RESP2 Data Types (5 types):**
  - Simple String (`+`): Non-binary string
  - Error (`-`): Error messages
  - Integer (`:`): 64-bit signed integer
  - Bulk String (`$`): Binary-safe, length-prefixed
  - Array (`*`): Ordered collection
- **RESP3 Additional Types (9 new types):**
  - Null (`_`): Explicit NULL
  - Boolean (`#`): True/false
  - Double (`,`): Floating-point
  - Big Number (`(`): Arbitrary precision integer
  - Bulk Error (`!`): Structured error
  - Verbatim String (`=`): String with encoding metadata
  - Map (`%`): Key-value dictionary
  - Set (`~`): Unordered collection
  - Push (`>`): Server-initiated push data

**Protocol Encoding:**
- Type prefix (single ASCII character)
- Length encoding where applicable
- CRLF (`\r\n`) line termination
- Little endian for multi-byte values

**Command Format:**
- All commands sent as RESP Arrays
- First element: command name
- Subsequent elements: arguments
- Example: `SET key value` → `*3\r\n$3\r\nSET\r\n$3\r\nkey\r\n$5\r\nvalue\r\n`

**Response Format:**
- Any RESP data type
- Success: `+OK\r\n`
- Error: `-ERR message\r\n`
- Integer: `:42\r\n`
- String: `$5\r\nHello\r\n`
- NULL: `$-1\r\n` (RESP2) or `_\r\n` (RESP3)

**Special Protocols:**
- **Pipelining:** Send multiple commands without waiting
- **Transactions:** MULTI/EXEC for atomic operations
- **Pub/Sub:** Subscribe/publish messaging
- **Streams:** Time-series data structures
- **Cluster:** Distributed Redis with MOVED/ASK redirects

**Protocol Upgrade:**
- Use HELLO command to negotiate RESP3
- Server returns capability information
- Backward compatible (RESP3 servers support RESP2 clients)

**Official Documentation:**
- Main: https://redis.io/docs/latest/develop/reference/protocol-spec/
- RESP3 Spec: https://github.com/redis/redis-specifications/blob/master/protocol/RESP3.md
- Commands: https://redis.io/docs/latest/commands/

**Use Cases:**
- Caching layer
- Session storage
- Real-time analytics
- Pub/Sub messaging
- Rate limiting
- Leaderboards
- Time-series data

**Performance Features:**
- Extremely low latency
- High throughput with pipelining (>100K ops/sec)
- Minimal protocol overhead
- Fast parsing (>1M ops/sec)
- Single-threaded execution (Redis 6.0+ has I/O threading)

**Security:**
- AUTH command for password authentication
- ACL (Access Control Lists) in Redis 6.0+
- TLS/SSL support (Redis 6.0+)
- Command renaming for hiding dangerous commands

---

## Protocol Comparison Matrix

| Feature | PostgreSQL | MySQL | Redis |
|---------|-----------|-------|-------|
| **Transport** | TCP/IP, Unix socket | TCP/IP, Unix socket, Named pipe, Shared memory | TCP/IP, Unix socket |
| **Default Port** | 5432 | 3306 | 6379 |
| **Protocol Type** | Binary message-based | Packet-based with sequence | ASCII text-based |
| **Encoding** | Big-endian | Little-endian | ASCII with binary data |
| **Connection Model** | Process per connection | Thread per connection | Single-threaded (I/O threads in 6.0+) |
| **Query Modes** | Simple, Extended, Pipelining | Text, Binary (prepared) | Request-response, Pipelining |
| **Authentication** | SCRAM, GSSAPI, MD5, OAuth | SHA256, Native, PAM, LDAP | Password, ACL |
| **Encryption** | SSL/TLS, GSSAPI | SSL/TLS | SSL/TLS (6.0+) |
| **Data Types** | Rich (arrays, JSON, etc.) | Standard SQL types | Simple (strings, integers, lists, etc.) |
| **Transactions** | Full ACID | Full ACID | Optimistic (MULTI/EXEC) |
| **Prepared Statements** | Yes (Parse/Bind/Execute) | Yes (COM_STMT_*) | Lua scripts |
| **Replication** | Streaming, Logical | Binary log replication | Master-replica, Cluster |
| **Pub/Sub** | LISTEN/NOTIFY | No native support | Full Pub/Sub support |
| **Compression** | No (at TLS layer) | Yes (zlib) | No (at TLS layer) |
| **Human Readable** | No | No | Yes (RESP) |
| **Parser Complexity** | High | Medium | Low |
| **Protocol Overhead** | Medium | Medium | Low |
| **Pipelining** | Yes | Limited | Excellent |

## Common Protocol Patterns

### 1. Connection Establishment

**PostgreSQL:**
```
Client: StartupMessage (protocol version, user, database)
Server: Authentication request
Client: Authentication response
Server: AuthenticationOk, ParameterStatus, BackendKeyData, ReadyForQuery
```

**MySQL:**
```
Server: Initial Handshake (version, capabilities, auth plugin)
Client: Handshake Response (capabilities, username, auth data)
Server: OK or Error
```

**Redis:**
```
Client: (connects, optionally sends HELLO 3 for RESP3)
Server: Connection info (if HELLO sent)
Client: AUTH (if authentication required)
Server: +OK or -ERR
```

### 2. Simple Query Execution

**PostgreSQL:**
```
Client: Query "SELECT * FROM users;"
Server: RowDescription, DataRow(s), CommandComplete, ReadyForQuery
```

**MySQL:**
```
Client: COM_QUERY "SELECT * FROM users;"
Server: Column Count, Column Definition(s), EOF, Result Row(s), EOF/OK
```

**Redis:**
```
Client: *2\r\n$3\r\nGET\r\n$3\r\nkey\r\n
Server: $5\r\nvalue\r\n (or $-1\r\n for NULL)
```

### 3. Prepared Statement Execution

**PostgreSQL:**
```
Client: Parse, Bind, Describe, Execute, Sync
Server: ParseComplete, BindComplete, RowDescription, DataRow(s), CommandComplete, ReadyForQuery
```

**MySQL:**
```
Client: COM_STMT_PREPARE
Server: Statement OK (statement ID, param count)
Client: COM_STMT_EXECUTE (statement ID, parameters)
Server: Result Set or OK
```

**Redis:**
```
N/A (use Lua scripts for similar functionality)
Client: EVAL "script" numkeys key [key ...] arg [arg ...]
Server: Script return value
```

### 4. Error Handling

**PostgreSQL:**
```
Server: ErrorResponse (severity, SQLSTATE, message, detail, hint)
Client: Reads error, may retry or abort
```

**MySQL:**
```
Server: Error Packet (error code, SQLSTATE, message)
Client: Throws exception or returns error
```

**Redis:**
```
Server: -ERR unknown command 'foobar'\r\n
Client: Raises exception
```

## Implementation Considerations

### Parsing Complexity

**Simplest to Implement:** Redis (RESP)
- Single-character type prefix
- Length-prefixed strings
- Line-oriented parsing
- No complex state machine needed

**Medium Complexity:** MySQL
- Fixed packet header structure
- Multiple packet types but well-defined
- Length-encoded integers
- Binary protocol more complex

**Most Complex:** PostgreSQL
- 40+ message types
- Multiple query protocols
- Complex authentication flows
- Binary data type encodings

### Performance Optimization

**All Protocols:**
1. Use connection pooling
2. Enable pipelining where supported
3. Prefer binary formats over text
4. Batch operations when possible
5. Monitor network latency
6. Use compression for high-latency links

**PostgreSQL Specific:**
- Use Extended Query protocol for repeated queries
- Enable binary format for large result sets
- Use COPY for bulk operations
- Prepared statements for plan caching

**MySQL Specific:**
- Use binary protocol (prepared statements)
- Enable compression for WAN connections
- Use batch inserts
- Consider Unix socket for local connections

**Redis Specific:**
- Pipeline as many commands as possible
- Use Lua scripts to reduce round trips
- Consider Redis Cluster for horizontal scaling
- Use RESP3 for better data type support

### Security Best Practices

**Authentication:**
- PostgreSQL: Use SCRAM-SHA-256, avoid MD5
- MySQL: Use caching_sha2_password, avoid legacy methods
- Redis: Use ACLs (6.0+), rename dangerous commands

**Encryption:**
- All: Use TLS/SSL for remote connections
- PostgreSQL: GSSAPI encryption available
- MySQL: Certificate validation recommended
- Redis: Consider stunnel for pre-6.0 versions

**Access Control:**
- All: Principle of least privilege
- All: Network isolation (firewall, VPC)
- PostgreSQL: Fine-grained permissions (GRANT)
- MySQL: Host-based access control
- Redis: ACLs with command restrictions (6.0+)

## Use Case Recommendations

### Choose PostgreSQL Protocol When:
- Need strong ACID guarantees
- Complex relational data models
- Rich data types (JSON, arrays, custom types)
- Full-text search
- Geographic data (PostGIS)
- Strong consistency requirements

### Choose MySQL Protocol When:
- Web application backend
- E-commerce platforms
- Replication for read scaling
- Wide ecosystem support
- Existing MySQL infrastructure
- Need for multiple storage engines

### Choose Redis Protocol When:
- Caching layer
- Session storage
- Real-time analytics
- Pub/Sub messaging
- Rate limiting
- Queue implementation
- Leaderboards/counters
- Time-series data

## Testing and Debugging

### Tools by Protocol

**PostgreSQL:**
- `psql` with `-E` (echo queries)
- Wireshark with PostgreSQL dissector
- pgShark protocol analyzer
- Protocol-level logging in postgresql.conf

**MySQL:**
- `mysql` client with `--debug`
- Wireshark with MySQL dissector
- General query log
- Performance Schema
- mysqlslap for benchmarking

**Redis:**
- `redis-cli` with `--raw` for protocol view
- `MONITOR` command for real-time observation
- `telnet`/`netcat` for manual protocol interaction
- Wireshark with Redis dissector

### Common Debugging Scenarios

**Connection Issues:**
- Check firewall/security groups
- Verify authentication credentials
- Check SSL/TLS configuration
- Review server logs

**Performance Issues:**
- Monitor network latency
- Check for N+1 query patterns
- Review query plans
- Enable connection pooling
- Use pipelining

**Protocol Errors:**
- Sequence mismatch (MySQL)
- Invalid message type
- Buffer overflow/underflow
- Encoding mismatch
- SSL/TLS handshake failures

## Additional Resources

### PostgreSQL
- **Official Docs:** https://www.postgresql.org/docs/current/
- **Source Code:** https://github.com/postgres/postgres
- **Wiki:** https://wiki.postgresql.org/wiki/Wire_Protocol
- **Mailing Lists:** pgsql-hackers, pgsql-general

### MySQL
- **Official Docs:** https://dev.mysql.com/doc/
- **Internals Manual:** https://dev.mysql.com/doc/internals/en/
- **Source Code:** https://github.com/mysql/mysql-server
- **Forums:** https://forums.mysql.com/

### Redis
- **Official Docs:** https://redis.io/docs/
- **Protocol Spec:** https://redis.io/docs/latest/develop/reference/protocol-spec/
- **Source Code:** https://github.com/redis/redis
- **Community:** Redis Discord, Stack Overflow

### Client Libraries

**Multi-Protocol:**
- Most languages have mature libraries for all three
- Check official websites for recommended libraries
- Consider connection pooling libraries

**Performance Libraries:**
- PostgreSQL: pgBouncer (connection pooler)
- MySQL: ProxySQL (connection pooler)
- Redis: redis-benchmark, hiredis (C library)

## Conclusion

This collection provides comprehensive documentation of three major database wire protocols:

1. **PostgreSQL:** Feature-rich, message-based protocol for advanced relational database operations
2. **MySQL:** Balanced protocol with good performance and wide compatibility
3. **Redis:** Simple, high-performance protocol optimized for caching and real-time operations

Each protocol reflects different design philosophies and trade-offs:

- **PostgreSQL:** Complexity for power and flexibility
- **MySQL:** Pragmatism for broad adoption
- **Redis:** Simplicity for performance and ease of implementation

These protocols serve as excellent reference examples for designing application-specific protocols, demonstrating various approaches to:

- Connection establishment and authentication
- Command encoding and execution
- Result set transmission
- Error handling
- Performance optimization
- Security and encryption

## Document Updates

To update this documentation:

1. Check official documentation for protocol changes
2. Verify version numbers and feature availability
3. Test protocol examples with latest server versions
4. Update performance benchmarks
5. Add new authentication methods or features
6. Note deprecations and migration paths

**Last Updated:** 2025-10-13
**Sources:** Official project documentation (postgresql.org, dev.mysql.com, redis.io)
