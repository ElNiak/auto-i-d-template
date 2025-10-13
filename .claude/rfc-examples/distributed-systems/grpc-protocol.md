# gRPC Protocol Specification

**Source:** https://github.com/grpc/grpc/blob/master/doc/PROTOCOL-HTTP2.md
**Organization:** Google
**Category:** RPC Framework
**Application Profile:** Distributed Systems - Remote Procedure Calls

## Abstract

gRPC is a high-performance, open-source universal RPC framework that uses HTTP/2 as the underlying transport mechanism. It defines a structured message exchange format over HTTP/2 streams with support for bidirectional streaming, authentication, and load balancing.

## Transport Protocol

### HTTP/2 Foundation
- Uses HTTP/2 as the underlying transport mechanism
- Leverages HTTP/2 streams for concurrent RPC calls
- Benefits from HTTP/2 features: multiplexing, flow control, header compression
- Supports both unary and streaming calls

### Connection Management
- Persistent connections recommended
- Uses HTTP/2 GOAWAY for graceful shutdown
- PING frames for connection health checks
- Handles connection failures with appropriate status codes

## Message Framing

### Length-Prefixed Messages
```
[Compressed-Flag][Message-Length][Message-Data]
     1 byte           4 bytes        variable
```

### Compression Flag
- 0: No compression
- 1: Message compressed using negotiated algorithm
- Compression contexts NOT maintained over message boundaries
- Each message independently compressed

### Message Length
- 4-byte unsigned integer (big-endian)
- Specifies length of message data
- Does not include compression flag or length bytes
- Maximum message size configurable

## Request/Response Structure

### Request Format
```
Request → Request-Headers *Length-Prefixed-Message EOS
```

### Response Format
```
Response → (Response-Headers *Length-Prefixed-Message Trailers) | Trailers-Only
```

### Stream Lifecycle
1. Client sends Request-Headers
2. Client sends zero or more Length-Prefixed-Messages
3. Client sends EOS (End-Of-Stream)
4. Server sends Response-Headers
5. Server sends zero or more Length-Prefixed-Messages
6. Server sends Trailers with status

## Headers and Metadata

### Standard Headers

#### Request Headers
- **:method**: Always "POST"
- **:scheme**: "http" or "https"
- **:path**: "/" + service-name + "/" + method-name
- **:authority**: Virtual host name
- **content-type**: "application/grpc" or "application/grpc+proto"
- **grpc-timeout**: Call timeout in format: TimeoutValue TimeoutUnit
- **grpc-encoding**: Message compression algorithm
- **grpc-accept-encoding**: Accepted compression algorithms

#### Response Headers
- **:status**: HTTP status code (always 200 for gRPC)
- **content-type**: Same as request
- **grpc-encoding**: Compression used for response
- **grpc-accept-encoding**: Server's accepted algorithms

### Custom Metadata
- Transmitted as HTTP/2 headers
- Key-value pairs for application use
- ASCII header names (lowercase, no binary)
- Binary headers end with "-bin" suffix
- Binary values base64-encoded

### Trailers
- **grpc-status**: gRPC status code (0 = OK)
- **grpc-message**: Error message (percent-encoded)
- **grpc-status-details-bin**: Protobuf-encoded error details

## Call Types

### Unary RPC
```
Request: Headers + Message + EOS
Response: Headers + Message + Trailers
```

### Server Streaming RPC
```
Request: Headers + Message + EOS
Response: Headers + *Message + Trailers
```

### Client Streaming RPC
```
Request: Headers + *Message + EOS
Response: Headers + Message + Trailers
```

### Bidirectional Streaming RPC
```
Request: Headers + *Message + EOS
Response: Headers + *Message + Trailers
```

## Status Codes

### Standard gRPC Status Codes
- **0 (OK)**: Success
- **1 (CANCELLED)**: Operation cancelled
- **2 (UNKNOWN)**: Unknown error
- **3 (INVALID_ARGUMENT)**: Invalid argument
- **4 (DEADLINE_EXCEEDED)**: Timeout
- **5 (NOT_FOUND)**: Resource not found
- **6 (ALREADY_EXISTS)**: Resource already exists
- **7 (PERMISSION_DENIED)**: Permission denied
- **8 (RESOURCE_EXHAUSTED)**: Resource exhausted
- **9 (FAILED_PRECONDITION)**: Operation rejected
- **10 (ABORTED)**: Operation aborted
- **11 (OUT_OF_RANGE)**: Out of range
- **12 (UNIMPLEMENTED)**: Not implemented
- **13 (INTERNAL)**: Internal error
- **14 (UNAVAILABLE)**: Service unavailable
- **15 (DATA_LOSS)**: Data loss/corruption
- **16 (UNAUTHENTICATED)**: Authentication required

## Error Handling

### HTTP/2 Error Mapping
- RST_STREAM with NO_ERROR → Status depends on received trailers
- RST_STREAM with CANCEL → CANCELLED status
- RST_STREAM with REFUSED_STREAM → UNAVAILABLE status
- Connection error → UNAVAILABLE status
- GOAWAY → UNAVAILABLE for new streams

### Error Propagation
- Errors communicated via trailers
- Status code mandatory
- Status message optional (human-readable)
- Status details optional (structured protobuf)

## Flow Control

### HTTP/2 Flow Control
- Stream-level flow control for messages
- Connection-level flow control
- Initial window size negotiable
- Window updates sent as needed

### Backpressure
- Receiver controls message flow
- Can slow down sender
- Prevents buffer overflow
- Enables resource management

## Authentication

### Supported Mechanisms
- **TLS/SSL**: Transport-level encryption
- **Token-based**: OAuth2, JWT
- **Channel credentials**: TLS certificates
- **Call credentials**: Per-RPC authentication

### Metadata-based Auth
- Authorization header for tokens
- Custom headers for auth data
- Interceptors for auth logic
- Automatic token refresh

## Compression

### Supported Algorithms
- **identity**: No compression
- **gzip**: GZIP compression
- **deflate**: DEFLATE compression
- **snappy**: Snappy compression (optional)

### Compression Negotiation
1. Client advertises accepted algorithms
2. Client specifies encoding for request
3. Server specifies encoding for response
4. Must support "identity" (no compression)

## Keepalive

### PING Frames
- Client sends PING at regular intervals
- Server responds with PING ACK
- Detects dead connections
- Configurable interval and timeout

### Settings
- **keepalive_time**: Time before sending PING
- **keepalive_timeout**: Time to wait for PING ACK
- **keepalive_permit_without_calls**: Allow PING on idle connection

## Load Balancing

### Client-side Load Balancing
- Service discovery integration
- Round-robin, least-loaded algorithms
- Health checking
- Subchannel management

### Server-side Load Balancing
- Load balancer proxy
- Backend selection
- Health checking
- Connection management

## Use Cases in Distributed Systems

1. **Microservices Architecture**: Efficient inter-service communication
2. **Mobile/Web Backends**: Low latency, efficient bandwidth usage
3. **Real-time Services**: Bidirectional streaming for live data
4. **Polyglot Environments**: Cross-language RPC with protobuf
5. **Cloud-Native Applications**: Service mesh integration, observability

## Performance Optimization

### Protocol Efficiency
- Binary protocol reduces overhead
- HTTP/2 multiplexing eliminates head-of-line blocking
- Header compression reduces metadata size
- Connection reuse improves resource utilization

### Message Optimization
- Protobuf serialization is compact and fast
- Compression reduces bandwidth
- Streaming enables incremental processing
- Flow control prevents memory exhaustion

## Implementation Considerations

### Client Implementation
- Connection pooling and management
- Deadline propagation
- Retry and hedging policies
- Interceptors for cross-cutting concerns

### Server Implementation
- Service registration and routing
- Concurrent request handling
- Resource limits and quotas
- Graceful shutdown

### Best Practices
- Use streaming for large data transfers
- Implement proper timeout handling
- Enable compression for large messages
- Monitor connection health
- Implement circuit breakers
- Use interceptors for logging/tracing
