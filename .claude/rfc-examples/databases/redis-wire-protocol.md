# Redis Wire Protocol (RESP)

## Overview

RESP (Redis Serialization Protocol) is the wire protocol used by Redis clients and servers to communicate. It is designed to be simple to implement, fast to parse, and human-readable.

**Current Versions:**
- **RESP2:** Introduced in Redis 2.0 (2010), standard protocol
- **RESP3:** Introduced in Redis 6.0 (2020), enhanced protocol with new data types

**Key Characteristics:**
- Binary-safe
- Human-readable ASCII protocol
- Request-response model (with Pub/Sub exceptions)
- Supports pipelining for reduced latency
- Simple length-prefixed encoding

## Official Documentation

- **RESP Specification:** https://redis.io/docs/latest/develop/reference/protocol-spec/
- **Command Reference:** https://redis.io/docs/latest/commands/
- **Client Implementation Guide:** https://redis.io/docs/latest/develop/clients/
- **RESP3 Features:** https://github.com/redis/redis-specifications/blob/master/protocol/RESP3.md

## Protocol Design Philosophy

RESP is optimized for:

1. **Simplicity:** Easy to implement in any language
2. **Performance:** Fast to parse with minimal overhead
3. **Human Readability:** Debuggable with telnet/netcat
4. **Binary Safety:** Can transmit any binary data
5. **Type Safety:** Explicit type markers for all data

## Transport

- **TCP Connection:** Standard Redis uses TCP on port 6379
- **Unix Domain Sockets:** Supported for local connections
- **TLS/SSL:** Redis 6.0+ supports TLS encryption
- **Connection Model:** Persistent connections with request pipelining

## RESP2 Data Types

RESP2 defines 5 basic data types, each prefixed with a single character:

| Prefix | Type | Description |
|--------|------|-------------|
| `+` | Simple String | Non-binary safe string |
| `-` | Error | Error message |
| `:` | Integer | Signed 64-bit integer |
| `$` | Bulk String | Binary-safe string |
| `*` | Array | Ordered collection of elements |

### Line Termination

All RESP elements end with `\r\n` (CRLF).

### 1. Simple Strings

Format: `+<string>\r\n`

**Example:**
```
+OK\r\n
```

**Use Cases:**
- Simple command responses (OK, PONG)
- Non-binary data
- Short status messages

**Limitations:**
- Cannot contain CR or LF characters
- Not binary-safe
- For most data, Bulk Strings are preferred

### 2. Errors

Format: `-<error type> <error message>\r\n`

**Example:**
```
-ERR unknown command 'foobar'\r\n
-WRONGTYPE Operation against a key holding the wrong kind of value\r\n
```

**Error Types (Convention):**
- `ERR`: Generic error
- `WRONGTYPE`: Wrong data type for operation
- `NOSCRIPT`: Script doesn't exist
- `MOVED`: Cluster redirect (slot moved)
- `ASK`: Cluster redirect (slot migrating)
- `CLUSTERDOWN`: Cluster is down
- `CROSSSLOT`: Multi-key operation on different slots
- `TRYAGAIN`: Try command again later

**Client Handling:**
- Treat errors as exceptions
- Don't parse error message programmatically (use error type)

### 3. Integers

Format: `:<number>\r\n`

**Examples:**
```
:0\r\n
:1000\r\n
:-1\r\n
```

**Use Cases:**
- Command return values (INCR, DECR, LLEN, SCARD)
- Boolean flags (0 = false, 1 = true)
- Array lengths
- Existence checks (-1 = doesn't exist)

**Range:** Signed 64-bit integers (-9,223,372,036,854,775,808 to 9,223,372,036,854,775,807)

### 4. Bulk Strings

Format: `$<length>\r\n<data>\r\n`

**Examples:**

Simple bulk string:
```
$5\r\nHello\r\n
```

Empty bulk string:
```
$0\r\n\r\n
```

NULL bulk string:
```
$-1\r\n
```

Binary data:
```
$10\r\nHello\x00\x01\x02\x03\r\n
```

**Use Cases:**
- Command arguments
- String values from database
- Binary data (images, serialized objects)
- NULL representation

**Key Features:**
- Binary-safe (can contain any byte sequence)
- Length-prefixed (no escaping needed)
- Efficient for large data

### 5. Arrays

Format: `*<count>\r\n<element1><element2>...<elementN>`

**Examples:**

Simple array:
```
*3\r\n
$3\r\nSET\r\n
$3\r\nkey\r\n
$5\r\nvalue\r\n
```

Empty array:
```
*0\r\n
```

NULL array:
```
*-1\r\n
```

Mixed types:
```
*5\r\n
:1\r\n
:2\r\n
:3\r\n
:4\r\n
$5\r\nHello\r\n
```

Nested arrays:
```
*2\r\n
*3\r\n
:1\r\n
:2\r\n
:3\r\n
*2\r\n
+Hello\r\n
-ERR error\r\n
```

**Use Cases:**
- Client commands (always sent as arrays)
- Multi-bulk replies (LRANGE, SMEMBERS, HGETALL)
- Nested data structures

## RESP3 Data Types

RESP3 is backward compatible with RESP2 and adds new types:

| Prefix | Type | Description |
|--------|------|-------------|
| `_` | Null | Explicit NULL value |
| `#` | Boolean | True or false |
| `,` | Double | Floating-point number |
| `(` | Big Number | Arbitrary precision integer |
| `!` | Bulk Error | Error with additional structure |
| `=` | Verbatim String | String with encoding/format |
| `%` | Map | Key-value map (dictionary) |
| `~` | Set | Unordered collection |
| `>` | Push | Server push data (Pub/Sub) |

### RESP3 Additional Types

#### Null

Format: `_\r\n`

**Example:**
```
_\r\n
```

Replaces `$-1\r\n` and `*-1\r\n` for clearer NULL representation.

#### Boolean

Format: `#t\r\n` (true) or `#f\r\n` (false)

**Examples:**
```
#t\r\n
#f\r\n
```

Better than using integers for boolean values.

#### Double

Format: `,<floating-point>\r\n`

**Examples:**
```
,1.23\r\n
,inf\r\n
,-inf\r\n
,nan\r\n
```

For floating-point numbers (INCRBYFLOAT, ZSCORE).

#### Big Number

Format: `(<decimal-string>\r\n`

**Example:**
```
(3492890328409238509324850943850943825024385\r\n
```

For integers beyond 64-bit range.

#### Bulk Error

Format: `!<length>\r\n<error>\r\n`

**Example:**
```
!21\r\nSYNTAX invalid syntax\r\n
```

Structured error with machine-readable error code.

#### Verbatim String

Format: `=<length>\r\n<encoding>:<data>\r\n`

**Example:**
```
=15\r\ntxt:Some string\r\n
=20\r\nmkd:# Markdown header\r\n
```

String with metadata about encoding/format (txt, mkd, etc.).

#### Map

Format: `%<count>\r\n<key1><value1><key2><value2>...`

**Example:**
```
%2\r\n
+first\r\n
:1\r\n
+second\r\n
:2\r\n
```

Represents hash/dictionary (HGETALL returns this in RESP3).

#### Set

Format: `~<count>\r\n<element1><element2>...`

**Example:**
```
~5\r\n
+apple\r\n
+banana\r\n
+cherry\r\n
+date\r\n
+elderberry\r\n
```

Unordered collection (SMEMBERS returns this in RESP3).

#### Push

Format: `><count>\r\n<element1><element2>...`

**Example:**
```
>3\r\n
+message\r\n
+channel\r\n
+Hello\r\n
```

Server-initiated push data (Pub/Sub messages, keyspace notifications).

## Request Format

### Client to Server: Commands

**All commands sent as RESP Arrays:**

```
*<argument-count>\r\n
$<arg1-length>\r\n<arg1>\r\n
$<arg2-length>\r\n<arg2>\r\n
...
```

**Examples:**

SET command:
```
*3\r\n
$3\r\nSET\r\n
$4\r\nname\r\n
$5\r\nAlice\r\n
```

GET command:
```
*2\r\n
$3\r\nGET\r\n
$4\r\nname\r\n
```

LPUSH with multiple values:
```
*4\r\n
$5\r\nLPUSH\r\n
$6\r\nmylist\r\n
$5\r\nworld\r\n
$5\r\nhello\r\n
```

### Inline Commands

For human interaction (telnet, redis-cli), Redis supports inline commands:

```
GET mykey\r\n
SET mykey "some value"\r\n
PING\r\n
```

**Parsing:**
- Split by spaces
- Quoted strings supported
- Newline-terminated
- Only for manual interaction, clients should use RESP arrays

## Response Format

### Server to Client: Replies

Server responds with any RESP data type:

**Success:**
```
+OK\r\n
```

**Integer result:**
```
:42\r\n
```

**String result:**
```
$11\r\nHello World\r\n
```

**Array result:**
```
*2\r\n
$5\r\nhello\r\n
$5\r\nworld\r\n
```

**NULL:**
```
$-1\r\n          (RESP2)
_\r\n             (RESP3)
```

**Error:**
```
-ERR unknown command 'foobar'\r\n
```

## Protocol Upgrade: RESP2 → RESP3

### Using HELLO Command

```
Client                              Server
  |                                    |
  |--- *2\r\n                           |
  |    $5\r\nHELLO\r\n                  |
  |    $1\r\n3\r\n                      |
  |    (request RESP3) --------------->|
  |                                    |
  |<-- %7\r\n                           |
  |    (Map with server info)          |
```

**HELLO Command:**
- Negotiates protocol version
- Returns server information (version, mode, role, modules)
- Can include AUTH username/password
- Optional SETNAME for connection naming

**Example HELLO 3:**
```
*2\r\n
$5\r\nHELLO\r\n
$1\r\n3\r\n
```

**Response (RESP3 Map):**
```
%7\r\n
+server\r\n
+redis\r\n
+version\r\n
+7.0.0\r\n
+proto\r\n
:3\r\n
+mode\r\n
+standalone\r\n
+role\r\n
+master\r\n
+modules\r\n
*0\r\n
```

### Backward Compatibility

- RESP3 servers support both RESP2 and RESP3 clients
- Default is RESP2 unless HELLO 3 sent
- RESP3 features gracefully degrade to RESP2 equivalents:
  - Map → Array of key-value pairs
  - Set → Array
  - Boolean → Integer (0/1)
  - Double → Bulk String
  - Null → Null bulk string

## Pipelining

Client can send multiple commands without waiting for responses:

```
Client                              Server
  |                                    |
  |--- Command 1 ---------------------->|
  |--- Command 2 ---------------------->|
  |--- Command 3 ---------------------->|
  |                                    |
  |<-- Response 1 -----------------------|
  |<-- Response 2 -----------------------|
  |<-- Response 3 -----------------------|
```

**Benefits:**
- Reduces round-trip latency
- Improves throughput significantly
- Essential for high-performance applications

**Example:**

Send:
```
*2\r\n$4\r\nINCR\r\n$1\r\nX\r\n
*2\r\n$4\r\nINCR\r\n$1\r\nX\r\n
*2\r\n$4\r\nINCR\r\n$1\r\nX\r\n
```

Receive:
```
:1\r\n
:2\r\n
:3\r\n
```

**Considerations:**
- Responses arrive in same order as requests
- Memory buffer required for pending requests
- Error in one command doesn't affect others (unless MULTI/EXEC)

## Transactions (MULTI/EXEC)

### Transaction Flow

```
Client                              Server
  |                                    |
  |--- MULTI --------------------------->|
  |<-- +OK --------------------------------|
  |                                    |
  |--- Command 1 ---------------------->|
  |<-- +QUEUED ----------------------------|
  |                                    |
  |--- Command 2 ---------------------->|
  |<-- +QUEUED ----------------------------|
  |                                    |
  |--- EXEC --------------------------->|
  |<-- *2\r\n (Array of results) ---------|
  |    [Result 1]                      |
  |    [Result 2]                      |
```

**MULTI:**
- Starts transaction block
- All commands are queued, not executed

**EXEC:**
- Executes all queued commands atomically
- Returns array of results (one per command)

**DISCARD:**
- Cancels transaction
- Discards all queued commands

**WATCH:**
- Optimistic locking
- EXEC fails if watched keys modified

### Example Transaction

Request:
```
*1\r\n$5\r\nMULTI\r\n
*3\r\n$3\r\nSET\r\n$3\r\nkey\r\n$5\r\nvalue\r\n
*2\r\n$3\r\nGET\r\n$3\r\nkey\r\n
*1\r\n$4\r\nEXEC\r\n
```

Response:
```
+OK\r\n
+QUEUED\r\n
+QUEUED\r\n
*2\r\n
+OK\r\n
$5\r\nvalue\r\n
```

## Pub/Sub Protocol

### Subscribe Flow

```
Client                              Server
  |                                    |
  |--- SUBSCRIBE channel1 ------------->|
  |<-- *3\r\n (Subscribe confirmation) ---|
  |                                    |
  [Server publishes to channel1]
  |                                    |
  |<-- *3\r\n (Message) -------------------|
  |    +message\r\n                    |
  |    +channel1\r\n                   |
  |    $11\r\nHello World\r\n          |
```

### RESP2 Pub/Sub Messages

**Subscribe Confirmation:**
```
*3\r\n
+subscribe\r\n
+channel-name\r\n
:1\r\n                (subscription count)
```

**Published Message:**
```
*3\r\n
+message\r\n
+channel-name\r\n
$<length>\r\n<data>\r\n
```

**Unsubscribe Confirmation:**
```
*3\r\n
+unsubscribe\r\n
+channel-name\r\n
:0\r\n                (subscription count)
```

### RESP3 Pub/Sub Messages

Uses Push type (`>` prefix):

**Subscribe Confirmation:**
```
>3\r\n
+subscribe\r\n
+channel-name\r\n
:1\r\n
```

**Published Message:**
```
>3\r\n
+message\r\n
+channel-name\r\n
$<length>\r\n<data>\r\n
```

**Advantages:**
- Distinguishes push messages from command responses
- Allows commands while subscribed (in RESP3)
- Clearer protocol semantics

### Pattern Subscribe

```
*2\r\n
$10\r\nPSUBSCRIBE\r\n
$7\r\nchannel.*\r\n
```

Response includes both pattern and actual channel:
```
*4\r\n
+pmessage\r\n
+channel.*\r\n
+channel.1\r\n
$4\r\ndata\r\n
```

## Cluster Protocol Extensions

### MOVED Redirection

When key is on different node:

```
-MOVED 3999 127.0.0.1:6381\r\n
```

Client should:
1. Update cluster topology cache
2. Retry command on correct node

### ASK Redirection

During slot migration:

```
-ASK 3999 127.0.0.1:6381\r\n
```

Client should:
1. Send ASKING command to target node
2. Retry original command on target
3. Don't update topology cache

### CLUSTER Commands

Special commands for cluster management:
- `CLUSTER NODES`: Get cluster topology
- `CLUSTER SLOTS`: Get slot mapping
- `CLUSTER MEET`: Join cluster
- `CLUSTER REPLICATE`: Become replica

## Streams Protocol

Redis Streams use special RESP structures:

### XREAD Response (RESP2)

```
*1\r\n                         (number of streams)
*2\r\n                         (stream entry)
$6\r\nmystream\r\n              (stream key)
*2\r\n                         (messages)
*2\r\n                         (message 1)
$15\r\n1526999352406-0\r\n      (message ID)
*4\r\n                         (field-value pairs)
$5\r\nfield1\r\n
$6\r\nvalue1\r\n
$5\r\nfield2\r\n
$6\r\nvalue2\r\n
```

### XREAD Response (RESP3)

```
%1\r\n                         (map: stream -> messages)
$6\r\nmystream\r\n              (stream key)
*1\r\n                         (messages array)
*2\r\n                         (message 1)
$15\r\n1526999352406-0\r\n      (message ID)
%2\r\n                         (field-value map)
$5\r\nfield1\r\n
$6\r\nvalue1\r\n
$5\r\nfield2\r\n
$6\r\nvalue2\r\n
```

Maps make streams more intuitive in RESP3.

## Lua Scripting Protocol

### EVAL Command

```
*4\r\n
$4\r\nEVAL\r\n
$44\r\nreturn {KEYS[1],KEYS[2],ARGV[1],ARGV[2]}\r\n
$1\r\n2\r\n                     (number of keys)
$4\r\nkey1\r\n
$4\r\nkey2\r\n
$5\r\nfirst\r\n
$6\r\nsecond\r\n
```

### Script Replies

Lua return values map to RESP:
- Lua number → RESP Integer
- Lua string → RESP Bulk String
- Lua table (array) → RESP Array
- Lua table (dict) → RESP Array (pairs) in RESP2, Map in RESP3
- Lua boolean → RESP Integer (0/1) in RESP2, Boolean in RESP3
- Lua nil → RESP Null

### EVALSHA

Uses SHA1 hash of script:

```
*3\r\n
$7\r\nEVALSHA\r\n
$40\r\n<sha1-hash>\r\n
$1\r\n0\r\n
```

If script not cached:
```
-NOSCRIPT No matching script. Please use EVAL.\r\n
```

Client should then send full EVAL command.

## Performance Characteristics

### Parsing Efficiency

RESP design enables efficient parsing:

1. **Single character type prefix:** O(1) type identification
2. **Length-prefixed strings:** No escaping, direct buffer copy
3. **Line-oriented:** Simple buffer scanning for `\r\n`
4. **No nested length calculation:** Each element self-contained

### Bandwidth Overhead

**Protocol overhead examples:**

Simple string "OK":
```
+OK\r\n               (5 bytes)
```

Bulk string "Hello":
```
$5\r\nHello\r\n      (12 bytes: 7 protocol + 5 data)
```

Integer 42:
```
:42\r\n              (5 bytes)
```

Array of 3 integers:
```
*3\r\n:1\r\n:2\r\n:3\r\n  (16 bytes)
```

### Pipelining Performance

**Without pipelining:**
- 1 RTT per command
- 100 commands = 100 RTT

**With pipelining:**
- 1 RTT for N commands
- 100 commands ≈ 1-2 RTT

**Typical improvement:** 10-100x for small commands over high-latency links.

## Implementation Guide

### Client Implementation

**Basic client structure:**

```python
class RedisClient:
    def __init__(self, host, port):
        self.socket = socket.create_connection((host, port))

    def execute(self, *args):
        # Send command as RESP array
        command = self._encode_command(args)
        self.socket.sendall(command)

        # Read and parse response
        return self._read_response()

    def _encode_command(self, args):
        lines = [f"*{len(args)}\r\n"]
        for arg in args:
            arg_bytes = str(arg).encode('utf-8')
            lines.append(f"${len(arg_bytes)}\r\n")
            lines.append(arg_bytes + b"\r\n")
        return b"".join(lines)

    def _read_response(self):
        type_byte = self.socket.recv(1)

        if type_byte == b'+':
            return self._read_simple_string()
        elif type_byte == b'-':
            raise RedisError(self._read_simple_string())
        elif type_byte == b':':
            return self._read_integer()
        elif type_byte == b'$':
            return self._read_bulk_string()
        elif type_byte == b'*':
            return self._read_array()
        else:
            raise ProtocolError(f"Unknown type: {type_byte}")
```

### Parser State Machine

1. Read type byte
2. Based on type, read format-specific data
3. For length-prefixed types, read length first
4. Read exact number of bytes specified
5. Verify CRLF terminator
6. Recursively parse nested structures (arrays)

### Error Handling

**Connection errors:**
- Socket closed unexpectedly
- Timeout during read/write
- Network unreachable

**Protocol errors:**
- Invalid type byte
- Malformed length field
- Missing CRLF terminator
- Unexpected EOF

**Redis errors:**
- Command not found
- Wrong number of arguments
- Operation on wrong type
- Out of memory

### Connection Management

**Single connection:**
```python
client = RedisClient()
result = client.execute("GET", "key")
```

**Connection pooling:**
```python
pool = ConnectionPool(size=10)
with pool.get_connection() as conn:
    result = conn.execute("GET", "key")
```

**Pipeline:**
```python
pipe = client.pipeline()
pipe.set("key1", "value1")
pipe.set("key2", "value2")
pipe.get("key1")
results = pipe.execute()
```

## Security Considerations

### Authentication

**AUTH command:**
```
*2\r\n
$4\r\nAUTH\r\n
$8\r\npassword\r\n
```

**ACL (Redis 6.0+):**
```
*3\r\n
$4\r\nAUTH\r\n
$8\r\nusername\r\n
$8\r\npassword\r\n
```

### TLS/SSL (Redis 6.0+)

Enable TLS:
```
redis-server --tls-port 6380 \
  --tls-cert-file cert.pem \
  --tls-key-file key.pem \
  --tls-ca-cert-file ca.pem
```

Client connects via TLS:
```
redis-cli --tls \
  --cert client-cert.pem \
  --key client-key.pem \
  --cacert ca.pem
```

### Protected Mode

Default in Redis 3.2+:
- Binds to loopback only
- Requires AUTH if remote access needed
- Prevents unauthorized access

### Command Renaming

Hide dangerous commands:
```
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command CONFIG secret-config-name
```

## Debugging Tools

### redis-cli Monitor

Watch all commands in real-time:
```bash
redis-cli MONITOR
```

### redis-cli Raw Protocol

See raw RESP:
```bash
redis-cli --raw
```

### netcat/telnet

Manual protocol interaction:
```bash
telnet localhost 6379
PING
+PONG
```

### Wireshark

Redis protocol dissector available for packet capture analysis.

## Client Libraries

Popular RESP implementations:

- **redis-py:** Python
- **node-redis:** Node.js
- **Jedis:** Java
- **StackExchange.Redis:** .NET
- **go-redis:** Go
- **Predis:** PHP
- **redis-rb:** Ruby
- **hiredis:** C (high-performance)

Most libraries support both RESP2 and RESP3.

## Protocol Evolution

### RESP History

- **RESP1:** Original protocol (pre-2.0)
- **RESP2:** Introduced in Redis 2.0 (2010)
  - Unified protocol for all commands
  - Binary-safe bulk strings
  - Multi-bulk replies (arrays)
- **RESP3:** Introduced in Redis 6.0 (2020)
  - Additional data types
  - Better semantic clarity
  - Push messages for Pub/Sub
  - Streaming support

### Future Considerations

- **RESP4:** No plans currently
- **Binary protocol:** Not planned (RESP3 is efficient enough)
- **Compression:** Can be added at transport layer (TLS)
- **Multiplexing:** Connection sharing being explored

## Comparison with Other Protocols

### vs. Memcached ASCII Protocol

**RESP advantages:**
- Type safety (explicit types)
- Nested structures (arrays, maps)
- Binary safety (length-prefixed)
- Richer data types

**Memcached advantages:**
- Slightly lower overhead for simple gets/sets
- More human-readable for basic operations

### vs. Memcached Binary Protocol

**RESP advantages:**
- Simpler to implement
- Human-readable for debugging
- Better documentation

**Memcached binary advantages:**
- More compact for some operations
- Better extensibility via opcodes

### vs. HTTP/JSON APIs

**RESP advantages:**
- Much lower latency
- Lower overhead (no HTTP headers)
- Binary data support
- Persistent connections by default

**HTTP/JSON advantages:**
- Universal tooling support
- Firewall-friendly (port 80/443)
- Better for public APIs

## Performance Benchmarks

Typical RESP overhead:

- **Simple command (PING):** ~40 bytes total
- **GET small key:** ~60 bytes total
- **SET small key/value:** ~80 bytes total
- **Parsing speed:** >1M ops/sec on modern CPU
- **Pipelined throughput:** >100K ops/sec single connection

## References

- **Official RESP Specification:** https://redis.io/docs/latest/develop/reference/protocol-spec/
- **RESP3 Specification:** https://github.com/redis/redis-specifications/blob/master/protocol/RESP3.md
- **Redis Commands:** https://redis.io/docs/latest/commands/
- **Redis Source Code:** https://github.com/redis/redis
- **Client Implementation Guide:** https://redis.io/docs/latest/develop/clients/

## Related Standards

- **TCP:** RFC 9293
- **TLS:** RFC 8446
- **UTF-8:** RFC 3629
- **ASCII:** ANSI X3.4-1986
