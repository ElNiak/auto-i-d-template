# RFC 7540 - HTTP/2

**Source:** https://www.rfc-editor.org/rfc/rfc7540.txt
**Category:** Standards Track
**Application Profile:** Distributed Systems - HTTP-based Communication

## Abstract

HTTP/2 is an optimized protocol for HTTP semantics, designed to improve performance and reduce latency. It introduces multiplexing of requests/responses on a single TCP connection and uses binary framing instead of text-based HTTP/1.1 protocols.

## Key Protocol Features

### Binary Framing Layer
- Uses binary framing instead of text-based HTTP/1.1 protocols
- Enables multiplexing of requests/responses on a single TCP connection
- Reduces network overhead through header compression
- Improves performance and reduces perceived latency

### Streams
- Independent, bidirectional communication channels within a connection
- Allows concurrent request/response exchanges
- Each stream has a unique identifier
- Supports prioritization and flow control

### Connection Management
- Single TCP connection for multiple concurrent streams
- Implements flow control at both stream and connection level
- Supports graceful connection termination
- Enables server push capabilities

## Frame Types

### DATA Frame
- Carries actual payload data
- Subject to flow control
- Can be padded for security

### HEADERS Frame
- Opens streams and carries header information
- Compressed using HPACK algorithm
- Can include priority information

### PRIORITY Frame
- Specifies stream priority
- Enables stream dependency trees
- Allows weight-based resource allocation

### RST_STREAM Frame
- Immediately terminates a stream
- Indicates error conditions
- Enables quick stream cancellation

### SETTINGS Frame
- Configures connection parameters
- Negotiates capabilities between peers
- Applied at connection level

### PUSH_PROMISE Frame
- Notifies peer about planned stream initiation
- Enables server push
- Allows client to reject unwanted pushes

### PING Frame
- Measures round-trip time
- Validates connection liveness
- Does not carry application data

### GOAWAY Frame
- Initiates graceful connection shutdown
- Indicates last processed stream
- Provides error information

### WINDOW_UPDATE Frame
- Implements flow control
- Adjusts receive window size
- Prevents buffer overflow

### CONTINUATION Frame
- Continues header block sequences
- Used when headers exceed frame size
- Maintains header compression context

## Security Considerations

### Protection Mechanisms
- Includes protections against various network attacks
- Provides padding mechanisms to obscure message sizes
- Requires careful implementation to prevent cross-protocol vulnerabilities
- Recommends TLS for confidentiality and integrity

### HTTP/2 over TLS
- Strong recommendation for encryption
- Uses ALPN (Application-Layer Protocol Negotiation)
- Minimum TLS version requirements
- Cipher suite restrictions

## Performance Optimization

### Header Compression
- HPACK compression algorithm
- Reduces overhead significantly
- Maintains compression context per connection
- Prevents compression-based attacks

### Stream Prioritization
- Weight-based resource allocation
- Dependency trees for complex scenarios
- Enables optimization of critical resources
- Flexible priority adjustment

### Flow Control
- Per-stream and connection-level control
- Prevents buffer overflow
- Allows receiver-driven resource management
- Configurable window sizes

## Use Cases in Distributed Systems

1. **Microservices Communication**: Efficient request multiplexing reduces connection overhead
2. **API Gateways**: Server push enables proactive resource delivery
3. **Real-time Applications**: Bidirectional streams support streaming data
4. **Load Balancing**: Connection reuse improves resource utilization
5. **Service Mesh**: Binary framing enables efficient protocol proxying

## Protocol Goals

- Enable more efficient use of network resources
- Reduce perception of latency
- Maintain HTTP/1.1 semantics
- Support existing HTTP use cases
- Provide upgrade path from HTTP/1.1
- Enable new capabilities (server push, multiplexing)

## Implementation Considerations

- Backward compatibility with HTTP/1.1
- Connection preface and upgrade mechanisms
- Error handling and recovery
- Resource management and limits
- Security requirements and best practices
- Testing and interoperability
