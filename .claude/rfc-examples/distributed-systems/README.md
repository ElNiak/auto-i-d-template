# Distributed Systems Protocol Examples

This directory contains protocol specifications for distributed systems communication patterns.

## Collection Date
2025-10-13

## Files

### IETF RFCs

1. **rfc7540-http2.md** (4.2KB)
   - RFC 7540: HTTP/2
   - Binary framing, multiplexing, server push
   - Source: https://www.rfc-editor.org/rfc/rfc7540.txt

2. **rfc6455-websocket.md** (6.6KB)
   - RFC 6455: WebSocket Protocol
   - Full-duplex communication, real-time messaging
   - Source: https://www.rfc-editor.org/rfc/rfc6455.txt

### Company Protocols

3. **grpc-protocol.md** (7.6KB)
   - gRPC Protocol Specification (Google)
   - RPC framework over HTTP/2, Protocol Buffers
   - Source: https://github.com/grpc/grpc/blob/master/doc/PROTOCOL-HTTP2.md

4. **kafka-protocol.md** (9.4KB)
   - Apache Kafka Wire Protocol
   - Binary streaming protocol, message batching
   - Source: https://kafka.apache.org/protocol

5. **nats-protocol.md** (10KB)
   - NATS Messaging Protocol
   - Text-based pub/sub, lightweight messaging
   - Source: https://docs.nats.io/reference/reference-protocols/nats-protocol

### Documentation

6. **summary.md** (13KB)
   - Comprehensive comparison and analysis
   - Cross-protocol patterns and use cases
   - Implementation guidance

7. **README.md** (this file)
   - Quick reference and navigation

## Quick Reference

### By Use Case

**Microservices Communication:**
- Primary: grpc-protocol.md
- Alternative: rfc7540-http2.md

**Real-time Web Applications:**
- Primary: rfc6455-websocket.md
- Alternative: rfc7540-http2.md (server push)

**Event Streaming:**
- Primary: kafka-protocol.md
- Alternative: nats-protocol.md (with JetStream)

**Lightweight Messaging:**
- Primary: nats-protocol.md
- Alternative: rfc6455-websocket.md

**Request/Response APIs:**
- Primary: grpc-protocol.md
- Alternative: rfc7540-http2.md

### By Protocol Characteristic

**Binary Protocols:**
- rfc7540-http2.md
- grpc-protocol.md
- kafka-protocol.md

**Text-Based Protocols:**
- nats-protocol.md

**Streaming Support:**
- rfc7540-http2.md (HTTP/2 streams)
- rfc6455-websocket.md (full-duplex)
- grpc-protocol.md (4 streaming types)
- kafka-protocol.md (log-based streaming)

**Pub/Sub Pattern:**
- kafka-protocol.md (topic-based)
- nats-protocol.md (subject-based)

**Persistent Storage:**
- kafka-protocol.md (durable log)
- nats-protocol.md (JetStream extension)

## Protocol Selection Guide

```
Need RPC with strong typing? → grpc-protocol.md
Need event streaming? → kafka-protocol.md
Need browser-compatible real-time? → rfc6455-websocket.md
Need lightweight pub/sub? → nats-protocol.md
Need HTTP semantics with performance? → rfc7540-http2.md
```

## Additional Resources

- **summary.md**: Detailed cross-protocol comparison, patterns, and implementation guidance
- See individual files for protocol-specific details, message formats, and security considerations

## Application Profile
Distributed Systems - Communication Protocols and Wire Formats
