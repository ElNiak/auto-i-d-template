# RFC 793 - Transmission Control Protocol (TCP)

**Source:** IETF RFC 793
**URL:** https://www.rfc-editor.org/rfc/rfc793.txt
**Category:** Network Protocol - Transport Layer

## Protocol Overview

The Transmission Control Protocol (TCP) provides reliable, connection-oriented, end-to-end communication over unreliable packet-switched networks. It supports full-duplex data transmission and is one of the core protocols of the Internet Protocol Suite.

## Key Characteristics

- **Reliability:** Provides guaranteed delivery of data through sequence numbers and acknowledgments
- **Connection-Oriented:** Establishes and maintains connections between endpoints
- **Full-Duplex:** Supports simultaneous bidirectional communication
- **Stream-Oriented:** Treats data as a continuous byte stream
- **Flow Control:** Implements sliding window mechanism to prevent receiver overflow
- **Ordered Delivery:** Ensures data arrives in the order it was sent

## TCP Segment Header Format

```
    0                   1                   2                   3
    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |          Source Port          |       Destination Port        |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                        Sequence Number                        |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                    Acknowledgment Number                      |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |  Data |           |U|A|P|R|S|F|                               |
   | Offset| Reserved  |R|C|S|S|Y|I|            Window             |
   |       |           |G|K|H|T|N|N|                               |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |           Checksum            |         Urgent Pointer        |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                    Options                    |    Padding    |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                             data                              |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

### Header Fields

- **Source Port (16 bits):** Port number of sending application
- **Destination Port (16 bits):** Port number of receiving application
- **Sequence Number (32 bits):** Position of first data byte in this segment
- **Acknowledgment Number (32 bits):** Next expected sequence number from peer
- **Data Offset (4 bits):** Header length in 32-bit words
- **Control Flags (6 bits):**
  - URG: Urgent pointer field significant
  - ACK: Acknowledgment field significant
  - PSH: Push function
  - RST: Reset the connection
  - SYN: Synchronize sequence numbers
  - FIN: No more data from sender
- **Window (16 bits):** Number of bytes willing to accept
- **Checksum (16 bits):** Error detection for header and data
- **Urgent Pointer (16 bits):** Offset to urgent data

## Connection State Machine

### Connection States

1. **LISTEN:** Waiting for connection request
2. **SYN-SENT:** Sent connection request, waiting for acknowledgment
3. **SYN-RECEIVED:** Received and sent connection request, waiting for acknowledgment
4. **ESTABLISHED:** Connection established, data transfer can occur
5. **FIN-WAIT-1:** Sent close request, waiting for acknowledgment
6. **FIN-WAIT-2:** Waiting for close request from peer
7. **CLOSE-WAIT:** Received close request, waiting for local close
8. **CLOSING:** Both sides simultaneously closing
9. **LAST-ACK:** Waiting for final acknowledgment of close
10. **TIME-WAIT:** Waiting to ensure remote received close acknowledgment
11. **CLOSED:** No connection

### Connection Establishment (Three-Way Handshake)

```
Client                                Server
  |                                     |
  |  SYN (seq=x)                        |
  |------------------------------------>|
  |                                     | [LISTEN -> SYN-RECEIVED]
  |            SYN-ACK (seq=y, ack=x+1) |
  |<------------------------------------|
  | [SYN-SENT -> ESTABLISHED]           |
  |  ACK (ack=y+1)                      |
  |------------------------------------>|
  |                                     | [SYN-RECEIVED -> ESTABLISHED]
  |         Data Transfer               |
  |<----------------------------------->|
```

**Steps:**
1. Client sends SYN segment with initial sequence number
2. Server responds with SYN-ACK containing its own initial sequence number
3. Client acknowledges server's SYN with ACK
4. Connection is established, data transfer can begin

**Simultaneous Connection:**
- Both endpoints can initiate connection simultaneously
- Resolves to single connection with proper state transitions

### Connection Termination

```
Client                                Server
  |                                     |
  |  FIN (seq=x)                        |
  |------------------------------------>|
  |                                     | [ESTABLISHED -> CLOSE-WAIT]
  |            ACK (ack=x+1)            |
  |<------------------------------------|
  | [ESTABLISHED -> FIN-WAIT-1]         |
  | [FIN-WAIT-1 -> FIN-WAIT-2]          |
  |                                     |
  |            FIN (seq=y)              |
  |<------------------------------------|
  |                                     | [CLOSE-WAIT -> LAST-ACK]
  |  ACK (ack=y+1)                      |
  |------------------------------------>|
  | [FIN-WAIT-2 -> TIME-WAIT]           |
  |                                     | [LAST-ACK -> CLOSED]
  | [TIME-WAIT -> CLOSED after 2MSL]    |
```

**Graceful Close:**
1. One side sends FIN segment
2. Other side acknowledges FIN
3. Second side sends its FIN
4. First side acknowledges and enters TIME-WAIT
5. After 2*MSL (Maximum Segment Lifetime), connection fully closes

## Sequence Number Management

### Sequence Space

- **32-bit unsigned integers:** Range 0 to 2^32 - 1
- **Circular:** Wraps around from 2^32 - 1 to 0
- **Initial Sequence Number (ISN):** Selected at connection establishment
- **Prevents Confusion:** Ensures old segments don't interfere with new connections

### Sequence Number Comparison

- Uses modular arithmetic for wraparound handling
- Defines "less than," "equal to," and "greater than" comparisons
- Ensures correct ordering even with sequence number wraparound

## Flow Control Mechanism

### Sliding Window Protocol

- **Window:** Range of acceptable sequence numbers
- **Sender Window:** Data that can be sent without acknowledgment
- **Receiver Window:** Buffer space available for incoming data
- **Window Size:** Advertised in each TCP segment (16-bit field)
- **Dynamic Adjustment:** Receiver adjusts window based on buffer availability

### Window Management

```
Sender Perspective:
  [Sent & Acked] [Sent, Not Acked] [Can Send] [Cannot Send Yet]
                 |<---Window--->|

Receiver Perspective:
  [Received & Acked] [Can Receive] [Cannot Receive Yet]
                     |<-Window-->|
```

### Zero Window

- Receiver can advertise window size of 0 to stop sender
- Sender must periodically probe to detect window reopening
- Prevents deadlock situations

## Retransmission and Timeout

### Retransmission Timer

- **Round-Trip Time (RTT) Estimation:** Dynamically calculated
- **Retransmission Timeout (RTO):** Based on RTT + variance
- **Exponential Backoff:** Doubles timeout on each retransmission
- **Maximum Retries:** Eventually gives up and resets connection

### Karn's Algorithm

- Don't update RTT estimate from retransmitted segments
- Prevents incorrect RTT measurements that could destabilize timeout

## Congestion Control Considerations

While RFC 793 predates formal congestion control algorithms, it establishes:

- **Slow Start:** Gradually increase sending rate
- **Congestion Avoidance:** Reduce rate when congestion detected
- **Fast Retransmit:** Retransmit on duplicate ACKs
- **Fast Recovery:** Avoid slow start after fast retransmit

(Note: Formal congestion control specified in later RFCs like RFC 5681)

## Error Handling

### Checksum Verification

- Computed over pseudo-header, TCP header, and data
- Detects corruption in transmission
- Invalid checksums cause segment discard

### Reset (RST) Handling

- Abruptly terminates connection
- Sent for various error conditions:
  - Connection to non-existent port
  - Invalid sequence numbers
  - Security violations
  - Resource exhaustion

### Duplicate Detection

- Sequence numbers prevent duplicate data processing
- Acknowledgments handle duplicate segments gracefully

## Design Principles

### Robustness Principle

**"Be conservative in what you send, liberal in what you accept"**

- Send well-formed, compliant segments
- Accept and process segments with minor variations
- Gracefully handle unexpected conditions

### Layered Architecture

- Clear separation from IP layer below
- Well-defined interface to applications above
- Encapsulation of transport concerns

### End-to-End Reliability

- Reliability implemented at endpoints, not in network
- Intermediate routers need not maintain connection state
- Enables scalability and simplicity in network infrastructure

## Key Protocol Features

### Urgent Data

- URG flag and Urgent Pointer indicate high-priority data
- Allows out-of-band signaling within TCP stream
- Application-specific interpretation

### Push Function

- PSH flag requests immediate delivery to application
- Prevents buffering delays
- Useful for interactive applications

### Keep-Alive

- Optional mechanism to detect dead connections
- Periodic probes sent during idle periods
- Not part of original specification but widely implemented

## Security Considerations

### Vulnerabilities in Original Spec

- **No Authentication:** Sequence numbers guessable
- **SYN Flooding:** Resource exhaustion attacks
- **Connection Hijacking:** Attacker can inject segments
- **No Encryption:** Data transmitted in clear

### Modern Extensions

- **TCP MD5 Signature (RFC 2385):** Authenticates segments
- **TLS/SSL:** Provides encryption and authentication above TCP
- **TCP Authentication Option (RFC 5925):** Enhanced security

## Performance Characteristics

### Throughput

- Limited by window size and round-trip time
- Maximum throughput ≈ Window Size / RTT
- Window scaling (RFC 1323) enables larger windows

### Latency

- Three-way handshake adds 1.5 RTT before data transfer
- Retransmissions increase latency for lost segments
- Head-of-line blocking: lost segment delays subsequent data

### Efficiency

- Header overhead: 20-60 bytes per segment
- Acknowledgment overhead: Piggybacking reduces cost
- Delayed ACKs reduce ACK traffic

## Applicability

### Ideal Use Cases

- Applications requiring reliability (file transfer, email, web)
- Long-lived connections (databases, remote terminals)
- Bulk data transfer where throughput matters

### Limitations

- Higher latency than UDP due to handshake and retransmissions
- Head-of-line blocking problematic for real-time applications
- Connection state overhead for short-lived connections

## Implementation Considerations

### Resource Management

- Memory for send and receive buffers
- Connection state (sockets) per active connection
- Timers for retransmission and keep-alive

### Nagle's Algorithm

- Coalesces small sends to reduce segment count
- Disabled for interactive applications (TCP_NODELAY)

### Silly Window Syndrome

- Avoids sending or advertising tiny windows
- Improves efficiency by batching data

## Historical Context

- **Published:** September 1981
- **Developed By:** DARPA Internet Program
- **Primary Authors:** Jon Postel, et al.
- **Obsoletes:** RFC 761
- **Standard:** Internet Standard (STD 7)

## Related RFCs

- **RFC 791:** Internet Protocol (IP) - Transport layer below TCP
- **RFC 1122:** Requirements for Internet Hosts (Host compliance)
- **RFC 1323:** TCP Extensions for High Performance (window scaling, timestamps)
- **RFC 2018:** TCP Selective Acknowledgment (SACK)
- **RFC 5681:** TCP Congestion Control
- **RFC 6298:** Computing TCP's Retransmission Timer
- **RFC 7323:** TCP Extensions for High Performance (updates 1323)

## Summary

RFC 793 defines TCP as a robust, reliable, connection-oriented transport protocol that has become fundamental to Internet communication. Its design principles of reliability, flow control, and ordered delivery have proven remarkably durable, with the protocol remaining largely unchanged at its core for over 40 years. Modern extensions address performance and security challenges while maintaining backward compatibility with the original specification.

The protocol's success lies in its careful balance of:
- **Simplicity:** Core mechanisms are straightforward
- **Robustness:** Handles diverse network conditions gracefully
- **Flexibility:** Extensible through options mechanism
- **Scalability:** Stateless intermediate nodes enable global deployment

TCP remains the workhorse of Internet transport, carrying the majority of Internet traffic and serving as the foundation for protocols like HTTP, SMTP, SSH, and countless application-level protocols.
