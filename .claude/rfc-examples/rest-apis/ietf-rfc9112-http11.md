# RFC 9112: HTTP/1.1

**Source:** IETF RFC 9112
**URL:** https://www.rfc-editor.org/rfc/rfc9112.txt
**Category:** Standards Track

## Abstract

The Hypertext Transfer Protocol (HTTP) is a stateless application-level protocol for distributed, collaborative, hypertext information systems. This document specifies HTTP/1.1 message syntax, framing, and connection management.

## Introduction

HTTP/1.1 is a request/response protocol that:
- Uses extensible semantics and self-descriptive messages
- Specifies message syntax, framing, and connection management
- Operates over TCP (or equivalent reliable transport)

## Message Format

### Core Structure

HTTP/1.1 messages consist of:
1. **Start-line**: Request-line or status-line
2. **Header fields**: Zero or more name-value pairs
3. **Empty line**: CRLF separator
4. **Message body**: Optional content

### Message Syntax

```
HTTP-message = start-line
               *( header-field CRLF )
               CRLF
               [ message-body ]
```

### Parsing Requirements

- Messages are sequences of octets (8-bit bytes)
- Case-sensitive in most contexts
- Whitespace rules strictly defined
- Security-focused parsing to prevent attacks

## Request Line

### Format

```
request-line = method SP request-target SP HTTP-version CRLF
```

### Components

1. **Method**: HTTP method token (GET, POST, PUT, DELETE, etc.)
2. **Request-target**: Resource identifier
3. **HTTP-version**: Protocol version (HTTP/1.1)

### Request-Target Formats

Four possible formats:

1. **Origin-form**: Most common
   ```
   GET /where?q=now HTTP/1.1
   ```

2. **Absolute-form**: Used with proxies
   ```
   GET http://www.example.org/pub/WWW/TheProject.html HTTP/1.1
   ```

3. **Authority-form**: Used with CONNECT
   ```
   CONNECT www.example.com:80 HTTP/1.1
   ```

4. **Asterisk-form**: Used with OPTIONS
   ```
   OPTIONS * HTTP/1.1
   ```

## Status Line

### Format

```
status-line = HTTP-version SP status-code SP reason-phrase CRLF
```

### Example

```
HTTP/1.1 200 OK
```

## Header Fields

### Structure

```
header-field = field-name ":" OWS field-value OWS
```

### Key Characteristics

- **Case-insensitive**: Field names are case-insensitive
- **Order**: Generally, field order is not significant
- **Repetition**: Some fields can appear multiple times
- **Whitespace**: Optional whitespace (OWS) around field values

### Common Header Fields

- **Host**: Required in HTTP/1.1 requests
- **Content-Length**: Size of message body
- **Content-Type**: Media type of message body
- **Transfer-Encoding**: Applied encodings
- **Connection**: Connection management

## Message Body

### Presence Determination

A message body is present when:
- **Content-Length** header is present with non-zero value
- **Transfer-Encoding** header is present

### Transfer Encodings

#### Chunked Transfer Encoding

Format:
```
chunked-body = *chunk
               last-chunk
               trailer-section
               CRLF
```

Chunk format:
```
chunk = chunk-size [ chunk-ext ] CRLF
        chunk-data CRLF
```

Example:
```
7\r\n
Mozilla\r\n
9\r\n
Developer\r\n
7\r\n
Network\r\n
0\r\n
\r\n
```

## Connection Management

### Persistent Connections

HTTP/1.1 uses persistent connections by default:
- **Keep-Alive**: Connection remains open after response
- **Pipeline**: Multiple requests can be sent before receiving responses
- **Close**: Connection closed after response

### Connection Header

```
Connection: keep-alive
Connection: close
```

### Connection Establishment

1. Client opens TCP connection to server
2. Client sends HTTP request
3. Server processes and sends response
4. Connection either persists or closes

### Connection Closure

Connections can close due to:
- **Client request**: Connection: close header
- **Server decision**: After sending response
- **Timeout**: Inactivity timeout
- **Error**: Network or protocol error

### Timeouts

- **Idle timeout**: Connection closed after period of inactivity
- **Request timeout**: Maximum time to receive complete request
- **Response timeout**: Maximum time to send complete response

## Concurrency and Parallelism

### Pipelining

- Multiple requests sent without waiting for responses
- Responses must be sent in same order as requests
- Not widely used due to head-of-line blocking

### Multiple Connections

- Clients may open multiple connections to same server
- Recommended: 2-6 concurrent connections per host
- More connections increase server load

## Security Considerations

### Response Splitting

- **Vulnerability**: CRLF injection in headers
- **Prevention**: Validate and sanitize all header values
- **Impact**: Can lead to cache poisoning or XSS attacks

### Message Parsing

- **Strict parsing**: Reject malformed messages
- **Length limits**: Enforce maximum sizes
- **Timeout enforcement**: Prevent resource exhaustion

### Request Smuggling

- **Vulnerability**: Ambiguous message boundaries
- **Prevention**: Clear framing with Content-Length or chunked encoding
- **Detection**: Monitor for inconsistent header combinations

## API Design Implications

### Message Framing

- Always specify either Content-Length or use chunked encoding
- Validate message boundaries to prevent smuggling attacks
- Use consistent framing approach across API

### Connection Handling

- Support persistent connections for efficiency
- Implement appropriate timeouts to prevent resource exhaustion
- Consider connection limits per client

### Header Management

- Use standard headers when available
- Validate all header values before processing
- Be cautious with custom headers in security contexts

### Error Handling

- Return appropriate status codes for malformed requests
- Close connections on protocol violations
- Log security-relevant parsing errors

### Performance Optimization

- Leverage persistent connections to reduce latency
- Consider HTTP/2 or HTTP/3 for modern deployments
- Implement proper caching headers

### Backward Compatibility

- Support HTTP/1.1 for broad compatibility
- Negotiate protocol versions appropriately
- Maintain consistent behavior across versions

## Best Practices

1. **Always include Host header** in HTTP/1.1 requests
2. **Use Content-Length** when message size is known
3. **Use chunked encoding** for streaming responses
4. **Implement connection timeouts** to prevent resource leaks
5. **Validate message format** strictly to prevent attacks
6. **Support persistent connections** for efficiency
7. **Handle connection closure** gracefully
8. **Log security-relevant events** for monitoring

## Relationship to HTTP/2 and HTTP/3

HTTP/1.1 characteristics compared to newer versions:
- **Text-based**: HTTP/2 and HTTP/3 use binary framing
- **Sequential**: HTTP/2+ support multiplexing
- **TCP-based**: HTTP/3 uses QUIC (UDP-based)
- **Header compression**: HTTP/2+ use HPACK/QPACK

## References

- Full RFC text: https://www.rfc-editor.org/rfc/rfc9112.txt
- Related RFCs:
  - RFC 9110 (HTTP Semantics)
  - RFC 9111 (HTTP Caching)
  - RFC 9113 (HTTP/2)
  - RFC 9114 (HTTP/3)

---

**Key Takeaways for REST API Implementation:**

1. Implement proper message framing with Content-Length or chunked encoding
2. Support persistent connections for improved performance
3. Validate all message components strictly to prevent security vulnerabilities
4. Handle connection lifecycle appropriately (establishment, maintenance, closure)
5. Use appropriate timeouts to prevent resource exhaustion
6. Consider upgrading to HTTP/2 or HTTP/3 for modern deployments
7. Maintain HTTP/1.1 support for backward compatibility
