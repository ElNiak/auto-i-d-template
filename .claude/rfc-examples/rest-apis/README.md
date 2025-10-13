# REST API RFC Examples Collection

This directory contains comprehensive research on REST API design patterns, extracted from IETF RFCs and industry-leading API documentation.

## Quick Start

Start with **[summary.md](summary.md)** for a comprehensive overview and comparative analysis.

## Documents

### IETF Standards (Foundation)

1. **[RFC 9110: HTTP Semantics](ietf-rfc9110-http-semantics.md)** (5.7 KB)
   - HTTP protocol fundamentals
   - Methods, status codes, headers
   - Resource-oriented design principles
   - Use when: Understanding HTTP basics, designing method semantics

2. **[RFC 9112: HTTP/1.1](ietf-rfc9112-http11.md)** (7.4 KB)
   - Message format and framing
   - Connection management
   - Security considerations
   - Use when: Implementing HTTP servers/clients, understanding protocol details

3. **[RFC 6570: URI Templates](ietf-rfc6570-uri-templates.md)** (8.7 KB)
   - URI template syntax
   - Variable expansion patterns
   - Query parameter handling
   - Use when: Designing API URLs, documenting endpoint patterns

4. **[RFC 7807: Problem Details for HTTP APIs](ietf-rfc7807-problem-details.md)** (11 KB)
   - Standardized error format
   - Machine-readable error details
   - Extension patterns
   - Use when: Designing error responses, implementing error handling

### Industry Best Practices

5. **[Google API Design Guide](google-api-design-guide.md)** (12 KB)
   - Resource-oriented design
   - Standard methods pattern
   - Protocol Buffers integration
   - Use when: Designing large-scale APIs, enterprise systems

6. **[AWS API Gateway Best Practices](aws-api-gateway-best-practices.md)** (14 KB)
   - Security and authentication
   - Monitoring and operations
   - Cloud-native deployment
   - Use when: Deploying APIs to cloud, security hardening

7. **[Stripe API Design](stripe-api-design.md)** (15 KB)
   - Developer experience focus
   - API evolution strategies
   - Backward compatibility patterns
   - Use when: Designing developer-friendly APIs, planning versioning

### Comprehensive Analysis

8. **[Summary: Comparative Analysis](summary.md)** (20 KB)
   - Cross-document analysis
   - Pattern comparisons
   - Design checklist
   - Best practice recommendations
   - Use when: Making design decisions, conducting design reviews

## By Use Case

### Designing a New API
1. Start with [summary.md](summary.md) - Design checklist section
2. Read [RFC 9110](ietf-rfc9110-http-semantics.md) - HTTP fundamentals
3. Review [Google API Design Guide](google-api-design-guide.md) - Resource patterns
4. Review [Stripe API Design](stripe-api-design.md) - Developer experience

### Implementing Error Handling
1. Read [RFC 7807](ietf-rfc7807-problem-details.md) - Standard error format
2. Review [summary.md](summary.md) - Error handling comparison section
3. Check [AWS Best Practices](aws-api-gateway-best-practices.md) - Security considerations

### Planning API Evolution
1. Read [Stripe API Design](stripe-api-design.md) - Evolution strategies
2. Review [summary.md](summary.md) - Versioning strategies section
3. Check [Google API Design Guide](google-api-design-guide.md) - Versioning approach

### Security Hardening
1. Read [AWS Best Practices](aws-api-gateway-best-practices.md) - Complete security section
2. Review [RFC 9110](ietf-rfc9110-http-semantics.md) - Security considerations
3. Check [RFC 9112](ietf-rfc9112-http11.md) - Protocol security

### URL Design
1. Read [RFC 6570](ietf-rfc6570-uri-templates.md) - URI template patterns
2. Review [summary.md](summary.md) - Resource design patterns section
3. Check [Google API Design Guide](google-api-design-guide.md) - Resource naming

## Key Concepts Quick Reference

### HTTP Methods
- **GET**: Retrieve (safe, idempotent) - [RFC 9110](ietf-rfc9110-http-semantics.md)
- **POST**: Create/action (non-idempotent) - [RFC 9110](ietf-rfc9110-http-semantics.md)
- **PUT**: Replace (idempotent) - [RFC 9110](ietf-rfc9110-http-semantics.md)
- **PATCH**: Update (idempotent) - [RFC 9110](ietf-rfc9110-http-semantics.md)
- **DELETE**: Remove (idempotent) - [RFC 9110](ietf-rfc9110-http-semantics.md)

### Status Codes
- **2xx**: Success - [RFC 9110](ietf-rfc9110-http-semantics.md)
- **4xx**: Client error - [RFC 9110](ietf-rfc9110-http-semantics.md)
- **5xx**: Server error - [RFC 9110](ietf-rfc9110-http-semantics.md)

### Error Handling
- **Standard format**: [RFC 7807](ietf-rfc7807-problem-details.md)
- **Google approach**: [Google API Design Guide](google-api-design-guide.md)
- **Stripe approach**: [Stripe API Design](stripe-api-design.md)

### Versioning
- **URL path**: [summary.md](summary.md) - Versioning section
- **Header-based**: [Stripe API Design](stripe-api-design.md)
- **Account-based**: [Stripe API Design](stripe-api-design.md)

### Security
- **Authentication**: [AWS Best Practices](aws-api-gateway-best-practices.md)
- **Authorization**: [AWS Best Practices](aws-api-gateway-best-practices.md)
- **Rate limiting**: [AWS Best Practices](aws-api-gateway-best-practices.md)

### Pagination
- **Cursor-based**: [summary.md](summary.md) - Pagination section
- **Token-based**: [Google API Design Guide](google-api-design-guide.md)

## Common Patterns

### Resource Collection Pattern
```
GET    /resources         # List
POST   /resources         # Create
GET    /resources/{id}    # Get
PATCH  /resources/{id}    # Update
DELETE /resources/{id}    # Delete
```
See: [Google API Design Guide](google-api-design-guide.md), [summary.md](summary.md)

### Error Response Pattern
```json
{
  "type": "https://example.com/probs/validation-error",
  "title": "Validation Failed",
  "status": 400,
  "detail": "The request contains invalid data"
}
```
See: [RFC 7807](ietf-rfc7807-problem-details.md)

### URI Template Pattern
```
/resources/{id}
/resources{?filter,limit,offset}
/resources/{id}/subresources
```
See: [RFC 6570](ietf-rfc6570-uri-templates.md)

## Design Decision Framework

When making API design decisions, consult:

1. **Standards first**: Check IETF RFCs for established patterns
2. **Industry practice**: See how Google, AWS, Stripe solved similar problems
3. **Trade-offs**: Review comparative analysis in [summary.md](summary.md)
4. **Context**: Consider your specific requirements and constraints

## File Sizes

| Document | Size | Depth |
|----------|------|-------|
| RFC 9110 | 5.7 KB | Fundamental |
| RFC 9112 | 7.4 KB | Detailed |
| RFC 6570 | 8.7 KB | Practical |
| RFC 7807 | 11 KB | Essential |
| Google | 12 KB | Comprehensive |
| AWS | 14 KB | Operational |
| Stripe | 15 KB | Philosophical |
| Summary | 20 KB | Comparative |

## Contributing

This collection was created on 2025-10-13. To update:

1. Add new documents following the naming pattern:
   - IETF RFCs: `ietf-rfc####-description.md`
   - Company guides: `company-description.md`

2. Update [summary.md](summary.md) with comparative analysis

3. Update this README with new document references

## References

### IETF RFCs
- https://www.rfc-editor.org/rfc/rfc9110.txt
- https://www.rfc-editor.org/rfc/rfc9112.txt
- https://www.rfc-editor.org/rfc/rfc6570.txt
- https://www.rfc-editor.org/rfc/rfc7807.txt

### Industry Documentation
- https://cloud.google.com/apis/design
- https://docs.aws.amazon.com/apigateway/
- https://docs.stripe.com/api
- https://stripe.com/blog/payment-api-design

## License

These documents are research summaries of publicly available standards and documentation. Original sources maintain their respective licenses:
- IETF RFCs: Public domain
- Company documentation: Respective company terms of use

---

**Collection Date**: 2025-10-13
**Location**: `/Users/elniak/Documents/AMC3/MARK/auto-i-d-template/.claude/rfc-examples/rest-apis/`
**Total Size**: ~104 KB across 8 markdown files
