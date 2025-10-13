# RFC 7617: HTTP Basic Authentication

**Status**: Standards Track
**Published**: September 2015
**Obsoletes**: RFC 2617
**URL**: https://www.rfc-editor.org/rfc/rfc7617.txt

## Overview

HTTP Basic Authentication is a simple challenge-response mechanism where credentials are transmitted as Base64-encoded strings in HTTP headers. Despite its simplicity, it is widely used but requires additional security measures.

## Authentication Flow

1. **Client Request**: Client attempts to access a protected resource
2. **Server Challenge**: Server responds with `401 Unauthorized` and `WWW-Authenticate: Basic realm="..."` header
3. **Credential Encoding**: Client obtains user-id and password, concatenates as `user-id:password`, and encodes with Base64
4. **Authorization**: Client sends `Authorization: Basic <base64-credentials>` header
5. **Validation**: Server decodes and validates credentials against the protection space

```
Client                                Server
  |                                      |
  |---(1) GET /protected --------------->|
  |                                      |
  |<--(2) 401 + WWW-Authenticate --------|
  |       Basic realm="example"          |
  |                                      |
  |---(3) GET /protected --------------->|
  |       Authorization: Basic QWxh...   |
  |                                      |
  |<--(4) 200 OK + Resource -------------|
```

## Credential Format

### Basic Structure
- **Format**: `Authorization: Basic <base64-encoded-credentials>`
- **Encoding**: Base64(user-id ":" password)
- **Example**: `Authorization: Basic QWxhZGRpbjpvcGVuIHNlc2FtZQ==`

### Character Encoding
- **Default**: US-ASCII (ISO-8859-1 subset)
- **Optional**: UTF-8 with charset parameter
- **Format with UTF-8**: `Authorization: Basic <credentials>, charset="UTF-8"`

### Constraints
- User-id MUST NOT contain colon character (`:`)
- User-id and password MUST NOT contain control characters
- Credentials are reusable within the same authentication scope (realm)

## Security Considerations

### Critical Vulnerabilities
1. **Cleartext Transmission**: Credentials transmitted in easily reversible Base64 encoding
2. **Password Interception**: Vulnerable to eavesdropping without encryption
3. **Server Spoofing**: No protection against counterfeit servers
4. **Credential Reuse**: Same credentials often used across multiple sites

### Security Requirements
- **MUST NOT** be used without additional transport-level security (TLS/HTTPS)
- **SHOULD** use strong encryption on the transport layer
- **SHOULD** implement proper certificate validation
- **NOT** considered a secure authentication method on its own

### Quote from RFC
> "This scheme is not considered to be a secure method of user authentication unless used in conjunction with some external secure system such as TLS (Transport Layer Security, [RFC5246]), as the user-id and password are passed over the network as cleartext."

## Technical Requirements

### Server Requirements
- Define protection space ("realm")
- Validate Base64-decoded credentials
- Support case-insensitive scheme matching
- Optional: Support UTF-8 character encoding

### Client Requirements
- Encode credentials in Base64
- Send credentials with each request in scope
- Cache credentials for same realm/authority
- Support optional charset parameter

### HTTP Headers
- **Request**: `Authorization: Basic <credentials>`
- **Challenge**: `WWW-Authenticate: Basic realm="<realm>", charset="UTF-8"`

## Use Cases

### Appropriate Use
- Development and testing environments
- Internal applications behind VPN/secure network
- Legacy system compatibility (with TLS)
- Simple authentication with HTTPS

### Inappropriate Use
- Public-facing applications without TLS
- High-security requirements
- Applications requiring multi-factor authentication
- API authentication without additional security

## Implementation Notes

1. **Always use HTTPS**: HTTP Basic Auth MUST be protected by TLS
2. **Realm Selection**: Choose meaningful realm names for user context
3. **Credential Storage**: Never store passwords in plaintext server-side
4. **Rate Limiting**: Implement to prevent brute-force attacks
5. **Migration Path**: Consider OAuth 2.0 or other modern alternatives

## Related RFCs

- RFC 7235: HTTP Authentication Framework
- RFC 5246: TLS (Transport Layer Security)
- RFC 7616: HTTP Digest Authentication (alternative)
- RFC 6749: OAuth 2.0 (modern alternative)

## Summary

HTTP Basic Authentication provides a simple but inherently insecure authentication mechanism. Its primary advantage is ease of implementation and wide support. However, it **must** be used with TLS/HTTPS and is generally suitable only for scenarios where simplicity outweighs security requirements or where it's protected by additional security layers.

**Recommendation**: Use only with HTTPS, or consider modern alternatives like OAuth 2.0 for better security.
