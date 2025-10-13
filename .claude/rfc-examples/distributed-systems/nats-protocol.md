# NATS Messaging Protocol

**Source:** https://docs.nats.io/reference/reference-protocols/nats-protocol
**Organization:** NATS.io / Synadia Communications
**Category:** Cloud-Native Messaging System
**Application Profile:** Distributed Systems - Lightweight Pub/Sub Messaging

## Abstract

NATS is a simple, secure, and high-performance messaging system for cloud-native applications, IoT messaging, and microservices architectures. It uses a text-based protocol over TCP/IP with support for publish/subscribe, request/reply, and queue groups.

## Protocol Characteristics

### Text-Based Protocol
- Human-readable message format
- Communicates over TCP/IP socket
- UTF-8 compatible
- Messages terminated by `\r\n`
- Simple parsing and debugging

### Design Principles
- Simplicity: Minimal protocol overhead
- Performance: High throughput, low latency
- Scalability: Millions of connections
- Resilience: Automatic reconnection
- Security: TLS and authentication support

## Core Protocol Operations

### INFO Operation
**Direction**: Server → Client
**Purpose**: Server sends connection details

```
INFO {json}
```

**JSON Fields**:
- **server_id**: Unique server identifier
- **server_name**: Server name
- **version**: Server version
- **go**: Go version server built with
- **host**: Server hostname
- **port**: Port number
- **max_payload**: Maximum payload size
- **proto**: Protocol version
- **client_id**: Client connection ID
- **auth_required**: Authentication required flag
- **tls_required**: TLS required flag
- **tls_verify**: TLS certificate verification
- **connect_urls**: List of alternate server URLs
- **headers**: Headers support flag
- **nonce**: Challenge for authentication

### CONNECT Operation
**Direction**: Client → Server
**Purpose**: Client configures connection parameters

```
CONNECT {json}\r\n
```

**JSON Fields**:
- **verbose**: Enable verbose protocol
- **pedantic**: Enable strict protocol
- **tls_required**: Client requires TLS
- **auth_token**: Authentication token
- **user**: Username
- **pass**: Password
- **name**: Client name
- **lang**: Client language
- **version**: Client version
- **protocol**: Protocol version
- **echo**: Echo published messages
- **sig**: Signature (NKEY authentication)
- **jwt**: JWT token (JWT authentication)
- **headers**: Headers support
- **no_responders**: No responders support

### PUB Operation
**Direction**: Client → Server
**Purpose**: Publish a message to a subject

```
PUB <subject> [reply-to] <#bytes>\r\n
[payload]\r\n
```

**Parameters**:
- **subject**: Subject name (required)
- **reply-to**: Reply subject (optional)
- **#bytes**: Payload size in bytes
- **payload**: Message data

**Example**:
```
PUB NOTIFY.USER 11\r\n
Hello World\r\n
```

### HPUB Operation
**Direction**: Client → Server
**Purpose**: Publish message with headers

```
HPUB <subject> [reply-to] <#header bytes> <#total bytes>\r\n
[headers]\r\n
\r\n
[payload]\r\n
```

**Headers Format**:
```
NATS/1.0\r\n
Header-Key1: value1\r\n
Header-Key2: value2\r\n
\r\n
```

### SUB Operation
**Direction**: Client → Server
**Purpose**: Subscribe to a subject

```
SUB <subject> [queue group] <sid>\r\n
```

**Parameters**:
- **subject**: Subject pattern with wildcards
- **queue group**: Queue group name (optional)
- **sid**: Subscription ID (unique per connection)

**Example**:
```
SUB NOTIFY.* 1\r\n
SUB ORDER.created workers 2\r\n
```

### UNSUB Operation
**Direction**: Client → Server
**Purpose**: Unsubscribe from a subject

```
UNSUB <sid> [max_msgs]\r\n
```

**Parameters**:
- **sid**: Subscription ID
- **max_msgs**: Auto-unsubscribe after N messages (optional)

**Example**:
```
UNSUB 1\r\n
UNSUB 2 5\r\n  (unsubscribe after 5 more messages)
```

### MSG Operation
**Direction**: Server → Client
**Purpose**: Deliver a message to a subscriber

```
MSG <subject> <sid> [reply-to] <#bytes>\r\n
[payload]\r\n
```

**Parameters**:
- **subject**: Subject message was published to
- **sid**: Subscription ID
- **reply-to**: Reply subject (optional)
- **#bytes**: Payload size
- **payload**: Message data

### HMSG Operation
**Direction**: Server → Client
**Purpose**: Deliver message with headers

```
HMSG <subject> <sid> [reply-to] <#header bytes> <#total bytes>\r\n
[headers]\r\n
\r\n
[payload]\r\n
```

### PING Operation
**Direction**: Client ↔ Server
**Purpose**: Connection keepalive

```
PING\r\n
```

Response:
```
PONG\r\n
```

### PONG Operation
**Direction**: Client ↔ Server
**Purpose**: Keepalive response

```
PONG\r\n
```

### +OK Operation
**Direction**: Server → Client
**Purpose**: Acknowledge command (verbose mode)

```
+OK\r\n
```

### -ERR Operation
**Direction**: Server → Client
**Purpose**: Error notification

```
-ERR <error message>\r\n
```

**Common Errors**:
- **'Unknown Protocol Operation'**: Invalid command
- **'Attempted To Connect To Route Port'**: Wrong port
- **'Authorization Violation'**: Auth failure
- **'Authorization Timeout'**: Auth took too long
- **'Parser Error'**: Malformed protocol
- **'Stale Connection'**: Connection timeout
- **'Maximum Payload Exceeded'**: Message too large
- **'Invalid Subject'**: Invalid subject format

## Subject Naming

### Subject Syntax
- Case-sensitive
- Tokens separated by dots: `foo.bar.baz`
- No spaces or special characters (except wildcards)
- Maximum length: 256 characters (typical)

### Wildcards

#### Single Token Wildcard (*)
- Matches exactly one token
- `foo.*.baz` matches `foo.bar.baz` but not `foo.bar.qux.baz`

#### Multi-Token Wildcard (>)
- Matches one or more tokens
- Must be last token in subject
- `foo.>` matches `foo.bar`, `foo.bar.baz`, etc.

**Examples**:
```
time.us.*          → matches: time.us.east, time.us.west
time.*.east        → matches: time.us.east, time.eu.east
time.>             → matches: time.us.east, time.us.east.atlanta
```

## Queue Groups

### Load Balancing
- Multiple subscribers in same queue group
- Message delivered to only one subscriber
- Random distribution (load balancing)
- Enables horizontal scaling

**Example**:
```
SUB orders.* workers 1\r\n   (Client 1)
SUB orders.* workers 2\r\n   (Client 2)
SUB orders.* workers 3\r\n   (Client 3)
```

Each published message to `orders.*` goes to only one worker.

## Request/Reply Pattern

### Request
```
PUB REQUEST.subject _INBOX.unique.reply.id 5\r\n
hello\r\n
```

### Reply
Subscriber receives request with reply-to subject, publishes response:
```
PUB _INBOX.unique.reply.id 7\r\n
goodbye\r\n
```

### INBOX Subjects
- Unique reply subjects
- Convention: `_INBOX.<unique-id>`
- Automatically generated by client libraries
- Short-lived subscriptions

## Headers

### Header Format
```
NATS/1.0\r\n
Header-Name: value\r\n
Another-Header: value\r\n
\r\n
```

### Standard Headers
- **Nats-Msg-Id**: Message deduplication ID
- **Nats-Expected-Stream**: JetStream stream name
- **Nats-Expected-Last-Msg-Id**: Expected last message ID
- **Nats-Expected-Last-Sequence**: Expected last sequence
- **Nats-Expected-Last-Subject-Sequence**: Subject-specific sequence

### Custom Headers
- Application-defined key-value pairs
- Used for metadata, routing, filtering
- Available in message delivery

## Authentication

### Token Authentication
```json
{
  "auth_token": "secret_token"
}
```

### Username/Password
```json
{
  "user": "username",
  "pass": "password"
}
```

### NKEY Authentication
```json
{
  "nkey": "UABC123...",
  "sig": "signature..."
}
```

### JWT Authentication
```json
{
  "jwt": "eyJhbGciOiJIUzI1NiIs...",
  "sig": "signature..."
}
```

## TLS/SSL

### TLS Upgrade
1. Client connects to server
2. Server sends INFO with `tls_required: true`
3. Client initiates TLS handshake
4. Secure connection established
5. Client sends CONNECT

### Certificate Verification
- Server certificate validation
- Client certificate authentication
- Mutual TLS support

## Connection Lifecycle

### Establishing Connection
1. Client opens TCP connection
2. Server sends INFO
3. Client sends CONNECT
4. Client subscribes (SUB operations)
5. Client publishes/receives messages

### Maintaining Connection
- PING/PONG for keepalive
- Default interval: 2 minutes
- Configurable timeout
- Auto-reconnection on failure

### Closing Connection
- Client closes TCP socket
- Server detects disconnection
- Automatic cleanup of subscriptions

## No Responders

### Problem
- Request sent but no subscribers
- Requester waits until timeout

### Solution
Server responds with special header:
```
HMSG _INBOX.xyz 1 0 46\r\n
NATS/1.0 503 No Responders\r\n
\r\n
\r\n
```

Client receives immediate feedback.

## Use Cases in Distributed Systems

1. **Microservices Communication**: Request/reply and pub/sub patterns
2. **Event Broadcasting**: Fanout to multiple subscribers
3. **Load Distribution**: Queue groups for worker pools
4. **Service Discovery**: Dynamic service registration
5. **Command/Control**: IoT device management
6. **Real-time Data Streams**: Sensor data, metrics, logs
7. **Chat and Notifications**: Real-time messaging

## Performance Optimization

### Protocol Efficiency
- Minimal framing overhead
- Text-based for simplicity
- Binary payload support
- No message acknowledgments (fire-and-forget)

### Connection Pooling
- Multiplexing subscriptions
- Single connection per client
- Low resource overhead
- Scales to millions of connections

### Subject-Based Routing
- Fast subject matching
- O(1) lookup for exact matches
- Efficient wildcard matching
- No routing tables

## JetStream Extension

### Persistent Messaging
- Message storage and replay
- Stream and consumer abstractions
- Exactly-once delivery
- Horizontal scalability

### Key-Value Store
- Subject-based KV pairs
- Built on JetStream streams
- Versioning and TTL support

### Object Store
- Large binary object storage
- Chunking and reassembly
- Metadata support

## Implementation Considerations

### Client Libraries
- Official libraries: Go, Java, JavaScript, Python, C, Ruby, etc.
- Auto-reconnection logic
- Buffering and flow control
- Error handling

### Server Deployment
- Standalone or clustered
- Super-cluster (global distribution)
- Gateway connections for bridging
- Leaf nodes for edge deployment

### Monitoring
- Connection statistics
- Message rates and throughput
- Subject activity
- Slow consumers detection

### Best Practices
- Use queue groups for scalability
- Implement proper subject naming hierarchy
- Handle reconnection gracefully
- Monitor slow consumers
- Use headers for metadata
- Implement circuit breakers
- Set appropriate timeouts
