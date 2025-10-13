# RFC 6749 - The OAuth 2.0 Authorization Framework

**Source:** https://www.rfc-editor.org/rfc/rfc6749.txt

## Protocol Purpose and Overview

OAuth 2.0 is an authorization framework that enables third-party applications to obtain limited access to HTTP services on behalf of a resource owner. It separates the roles of client, resource owner, authorization server, and resource server to provide secure delegated access.

### Key Roles:
- **Resource Owner**: End-user who can grant access to protected resources
- **Client**: Application requesting access to protected resources
- **Authorization Server**: Server issuing access tokens after authentication
- **Resource Server**: Server hosting protected resources

## Key Security Considerations

### Security Benefits:
- **Prevents credential sharing**: Third-party applications never see resource owner credentials
- **Granular access control**: Allows scoped, limited access to protected resources
- **Revocable access**: Access can be revoked without changing passwords
- **Reduced credential exposure**: Eliminates need to store passwords in clear text
- **Flexible grant types**: Different flows for various security requirements

### Core Security Principle:
Separation of authorization (OAuth) from authentication (handled by other protocols like OpenID Connect).

## Protocol Flows

### 1. Authorization Code Grant (Most Secure)
**Use Case**: Confidential clients (server-side web applications)

**Flow:**
1. Client redirects resource owner to authorization server
2. Resource owner authenticates and authorizes client
3. Authorization server redirects back with authorization code
4. Client exchanges authorization code for access token
5. Client uses access token to access protected resources

**Security Features:**
- Two-step process (code exchange separates authorization from token issuance)
- Client authentication required for token exchange
- Code is single-use and short-lived
- Prevents token exposure to user-agent

### 2. Implicit Grant (Deprecated)
**Use Case**: Public clients in browser-based applications (now discouraged)

**Flow:**
1. Client redirects resource owner to authorization server
2. Authorization server returns access token directly in redirect URI

**Security Limitations:**
- Access token exposed in URL fragment
- No client authentication
- No refresh tokens
- Vulnerable to token leakage

**Recommendation**: Use Authorization Code with PKCE instead.

### 3. Resource Owner Password Credentials Grant
**Use Case**: High-trust scenarios (legacy migration)

**Flow:**
1. Resource owner provides credentials directly to client
2. Client exchanges credentials for access token

**Security Limitations:**
- Requires sharing credentials with client
- Only use when other flows are not viable
- Client must be highly trusted

### 4. Client Credentials Grant
**Use Case**: Machine-to-machine communication

**Flow:**
1. Client authenticates with its own credentials
2. Authorization server issues access token

**Security Features:**
- No user interaction required
- Client acts on its own behalf
- Simplest flow for service accounts

## Token Handling and Security

### Access Tokens:
- **Purpose**: Time-limited credentials representing authorization
- **Format**: Opaque to client (often JWT in practice)
- **Scope**: Limited to specific permissions
- **Lifetime**: Short-lived (minutes to hours)
- **Transmission**: Must be over TLS

### Refresh Tokens:
- **Purpose**: Obtain new access tokens without re-authorization
- **Lifetime**: Long-lived (days to months)
- **Security**: More sensitive than access tokens
- **Rotation**: Can be rotated on each use for enhanced security

### Token Security Requirements:
- Protect tokens as bearer credentials
- Transmit only over TLS
- Store securely (encrypted at rest)
- Implement token expiration
- Support token revocation

## Important Security Requirements

### Transport Security:
- **Mandatory TLS**: All authorization and token exchanges must use TLS
- **Certificate validation**: Clients must validate server certificates
- **TLS version**: Use modern TLS versions (1.2+)

### Client Authentication:
- **Confidential clients**: Must authenticate with client credentials
- **Public clients**: Cannot maintain credential confidentiality
- **Authentication methods**: Client secret, public key, assertions

### Redirect URI Validation:
- **Registration**: Pre-register all redirect URIs
- **Exact matching**: Validate redirect URIs exactly (no partial matches)
- **HTTPS requirement**: Use HTTPS for web clients

### Protection Against Attacks:

#### CSRF Protection:
- Use `state` parameter to maintain state and prevent CSRF
- Validate `state` parameter on callback

#### Authorization Code Injection:
- Bind authorization code to client
- Use PKCE for additional protection

#### Token Leakage:
- Minimize token scope and lifetime
- Use separate tokens for different resources
- Implement token introspection

#### Brute Force Attacks:
- Rate limiting on token endpoints
- Account lockout mechanisms
- Strong client secret requirements

### Scope Management:
- **Principle of least privilege**: Request minimal necessary scopes
- **Scope validation**: Authorization server validates and may reduce scopes
- **User consent**: Resource owner must approve requested scopes

## Security Best Practices

1. **Use PKCE**: Always use Proof Key for Code Exchange (RFC 7636) with Authorization Code flow
2. **Short-lived tokens**: Keep access token lifetime short
3. **Rotate refresh tokens**: Issue new refresh token with each access token refresh
4. **Validate all inputs**: Strict validation of all OAuth parameters
5. **Audit logging**: Log all authorization and token operations
6. **Rate limiting**: Implement rate limits on all endpoints
7. **Token binding**: Bind tokens to client instances when possible
8. **Secure storage**: Encrypt tokens at rest
9. **HTTPS everywhere**: Use HTTPS for all OAuth communications
10. **Regular rotation**: Rotate client secrets periodically

## Key Takeaways for Authorization Protocol Design

1. **Separation of concerns**: Clear separation between authorization and authentication
2. **Flexibility**: Multiple grant types for different use cases and security requirements
3. **Token-based access**: Avoid sharing credentials, use time-limited tokens
4. **Extensibility**: Framework allows extensions (PKCE, token introspection, etc.)
5. **Defense in depth**: Multiple security layers (TLS, client auth, token expiry, CSRF protection)
6. **Least privilege**: Scope-based access control for minimal necessary permissions
7. **Revocability**: Support for token revocation without credential changes

## Evolution and Extensions

OAuth 2.0 is a framework with important extensions:
- **RFC 7636**: PKCE (Proof Key for Code Exchange) - mandatory for public clients
- **RFC 7662**: Token Introspection - validate token status
- **RFC 7009**: Token Revocation - explicit token revocation
- **RFC 8628**: Device Authorization Grant - for input-constrained devices
- **OAuth 2.1 (Draft)**: Consolidates best practices and removes deprecated flows
