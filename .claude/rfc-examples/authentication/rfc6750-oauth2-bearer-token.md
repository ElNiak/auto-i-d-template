# RFC 6750: OAuth 2.0 Bearer Token Usage

**Status**: Standards Track
**Published**: October 2012
**Category**: OAuth 2.0
**URL**: https://www.rfc-editor.org/rfc/rfc6750.txt

## Overview

RFC 6750 defines how to use bearer tokens in HTTP requests to access OAuth 2.0 protected resources. A bearer token is a security token where possession of the token is sufficient to gain access - "any party in possession of a bearer token can use it to get access to the associated resources."

## Authentication Flow

1. **Token Acquisition**: Client obtains access token from authorization server (per RFC 6749)
2. **Token Presentation**: Client presents token to resource server
3. **Token Validation**: Resource server validates token with authorization server
4. **Resource Access**: Upon successful validation, resource server grants access

```
     +--------+                               +---------------+
     |        |--(A)- Authorization Request ->|   Resource    |
     |        |                               |     Owner     |
     |        |<-(B)-- Authorization Grant ---|               |
     |        |                               +---------------+
     |        |
     |        |                               +---------------+
     |        |--(C)-- Authorization Grant -->| Authorization |
     | Client |                               |     Server    |
     |        |<-(D)----- Access Token -------|               |
     |        |                               +---------------+
     |        |
     |        |                               +---------------+
     |        |--(E)----- Access Token ------>|    Resource   |
     |        |                               |     Server    |
     |        |<-(F)--- Protected Resource ---|               |
     +--------+                               +---------------+
```

## Token Format and Usage

### Token Characteristics
- **Opaque**: Token structure not defined by spec (implementation-specific)
- **Short-lived**: RECOMMENDED lifetime of 1 hour or less
- **Scoped**: Limited to specific resources and operations
- **Confidential**: Requires protection during storage and transmission

### Token Transmission Methods

#### 1. Authorization Request Header (RECOMMENDED)
```http
GET /resource HTTP/1.1
Host: server.example.com
Authorization: Bearer mF_9.B5f-4.1JqM
```

**Characteristics**:
- REQUIRED method for OAuth 2.0
- Most secure and widely supported
- Avoids URL-based token exposure

#### 2. Form-Encoded Body Parameter
```http
POST /resource HTTP/1.1
Host: server.example.com
Content-Type: application/x-www-form-urlencoded

access_token=mF_9.B5f-4.1JqM
```

**Requirements**:
- HTTP method MUST be POST
- Content-Type MUST be `application/x-www-form-urlencoded`
- MUST NOT be used with Authorization header simultaneously
- Entity-body MUST be single-part

#### 3. URI Query Parameter (NOT RECOMMENDED)
```http
GET /resource?access_token=mF_9.B5f-4.1JqM HTTP/1.1
Host: server.example.com
```

**Warnings**:
- MAY be logged in server logs
- MAY be stored in browser history
- MAY be exposed via HTTP Referer header
- Use only when Authorization header not possible

## Security Considerations

### Primary Threats

#### 1. Token Manufacture/Modification
**Risk**: Attacker creates fake token or modifies existing token
**Mitigation**:
- Use authenticated encryption
- Implement token signature verification
- Use secure token generation algorithms

#### 2. Token Disclosure
**Risk**: Token intercepted during transmission or storage
**Mitigation**:
- MUST use TLS for all token exchanges
- MUST validate TLS certificate chains
- MUST NOT store tokens in cookies without HttpOnly/Secure flags
- MUST NOT pass tokens in page URLs

#### 3. Token Redirect
**Risk**: Token sent to unintended resource server
**Mitigation**:
- Implement audience restrictions
- Validate token audience claims
- Use scoped tokens per resource

#### 4. Token Replay
**Risk**: Attacker reuses captured token
**Mitigation**:
- Issue short-lived tokens
- Implement token revocation
- Use one-time-use tokens where appropriate

### Security Requirements

**MUST Requirements**:
- Use TLS (version 1.2 or higher recommended as of 2025)
- Validate TLS certificate chains
- Protect token confidentiality during storage
- Not use bearer tokens over non-TLS connections

**SHOULD Requirements**:
- Issue scoped tokens
- Issue short-lived tokens (≤1 hour)
- Implement token revocation
- Use audience restrictions
- Validate token scope before access

**SHOULD NOT Requirements**:
- Pass tokens in page URLs
- Store tokens in cookies without security flags
- Transmit tokens in clear-text cookies

## Error Responses

### Error Codes

#### 1. invalid_request (400 Bad Request)
- Missing required parameter
- Multiple token transmission methods used
- Invalid request structure

```http
HTTP/1.1 400 Bad Request
WWW-Authenticate: Bearer realm="example",
                  error="invalid_request",
                  error_description="The access token is missing"
```

#### 2. invalid_token (401 Unauthorized)
- Token expired
- Token revoked
- Token malformed
- Token unknown

```http
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Bearer realm="example",
                  error="invalid_token",
                  error_description="The access token expired"
```

#### 3. insufficient_scope (403 Forbidden)
- Token lacks required scope for resource
- Requires additional authorization

```http
HTTP/1.1 403 Forbidden
WWW-Authenticate: Bearer realm="example",
                  error="insufficient_scope",
                  error_description="The request requires higher privileges",
                  scope="read write"
```

## Technical Requirements

### Client Implementation

**Token Acquisition**:
1. Obtain token from authorization server (RFC 6749)
2. Store token securely (encrypted storage recommended)
3. Handle token expiration and refresh

**Token Usage**:
1. Include token in Authorization header (preferred)
2. Use TLS for all requests
3. Handle error responses appropriately
4. Implement token refresh logic

### Resource Server Implementation

**Token Validation**:
1. Extract token from request
2. Validate token authenticity
3. Check token expiration
4. Verify token scope
5. Confirm token audience

**Error Handling**:
1. Return appropriate HTTP status code
2. Include WWW-Authenticate header with error details
3. Provide error_description for debugging
4. MUST NOT include sensitive information in errors

### Authorization Server Responsibilities
- Issue tokens with appropriate lifetime
- Implement token revocation endpoints
- Maintain token-to-user/client mapping
- Support token introspection (RFC 7662)

## Implementation Best Practices

1. **Always Use TLS**: Never transmit bearer tokens over unencrypted connections
2. **Short Token Lifetime**: Limit exposure window with 1-hour or shorter lifetime
3. **Scope Limitation**: Issue minimally-scoped tokens for specific operations
4. **Token Storage**: Use secure, encrypted storage for tokens
5. **Refresh Tokens**: Implement refresh token flow for long-lived sessions
6. **Rate Limiting**: Protect against brute-force token attacks
7. **Monitoring**: Log and monitor token usage patterns
8. **Revocation**: Implement immediate token revocation capability

## Example Implementation

### Client Request
```http
GET /api/profile HTTP/1.1
Host: api.example.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

### Successful Response
```http
HTTP/1.1 200 OK
Content-Type: application/json
Cache-Control: no-store
Pragma: no-cache

{
  "user_id": "12345",
  "name": "John Doe",
  "email": "john@example.com"
}
```

### Error Response
```http
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Bearer realm="api.example.com",
                  error="invalid_token",
                  error_description="Token has expired"
Content-Type: application/json

{
  "error": "invalid_token",
  "error_description": "Token has expired"
}
```

## Related Specifications

- **RFC 6749**: OAuth 2.0 Authorization Framework (core spec)
- **RFC 7662**: OAuth 2.0 Token Introspection
- **RFC 7009**: OAuth 2.0 Token Revocation
- **RFC 8414**: OAuth 2.0 Authorization Server Metadata
- **RFC 8705**: OAuth 2.0 Mutual-TLS Client Authentication

## Summary

RFC 6750 Bearer Tokens provide a simple, widely-adopted authentication mechanism for OAuth 2.0. The key principle is that possession of the token grants access, making token confidentiality and short lifetimes critical.

**Key Takeaways**:
- Bearer tokens are possession-based (no proof required)
- TLS is mandatory for all token transmission
- Authorization header is the preferred transmission method
- Tokens should be short-lived and scoped
- Comprehensive error handling is essential

**Recommendation**: Use bearer tokens for OAuth 2.0 implementations with proper TLS protection, short token lifetimes, and robust token management infrastructure.
