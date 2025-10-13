# RFC 9110: HTTP Semantics

**Source:** IETF RFC 9110
**URL:** https://www.rfc-editor.org/rfc/rfc9110.txt
**Published:** June 2022
**Category:** Standards Track

## Abstract

HTTP is a stateless application-level protocol for distributed, collaborative, hypertext information systems. This document defines the core HTTP protocol architecture and terminology, including HTTP versions and semantic evolution.

## Key Concepts

### Resources

- **Definition**: Resources are identified by Uniform Resource Identifiers (URIs)
- **Flexibility**: Can represent anything, not limited by nature
- **Separation**: Request semantics are separated from resource representation

### Representations

- **Purpose**: Information reflecting a resource's state
- **Transfer**: Transferable via protocol
- **Multiplicity**: Multiple representations can exist for the same resource

### Message Structure

HTTP messages consist of:
- **Control data**: Directives for message routing and processing
- **Header fields**: Metadata about the message
- **Content stream**: The actual payload (optional)
- **Trailer fields**: Additional metadata after the content (optional)

## Communication Model

- **Client-Server**: Client sends request messages, server interprets and responds
- **Stateless Design**: No session state is retained between requests
- **Request-Response**: Synchronous message exchange pattern

## HTTP Methods

### Standard Methods

| Method | Purpose | Safe | Idempotent |
|--------|---------|------|------------|
| GET | Retrieve resource representation | Yes | Yes |
| POST | Process information | No | No |
| PUT | Update resource state | No | Yes |
| DELETE | Remove resource | No | Yes |
| HEAD | Retrieve headers without content | Yes | Yes |
| OPTIONS | Query communication options | Yes | Yes |
| CONNECT | Establish tunnel | No | No |
| TRACE | Message diagnostic loop | Yes | Yes |

### Method Semantics

- **Safe Methods**: Do not modify resources (GET, HEAD, OPTIONS, TRACE)
- **Idempotent Methods**: Same result regardless of repetition (GET, PUT, DELETE, HEAD, OPTIONS, TRACE)

## Status Codes

HTTP status codes are categorized into five classes:

### 1xx: Informational
- Interim response before the actual response
- Indicate that the request was received and is being processed

### 2xx: Successful
- Request was successfully received, understood, and accepted
- Examples: 200 OK, 201 Created, 204 No Content

### 3xx: Redirection
- Further action needed to complete the request
- Examples: 301 Moved Permanently, 302 Found, 304 Not Modified

### 4xx: Client Errors
- Request contains bad syntax or cannot be fulfilled
- Examples: 400 Bad Request, 401 Unauthorized, 404 Not Found

### 5xx: Server Errors
- Server failed to fulfill a valid request
- Examples: 500 Internal Server Error, 503 Service Unavailable

## HTTP Versions

- **Major version**: Indicates messaging syntax and framing
- **Minor version**: Indicates sender's communication capabilities
- **Version Format**: HTTP/major.minor (e.g., HTTP/1.1, HTTP/2.0)

## Header Fields

HTTP header fields provide metadata about:
- Request or response messages
- Resource representations
- Connection parameters
- Authentication credentials
- Caching directives
- Content negotiation

## Content Negotiation

- **Proactive**: Server selects representation based on client preferences
- **Reactive**: Server provides list of alternatives for client to choose
- **Transparent**: Combination of proactive and reactive negotiation

## API Design Implications

### Resource-Oriented Design
- Design APIs around resources (nouns) rather than actions (verbs)
- Use HTTP methods to express operations on resources
- Leverage URI structure to represent resource hierarchies

### Stateless Operations
- Each request must contain all information needed to understand and process it
- Server should not rely on previous requests
- Use tokens or identifiers for maintaining application state

### Idempotency
- Design PUT and DELETE operations to be idempotent
- Consider idempotency for POST operations where appropriate
- Use idempotency keys for safe retries

### Status Code Usage
- Use appropriate status codes to convey operation results
- 2xx for successful operations
- 4xx for client errors (validation, authentication, authorization)
- 5xx for server errors

### Header Field Best Practices
- Use standard headers when available
- Create custom headers with appropriate prefixes
- Document custom header semantics clearly

## Security Considerations

- **Authentication**: Use appropriate authentication schemes
- **Authorization**: Validate permissions for each request
- **Confidentiality**: Use TLS/HTTPS for sensitive data
- **Integrity**: Validate input and sanitize output
- **Privacy**: Minimize sensitive data in logs and error messages

## Versioning Considerations

- **Major version changes**: Breaking changes to message syntax
- **Minor version changes**: Backward-compatible additions
- **API versioning**: Separate from HTTP protocol versioning
- **Version signaling**: Use HTTP version, URI path, or custom headers

## References

- Full RFC text: https://www.rfc-editor.org/rfc/rfc9110.txt
- Related RFCs:
  - RFC 9111 (HTTP Caching)
  - RFC 9112 (HTTP/1.1)
  - RFC 9113 (HTTP/2)
  - RFC 9114 (HTTP/3)

---

**Key Takeaways for REST API Design:**

1. Use HTTP methods semantically (GET for retrieval, POST for creation, PUT for updates, DELETE for removal)
2. Design stateless APIs where each request is self-contained
3. Leverage appropriate status codes to communicate operation results
4. Use header fields for metadata and control information
5. Design idempotent operations where possible for reliability
6. Separate resource identification (URI) from representation (content negotiation)
7. Follow the uniform interface constraint for consistency
