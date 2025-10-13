# MySQL Wire Protocol

## Overview

The MySQL Client/Server Protocol defines communication between MySQL clients and servers. It supports transparent encryption (SSL/TLS) and compression, enabling secure and efficient data transfer.

**Current Version:** Protocol Version 10 (used by MySQL 8.x and later)
**Compatibility:** MariaDB uses the same core protocol with minor extensions

## Official Documentation

- **Main Protocol Documentation:** https://dev.mysql.com/doc/dev/mysql-server/9.3.0/PAGE_PROTOCOL.html
- **Protocol Basics:** https://dev.mysql.com/doc/dev/mysql-server/9.3.0/page_protocol_basics.html
- **Transport Protocols:** https://dev.mysql.com/doc/refman/8.1/en/transport-protocols.html
- **Connection Phase:** https://dev.mysql.com/doc/dev/mysql-server/9.3.0/page_protocol_connection_phase.html
- **Command Phase:** https://dev.mysql.com/doc/dev/mysql-server/9.3.0/page_protocol_command_phase.html
- **MariaDB Protocol:** https://mariadb.com/kb/en/clientserver-protocol/

## Architecture

### Connection Model

- Client initiates connection to server
- Server responds with handshake
- Two-phase protocol: Connection Phase and Command Phase
- Packet-based communication with sequence numbering
- Supports multiplexing through packet sequencing

### Transport Layer Options

MySQL supports four transport protocols:

1. **TCP/IP**
   - Available on all platforms
   - Supports both local and remote connections
   - Default port: 3306
   - Not secure by default (requires SSL/TLS)
   - Most commonly used protocol

2. **Unix Socket File**
   - Unix/Unix-like systems only
   - Local connections only
   - Secure by default (file system permissions)
   - Faster than TCP/IP for local connections
   - Can optionally use SSL/TLS (minimal security benefit)

3. **Named Pipe** (Windows)
   - Windows only
   - Local connections only
   - Not secure by default
   - Cannot be encrypted
   - Default pipe name: `MySQL`

4. **Shared Memory** (Windows)
   - Windows only
   - Local connections only
   - Secure by default
   - Fastest for local Windows connections
   - Limited buffer size

### Protocol Selection

**On Unix-like systems:**
```bash
# TCP/IP
mysql -h 127.0.0.1 --protocol=tcp

# Unix socket
mysql -h localhost --protocol=socket
# OR
mysql --socket=/tmp/mysql.sock
```

**On Windows:**
```bash
# TCP/IP
mysql -h localhost --protocol=tcp

# Named pipe
mysql -h localhost --protocol=pipe

# Shared memory
mysql -h localhost --protocol=memory
```

## Packet Structure

All MySQL protocol communication uses packets with this structure:

```
+----------------+----------------+----------------+----------------+
| Payload Length (3 bytes)                         | Sequence ID   |
+----------------+----------------+----------------+----------------+
| Payload (variable length)                                         |
+------------------------------------------------------------------+
```

### Packet Header (4 bytes)

- **Payload Length (3 bytes):** Length of packet payload (max 16MB - 1)
- **Sequence ID (1 byte):** Packet sequence number (starts at 0, increments)

### Large Packets

For payloads > 16MB - 1 bytes:
1. Send packet with 16MB - 1 payload
2. Continue with next packet (incremented sequence)
3. Last packet has length < 16MB - 1 (may be 0)

### Packet Sequencing

- Each command/response starts with sequence 0
- Each packet increments sequence by 1
- Both client and server maintain sequence counter
- Sequence mismatches indicate protocol errors

## Protocol Phases

### 1. Connection Phase

Establishes connection and authenticates user.

```
Client                              Server
  |                                    |
  |<-- Initial Handshake Packet -------|
  |    (server version, capabilities)  |
  |                                    |
  |--- Handshake Response ------------>|
  |    (username, password hash)       |
  |                                    |
  |<-- OK Packet or Error Packet ------|
  |                                    |
```

#### Initial Handshake Packet (Server → Client)

```
 1  [protocol version]             uint8
 n  [server version]               string<NUL>
 4  [connection id]                uint32
 8  [auth_plugin_data part 1]     byte[8]
 1  [filler]                       0x00
 2  [capability flags (lower)]     uint16
 1  [character set]                uint8
 2  [status flags]                 uint16
 2  [capability flags (upper)]     uint16
 1  [auth_plugin_data length]      uint8
10  [reserved]                     byte[10] (0x00)
 n  [auth_plugin_data part 2]     byte[n]
 n  [auth_plugin name]             string<NUL>
```

**Key Fields:**
- **Protocol Version:** Currently 10
- **Server Version:** E.g., "8.0.35-MySQL"
- **Connection ID:** Thread ID for this connection
- **Capability Flags:** Bitmask of supported features
- **Auth Plugin:** Authentication method (e.g., mysql_native_password, caching_sha2_password)

#### Handshake Response Packet (Client → Server)

```
 4  [capability flags]             uint32
 4  [max packet size]              uint32
 1  [character set]                uint8
23  [reserved]                     byte[23] (0x00)
 n  [username]                     string<NUL>
 n  [auth response length]         lenenc
 n  [auth response]                byte[n]
 n  [database]                     string<NUL> (optional)
 n  [auth plugin name]             string<NUL> (optional)
 n  [connection attributes]        lenenc-int, lenenc-str pairs
```

**Capability Flags:** Negotiated capabilities (client & server)

**Common Capabilities:**
- `CLIENT_PROTOCOL_41` (0x0200): New 4.1 protocol
- `CLIENT_SSL` (0x0800): SSL/TLS support
- `CLIENT_TRANSACTIONS` (0x2000): Transaction support
- `CLIENT_SECURE_CONNECTION` (0x8000): Secure password hashing
- `CLIENT_MULTI_STATEMENTS` (0x10000): Multiple statement support
- `CLIENT_MULTI_RESULTS` (0x20000): Multiple result sets
- `CLIENT_PLUGIN_AUTH` (0x80000): Pluggable authentication
- `CLIENT_CONNECT_ATTRS` (0x100000): Connection attributes
- `CLIENT_DEPRECATE_EOF` (0x1000000): Deprecate EOF packet

#### Authentication Methods

**mysql_native_password (Legacy):**
```
SHA1(password) XOR SHA1(salt + SHA1(SHA1(password)))
```

**caching_sha2_password (MySQL 8.0+ default):**
- Uses SHA256 for password hashing
- Two-phase authentication:
  1. Fast path: Server caches SHA256 hash
  2. Full path: Uses RSA public key or SSL for secure transmission

**sha256_password:**
- SHA256-based authentication
- Requires SSL or RSA encryption for password transmission

**Authentication Plugins:**
- `mysql_native_password`: Pre-8.0 default (SHA1-based)
- `caching_sha2_password`: 8.0+ default (SHA256-based, cached)
- `sha256_password`: SHA256-based (no caching)
- `auth_pam`: PAM authentication (Unix)
- `auth_ldap`: LDAP authentication
- `auth_kerberos`: Kerberos authentication

### 2. Command Phase

Client sends commands, server processes and responds.

```
Client                              Server
  |                                    |
  |--- Command Packet ---------------->|
  |    (command type + payload)        |
  |                                    |
  |<-- Response Packet(s) -------------|
  |    (result set or OK/Error)        |
  |                                    |
```

#### Command Packet Format

```
 1  [command type]                 uint8
 n  [command payload]              byte[n]
```

#### Command Types

| Type | Name | Description |
|------|------|-------------|
| 0x00 | COM_SLEEP | Deprecated |
| 0x01 | COM_QUIT | Close connection |
| 0x02 | COM_INIT_DB | Select database (USE db) |
| 0x03 | COM_QUERY | Execute SQL query |
| 0x04 | COM_FIELD_LIST | List table fields (deprecated) |
| 0x05 | COM_CREATE_DB | Create database (deprecated) |
| 0x06 | COM_DROP_DB | Drop database (deprecated) |
| 0x07 | COM_REFRESH | Flush caches |
| 0x08 | COM_SHUTDOWN | Shutdown server |
| 0x09 | COM_STATISTICS | Get server statistics |
| 0x0A | COM_PROCESS_INFO | Get process list (deprecated) |
| 0x0B | COM_CONNECT | Internal thread state |
| 0x0C | COM_PROCESS_KILL | Kill connection |
| 0x0D | COM_DEBUG | Dump debug info |
| 0x0E | COM_PING | Check server alive |
| 0x0F | COM_TIME | Internal thread state |
| 0x10 | COM_DELAYED_INSERT | Internal thread state |
| 0x11 | COM_CHANGE_USER | Change user |
| 0x12 | COM_BINLOG_DUMP | Replication: dump binlog |
| 0x13 | COM_TABLE_DUMP | Internal |
| 0x14 | COM_CONNECT_OUT | Internal |
| 0x15 | COM_REGISTER_SLAVE | Replication: register replica |
| 0x16 | COM_STMT_PREPARE | Prepared statement: prepare |
| 0x17 | COM_STMT_EXECUTE | Prepared statement: execute |
| 0x18 | COM_STMT_SEND_LONG_DATA | Prepared statement: send BLOB |
| 0x19 | COM_STMT_CLOSE | Prepared statement: close |
| 0x1A | COM_STMT_RESET | Prepared statement: reset |
| 0x1B | COM_SET_OPTION | Set server option |
| 0x1C | COM_STMT_FETCH | Prepared statement: fetch rows |
| 0x1D | COM_DAEMON | Internal |
| 0x1E | COM_BINLOG_DUMP_GTID | Replication: dump with GTID |
| 0x1F | COM_RESET_CONNECTION | Reset connection state |

#### Most Common Commands

**COM_QUERY (0x03):** Execute SQL statement

```
 1  [0x03]                         uint8
 n  [SQL statement]                string<EOF>
```

**COM_QUIT (0x01):** Graceful disconnect

```
 1  [0x01]                         uint8
```

**COM_PING (0x0E):** Keep-alive check

```
 1  [0x0E]                         uint8
```

**COM_INIT_DB (0x02):** Change database

```
 1  [0x02]                         uint8
 n  [database name]                string<EOF>
```

### Response Packets

#### OK Packet (Success)

```
 1  [0x00 or 0xFE]                 uint8 (header)
 n  [affected rows]                lenenc-int
 n  [last insert id]               lenenc-int
 2  [status flags]                 uint16
 2  [warnings]                     uint16
 n  [info message]                 string<EOF>
```

**Status Flags:**
- `SERVER_STATUS_IN_TRANS` (0x0001): In transaction
- `SERVER_STATUS_AUTOCOMMIT` (0x0002): Autocommit enabled
- `SERVER_MORE_RESULTS_EXISTS` (0x0008): More results exist
- `SERVER_STATUS_CURSOR_EXISTS` (0x0040): Cursor exists

#### Error Packet (Failure)

```
 1  [0xFF]                         uint8 (header)
 2  [error code]                   uint16
 1  [sql state marker '#']         byte
 5  [sql state]                    byte[5]
 n  [error message]                string<EOF>
```

**Common Error Codes:**
- 1044: Access denied for user
- 1045: Access denied (bad password)
- 1046: No database selected
- 1054: Unknown column
- 1064: SQL syntax error
- 1146: Table doesn't exist
- 2002: Connection refused
- 2003: Cannot connect to server

#### EOF Packet (Deprecated)

```
 1  [0xFE]                         uint8
 2  [warnings]                     uint16
 2  [status flags]                 uint16
```

**Note:** With `CLIENT_DEPRECATE_EOF` capability, OK packets replace EOF packets.

### Result Set Response

For queries returning data (SELECT, SHOW, etc.):

```
Client                              Server
  |                                    |
  |<-- Column Count Packet ------------|
  |<-- Column Definition Packet -------|
  |<-- Column Definition Packet -------|
  |<-- ...                              |
  |<-- EOF Packet (or OK) --------------|
  |<-- Result Row Packet ---------------|
  |<-- Result Row Packet ---------------|
  |<-- ...                              |
  |<-- EOF Packet (or OK) --------------|
```

#### Column Definition Packet

```
 n  [catalog]                      lenenc-str (usually "def")
 n  [schema]                       lenenc-str (database)
 n  [table alias]                  lenenc-str
 n  [table]                        lenenc-str (original table)
 n  [column alias]                 lenenc-str
 n  [column]                       lenenc-str (original column)
 1  [length of fixed fields]       lenenc-int (0x0C)
 2  [character set]                uint16
 4  [column length]                uint32
 1  [column type]                  uint8
 2  [column flags]                 uint16
 1  [decimals]                     uint8
 2  [filler]                       0x00 0x00
```

**Column Types:**
- 0x00: DECIMAL
- 0x01: TINY (TINYINT)
- 0x02: SHORT (SMALLINT)
- 0x03: LONG (INT)
- 0x04: FLOAT
- 0x05: DOUBLE
- 0x06: NULL
- 0x07: TIMESTAMP
- 0x08: LONGLONG (BIGINT)
- 0x09: INT24 (MEDIUMINT)
- 0x0A: DATE
- 0x0B: TIME
- 0x0C: DATETIME
- 0x0D: YEAR
- 0x0F: VARCHAR
- 0x10: BIT
- 0xF6: NEWDECIMAL
- 0xF7: ENUM
- 0xF8: SET
- 0xF9: TINY_BLOB
- 0xFA: MEDIUM_BLOB
- 0xFB: LONG_BLOB
- 0xFC: BLOB
- 0xFD: VAR_STRING
- 0xFE: STRING
- 0xFF: GEOMETRY

#### Result Row Packet (Text Protocol)

```
 n  [column value]                 lenenc-str (NULL = 0xFB)
 n  [column value]                 lenenc-str
 ...
```

Each column value is encoded as a length-encoded string. NULL is represented as 0xFB.

## Binary Protocol (Prepared Statements)

Binary protocol uses efficient binary encoding for parameters and results.

### Prepared Statement Lifecycle

```
Client                              Server
  |                                    |
  |--- COM_STMT_PREPARE -------------->|
  |    (SQL with ? placeholders)       |
  |                                    |
  |<-- Prepared Statement Response ----|
  |    (statement ID, param count)     |
  |                                    |
  |--- COM_STMT_EXECUTE -------------->|
  |    (statement ID + binary params)  |
  |                                    |
  |<-- Binary Result Set --------------|
  |                                    |
  |--- COM_STMT_CLOSE ---------------->|
```

### COM_STMT_PREPARE Response

```
 1  [0x00]                         uint8 (OK)
 4  [statement id]                 uint32
 2  [number of columns]            uint16
 2  [number of parameters]         uint16
 1  [filler]                       0x00
 2  [warning count]                uint16
```

Followed by parameter and column definitions if count > 0.

### COM_STMT_EXECUTE Packet

```
 1  [0x17]                         uint8 (COM_STMT_EXECUTE)
 4  [statement id]                 uint32
 1  [flags]                        uint8
 4  [iteration count]              uint32 (always 1)
 n  [null bitmap]                  byte[(param_count + 7) / 8]
 1  [new params bound flag]        uint8
 n  [parameter types]              uint16[param_count] (if flag=1)
 n  [parameter values]             binary encoded
```

### Binary Protocol Data Types

**Integer Types:**
- TINY: 1 byte
- SHORT: 2 bytes (little-endian)
- LONG: 4 bytes (little-endian)
- LONGLONG: 8 bytes (little-endian)

**Floating Point:**
- FLOAT: 4 bytes (IEEE 754)
- DOUBLE: 8 bytes (IEEE 754)

**Temporal Types:**
- DATE: 4 bytes (year, month, day)
- TIME: 8-12 bytes (neg, days, hours, mins, secs, micros)
- DATETIME: 7-11 bytes (year, month, day, hour, min, sec, micro)
- TIMESTAMP: Same as DATETIME

**String Types:**
- All string types encoded as length-encoded strings

**NULL:**
- Indicated by NULL bitmap (1 bit per parameter)

## Data Encoding

### Length-Encoded Integer (lenenc-int)

```
If value < 0xFB         -> 1 byte
If value = 0xFC         -> 2 bytes following
If value = 0xFD         -> 3 bytes following
If value = 0xFE         -> 8 bytes following
If value = 0xFB         -> NULL (in specific contexts)
```

### Length-Encoded String (lenenc-str)

```
 n  [length]                       lenenc-int
 n  [string]                       byte[length]
```

### Fixed-Length Integer

All multi-byte integers are little-endian:
- uint16: 2 bytes
- uint24: 3 bytes
- uint32: 4 bytes
- uint64: 8 bytes

### NULL-Terminated String (string<NUL>)

String ending with 0x00 byte.

### End-of-Packet String (string<EOF>)

String extending to end of packet (no terminator or length).

## Compression

When compression is enabled (capability flag):

1. Client and server negotiate compression
2. After handshake, all packets are compressed
3. Compressed packet format:

```
 3  [compressed payload length]    uint24
 1  [sequence id]                  uint8
 3  [uncompressed payload length]  uint24 (0 if uncompressed)
 n  [compressed payload]           byte[n]
```

**Compression Algorithm:** zlib (deflate)

**Compression Decision:**
- If compressed size >= uncompressed, send uncompressed (length = 0)
- Small packets may not benefit from compression

## SSL/TLS Encryption

### SSL Handshake Flow

```
Client                              Server
  |                                    |
  |<-- Initial Handshake Packet -------|
  |    (with CLIENT_SSL capability)    |
  |                                    |
  |--- SSL Request Packet ------------>|
  |    (capabilities, no auth data)    |
  |                                    |
  [SSL/TLS Handshake]
  |                                    |
  |--- Handshake Response (encrypted)->|
  |                                    |
  |<-- OK Packet (encrypted) ----------|
```

### SSL Request Packet

```
 4  [capability flags]             uint32 (with CLIENT_SSL)
 4  [max packet size]              uint32
 1  [character set]                uint8
23  [reserved]                     byte[23] (0x00)
```

After sending, client initiates TLS handshake. All subsequent packets are encrypted.

### SSL Configuration

Server variables:
- `require_secure_transport`: Force SSL for all connections
- `ssl_ca`, `ssl_cert`, `ssl_key`: Certificate configuration
- `tls_version`: Allowed TLS versions (TLSv1.2, TLSv1.3)

Client options:
- `--ssl-mode`: DISABLED, PREFERRED, REQUIRED, VERIFY_CA, VERIFY_IDENTITY
- `--ssl-ca`, `--ssl-cert`, `--ssl-key`: Certificate paths

## Replication Protocol

MySQL protocol includes extensions for master-replica replication:

### COM_BINLOG_DUMP (0x12)

Request binary log events from master.

```
 1  [0x12]                         uint8
 4  [binlog position]              uint32
 2  [flags]                        uint16
 4  [server id]                    uint32
 n  [binlog filename]              string<EOF>
```

### COM_BINLOG_DUMP_GTID (0x1E)

Request binary log with GTID (Global Transaction ID).

```
 1  [0x1E]                         uint8
 2  [flags]                        uint16
 4  [server id]                    uint32
 4  [binlog filename length]       uint32
 n  [binlog filename]              byte[n]
 8  [binlog position]              uint64
 4  [data size]                    uint32
 n  [GTID data]                    byte[n]
```

### COM_REGISTER_SLAVE (0x15)

Register as replica to master.

```
 1  [0x15]                         uint8
 4  [server id]                    uint32
 1  [hostname length]              uint8
 n  [hostname]                     byte[n]
 1  [username length]              uint8
 n  [username]                     byte[n]
 1  [password length]              uint8
 n  [password]                     byte[n]
 2  [port]                         uint16
 4  [replication rank]             uint32
 4  [master id]                    uint32
```

## Load Data Infile

Special protocol for loading data from file:

```
Client                              Server
  |                                    |
  |--- COM_QUERY (LOAD DATA) --------->|
  |                                    |
  |<-- Local Infile Request ------------|
  |    (filename)                      |
  |                                    |
  |--- File Data Packets -------------->|
  |--- Empty Packet (end) ------------>|
  |                                    |
  |<-- OK Packet -----------------------|
```

**Security Consideration:** `local_infile` can be security risk; disabled by default in modern MySQL.

## Multi-Statement and Multi-Result

With `CLIENT_MULTI_STATEMENTS` and `CLIENT_MULTI_RESULTS`:

### Multi-Statement Query

```sql
SELECT * FROM users; UPDATE users SET active=1; SELECT COUNT(*) FROM users;
```

Server processes all statements and returns multiple result sets.

### Response Sequence

```
[Result Set 1]
[OK Packet with SERVER_MORE_RESULTS_EXISTS flag]
[Result Set 2]
[OK Packet with SERVER_MORE_RESULTS_EXISTS flag]
[Result Set 3]
[OK Packet without flag]
```

## Error Handling

### Client Error Handling

1. Check packet type (0xFF = error)
2. Extract error code and SQLSTATE
3. Log error message
4. Handle specific error codes
5. Retry or abort as appropriate

### Server Error Conditions

- **Connection errors:** Authentication failure, max connections
- **Query errors:** Syntax errors, permission denied
- **Data errors:** Constraint violations, data type mismatches
- **Resource errors:** Out of memory, disk full

### Connection Recovery

- Reconnect on connection loss
- Re-authenticate
- Restore session state (database, variables, prepared statements)
- Replay or rollback uncommitted transactions

## Performance Considerations

### Optimization Techniques

1. **Use Prepared Statements:** Reduce parsing overhead
2. **Binary Protocol:** More efficient than text protocol
3. **Compression:** Reduce network bandwidth (at cost of CPU)
4. **Pipelining:** Send multiple queries without waiting
5. **Connection Pooling:** Reuse connections to avoid handshake overhead
6. **SSL Session Resumption:** Reduce TLS handshake overhead

### Benchmarking

- **Latency:** Time from COM_QUERY to first result packet
- **Throughput:** Queries per second
- **Connection overhead:** Time to establish connection
- **Protocol overhead:** Packet header and encoding overhead

## Implementation Notes

### Client Libraries

Popular MySQL protocol implementations:

- **libmysqlclient:** Official C library
- **MySQL Connector/J:** Java (JDBC)
- **MySQL Connector/Python:** Python
- **MySQL Connector/NET:** .NET
- **PyMySQL:** Pure Python implementation
- **mysql2:** Node.js
- **go-sql-driver/mysql:** Go
- **mysqlclient-sys:** Rust

### Common Pitfalls

1. **Sequence ID:** Must increment correctly or server rejects packets
2. **Packet Splitting:** Payloads > 16MB require special handling
3. **NULL Encoding:** Different in text vs binary protocol
4. **Endianness:** All integers are little-endian
5. **Character Encoding:** Must match server encoding or use utf8mb4
6. **Compression:** Only applies after authentication
7. **SSL Timing:** Must send SSL request before TLS handshake

### Debugging Tools

- **Wireshark:** MySQL protocol dissector built-in
- **tcpdump:** Capture raw packets
- **MySQL General Log:** Server-side query logging
- **Performance Schema:** Monitor protocol operations
- **mysqlslap:** Protocol-level load testing

## Security Considerations

### Authentication Security

- **Default Plugin:** Use `caching_sha2_password` (MySQL 8.0+)
- **Avoid Legacy:** Don't use `mysql_native_password` if possible
- **SSL Required:** Force SSL for password transmission
- **Certificate Validation:** Use VERIFY_IDENTITY mode

### Connection Security

- **Principle of Least Privilege:** Grant minimal necessary permissions
- **Network Isolation:** Bind to localhost or private network
- **Firewall Rules:** Restrict access to MySQL port
- **SSL/TLS:** Always use encryption for remote connections

### Protocol Security

- **SQL Injection:** Always use prepared statements with parameters
- **Buffer Overflows:** Validate packet lengths
- **Resource Exhaustion:** Limit max packet size, connection count
- **Local Infile:** Disable `local_infile` unless necessary

## Version Differences

### MySQL 5.7 vs 8.0

- **Default Auth Plugin:** `mysql_native_password` → `caching_sha2_password`
- **Deprecated EOF:** `CLIENT_DEPRECATE_EOF` recommended
- **Improved Compression:** zstd compression algorithm support
- **Better SSL:** TLS 1.3 support

### MySQL vs MariaDB

MariaDB maintains protocol compatibility but adds extensions:

- **Extended Capabilities:** Additional capability flags
- **Bulk Operations:** Enhanced bulk insert protocols
- **Progress Reporting:** Server progress reports during long queries
- **Multi-Source Replication:** Enhanced replication protocols

## References

- **MySQL Protocol Documentation:** https://dev.mysql.com/doc/dev/mysql-server/9.3.0/PAGE_PROTOCOL.html
- **MySQL Internals Manual:** https://dev.mysql.com/doc/internals/en/
- **MariaDB Protocol:** https://mariadb.com/kb/en/clientserver-protocol/
- **MySQL Source Code:** https://github.com/mysql/mysql-server
- **Protocol Implementation Examples:** Various client library source code

## Related Standards

- **SQL Standard:** ISO/IEC 9075
- **TLS:** RFC 8446
- **TCP:** RFC 9293
- **zlib Compression:** RFC 1950, RFC 1951
- **Character Encodings:** UTF-8 (RFC 3629), Unicode
