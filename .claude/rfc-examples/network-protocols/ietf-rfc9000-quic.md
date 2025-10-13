# RFC 9000 - QUIC: A UDP-Based Multiplexed and Secure Transport

**Source:** IETF RFC 9000
**URL:** https://www.rfc-editor.org/rfc/rfc9000.txt
**Category:** Network Protocol - Transport Layer

## Protocol Overview

QUIC is a UDP-based multiplexed and secure transport protocol designed for modern Internet applications. It combines the functionality of TCP, TLS, and HTTP/2's multiplexing into a single, integrated protocol that provides low-latency connection establishment, built-in security, and advanced stream management.

## Key Characteristics

- **UDP-Based:** Built on top of UDP for deployment flexibility
- **Multiplexed Streams:** Multiple concurrent streams within single connection
- **Integrated Security:** TLS 1.3 built into protocol (not layered on top)
- **Connection Migration:** Survives network path changes (WiFi to cellular)
- **Low Latency:** 0-RTT and 1-RTT connection establishment
- **No Head-of-Line Blocking:** Independent stream delivery
- **Flow Control:** Both stream-level and connection-level
- **Extensible:** Version negotiation and extension framework

## Protocol Architecture

### Layering

```
+----------+
|   HTTP   |  (or other application protocol)
+----------+
|   QUIC   |  (streams, reliability, flow control, congestion control)
+----------+
|   UDP    |  (unreliable datagram delivery)
+----------+
|   IP     |
+----------+
```

### QUIC Packet Structure

```
Long Header Packet (used during handshake):
+-+-+-+-+-+-+-+-+
|1|1|T T|X X X X|
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                         Version                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
| DCID Len (8)  |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|               Destination Connection ID (0..160)            ...
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
| SCID Len (8)  |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                 Source Connection ID (0..160)               ...
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

Short Header Packet (used after handshake):
+-+-+-+-+-+-+-+-+
|0|1|S|R|R|K|P P|
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|               Destination Connection ID (0..160)            ...
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                     Packet Number (8/16/24/32)              ...
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                     Protected Payload (*)                   ...
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

## Connection Establishment

### 1-RTT Handshake

```
Client                                                  Server

Initial[0]: CRYPTO[CH] ->
                                    <- Initial[0]: CRYPTO[SH] ACK[0]
                               Handshake[0]: CRYPTO[EE, CERT, CV, FIN]
                                                <- 1-RTT[0]: STREAM[1, "..."]

Handshake[0]: CRYPTO[FIN], ACK[0] ->
1-RTT[0]: STREAM[0, "..."], ACK[0] ->
```

**Packet Types During Handshake:**
- **Initial:** First packets exchanged (protected with version-specific keys)
- **Handshake:** Contains TLS handshake messages (protected with handshake keys)
- **1-RTT:** Application data packets (protected with application keys)

**Key Points:**
- Combines transport and cryptographic handshake
- TLS 1.3 messages carried in CRYPTO frames
- Connection established after one round trip
- Application data can be sent immediately after client receives server's response

### 0-RTT Connection Establishment

```
Client                                                  Server

Initial[0]: CRYPTO[CH], 0-RTT[0]: STREAM[0, "..."] ->
                                    <- Initial[0]: CRYPTO[SH] ACK[0]
                               Handshake[0]: CRYPTO[EE, FIN], ACK[0]
                                                <- 1-RTT[0]: STREAM[1, "..."]

Handshake[0]: CRYPTO[FIN], ACK[0] ->
1-RTT[1]: STREAM[0, "..."], ACK[0] ->
```

**0-RTT Characteristics:**
- Requires previous connection and resumption ticket
- Application data sent with first flight
- **No replay protection** for 0-RTT data
- Server may reject 0-RTT data
- Provides lowest possible latency

## Connection Identifiers

### Purpose

- **Connection Tracking:** Identify connection across network changes
- **Load Balancing:** Route packets to correct server
- **Privacy:** Can change to prevent tracking
- **Migration:** Maintain connection during IP address changes

### Connection ID Properties

- **Length:** 0-20 bytes (variable)
- **Multiple IDs:** Endpoints can use different IDs over connection lifetime
- **Rotation:** Can be changed to improve privacy
- **Server-Generated:** Server provides CIDs to client for use

### NEW_CONNECTION_ID Frame

```
NEW_CONNECTION_ID Frame {
  Type (i) = 0x18,
  Sequence Number (i),
  Retire Prior To (i),
  Length (8),
  Connection ID (8..160),
  Stateless Reset Token (128),
}
```

## Stream Management

### Stream Types

1. **Bidirectional Streams:** Data flows both directions
   - Client-initiated: IDs 0x00, 0x04, 0x08, ...
   - Server-initiated: IDs 0x01, 0x05, 0x09, ...

2. **Unidirectional Streams:** Data flows one direction
   - Client-initiated: IDs 0x02, 0x06, 0x0a, ...
   - Server-initiated: IDs 0x03, 0x07, 0x0b, ...

### Stream Identifier Encoding

```
Stream ID = 4 * stream_number + stream_type_bits

stream_type_bits:
  0x00 = Client-initiated, Bidirectional
  0x01 = Server-initiated, Bidirectional
  0x02 = Client-initiated, Unidirectional
  0x03 = Server-initiated, Unidirectional
```

### Stream States

**Sending States:**
```
       o
       | Create Stream (Sending)
       v
   +-------+
   | Ready | Send STREAM/STREAM_DATA_BLOCKED
   +-------+
       |
       | Send STREAM with FIN
       v
   +-------+
   | Send  | Send STREAM/STREAM_DATA_BLOCKED
   +-------+
       |
       | Send STREAM with FIN
       v
   +-------+
   | Data  |
   | Sent  |
   +-------+
       |
       | All data acknowledged
       v
   +-------+
   | Data  |
   |Recvd  |
   +-------+
```

**Receiving States:**
```
       o
       | Recv STREAM
       v
   +-------+
   | Recv  | Recv STREAM/STREAM_DATA_BLOCKED
   +-------+
       |
       | Recv STREAM with FIN
       v
   +-------+
   | Size  |
   | Known |
   +-------+
       |
       | All data received
       v
   +-------+
   | Data  |
   | Recvd |
   +-------+
       |
       | Data delivered to application
       v
   +-------+
   | Data  |
   | Read  |
   +-------+
```

### STREAM Frame

```
STREAM Frame {
  Type (i) = 0x08..0x0f,
  Stream ID (i),
  [Offset (i)],
  [Length (i)],
  Stream Data (..),
}
```

**Type Bits:**
- 0x04: FIN bit (last data on stream)
- 0x02: Length present
- 0x01: Offset present

## Flow Control

### Two-Level Flow Control

1. **Stream-Level Flow Control:**
   - Limits data on individual streams
   - Prevents single stream from consuming all bandwidth
   - Each stream has independent flow control window

2. **Connection-Level Flow Control:**
   - Limits total data across all streams
   - Prevents connection from overwhelming receiver
   - Applies to sum of all stream data

### Flow Control Mechanism

**Credit-Based System:**
```
MAX_STREAM_DATA Frame {
  Type (i) = 0x11,
  Stream ID (i),
  Maximum Stream Data (i),
}

MAX_DATA Frame {
  Type (i) = 0x10,
  Maximum Data (i),
}
```

**How it Works:**
1. Receiver advertises maximum amount of data it can receive
2. Sender must not send beyond advertised limit
3. Receiver sends updates (MAX_DATA/MAX_STREAM_DATA) as it consumes data
4. Sender blocked if limit reached (sends STREAM_DATA_BLOCKED/DATA_BLOCKED)

### Stream Limit Control

```
MAX_STREAMS Frame {
  Type (i) = 0x12..0x13,
  Maximum Streams (i),
}

STREAMS_BLOCKED Frame {
  Type (i) = 0x16..0x17,
  Maximum Streams (i),
}
```

Controls maximum number of concurrent streams.

## Loss Detection and Recovery

### Packet Number Encoding

- **Unique per packet:** Never reused within same packet number space
- **Monotonically increasing:** Always increases by at least 1
- **Variable length:** Encoded using 1-4 bytes
- **Three spaces:** Initial, Handshake, Application (1-RTT)

### Acknowledgment Mechanism

**ACK Frame:**
```
ACK Frame {
  Type (i) = 0x02..0x03,
  Largest Acknowledged (i),
  ACK Delay (i),
  ACK Range Count (i),
  First ACK Range (i),
  ACK Range (..) ...,
  [ECN Counts (..)],
}
```

**ACK Ranges:**
- Efficiently encode gaps in packet number space
- Support selective acknowledgment (SACK-like)
- Include timing information (ACK delay)

### Loss Detection

**Mechanisms:**
1. **Time Threshold:** Packet deemed lost if not acknowledged within threshold
2. **Packet Threshold:** Packet deemed lost if packets sent later are acknowledged
3. **Probe Timeout (PTO):** Send probe if no acknowledgment received

**No Ambiguous Retransmissions:**
- Unlike TCP, retransmitted data gets new packet number
- Enables accurate RTT measurements for all packets
- Simplifies loss detection logic

## Congestion Control

### Algorithm Requirements

RFC 9000 doesn't mandate specific algorithm, but requires:
- Slow start
- Congestion avoidance
- Loss-based reduction
- ECN support (if available)

### Congestion Window Management

**Initial Window:**
- 10 packets (approximately 14,400 bytes)
- Conservative start to prevent network overload

**On Loss:**
- Reduce congestion window
- Enter congestion avoidance mode
- Typically multiplicative decrease (e.g., CUBIC, NewReno)

**On ACK:**
- Increase congestion window
- Rate depends on current mode (slow start vs. congestion avoidance)

### Pacing

- Recommended but not required
- Spreads packet transmission over RTT
- Reduces burstiness
- Improves fairness with other flows

## Connection Migration

### Migration Process

**Scenario: Client IP Address Changes**

```
Client (old IP)                              Server

1-RTT[...]: STREAM[...] ->
                                         <- 1-RTT[...]: STREAM[...]

[Network change - client gets new IP address]

Client (new IP)                              Server

1-RTT[...]: STREAM[...] ->
          (with PATH_CHALLENGE)
                                         <- 1-RTT[...]: PATH_RESPONSE
                                            1-RTT[...]: STREAM[...]
```

**Key Points:**
- Connection ID remains same across migration
- PATH_CHALLENGE/PATH_RESPONSE validate new path
- Server only sends non-probing packets after validation
- Prevents address spoofing attacks

### Connection ID Usage During Migration

1. Client initiates migration using new path
2. Client includes PATH_CHALLENGE frame
3. Server responds on new path with PATH_RESPONSE
4. Server can provide new Connection IDs via NEW_CONNECTION_ID
5. Client can retire old Connection IDs via RETIRE_CONNECTION_ID

## QUIC Frames

### Frame Types Overview

| Type | Frame Name | Purpose |
|------|------------|---------|
| 0x00 | PADDING | Increase packet size |
| 0x01 | PING | Keepalive |
| 0x02-0x03 | ACK | Acknowledge packets |
| 0x04 | RESET_STREAM | Abort stream |
| 0x05 | STOP_SENDING | Request peer stop sending |
| 0x06 | CRYPTO | TLS handshake data |
| 0x07 | NEW_TOKEN | Address validation token |
| 0x08-0x0f | STREAM | Stream data |
| 0x10 | MAX_DATA | Update connection flow control |
| 0x11 | MAX_STREAM_DATA | Update stream flow control |
| 0x12-0x13 | MAX_STREAMS | Update stream limit |
| 0x14 | DATA_BLOCKED | Connection flow control blocked |
| 0x15 | STREAM_DATA_BLOCKED | Stream flow control blocked |
| 0x16-0x17 | STREAMS_BLOCKED | Stream limit reached |
| 0x18 | NEW_CONNECTION_ID | Provide new Connection ID |
| 0x19 | RETIRE_CONNECTION_ID | Retire Connection ID |
| 0x1a | PATH_CHALLENGE | Validate network path |
| 0x1b | PATH_RESPONSE | Respond to path validation |
| 0x1c | CONNECTION_CLOSE | Terminate connection |
| 0x1d | CONNECTION_CLOSE | Terminate connection (app error) |
| 0x1e | HANDSHAKE_DONE | Handshake completion |

### CRYPTO Frame

```
CRYPTO Frame {
  Type (i) = 0x06,
  Offset (i),
  Length (i),
  Crypto Data (..),
}
```

- Carries TLS handshake messages
- Similar to STREAM frame but for handshake
- Three packet number spaces (Initial, Handshake, 1-RTT)
- Reliable delivery guaranteed

### Connection Termination

**CONNECTION_CLOSE Frame:**
```
CONNECTION_CLOSE Frame {
  Type (i) = 0x1c..0x1d,
  Error Code (i),
  [Frame Type (i)],
  Reason Phrase Length (i),
  Reason Phrase (..),
}
```

**Types:**
- 0x1c: QUIC transport error
- 0x1d: Application protocol error

**Immediate Close:**
- Endpoint sends CONNECTION_CLOSE
- Peer responds with CONNECTION_CLOSE
- Connection immediately terminated
- No more data exchanged

**Stateless Reset:**
- Used when endpoint loses connection state
- Small packet with Stateless Reset Token
- Allows peer to immediately close connection
- Prevents resource exhaustion attacks

## Packet Protection

### Protection Levels

1. **Initial Packets:** Protected with version-specific keys (derived from Destination Connection ID)
2. **Handshake Packets:** Protected with keys from TLS handshake
3. **0-RTT Packets:** Protected with early data keys from TLS
4. **1-RTT Packets:** Protected with application keys from TLS

### AEAD Usage

**Packet Protection:**
```
protected_payload = AEAD_Encrypt(packet_protection_key,
                                  packet_number,
                                  header,
                                  payload)
```

**Header Protection:**
- Packet number encrypted to prevent inference
- Sample taken from protected payload
- Applied after payload encryption
- Prevents connection tracking and traffic analysis

### Key Updates

**KEY_UPDATE Frame:**
```
KEY_UPDATE Frame {
  Type (i) = 0x1e,
}
```

- Allows refreshing packet protection keys
- Uses TLS key update mechanism
- Can be initiated by either endpoint
- Prevents key exhaustion

## Version Negotiation

### Version Selection

**Client:**
- Sends preferred version in first packet
- May include version-independent fields

**Server:**
- Accepts version or sends Version Negotiation packet
- Version Negotiation lists supported versions
- Client selects compatible version and reconnects

**Version Negotiation Packet:**
```
Version Negotiation Packet {
  Header Form (1) = 1,
  Unused (7),
  Version (32) = 0,
  DCID Len (8),
  Destination Connection ID (0..2040),
  SCID Len (8),
  Source Connection ID (0..2040),
  Supported Version (32) ...,
}
```

### Version Invariants

Fields guaranteed to remain consistent across versions:
- Long header format bit (first bit)
- Version field location (bytes 2-5)
- Connection ID fields in long header
- Version Negotiation packet format

## Transport Parameters

Negotiated during connection establishment via TLS extension:

```
Transport Parameters {
  original_destination_connection_id (0x00),
  max_idle_timeout (0x01),
  stateless_reset_token (0x02),
  max_udp_payload_size (0x03),
  initial_max_data (0x04),
  initial_max_stream_data_bidi_local (0x05),
  initial_max_stream_data_bidi_remote (0x06),
  initial_max_stream_data_uni (0x07),
  initial_max_streams_bidi (0x08),
  initial_max_streams_uni (0x09),
  ack_delay_exponent (0x0a),
  max_ack_delay (0x0b),
  disable_active_migration (0x0c),
  preferred_address (0x0d),
  active_connection_id_limit (0x0e),
  initial_source_connection_id (0x0f),
  retry_source_connection_id (0x10),
}
```

## Security Considerations

### Built-in Security

- **Mandatory Encryption:** All packets encrypted (except Version Negotiation)
- **TLS 1.3 Integration:** Leverages modern cryptographic protocols
- **Forward Secrecy:** Ephemeral key exchange required
- **Authentication:** Server always authenticated, client optionally

### Attack Mitigations

**Address Validation:**
- Prevents amplification attacks
- Uses address validation tokens
- Limits initial packet size from unvalidated addresses

**Denial of Service:**
- Stateless packet handling during handshake
- Connection limits per client
- Token-based validation reduces state requirements

**Connection Migration Security:**
- PATH_CHALLENGE/PATH_RESPONSE prevents address spoofing
- Only validated paths used for non-probing packets
- Connection ID rotation improves privacy

**Version Downgrade Protection:**
- Cryptographic binding prevents version rollback
- Compatible versions only after explicit negotiation

## Performance Characteristics

### Latency Benefits

- **0-RTT:** Lowest latency for resumed connections
- **1-RTT:** Faster than TCP+TLS (2-RTT)
- **No Head-of-Line Blocking:** Independent stream delivery
- **Connection Migration:** Seamless network transitions

### Throughput

- **Stream Multiplexing:** Efficient use of network capacity
- **Flexible Congestion Control:** Adapts to network conditions
- **Improved Loss Recovery:** Accurate RTT measurements

### Overhead

- **Header Size:**
  - Long header: ~20-30 bytes
  - Short header: ~10-20 bytes (variable)
- **Per-Frame:** 1-8 bytes type + variable payload
- **Encryption:** AEAD adds 16 bytes per packet

## Implementation Considerations

### Mandatory Features

- TLS 1.3 integration
- Connection establishment (1-RTT)
- Stream management
- Flow control
- Loss detection and recovery
- Connection termination

### Optional Features

- 0-RTT resumption
- Connection migration
- Key updates
- ECN support
- PMTU discovery

### Testing Requirements

- Interoperability testing
- Security validation
- Performance benchmarking
- Loss recovery under packet loss
- Congestion control fairness

## Use Cases

### HTTP/3

- Primary motivation for QUIC development
- Eliminates HTTP/2 over TCP head-of-line blocking
- Improves page load times
- Better mobile network performance

### Streaming Media

- Low-latency live streaming
- Adaptive bitrate without HOL blocking
- Stream prioritization

### Gaming

- Low-latency real-time communication
- Connection migration for mobile gaming
- Unreliable delivery option (DATAGRAM extension)

### IoT and Mobile

- Connection migration across networks
- Fast connection establishment
- Efficient for intermittent connectivity

## Related Specifications

- **RFC 8999:** Version-Independent Properties of QUIC
- **RFC 9001:** Using TLS to Secure QUIC
- **RFC 9002:** QUIC Loss Detection and Congestion Control
- **RFC 9114:** HTTP/3
- **RFC 9221:** QUIC Datagrams
- **RFC 9287:** Greasing the QUIC Bit
- **RFC 9368:** Compatible Version Negotiation for QUIC

## Summary

QUIC represents a fundamental rethinking of transport protocol design for the modern Internet. By integrating security, multiplexing, and advanced connection management into a UDP-based protocol, QUIC provides:

1. **Lower Latency:** Faster connection establishment through 0-RTT and 1-RTT modes
2. **Better Performance:** Elimination of head-of-line blocking improves throughput
3. **Enhanced Mobility:** Connection migration supports seamless network transitions
4. **Built-in Security:** TLS 1.3 integration provides mandatory encryption
5. **Deployment Flexibility:** UDP-based design enables user-space implementation and rapid evolution

The protocol has been rapidly adopted as the foundation for HTTP/3 and demonstrates significant performance improvements over TCP-based protocols, especially on mobile networks and lossy connections. QUIC's design enables innovation in transport protocol development while maintaining security and reliability guarantees.
