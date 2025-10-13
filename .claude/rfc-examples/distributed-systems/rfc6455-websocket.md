# RFC 6455 - The WebSocket Protocol

**Source:** https://www.rfc-editor.org/rfc/rfc6455.txt
**Category:** Standards Track
**Application Profile:** Distributed Systems - Real-time Bidirectional Communication

## Abstract

The WebSocket Protocol enables two-way communication between a client and a remote host, using an origin-based security model. It provides a mechanism for browser-based applications to communicate with servers without relying on multiple HTTP connections.

## Protocol Characteristics

### Full-Duplex Communication
- Provides full-duplex communication over a single TCP connection
- Designed to work over HTTP ports 80 and 443
- Includes an opening handshake and basic message framing
- Supports both text and binary message types

### Design Goals
- Minimal framing overhead
- Origin-based security model compatible with browsers
- Single TCP connection for traffic in both directions
- Ability to coexist with HTTP on same port
- Proxy and firewall friendly

## Opening Handshake

### Client Request
```
GET /chat HTTP/1.1
Host: server.example.com
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
Sec-WebSocket-Version: 13
Origin: http://example.com
```

### Server Response
```
HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
```

### Handshake Process
1. Client sends HTTP Upgrade request with special headers
2. Includes `Sec-WebSocket-Key` for validation
3. Server validates and responds with 101 Switching Protocols
4. Server computes `Sec-WebSocket-Accept` from client key
5. Connection upgrades from HTTP to WebSocket protocol

## Data Framing

### Frame Structure
- Uses binary frame format with specific bit allocations
- Frame header includes opcode, mask flag, payload length
- Supports fragmentation of messages
- Payload can be masked (required for client-to-server)

### Frame Format
```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-------+-+-------------+-------------------------------+
|F|R|R|R| opcode|M| Payload len |    Extended payload length    |
|I|S|S|S|  (4)  |A|     (7)     |             (16/64)           |
|N|V|V|V|       |S|             |   (if payload len==126/127)   |
| |1|2|3|       |K|             |                               |
+-+-+-+-+-------+-+-------------+ - - - - - - - - - - - - - - - +
|     Extended payload length continued, if payload len == 127  |
+ - - - - - - - - - - - - - - - +-------------------------------+
|                               |Masking-key, if MASK set to 1  |
+-------------------------------+-------------------------------+
| Masking-key (continued)       |          Payload Data         |
+-------------------------------- - - - - - - - - - - - - - - - +
:                     Payload Data continued ...                :
+ - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - +
|                     Payload Data continued ...                |
+---------------------------------------------------------------+
```

### Opcodes
- **0x0**: Continuation frame
- **0x1**: Text frame (UTF-8)
- **0x2**: Binary frame
- **0x8**: Connection close
- **0x9**: Ping
- **0xA**: Pong

### Control Frames

#### Ping Frame
- Can be sent at any time
- Must include payload from ping in pong response
- Used for keepalive and latency measurement

#### Pong Frame
- Response to ping frame
- Can be sent unsolicited as heartbeat
- Must echo ping payload

#### Close Frame
- Initiates connection close
- Can include status code and reason
- Both peers must send close frame for clean shutdown

## Message Fragmentation

### Fragmentation Support
- Large messages can be split into multiple frames
- First frame has opcode, continuation frames use 0x0
- Final frame has FIN bit set
- Control frames can be interleaved between fragments

### Example
```
Frame 1: FIN=0, opcode=0x1 (text), payload="Hello "
Frame 2: FIN=0, opcode=0x0 (continuation), payload="World"
Frame 3: FIN=1, opcode=0x0 (continuation), payload="!"
```

## Security Considerations

### Origin-Based Security Model
- Uses origin-based security model for browser contexts
- Server validates Origin header
- Designed to fail connections from unauthorized sources
- Supports extension of security through negotiated extensions

### Masking
- Client-to-server frames MUST be masked
- Masking prevents cache poisoning attacks
- Uses 32-bit masking key
- Server-to-client frames MUST NOT be masked

### TLS Support
- WebSocket Secure (wss://) uses TLS
- Provides confidentiality and integrity
- Prevents man-in-the-middle attacks
- Recommended for sensitive data

## Extensions

### Extension Mechanism
- Negotiated during handshake
- Sec-WebSocket-Extensions header
- Can modify frame structure
- Examples: compression, multiplexing

### Common Extensions
- **permessage-deflate**: Per-message compression
- **permessage-bzip2**: Alternative compression
- **multiplexing**: Multiple logical connections

## Subprotocols

### Subprotocol Negotiation
- Sec-WebSocket-Protocol header
- Defines application-level protocol
- Server selects single subprotocol
- Examples: STOMP, MQTT, custom protocols

## Use Cases in Distributed Systems

1. **Real-time Messaging**: Chat applications, notifications, alerts
2. **Live Data Streams**: Stock tickers, sports scores, sensor data
3. **Collaborative Tools**: Shared documents, whiteboards, multiplayer games
4. **IoT Communication**: Device control, telemetry, command/response
5. **Event Broadcasting**: Push notifications, status updates, live feeds

## Connection Management

### Establishing Connection
1. DNS lookup and TCP connection
2. TLS handshake (for wss://)
3. HTTP upgrade handshake
4. WebSocket data transfer

### Maintaining Connection
- Ping/Pong frames for keepalive
- Timeout detection
- Automatic reconnection strategies
- Connection state monitoring

### Closing Connection
1. Send close frame with status code
2. Wait for close frame from peer
3. Close TCP connection
4. Clean up resources

## Error Handling

### Status Codes
- **1000**: Normal closure
- **1001**: Going away
- **1002**: Protocol error
- **1003**: Unsupported data
- **1006**: Abnormal closure
- **1007**: Invalid frame payload
- **1008**: Policy violation
- **1009**: Message too big
- **1010**: Mandatory extension
- **1011**: Internal server error

## Implementation Considerations

- Connection limits and resource management
- Buffer size and message size limits
- Timeout and keepalive configuration
- Error handling and recovery
- Security validation and sanitization
- Performance optimization (buffering, batching)
- Proxy and firewall compatibility
