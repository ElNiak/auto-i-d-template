# PostgreSQL Wire Protocol

## Overview

The PostgreSQL Frontend/Backend Protocol is a message-based communication protocol for client-server interaction. It operates over TCP/IP and Unix-domain sockets, typically using port 5432.

**Current Version:** Protocol 3.2 (introduced in PostgreSQL 18)
**Backward Compatibility:** Compatible with Protocol 3.0 (PostgreSQL 7.4+)

## Official Documentation

- **Main Protocol Documentation:** https://www.postgresql.org/docs/current/protocol.html
- **Protocol Overview:** https://www.postgresql.org/docs/current/protocol-overview.html
- **Protocol Flow:** https://www.postgresql.org/docs/current/protocol-flow.html
- **Message Formats:** https://www.postgresql.org/docs/current/protocol-message-formats.html
- **SSL/TLS:** https://www.postgresql.org/docs/current/ssl-tcp.html

## Architecture

### Connection Model

- Server launches a separate backend process for each client connection
- Client and server communicate through bidirectional message exchange
- Messages are tagged with type identifiers and include length prefixes
- Binary-safe protocol supporting both text and binary data formats

### Transport Layer

- **TCP/IP:** Standard network connections on any non-privileged port
- **Unix Domain Sockets:** Local connections on Unix-like systems
- **SSL/TLS Encryption:** Optional secure session encryption
- **GSSAPI Encryption:** Optional GSSAPI-based session encryption

## Protocol Flow

### 1. Connection Establishment

```
Client                                Server
  |                                      |
  |--- StartupMessage ------------------>|
  |    (protocol version, parameters)    |
  |                                      |
  |<-- AuthenticationRequest ------------|
  |    (authentication method)           |
  |                                      |
  |--- Authentication Response --------->|
  |    (credentials)                     |
  |                                      |
  |<-- AuthenticationOk -----------------|
  |<-- ParameterStatus ------------------|
  |<-- BackendKeyData -------------------|
  |<-- ReadyForQuery --------------------|
```

**StartupMessage Contents:**
- Protocol version number (currently 196608 for 3.0)
- User name
- Database name
- Optional parameters (application_name, client_encoding, etc.)

### 2. Authentication Methods

The server selects one of several authentication methods:

- **AuthenticationOk:** No authentication required
- **AuthenticationCleartextPassword:** Plain text password
- **AuthenticationMD5Password:** MD5-hashed password with salt
- **AuthenticationSASL:** SASL authentication framework
  - **SCRAM-SHA-256:** Preferred secure method
- **AuthenticationGSS:** GSSAPI/Kerberos
- **AuthenticationSSPI:** Windows SSPI
- **AuthenticationKerberosV5:** Legacy Kerberos (deprecated)
- **OAUTHBEARER:** OAuth 2.0 bearer token authentication

### 3. Query Execution Modes

#### A. Simple Query Protocol

```
Client                                Server
  |                                      |
  |--- Query (SQL string) -------------->|
  |                                      |
  |<-- RowDescription -------------------|
  |<-- DataRow --------------------------|
  |<-- DataRow --------------------------|
  |<-- ... ------------------------------|
  |<-- CommandComplete ------------------|
  |<-- ReadyForQuery --------------------|
```

**Characteristics:**
- Entire SQL statement sent as single message
- Server processes immediately
- Supports multiple statements separated by semicolons
- Results returned as text strings

#### B. Extended Query Protocol

```
Client                                Server
  |                                      |
  |--- Parse (SQL with placeholders) --->|
  |<-- ParseComplete --------------------|
  |                                      |
  |--- Bind (parameters) --------------->|
  |<-- BindComplete ----------------------|
  |                                      |
  |--- Describe ------------------------>|
  |<-- RowDescription -------------------|
  |                                      |
  |--- Execute ------------------------->|
  |<-- DataRow --------------------------|
  |<-- DataRow --------------------------|
  |<-- CommandComplete ------------------|
  |                                      |
  |--- Sync ---------------------------->|
  |<-- ReadyForQuery --------------------|
```

**Characteristics:**
- Separates query parsing, binding, and execution
- Supports parameterized queries with type-safe binding
- Allows query plan caching and reuse
- Supports binary data formats for parameters and results
- Enables portal cursors for partial result fetching

#### C. Pipelining

- Client can send multiple requests without waiting for responses
- Server processes requests in order
- Responses sent back in same order
- Improves latency in high-latency networks
- Available in both Simple and Extended Query protocols

### 4. COPY Operations

#### COPY IN (Client to Server)

```
Client                                Server
  |                                      |
  |--- Query (COPY FROM STDIN) --------->|
  |<-- CopyInResponse -------------------|
  |                                      |
  |--- CopyData ----------------------->|
  |--- CopyData ----------------------->|
  |--- CopyDone or CopyFail ------------>|
  |                                      |
  |<-- CommandComplete ------------------|
  |<-- ReadyForQuery --------------------|
```

#### COPY OUT (Server to Client)

```
Client                                Server
  |                                      |
  |--- Query (COPY TO STDOUT) ---------->|
  |<-- CopyOutResponse ------------------|
  |<-- CopyData -------------------------|
  |<-- CopyData -------------------------|
  |<-- CopyDone -------------------------|
  |<-- CommandComplete ------------------|
  |<-- ReadyForQuery --------------------|
```

### 5. Function Calls

```
Client                                Server
  |                                      |
  |--- FunctionCall ------------------->|
  |    (OID, arguments)                  |
  |                                      |
  |<-- FunctionCallResponse -------------|
  |    (return value)                    |
  |<-- ReadyForQuery --------------------|
```

**Note:** Function call protocol is legacy; use SQL `SELECT function(args)` instead.

### 6. Asynchronous Operations

Server can send unsolicited messages at any time:

- **NoticeResponse:** Warning or informational messages
- **NotificationResponse:** LISTEN/NOTIFY pub/sub messages
- **ParameterStatus:** Runtime parameter changes

### 7. Connection Termination

#### Graceful Termination

```
Client                                Server
  |                                      |
  |--- Terminate ----------------------->|
  |                                      |
  [Connection closed]
```

- Any open transaction is automatically rolled back
- Server releases all resources

#### Forced Termination

- Client closes connection without Terminate message
- Server detects disconnection and rolls back transaction
- Can use `pg_terminate_backend()` to force disconnect

## Message Format Structure

All messages (except StartupMessage and SSLRequest) follow this structure:

```
+--------+----------+--------+
| Type   | Length   | Data   |
| (1B)   | (4B)     | (N-4B) |
+--------+----------+--------+
```

- **Type:** Single ASCII character identifying message type
- **Length:** Int32 length of message (includes self, excludes Type byte)
- **Data:** Message-specific payload

### Message Direction Indicators

- **(F)** Frontend (client) only
- **(B)** Backend (server) only
- **(F & B)** Can be sent by either

## Key Message Types

### Connection Phase

| Type | Name | Direction | Description |
|------|------|-----------|-------------|
| - | StartupMessage | F | Initial connection with protocol version |
| - | SSLRequest | F | Request SSL before startup |
| R | Authentication* | B | Authentication challenges |
| p | PasswordMessage | F | Password response |
| K | BackendKeyData | B | Process ID and secret for cancel requests |
| S | ParameterStatus | B | Runtime parameter values |
| Z | ReadyForQuery | B | Ready for new query (with transaction status) |
| X | Terminate | F | Close connection |

### Query Phase

| Type | Name | Direction | Description |
|------|------|-----------|-------------|
| Q | Query | F | Simple query (SQL string) |
| P | Parse | F | Parse SQL with placeholders |
| B | Bind | F | Bind parameters to parsed statement |
| E | Execute | F | Execute portal |
| D | Describe | F | Describe statement or portal |
| C | Close | F | Close statement or portal |
| S | Sync | F | Synchronization point |
| 1 | ParseComplete | B | Parse completed successfully |
| 2 | BindComplete | B | Bind completed successfully |
| 3 | CloseComplete | B | Close completed successfully |
| T | RowDescription | B | Describes fields in result rows |
| D | DataRow | B | Single row of query results |
| C | CommandComplete | B | Command completed with tag |
| I | EmptyQueryResponse | B | Query string was empty |

### COPY Operations

| Type | Name | Direction | Description |
|------|------|-----------|-------------|
| G | CopyInResponse | B | Ready to receive COPY data |
| H | CopyOutResponse | B | Ready to send COPY data |
| d | CopyData | F & B | COPY data stream |
| c | CopyDone | F & B | COPY completed successfully |
| f | CopyFail | F | COPY aborted by client |

### Function Calls

| Type | Name | Direction | Description |
|------|------|-----------|-------------|
| F | FunctionCall | F | Call server-side function |
| V | FunctionCallResponse | B | Function return value |

### Error and Notice

| Type | Name | Direction | Description |
|------|------|-----------|-------------|
| E | ErrorResponse | B | Error occurred |
| N | NoticeResponse | B | Warning or informational message |

### Asynchronous

| Type | Name | Direction | Description |
|------|------|-----------|-------------|
| A | NotificationResponse | B | LISTEN/NOTIFY notification |
| S | ParameterStatus | B | Runtime parameter changed |

## Data Type Representation

### Text Format

- All values encoded as text strings
- Numbers as ASCII decimal
- Strings as-is (with proper escaping)
- NULLs as absence of data
- Character encoding specified in connection parameters

### Binary Format

Each data type has a specific binary encoding:

**Integers:**
- INT2: 2 bytes, network byte order (big-endian)
- INT4: 4 bytes, network byte order
- INT8: 8 bytes, network byte order

**Floating Point:**
- FLOAT4: 4 bytes, IEEE 754 single precision
- FLOAT8: 8 bytes, IEEE 754 double precision

**Numeric:**
- Custom format with sign, weight, scale, and digit array

**Strings/Text:**
- Raw bytes in specified character encoding
- No null terminator

**Timestamps:**
- 8 bytes, microseconds since 2000-01-01 00:00:00 UTC

**Arrays:**
- Dimension count, flags, element OID, then dimension data

**NULL Values:**
- Indicated by -1 length field in DataRow messages

## Error Handling

### ErrorResponse Structure

ErrorResponse messages contain multiple fields:

- **S** Severity: ERROR, FATAL, PANIC, WARNING, NOTICE, etc.
- **C** SQLSTATE code: 5-character SQL standard error code
- **M** Message: Primary human-readable error message
- **D** Detail: Optional detailed error description
- **H** Hint: Optional suggestion for fixing the error
- **P** Position: Character position in query where error occurred
- **W** Where: Context of error (function name, etc.)
- **F** File: Source code file where error was generated
- **L** Line: Line number in source code
- **R** Routine: Function name in source code

### Transaction States

ReadyForQuery message includes transaction status:

- **I** Idle (no transaction)
- **T** In transaction block
- **E** Failed transaction (commands ignored until rollback)

## Security Features

### SSL/TLS Encryption

1. Client sends SSLRequest message
2. Server responds with 'S' (supported) or 'N' (not supported)
3. If supported, client initiates TLS handshake
4. After TLS established, client sends StartupMessage

### Authentication Security

- **SCRAM-SHA-256:** Modern password authentication with:
  - Salt and iteration count for password hashing
  - Mutual authentication (server proves it knows password)
  - Channel binding support
  - Protection against replay attacks

- **MD5 (legacy):** Uses MD5(MD5(password + username) + salt)
  - Deprecated due to MD5 weaknesses
  - Still supported for compatibility

### GSSAPI/Kerberos

- Industry-standard authentication framework
- Supports encryption in addition to authentication
- Common in enterprise environments

### OAuth Bearer Tokens

- Support for modern OAuth 2.0 bearer tokens
- Introduced for cloud and API gateway integration

## Streaming Replication

PostgreSQL protocol includes extensions for streaming replication:

- **START_REPLICATION:** Begin streaming WAL (Write-Ahead Log)
- **Standby Status Messages:** Feedback from replica to primary
- **WAL Sender:** Server process that streams WAL data
- **Logical Replication:** Stream logical changesets instead of physical WAL

## Protocol Versioning

### Version Negotiation

- Client specifies protocol version in StartupMessage
- Server responds with NegotiateProtocolVersion if version mismatch
- Server lists supported minor protocol versions
- Client can downgrade and retry connection

### Protocol Evolution

- **3.0 (PostgreSQL 7.4):** First modern protocol version
- **3.1:** Added streaming replication support
- **3.2 (PostgreSQL 18):** Added new features and message types

Minor version changes maintain backward compatibility.

## Implementation Considerations

### Client Libraries

Popular PostgreSQL client libraries implementing this protocol:

- **libpq:** Official C library
- **psycopg2/psycopg3:** Python
- **pg:** Node.js
- **pgx:** Go
- **jdbc-postgresql:** Java
- **pq:** Go (pure Go implementation)
- **tokio-postgres:** Rust

### Performance Optimizations

1. **Use Extended Query Protocol** for repeated queries with parameters
2. **Enable pipelining** to reduce round-trip latency
3. **Use binary format** for large result sets to reduce parsing overhead
4. **Prepared statements** for query plan caching
5. **Connection pooling** to reduce connection establishment overhead
6. **COPY protocol** for bulk data loading (much faster than INSERT)

### Debugging Tools

- **Wireshark:** Can dissect PostgreSQL protocol packets
- **pgShark:** PostgreSQL protocol analyzer
- **tcpdump:** Capture raw TCP traffic for analysis
- **Protocol-level logging:** `log_connections`, `log_statement` in postgresql.conf

## Example Message Sequences

### Simple SELECT Query

```
→ Query "SELECT * FROM users WHERE id = 1;"
← RowDescription (columns: id, name, email)
← DataRow (1, "Alice", "alice@example.com")
← CommandComplete "SELECT 1"
← ReadyForQuery (I)
```

### Extended Query with Parameters

```
→ Parse "S_1" "SELECT * FROM users WHERE id = $1"
← ParseComplete
→ Bind "P_1" "S_1" [1]
← BindComplete
→ Describe "P_1"
← RowDescription (columns: id, name, email)
→ Execute "P_1" (max rows: 0)
← DataRow (1, "Alice", "alice@example.com")
← CommandComplete "SELECT 1"
→ Sync
← ReadyForQuery (I)
```

### Failed Query in Transaction

```
→ Query "BEGIN;"
← CommandComplete "BEGIN"
← ReadyForQuery (T)
→ Query "INSERT INTO users VALUES (1);"
← ErrorResponse (duplicate key)
← ReadyForQuery (E)
→ Query "COMMIT;"
← CommandComplete "ROLLBACK"
← ReadyForQuery (I)
```

## References

- **Official Protocol Documentation:** https://www.postgresql.org/docs/current/protocol.html
- **PostgreSQL Source Code:** https://github.com/postgres/postgres/tree/master/src/backend/libpq
- **Protocol Specification History:** Various versions in https://www.postgresql.org/docs/
- **Community Wiki:** https://wiki.postgresql.org/wiki/Wire_Protocol

## Related Standards

- **SQL Standard:** ISO/IEC 9075
- **SQLSTATE Codes:** ISO/IEC 9075-2
- **SASL Framework:** RFC 4422
- **SCRAM-SHA-256:** RFC 7677
- **Kerberos:** RFC 4120
- **TLS:** RFC 8446
