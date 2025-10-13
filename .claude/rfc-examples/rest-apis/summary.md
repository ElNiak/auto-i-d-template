# REST API Examples and Patterns: Summary

**Collection Date:** 2025-10-13
**Purpose:** Reference examples for REST API application profile design
**Total Documents:** 7 (4 IETF RFCs + 3 Company Standards)

## Document Index

### IETF Standards

1. **RFC 9110: HTTP Semantics**
   - File: `ietf-rfc9110-http-semantics.md`
   - Focus: Core HTTP protocol, methods, status codes, headers
   - Key for: Understanding HTTP fundamentals

2. **RFC 9112: HTTP/1.1**
   - File: `ietf-rfc9112-http11.md`
   - Focus: Message format, framing, connection management
   - Key for: Implementation details, security considerations

3. **RFC 6570: URI Templates**
   - File: `ietf-rfc6570-uri-templates.md`
   - Focus: URI template syntax and expansion
   - Key for: API URL design, documentation

4. **RFC 7807: Problem Details for HTTP APIs**
   - File: `ietf-rfc7807-problem-details.md`
   - Focus: Standardized error response format
   - Key for: Error handling design

### Industry Best Practices

5. **Google API Design Guide**
   - File: `google-api-design-guide.md`
   - Focus: Resource-oriented design, standard methods, Protocol Buffers
   - Key for: Enterprise API architecture

6. **AWS API Gateway Best Practices**
   - File: `aws-api-gateway-best-practices.md`
   - Focus: Security, authentication, monitoring, operations
   - Key for: Cloud-native API deployment

7. **Stripe API Design**
   - File: `stripe-api-design.md`
   - Focus: Developer experience, API evolution, backward compatibility
   - Key for: API versioning and migration strategies

## Comparative Analysis

### Core Design Philosophy

| Source | Philosophy | Primary Focus |
|--------|-----------|---------------|
| **IETF RFCs** | Standards-based, protocol-focused | Interoperability, correctness |
| **Google** | Resource-oriented, consistency | Large-scale systems, typed APIs |
| **AWS** | Security-first, cloud-native | Operations, monitoring, cost |
| **Stripe** | Developer experience, simplicity | Ease of use, backward compatibility |

### Resource Design Patterns

#### URL Structure

**Google Approach:**
```
/v1/publishers/{publisher}/books/{book}
```
- Hierarchical resource names
- Collection/resource pairs
- Explicit version in path

**AWS Approach:**
```
/users/{userId}
/users/{userId}/orders/{orderId}
```
- RESTful resource paths
- Nested resources
- Stage-based versioning

**Stripe Approach:**
```
/v1/charges/{charge_id}
/v1/customers/{customer_id}/sources
```
- Flat resource structure
- Limited nesting
- Account-based versioning

#### HTTP Method Usage

**Standard Pattern (RFC 9110):**
- GET: Retrieve (safe, idempotent)
- POST: Create (non-idempotent)
- PUT: Replace (idempotent)
- PATCH: Update (idempotent)
- DELETE: Remove (idempotent)

**Google Extensions:**
- Standard methods: List, Get, Create, Update, Delete
- Custom methods: `POST /:customVerb` (e.g., `:publish`, `:cancel`)

**Stripe Simplification:**
- Primarily GET, POST, DELETE
- Limited PUT usage
- POST for both create and update operations

### Authentication & Authorization

| Approach | Method | Use Case |
|----------|--------|----------|
| **OAuth 2.0** | Token-based | Public APIs, third-party access |
| **API Keys** | Simple key | Internal APIs, rate limiting |
| **JWT** | Self-contained tokens | Stateless authentication |
| **IAM** | AWS-specific | Cloud resource access |
| **mTLS** | Certificate-based | Service-to-service |

**Best Practices from Collection:**
- Don't use API keys for authentication (AWS)
- Implement least privilege access (AWS)
- Use proper authorization schemes (RFC 9110)
- Consider Lambda/Cognito authorizers (AWS)
- Support multiple authentication methods (Google)

### Error Handling Patterns

#### RFC 7807 Problem Details (Standard)
```json
{
  "type": "https://example.com/probs/out-of-credit",
  "title": "You do not have enough credit",
  "status": 403,
  "detail": "Your current balance is 30, but that costs 50",
  "instance": "/account/12345/msgs/abc"
}
```

#### Google Error Format
```json
{
  "error": {
    "code": 404,
    "message": "Resource not found",
    "status": "NOT_FOUND",
    "details": [...]
  }
}
```

#### Stripe Error Format
```json
{
  "error": {
    "type": "invalid_request_error",
    "message": "Amount must be at least $0.50 usd",
    "param": "amount",
    "code": "amount_too_small"
  }
}
```

**Common Elements:**
- HTTP status code
- Machine-readable error type/code
- Human-readable message
- Context-specific details

### Versioning Strategies

#### URL Path Versioning (Google, Stripe)
```
/v1/resources
/v2/resources
```
**Pros:** Clear, cacheable, easy to route
**Cons:** Proliferates endpoints

#### Header Versioning (Stripe alternate)
```
Stripe-Version: 2023-10-16
```
**Pros:** Clean URLs, account-level control
**Cons:** Less visible, caching complexity

#### API Gateway Stage Versioning (AWS)
```
/dev/resources
/prod/resources
```
**Pros:** Environment separation
**Cons:** Not true versioning

#### Breaking vs. Non-Breaking Changes

**Breaking Changes (require new version):**
- Removing endpoints or fields
- Changing field types
- Changing response structure
- New required parameters
- Behavior changes

**Non-Breaking Changes (safe to deploy):**
- Adding endpoints
- Adding optional fields
- Adding response fields
- New optional parameters
- Performance improvements

### Pagination Patterns

#### Cursor-Based (Stripe, Google)
```
GET /resources?limit=10&starting_after=cursor_abc
```
**Response:**
```json
{
  "data": [...],
  "has_more": true
}
```

#### Token-Based (Google)
```
GET /resources?page_size=10&page_token=token_abc
```
**Response:**
```json
{
  "resources": [...],
  "next_page_token": "token_def"
}
```

#### Offset-Based (Common but discouraged)
```
GET /resources?limit=10&offset=20
```

**Best Practice:** Cursor or token-based for consistency with data changes

### Filtering and Query Patterns

#### URI Templates (RFC 6570)
```
/search{?q,limit,offset}
/users{?status,role*}
```

#### Google Filtering
```
GET /books?filter=genre='fiction' AND publish_year>2020
```

#### AWS Query Parameters
```
GET /users?status=active&role=admin
```

#### Stripe Expansion
```
GET /charges/ch_123?expand[]=customer&expand[]=invoice
```

## Key Design Principles Extracted

### 1. Resource-Oriented Design

**From Google:**
- Design around resources (nouns), not operations (verbs)
- Use standard methods for common operations
- Hierarchical resource naming

**Application:**
```
Good: GET /users/123
Bad:  GET /getUser?id=123
```

### 2. Statelessness

**From RFC 9110:**
- Each request contains all necessary information
- No server-side session state
- Use tokens/cookies for application state

### 3. Idempotency

**From Stripe:**
- Use idempotency keys for POST operations
- Design PUT and DELETE to be idempotent
- Enable safe retries

**Implementation:**
```
POST /charges
Idempotency-Key: unique_key_123
```

### 4. Predictable State Machines

**From Stripe PaymentIntents:**
```
requires_payment_method → requires_confirmation
                       ↓
                  requires_action
                       ↓
                   processing
                       ↓
                   succeeded
```

### 5. Security by Default

**From AWS:**
- Implement authentication on all endpoints
- Use least privilege access
- Enable logging and monitoring
- Validate all inputs
- Private by default, public by exception

### 6. Developer Experience

**From Stripe:**
- Make simple cases simple
- Provide clear error messages
- Comprehensive documentation
- Interactive examples
- Powerful CLI tools

### 7. Backward Compatibility

**From Stripe Evolution:**
- Layer new APIs over old ones
- Provide migration paths
- Don't force breaking changes
- Version at appropriate granularity

### 8. Observability

**From AWS:**
- Comprehensive logging
- Metrics collection
- Distributed tracing
- Error monitoring
- Performance tracking

## Common Patterns

### 1. Collection and Resource Pattern

```
GET    /resources         # List collection
POST   /resources         # Create resource
GET    /resources/{id}    # Get resource
PUT    /resources/{id}    # Replace resource
PATCH  /resources/{id}    # Update resource
DELETE /resources/{id}    # Delete resource
```

### 2. Nested Resources

```
GET /users/{userId}/posts
GET /users/{userId}/posts/{postId}
```

**When to nest:**
- Strong ownership relationship
- Resource cannot exist independently
- Clear hierarchical structure

**When not to nest:**
- Deep nesting (limit to 2 levels)
- Resource used in multiple contexts
- Complex query requirements

### 3. Actions on Resources

**Google Custom Methods:**
```
POST /resources/{id}:action
```

**Examples:**
```
POST /posts/{id}:publish
POST /orders/{id}:cancel
POST /emails/{id}:send
```

### 4. Batch Operations

**Google Batch Pattern:**
```
POST /resources:batchGet
POST /resources:batchCreate
POST /resources:batchUpdate
```

**Considerations:**
- Transaction semantics
- Partial failure handling
- Result reporting

### 5. Long-Running Operations

**Google LRO Pattern:**
```
POST /resources:import
→ Returns: {name: "operations/123", done: false}

GET /operations/123
→ Returns: {name: "operations/123", done: true, response: {...}}
```

### 6. Filtering and Searching

**Query Parameters:**
```
GET /resources?filter=field:value
GET /resources?q=search_term
GET /resources?status=active&sort=created_desc
```

### 7. Field Selection

**Partial Responses:**
```
GET /resources?fields=id,name,created
```

**Expansion:**
```
GET /resources?expand=related_resource
```

### 8. Versioning

**API Version:**
```
/v1/resources
/v2/resources
```

**Resource Version/ETag:**
```
If-Match: "version_string"
ETag: "version_string"
```

## HTTP Status Code Usage Guide

### Success (2xx)

- **200 OK**: Standard success response
- **201 Created**: Resource created (include Location header)
- **202 Accepted**: Async operation accepted
- **204 No Content**: Success with no response body (DELETE)

### Client Error (4xx)

- **400 Bad Request**: Invalid request (validation failure)
- **401 Unauthorized**: Authentication required
- **403 Forbidden**: Authenticated but not authorized
- **404 Not Found**: Resource doesn't exist
- **405 Method Not Allowed**: HTTP method not supported
- **409 Conflict**: Resource state conflict (e.g., already exists)
- **422 Unprocessable Entity**: Semantic validation failure
- **429 Too Many Requests**: Rate limit exceeded

### Server Error (5xx)

- **500 Internal Server Error**: Unexpected server error
- **502 Bad Gateway**: Upstream service error
- **503 Service Unavailable**: Temporary unavailability
- **504 Gateway Timeout**: Upstream timeout

## Header Usage Patterns

### Standard Headers

**Request:**
```
Authorization: Bearer token
Content-Type: application/json
Accept: application/json
If-Match: "etag_value"
Idempotency-Key: unique_key
```

**Response:**
```
Content-Type: application/json
ETag: "etag_value"
Location: /resources/new_id
Cache-Control: max-age=3600
Retry-After: 60
```

### Custom Headers

**Best Practices:**
- Use `X-` prefix for custom headers (deprecated but common)
- Or use vendor-specific prefix: `Stripe-Version`
- Document all custom headers
- Consider standardization

## Security Considerations Summary

### From RFC 9110 & 9112
- Use HTTPS for all APIs
- Validate message format strictly
- Prevent request smuggling
- Implement timeouts
- Sanitize error messages

### From AWS
- Implement authentication on all endpoints
- Use IAM with least privilege
- Enable CloudWatch logging
- Use CloudTrail for audit
- Private APIs for internal services
- Request validation at gateway
- Rate limiting and throttling

### From Industry Practice
- Don't expose internal details in errors
- Verify webhook signatures
- Use short-lived tokens
- Implement CORS properly
- Validate all inputs
- Sanitize outputs
- Regular security audits

## Performance Optimization

### Caching Strategies

**Client-Side Caching:**
```
Cache-Control: public, max-age=3600
ETag: "resource_version"
Last-Modified: Thu, 01 Dec 2024 16:00:00 GMT
```

**Conditional Requests:**
```
If-None-Match: "etag_value"
If-Modified-Since: Thu, 01 Dec 2024 16:00:00 GMT
```

**Server-Side Caching (AWS):**
- API Gateway caching
- CloudFront CDN
- ElastiCache for data

### Connection Management

**HTTP/1.1 (RFC 9112):**
- Persistent connections by default
- Connection: keep-alive
- Multiple connections per host (2-6)

**HTTP/2 & HTTP/3:**
- Multiplexing
- Server push
- Header compression

### Pagination Best Practices

- Limit maximum page size
- Use cursor-based pagination
- Return total count only when needed
- Allow clients to specify page size

### Field Selection

- Support partial responses
- Allow clients to request only needed fields
- Expansion for related resources
- Balance between flexibility and complexity

## Documentation Best Practices

### From Stripe
- Interactive API reference
- Code examples in multiple languages
- Working examples with test data
- Version-specific documentation
- Migration guides for version changes

### From Google
- Inline documentation in API definitions
- High-level overview
- Quickstart guides
- Comprehensive method documentation
- Error code reference

### Essential Documentation Elements

1. **Overview**: What the API does
2. **Authentication**: How to authenticate
3. **Quickstart**: Getting started guide
4. **API Reference**: Complete endpoint documentation
5. **Error Handling**: Error codes and meanings
6. **Rate Limits**: Throttling policies
7. **Changelog**: Version history
8. **SDKs**: Client libraries
9. **Examples**: Real-world code samples
10. **Migration Guides**: Version upgrade paths

## Testing Strategies

### From Stripe
- Separate test and production environments
- Test API keys
- Special test values (test card numbers)
- Webhook testing tools (Stripe CLI)

### From AWS
- Canary deployments
- Blue/green deployments
- Automated testing in CI/CD
- Load testing
- Security testing

### Test Coverage Areas
- Happy path scenarios
- Error conditions
- Edge cases
- Performance under load
- Security vulnerabilities
- Backward compatibility
- API versioning transitions

## Monitoring and Observability

### Key Metrics (from AWS)

**Request Metrics:**
- Request count
- Error rate (4xx, 5xx)
- Latency (p50, p95, p99)
- Request size
- Response size

**System Metrics:**
- Cache hit rate
- Integration latency
- Throttle count
- Quota usage

**Business Metrics:**
- Active users
- API usage by client
- Feature adoption
- Error types distribution

### Logging Best Practices

**Structured Logging:**
```json
{
  "timestamp": "2024-12-01T16:00:00Z",
  "request_id": "req_123",
  "method": "POST",
  "path": "/resources",
  "status": 201,
  "duration_ms": 150,
  "user_id": "user_456"
}
```

**What to Log:**
- Request/response metadata
- Error details
- Performance metrics
- Security events
- Business events

**What NOT to Log:**
- Sensitive data (passwords, tokens)
- Personal information (without consent)
- Credit card numbers
- Full request/response bodies (unless necessary)

## REST API Design Checklist

### Design Phase
- [ ] Define resources and their relationships
- [ ] Design URL structure following REST conventions
- [ ] Choose appropriate HTTP methods
- [ ] Define request/response formats
- [ ] Design error response format (consider RFC 7807)
- [ ] Plan versioning strategy
- [ ] Design authentication/authorization
- [ ] Plan pagination approach
- [ ] Define filtering/searching patterns
- [ ] Consider API evolution and backward compatibility

### Security
- [ ] Implement authentication on all endpoints
- [ ] Use HTTPS exclusively
- [ ] Validate all inputs
- [ ] Implement rate limiting
- [ ] Use proper authorization checks
- [ ] Sanitize error messages
- [ ] Implement audit logging
- [ ] Regular security reviews
- [ ] Verify webhook signatures
- [ ] Use short-lived tokens

### Implementation
- [ ] Implement idempotency for POST operations
- [ ] Support pagination for list operations
- [ ] Implement proper error handling
- [ ] Add request validation
- [ ] Implement caching where appropriate
- [ ] Support conditional requests (ETags)
- [ ] Add monitoring and logging
- [ ] Implement health check endpoint
- [ ] Handle timeouts appropriately
- [ ] Support graceful degradation

### Documentation
- [ ] API overview and introduction
- [ ] Authentication guide
- [ ] Quickstart tutorial
- [ ] Complete API reference
- [ ] Error code documentation
- [ ] Code examples in multiple languages
- [ ] Changelog for versions
- [ ] Migration guides
- [ ] Rate limit documentation
- [ ] Support/contact information

### Operations
- [ ] Set up monitoring and alerts
- [ ] Implement centralized logging
- [ ] Define SLAs and SLOs
- [ ] Create runbooks for common issues
- [ ] Set up error tracking
- [ ] Implement performance monitoring
- [ ] Plan for capacity
- [ ] Create disaster recovery plan
- [ ] Regular load testing
- [ ] Security scanning

### Client Experience
- [ ] Provide SDKs in popular languages
- [ ] Interactive API explorer
- [ ] Sandbox/test environment
- [ ] Clear error messages
- [ ] Consistent behavior
- [ ] Predictable patterns
- [ ] Comprehensive examples
- [ ] Developer support channels
- [ ] Status page for outages
- [ ] Developer community/forum

## Key Recommendations

### For New APIs

1. **Start with RFC 7807** for error handling
2. **Use URI Templates (RFC 6570)** in documentation
3. **Follow resource-oriented design** (Google approach)
4. **Implement proper HTTP semantics** (RFC 9110)
5. **Plan for versioning** from day one (Stripe approach)
6. **Security by default** (AWS approach)
7. **Focus on developer experience** (Stripe philosophy)

### For API Evolution

1. **Avoid breaking changes** when possible
2. **Use versioning** for breaking changes
3. **Provide migration guides** for version transitions
4. **Support multiple versions** during transition
5. **Deprecate gradually** with clear timelines
6. **Monitor adoption** of new versions
7. **Learn from user feedback** continuously

### For Scale

1. **Implement rate limiting** early
2. **Use pagination** for all list operations
3. **Support caching** with proper headers
4. **Monitor performance** continuously
5. **Plan for capacity** growth
6. **Consider geographic distribution**
7. **Optimize database queries**
8. **Use async operations** for long-running tasks

## Conclusion

This collection of RFC examples and industry best practices provides a comprehensive foundation for REST API design. Key themes across all sources:

1. **Consistency**: Predictable patterns reduce cognitive load
2. **Simplicity**: Make common cases simple, allow complexity when needed
3. **Security**: Security by default, not an afterthought
4. **Evolution**: Design for change, maintain compatibility
5. **Developer Experience**: Documentation and tooling matter
6. **Standards**: Build on established standards (HTTP, URI, JSON)
7. **Observability**: Monitor, log, and instrument everything

Use these examples as reference points, not rigid rules. Every API has unique requirements, but starting from established patterns increases the likelihood of success.

## Additional Resources

### IETF RFCs
- RFC 9110: HTTP Semantics - https://www.rfc-editor.org/rfc/rfc9110.txt
- RFC 9112: HTTP/1.1 - https://www.rfc-editor.org/rfc/rfc9112.txt
- RFC 6570: URI Templates - https://www.rfc-editor.org/rfc/rfc6570.txt
- RFC 7807: Problem Details - https://www.rfc-editor.org/rfc/rfc7807.txt

### Industry Guides
- Google API Design Guide: https://cloud.google.com/apis/design
- Google AIPs: https://google.aip.dev/
- AWS API Gateway Docs: https://docs.aws.amazon.com/apigateway/
- Stripe API Docs: https://docs.stripe.com/api
- Stripe API Design Blog: https://stripe.com/blog/payment-api-design

### Related Standards
- RFC 9111: HTTP Caching
- RFC 9113: HTTP/2
- RFC 9114: HTTP/3
- RFC 6749: OAuth 2.0
- RFC 7519: JSON Web Token (JWT)
- RFC 8259: JSON Data Interchange Format

---

**Document Prepared:** 2025-10-13
**Collection Location:** `/Users/elniak/Documents/AMC3/MARK/auto-i-d-template/.claude/rfc-examples/rest-apis/`
**Total Files:** 8 (7 detailed documents + 1 summary)
