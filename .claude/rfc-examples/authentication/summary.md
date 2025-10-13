# Authentication Patterns: RFC and Industry Examples Summary

**Created**: 2025-10-13
**Purpose**: Reference collection of authentication patterns from RFCs and major tech companies
**Location**: `/Users/elniak/Documents/AMC3/MARK/auto-i-d-template/.claude/rfc-examples/authentication/`

## Overview

This directory contains comprehensive documentation of authentication patterns extracted from IETF RFCs and real-world implementations by major technology companies. These examples serve as reference material for designing authentication systems and understanding industry best practices.

## Contents

### IETF RFCs

#### 1. RFC 7617: HTTP Basic Authentication
**File**: `rfc7617-http-basic-auth.md`

**Summary**: Simple challenge-response mechanism using Base64-encoded credentials in HTTP headers.

**Key Characteristics**:
- **Flow**: Client encodes `username:password` in Base64 and sends in Authorization header
- **Format**: `Authorization: Basic <base64-credentials>`
- **Security**: Inherently insecure (cleartext transmission), MUST use HTTPS
- **Use Case**: Simple authentication for internal systems, development environments

**Critical Takeaway**: Not secure without TLS. Consider modern alternatives for production systems.

**Authentication Flow Complexity**: Low (single request-response)

**Token Lifetime**: Credentials reused for entire session

---

#### 2. RFC 6750: OAuth 2.0 Bearer Token Usage
**File**: `rfc6750-oauth2-bearer-token.md`

**Summary**: Defines how to use bearer tokens for OAuth 2.0 protected resource access.

**Key Characteristics**:
- **Flow**: Client obtains token from authorization server, presents to resource server
- **Format**: `Authorization: Bearer <token>` (preferred), form-encoded body, or query param
- **Token Type**: Possession-based (anyone with token can use it)
- **Lifetime**: Short-lived (recommended ≤1 hour)
- **Security**: TLS mandatory, scope-limited tokens, audience restrictions

**Critical Takeaway**: Possession = access. Token security and short lifetimes are critical.

**Token Transmission Methods**:
1. Authorization header (RECOMMENDED)
2. Form-encoded body (POST only)
3. URI query parameter (NOT RECOMMENDED)

**Error Codes**:
- `invalid_request` (400): Malformed request
- `invalid_token` (401): Token expired/revoked/invalid
- `insufficient_scope` (403): Token lacks required permissions

---

#### 3. RFC 8471: Token Binding over HTTP
**File**: `rfc8471-token-binding.md`

**Summary**: Cryptographically binds security tokens to TLS layer to prevent token theft.

**Key Characteristics**:
- **Flow**: Client generates key pair, proves possession with each TLS connection
- **Format**: `Sec-Token-Binding: <base64-encoded-message>` header with cryptographic proof
- **Binding Types**: `provided_token_binding` (direct) and `referred_token_binding` (federated)
- **Signature**: HMAC over Exported Keying Material (EKM) from TLS
- **Security**: Strong protection against token export and replay attacks

**Critical Takeaway**: Stolen tokens useless without private key. Excellent security but complex deployment.

**Cryptographic Details**:
- Key Parameters: RSA 2048, ECDSA P-256 (recommended)
- Signature over: `key_parameters || key_length || public_key || EKM`
- Validation: Verify signature, check Token Binding ID consistency

**Deployment Status**: Limited adoption as of 2025; consider OAuth 2.0 DPoP (RFC 9449) as alternative

---

#### 4. RFC 4559: SPNEGO-based HTTP Authentication (Negotiate)
**File**: `rfc4559-spnego-http-auth.md`

**Summary**: Enterprise single sign-on using SPNEGO (GSS-API) with Kerberos or NTLM.

**Key Characteristics**:
- **Flow**: Multi-round negotiation using GSS-API security context
- **Format**: `Authorization: Negotiate <base64-gss-token>`
- **Mechanisms**: Kerberos (preferred), NTLM (legacy)
- **Use Case**: Enterprise intranet with Active Directory or Kerberos infrastructure
- **Security**: Authentication only (no data protection - use TLS)

**Critical Takeaway**: Excellent for enterprise SSO but requires infrastructure. Authentication-only, always use HTTPS.

**Token Exchange**:
1. Client sends `InitialContextToken` (SPNEGO negotiation)
2. Server responds with mechanism selection
3. Multiple rounds possible until context established
4. Server principal format: `HTTP/<hostname>`

**Browser Support**:
- IE/Edge: Native (Windows Integrated Auth)
- Firefox: Configure `network.negotiate-auth.trusted-uris`
- Chrome: Uses OS authentication
- Safari: Kerberos support on macOS

---

### Company Authentication Patterns

#### 5. GitHub OAuth Implementation
**File**: `github-oauth-patterns.md`

**Summary**: GitHub's OAuth 2.0 implementation with multiple flows for different application types.

**Key Characteristics**:
- **Flows**: Web Application Flow, Device Flow, Non-Web Application Flow
- **Token Format**: Prefixed tokens (e.g., `gho_` for OAuth apps)
- **Token Lifetime**: No expiration by default (until revoked)
- **Scopes**: Fine-grained permissions (`repo`, `user`, `workflow`, etc.)
- **Security**: State parameter (CSRF), 10-minute code expiration, PKCE support

**Authentication Flows**:

1. **Web Application Flow**:
   - Authorization code exchange
   - State parameter for CSRF protection
   - Code expires in 10 minutes (single-use)

2. **Device Flow**:
   - User code: `WDJB-MJHT` (user enters in browser)
   - Device code: Opaque string (for polling)
   - 15-minute expiration, 5-second polling interval

3. **Token Prefixes**:
   - `gho_`: OAuth app token
   - `ghp_`: Personal access token
   - `ghs_`: Server-to-server token
   - `ghu_`: User access token (GitHub App)

**Best Practices**:
- Always validate state parameter
- Use Authorization header (not URL params)
- Request minimal scopes
- Consider GitHub Apps for automation (fine-grained permissions)

**Rate Limits**: 5,000 requests/hour (authenticated)

---

#### 6. AWS Signature Version 4 (SigV4)
**File**: `aws-sigv4-signing.md`

**Summary**: Cryptographic request signing protocol for AWS API authentication.

**Key Characteristics**:
- **Flow**: Sign each request with HMAC-SHA256 using derived key
- **Format**: `Authorization: AWS4-HMAC-SHA256 Credential=..., SignedHeaders=..., Signature=...`
- **Key Derivation**: Daily scoped keys (service + region + date)
- **Payload Protection**: SHA256 hash of request body included in signature
- **Security**: Secret key never transmitted, request integrity guaranteed

**Signing Process** (4 steps):

1. **Create Canonical Request**:
   - Normalize HTTP method, URI, query string, headers
   - Include SHA256 hash of payload
   - Result: Standardized request representation

2. **Create String to Sign**:
   - Format: `AWS4-HMAC-SHA256\n<timestamp>\n<credential-scope>\n<hashed-canonical-request>`
   - Credential scope: `<date>/<region>/<service>/aws4_request`

3. **Calculate Signing Key** (nested HMAC):
   ```
   kDate = HMAC("AWS4" + SecretKey, Date)
   kRegion = HMAC(kDate, Region)
   kService = HMAC(kRegion, Service)
   kSigning = HMAC(kService, "aws4_request")
   ```

4. **Calculate Signature**:
   - `Signature = Hex(HMAC-SHA256(SigningKey, StringToSign))`

**Required Headers**:
- `Host`: Service endpoint
- `X-Amz-Date`: ISO 8601 timestamp
- `Authorization`: Signature details

**Security Features**:
- Timestamp validation (5-minute window) prevents replay
- Payload hashing prevents tampering
- Service/region scoped signatures limit exposure
- Daily key derivation reduces compromise window

**Variants**:
- **SigV4**: Standard (symmetric HMAC)
- **SigV4a**: Asymmetric (ECDSA, multi-region)
- **Presigned URLs**: Signature in query string (time-limited)

**Critical Takeaway**: Always use AWS SDK. Manual signing is complex and error-prone.

---

#### 7. Azure AD Authentication Patterns
**File**: `azure-ad-auth-patterns.md`

**Summary**: Microsoft's comprehensive identity platform built on OAuth 2.0 and OpenID Connect.

**Key Characteristics**:
- **Standards**: OAuth 2.0, OpenID Connect
- **Flows**: Authorization Code, Client Credentials, Device Code, On-Behalf-Of, ROPC (deprecated)
- **Token Types**: Access Token (JWT), ID Token (JWT), Refresh Token (opaque)
- **Library**: MSAL (Microsoft Authentication Library) for all platforms
- **Enterprise Features**: Conditional access, MFA, SSO, dynamic consent

**Authentication Flows**:

1. **Authorization Code Flow** (Recommended for most scenarios):
   - Uses PKCE for public clients
   - Supports refresh tokens
   - Full support for conditional access and MFA

2. **Client Credentials Flow** (Daemon/background services):
   - No user context (app-only)
   - Uses client secret or certificate
   - No refresh tokens

3. **Device Flow** (Input-constrained devices):
   - User code: `CNGBK-QFT7N`
   - Two-device authentication
   - 15-minute expiration, 5-second polling

4. **On-Behalf-Of Flow** (Middle-tier services):
   - Preserves user identity across services
   - Token exchange mechanism
   - Maintains consent and permissions

5. **ROPC Flow** (Not Recommended):
   - Username/password to app
   - No MFA/conditional access support
   - Legacy only

**Token Types**:

1. **Access Token** (JWT):
   - Lifetime: 1 hour (default)
   - Contains: `aud`, `iss`, `exp`, `scp` (scopes), `roles`
   - Used for: API authorization

2. **ID Token** (JWT):
   - Contains: `name`, `preferred_username`, `email`, `oid` (user ID)
   - Used for: User identity (display only, not authorization)

3. **Refresh Token** (opaque):
   - Lifetime: 90 days (default)
   - Single-use (new token issued each time)
   - Revocable by admin

**Security Best Practices**:
- Always use PKCE for public clients
- Validate JWT signature, issuer, audience, expiration
- Use MSAL libraries (handle caching, refresh, errors)
- Store tokens securely (never in localStorage for SPAs)
- Request minimal scopes (least privilege)
- Support conditional access challenges

**MSAL Library Benefits**:
- Automatic token caching
- Automatic token refresh
- PKCE implementation
- Error handling
- Cross-platform support

**Platform Support**:
- JavaScript/TypeScript (MSAL.js)
- .NET (MSAL.NET)
- Python, Java, iOS, Android, Node.js

**Critical Takeaway**: Use MSAL for all Azure AD integrations. Don't implement OAuth manually.

---

## Comparison Matrix

| Feature | HTTP Basic | OAuth 2.0 Bearer | Token Binding | SPNEGO | GitHub OAuth | AWS SigV4 | Azure AD |
|---------|-----------|------------------|---------------|---------|--------------|-----------|----------|
| **Standard** | RFC 7617 | RFC 6750 | RFC 8471 | RFC 4559 | OAuth 2.0 | AWS proprietary | OAuth 2.0/OIDC |
| **Complexity** | Very Low | Medium | High | High | Medium | High | Medium-High |
| **Token Lifetime** | Session | Short (≤1h) | Bound to TLS | Session | No expiration | Per-request | 1 hour |
| **Requires TLS** | Yes | Yes | Yes | Yes | Yes | No* | Yes |
| **User Context** | Yes | Yes | Yes | Yes | Yes | Yes (IAM user) | Yes |
| **Token Format** | Base64 | Opaque/JWT | Cryptographic proof | GSS-API token | Opaque (prefixed) | HMAC signature | JWT |
| **Replay Protection** | No | Limited | Excellent | Limited | No | Excellent (5min) | Limited |
| **Token Theft Protection** | None | None | Excellent | None | None | N/A (no token) | None |
| **Enterprise SSO** | No | No | No | Yes | No | No | Yes |
| **MFA Support** | No | Depends on issuer | Depends on flow | Yes | Depends on org | No | Yes |
| **Refresh Tokens** | No | Yes | Depends | No | Yes | N/A | Yes |
| **Mobile Support** | Yes | Yes | Limited | Limited | Yes | Yes | Excellent |
| **Best For** | Dev/internal | API access | High security | Enterprise SSO | GitHub integration | AWS services | Microsoft ecosystem |

**Notes**:
- *AWS SigV4 doesn't require TLS cryptographically but HTTPS is strongly recommended for all AWS API calls
- Token Binding provides the strongest protection against token theft but has limited deployment
- SPNEGO excels in enterprise environments but requires infrastructure (Kerberos/AD)

---

## Authentication Flow Categories

### 1. Credential-Based (Direct Authentication)
**Examples**: HTTP Basic Auth, ROPC Flow

**Characteristics**:
- User provides credentials directly to application
- Application validates credentials
- Simple but less secure
- No support for modern features (MFA, SSO)

**Use Cases**: Internal systems, legacy applications, development

---

### 2. Token-Based (Indirect Authentication)
**Examples**: OAuth 2.0 Bearer Token, GitHub OAuth, Azure AD

**Characteristics**:
- User authenticates with identity provider
- Application receives token
- Token presented to resource server
- Supports delegation, scopes, refresh

**Use Cases**: API access, third-party integrations, modern applications

---

### 3. Signature-Based (Request Signing)
**Examples**: AWS SigV4, Token Binding

**Characteristics**:
- Cryptographic proof with each request
- Secret key never transmitted
- Strong protection against tampering and replay
- More complex implementation

**Use Cases**: High-security scenarios, API gateways, service-to-service

---

### 4. SSO-Based (Federated Authentication)
**Examples**: SPNEGO/Negotiate, Azure AD (with SAML/OIDC)

**Characteristics**:
- Centralized identity provider
- Single login for multiple applications
- Enterprise-grade features
- Requires infrastructure

**Use Cases**: Enterprise intranet, multi-application ecosystems

---

## Security Considerations Across Patterns

### Universal Requirements
1. **Always use HTTPS/TLS** for authentication traffic
2. **Validate tokens/signatures** before granting access
3. **Implement rate limiting** to prevent brute force
4. **Log authentication events** for security monitoring
5. **Rotate credentials/keys regularly**

### Token-Specific Security
1. **Short token lifetimes** reduce exposure window (≤1 hour recommended)
2. **Scope limitation** restricts what token can access (principle of least privilege)
3. **Secure storage** prevents token theft (encrypted DB, secure OS storage)
4. **Token revocation** enables immediate access termination
5. **Refresh tokens** allow long sessions without long-lived access tokens

### Request Signing Security
1. **Timestamp validation** prevents replay attacks (typical window: 5 minutes)
2. **Payload hashing** ensures request integrity
3. **Derived keys** limit exposure from key compromise
4. **Never log secrets** or signatures in plaintext

### Enterprise SSO Security
1. **Infrastructure security** (Kerberos KDC, AD) is critical
2. **Network security** required (not suitable for public internet)
3. **Transport encryption** necessary (authentication-only protection)
4. **Credential delegation** should be constrained and audited

---

## Common Implementation Patterns

### Pattern 1: Web Application (Server-Side)
**Flow**: Authorization Code Flow
**Examples**: Azure AD Web App, GitHub OAuth Web Flow
**Implementation**:
- Server-side code exchange
- Session-based token storage
- Automatic refresh token handling

**Technology Choices**:
- Backend: Node.js, ASP.NET, Python, Java
- Libraries: MSAL, Passport.js, Spring Security
- Storage: Encrypted sessions, Redis

---

### Pattern 2: Single-Page Application (SPA)
**Flow**: Authorization Code Flow + PKCE
**Examples**: Azure AD MSAL.js, GitHub OAuth (SPA)
**Implementation**:
- Browser-based authentication
- Memory-only token storage (no localStorage)
- Automatic token refresh with fallback to interactive

**Technology Choices**:
- Frontend: React, Angular, Vue.js
- Libraries: MSAL.js, oidc-client-ts
- Storage: Memory (in-app state management)

---

### Pattern 3: Mobile Application
**Flow**: Authorization Code Flow + PKCE (System Browser)
**Examples**: Azure AD MSAL Mobile, GitHub Device Flow
**Implementation**:
- System browser for authentication (not WebView)
- Secure OS storage for tokens
- Biometric authentication support

**Technology Choices**:
- iOS: MSAL iOS, Keychain
- Android: MSAL Android, Keystore
- React Native: MSAL React Native

---

### Pattern 4: CLI/Device Application
**Flow**: Device Code Flow
**Examples**: Azure AD Device Flow, GitHub Device Flow
**Implementation**:
- Display user code to user
- Poll for token completion
- Secure file storage for tokens

**Technology Choices**:
- Languages: Python, Go, Node.js
- Libraries: MSAL Python, GitHub CLI libraries
- Storage: Encrypted credential files

---

### Pattern 5: Background Service/Daemon
**Flow**: Client Credentials Flow
**Examples**: Azure AD Client Credentials, AWS SigV4 (IAM)
**Implementation**:
- No user interaction
- Service account credentials
- Token caching with expiration

**Technology Choices**:
- Platforms: Docker, Kubernetes, Lambda
- Credentials: Certificates (preferred), secrets
- Storage: Key Vault, Secrets Manager, environment variables

---

### Pattern 6: API-to-API (Microservices)
**Flow**: On-Behalf-Of Flow, Service Tokens
**Examples**: Azure AD OBO, AWS SigV4 service-to-service
**Implementation**:
- Preserve user context across services
- Token exchange at service boundaries
- Service mesh integration (Istio, Linkerd)

**Technology Choices**:
- Architecture: Microservices, service mesh
- Protocols: gRPC, REST
- Token propagation: Headers, sidecars

---

## Decision Framework: Which Pattern to Use?

### Decision Tree

```
1. What type of application?
   ├─ Web App (server-side)
   │  └─ Use: Authorization Code Flow (OAuth 2.0)
   │     Examples: Azure AD Web, GitHub OAuth Web Flow
   │
   ├─ Single-Page App (browser-only)
   │  └─ Use: Authorization Code + PKCE
   │     Examples: Azure AD MSAL.js, GitHub OAuth SPA
   │
   ├─ Mobile App (iOS/Android)
   │  └─ Use: Authorization Code + PKCE (system browser)
   │     Examples: Azure AD MSAL Mobile, GitHub OAuth Mobile
   │
   ├─ CLI/Device (limited input)
   │  └─ Use: Device Code Flow
   │     Examples: Azure AD Device Flow, GitHub Device Flow
   │
   ├─ Background Service/Daemon (no user)
   │  └─ Use: Client Credentials Flow or Request Signing
   │     Examples: Azure AD Client Credentials, AWS SigV4
   │
   └─ Enterprise Intranet (SSO required)
      └─ Use: SPNEGO/Negotiate or SAML/OIDC Federation
         Examples: Kerberos/AD, Azure AD SAML

2. What's your infrastructure?
   ├─ Cloud (AWS)
   │  └─ Use: AWS SigV4 (IAM)
   │
   ├─ Cloud (Azure)
   │  └─ Use: Azure AD (OAuth 2.0/OIDC)
   │
   ├─ Cloud (GitHub)
   │  └─ Use: GitHub OAuth or GitHub Apps
   │
   ├─ Enterprise (Active Directory/Kerberos)
   │  └─ Use: SPNEGO/Negotiate
   │
   └─ Custom/Self-hosted
      └─ Use: OAuth 2.0 Bearer Token (with your own IdP)

3. What's your security requirement?
   ├─ Maximum security (prevent token theft)
   │  └─ Use: Token Binding or Request Signing (AWS SigV4)
   │
   ├─ Standard security (modern best practices)
   │  └─ Use: OAuth 2.0 with PKCE + short-lived tokens
   │
   ├─ Legacy compatibility
   │  └─ Use: HTTP Basic Auth (with HTTPS) or SPNEGO
   │
   └─ Development/Testing only
      └─ Use: HTTP Basic Auth (simplest)
```

### Quick Reference: Scenario → Pattern

| Scenario | Recommended Pattern | Example |
|----------|-------------------|---------|
| React SPA calling REST API | Auth Code + PKCE (OAuth 2.0) | Azure AD MSAL.js |
| Mobile app (iOS/Android) | Auth Code + PKCE (system browser) | Azure AD MSAL Mobile |
| Server-side web app | Auth Code Flow (OAuth 2.0) | Azure AD Web, GitHub OAuth |
| CLI tool (user auth) | Device Code Flow | GitHub CLI, Azure CLI |
| CLI tool (API access) | Personal Access Token or Client Credentials | GitHub PAT, AWS credentials |
| Background job (no user) | Client Credentials Flow | Azure AD daemon app |
| Lambda function | Request Signing (IAM) | AWS SigV4 |
| Microservices (user context) | On-Behalf-Of Flow | Azure AD OBO |
| Microservices (service-to-service) | Client Credentials or mTLS | Azure AD app-to-app |
| Enterprise SSO (intranet) | SPNEGO/Negotiate | Kerberos/AD |
| Third-party app integration | OAuth 2.0 Authorization Code | GitHub OAuth, Azure AD |
| IoT device (limited input) | Device Code Flow | Azure AD Device Flow |
| Embedded system (no browser) | Device Code Flow or Client Credentials | Azure AD Device Flow |
| Legacy system migration | HTTP Basic Auth (with HTTPS) | Temporary during migration |

---

## Implementation Checklist

### For Any Authentication System

**Security Basics**:
- [ ] All authentication traffic over HTTPS/TLS
- [ ] Tokens/credentials stored securely (encrypted, OS keychain)
- [ ] Secrets never in source code or logs
- [ ] Rate limiting on authentication endpoints
- [ ] Failed authentication attempts logged and monitored
- [ ] Regular credential rotation policy

**Token Management**:
- [ ] Short token lifetimes (≤1 hour for access tokens)
- [ ] Refresh token mechanism for long sessions
- [ ] Token revocation capability
- [ ] Token validation on every protected request
- [ ] Scope/permission checking before operations

**CSRF/XSRF Protection**:
- [ ] State parameter validation (OAuth flows)
- [ ] PKCE for public clients (SPAs, mobile, CLI)
- [ ] SameSite cookies where applicable
- [ ] Anti-forgery tokens for form submissions

**Error Handling**:
- [ ] Graceful degradation (fallback to interactive auth)
- [ ] User-friendly error messages
- [ ] Detailed logging (without sensitive data)
- [ ] Retry logic with exponential backoff

**Compliance**:
- [ ] GDPR compliance (data handling, consent)
- [ ] SOC 2 compliance (audit logging, access control)
- [ ] Industry-specific requirements (HIPAA, PCI DSS, etc.)

---

### OAuth 2.0 Specific

**Authorization Code Flow**:
- [ ] State parameter for CSRF protection
- [ ] PKCE for public clients (code_challenge/code_verifier)
- [ ] Code expiration (≤10 minutes)
- [ ] Secure redirect URI validation
- [ ] Authorization code single-use enforcement

**Token Handling**:
- [ ] Bearer token in Authorization header (not URL)
- [ ] Access token lifetime ≤1 hour
- [ ] Refresh token secure storage
- [ ] Refresh token rotation
- [ ] Token audience validation

**Client Types**:
- [ ] Confidential clients use client secret/certificate
- [ ] Public clients use PKCE (no client secret)
- [ ] Client ID validation
- [ ] Redirect URI whitelist

---

### Request Signing Specific (AWS SigV4, Token Binding)

**Signing Process**:
- [ ] Canonical request creation (normalization)
- [ ] Payload hashing (SHA256)
- [ ] Timestamp inclusion and validation
- [ ] Signature calculation (HMAC-SHA256 or ECDSA)
- [ ] Signature in Authorization header

**Key Management**:
- [ ] Secret key never transmitted
- [ ] Derived keys scoped (service/region/date)
- [ ] Key rotation schedule
- [ ] Secure key storage (KMS, Key Vault)

**Validation**:
- [ ] Signature verification
- [ ] Timestamp validation (typically 5-minute window)
- [ ] Payload hash verification
- [ ] Replay attack prevention

---

### Enterprise SSO Specific (SPNEGO)

**Infrastructure**:
- [ ] Kerberos KDC or Active Directory configured
- [ ] Service principal created (HTTP/<hostname>)
- [ ] Keytab file secured (read-only by service account)
- [ ] DNS resolution correct (forward and reverse)

**HTTP Configuration**:
- [ ] WWW-Authenticate: Negotiate header
- [ ] GSS-API context handling (multi-round)
- [ ] Fallback authentication method (Basic, form)
- [ ] TLS for data protection

**Client Configuration**:
- [ ] Browser trusted sites configuration
- [ ] Kerberos ticket acquisition (kinit)
- [ ] Service Principal Name (SPN) correct
- [ ] Clock synchronization (±5 minutes)

---

## Common Pitfalls and Solutions

### Pitfall 1: Storing Tokens in localStorage (SPAs)
**Problem**: XSS attacks can steal tokens
**Solution**: Store in memory only, use session-based approach for server-side

### Pitfall 2: Not Using PKCE for Public Clients
**Problem**: Authorization code interception attacks
**Solution**: Always use PKCE for SPAs, mobile apps, CLI tools

### Pitfall 3: Long-Lived Access Tokens
**Problem**: Extended exposure window if token stolen
**Solution**: Access tokens ≤1 hour, use refresh tokens for long sessions

### Pitfall 4: Insufficient Token Validation
**Problem**: Accepting invalid/expired/tampered tokens
**Solution**: Validate signature, issuer, audience, expiration, scopes

### Pitfall 5: Tokens in URLs
**Problem**: Logged in server logs, browser history, referrer headers
**Solution**: Use Authorization header exclusively, never query parameters

### Pitfall 6: Manual OAuth Implementation
**Problem**: Complex spec, easy to make mistakes, security vulnerabilities
**Solution**: Use established libraries (MSAL, Passport.js, etc.)

### Pitfall 7: Not Implementing Token Refresh
**Problem**: Users re-authenticate frequently, poor UX
**Solution**: Implement refresh token flow with silent renewal

### Pitfall 8: Broad Scopes/Permissions
**Problem**: Excessive access if token compromised
**Solution**: Principle of least privilege, request minimal necessary scopes

### Pitfall 9: Clock Skew in Signature Validation
**Problem**: Valid requests rejected due to timestamp mismatch
**Solution**: Sync system clocks (NTP), allow ±5 minute tolerance

### Pitfall 10: Not Handling Conditional Access (Azure AD)
**Problem**: Authentication fails with MFA/conditional access policies
**Solution**: Handle claims challenges, support interactive re-authentication

---

## Testing Authentication Systems

### Unit Tests
- Token validation logic (signature, claims, expiration)
- PKCE generation and verification
- Signature calculation (canonical request, string to sign)
- Error handling (invalid tokens, expired credentials)

### Integration Tests
- Full OAuth flow (authorization code exchange)
- Token refresh flow
- Token revocation
- Multi-round authentication (SPNEGO)
- API calls with tokens

### Security Tests
- CSRF attack prevention (state parameter)
- Token theft scenarios
- Replay attack prevention
- XSS/injection attacks
- Authorization bypass attempts

### Load Tests
- Token validation performance
- Concurrent authentication requests
- Token cache efficiency
- Rate limiting effectiveness

### End-to-End Tests
- Browser-based authentication flows
- Mobile app authentication
- CLI authentication (device flow)
- SSO across multiple applications

---

## References and Further Reading

### Standards
- **RFC 6749**: OAuth 2.0 Authorization Framework
- **RFC 6750**: OAuth 2.0 Bearer Token Usage
- **RFC 7617**: HTTP Basic Authentication
- **RFC 4559**: SPNEGO-based HTTP Authentication
- **RFC 8471**: Token Binding over HTTP
- **RFC 7519**: JSON Web Token (JWT)
- **RFC 7662**: OAuth 2.0 Token Introspection
- **RFC 8252**: OAuth 2.0 for Native Apps
- **RFC 9449**: OAuth 2.0 Demonstrating Proof-of-Possession (DPoP)

### Documentation
- **Azure AD**: https://learn.microsoft.com/en-us/azure/active-directory/develop/
- **AWS IAM**: https://docs.aws.amazon.com/IAM/latest/UserGuide/
- **GitHub OAuth**: https://docs.github.com/en/apps/oauth-apps
- **OAuth 2.0**: https://oauth.net/2/
- **OpenID Connect**: https://openid.net/connect/

### Security Best Practices
- **OWASP Authentication Cheat Sheet**: https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html
- **OAuth 2.0 Security Best Current Practice**: https://datatracker.ietf.org/doc/html/draft-ietf-oauth-security-topics
- **NIST Digital Identity Guidelines**: https://pages.nist.gov/800-63-3/

### Books
- "OAuth 2.0 in Action" by Justin Richer and Antonio Sanso
- "Identity and Data Security for Web Development" by Jonathan LeBlanc and Tim Messerschmidt
- "API Security in Action" by Neil Madden

---

## Document Maintenance

**Last Updated**: 2025-10-13

**Update Schedule**: Review quarterly for RFC updates, security advisories, and industry changes

**Contributing**: When adding new authentication patterns:
1. Follow existing document structure
2. Include complete flow diagrams
3. Provide implementation examples
4. Document security considerations
5. Add to comparison matrix and decision framework

**Version History**:
- 2025-10-13: Initial compilation of 7 authentication patterns (4 RFCs, 3 company implementations)

---

## Quick Start Recommendations

### For New Projects Starting Today (2025)

**Web Application (React/Angular/Vue + Backend)**:
- Use: OAuth 2.0 Authorization Code Flow + PKCE
- Library: MSAL.js (Azure AD) or Auth0 SDK
- Backend: Validate JWT tokens
- Session: Server-side with refresh tokens

**Mobile Application (iOS/Android/React Native)**:
- Use: OAuth 2.0 Authorization Code Flow + PKCE (system browser)
- Library: MSAL Mobile or AppAuth
- Storage: OS secure storage (Keychain/Keystore)
- Biometric: Add biometric unlock for tokens

**CLI Tool (User Authentication)**:
- Use: Device Code Flow
- Library: MSAL Python/Node.js or oidc-client
- Storage: Encrypted credential file (~/.config/app/credentials)
- Refresh: Automatic silent refresh

**Background Service (No User)**:
- Use: Client Credentials Flow or AWS IAM (if on AWS)
- Authentication: Certificate (preferred) or client secret
- Library: MSAL or AWS SDK
- Caching: Token cache with expiration

**Enterprise Intranet (SSO Required)**:
- Use: SPNEGO/Negotiate or SAML/OIDC Federation
- Infrastructure: Active Directory or Azure AD
- Fallback: Form-based authentication
- Transport: Always HTTPS

---

## Conclusion

This collection represents diverse approaches to authentication across RFCs and industry implementations. Key insights:

1. **No one-size-fits-all**: Choose based on application type, infrastructure, and security requirements
2. **Standards-based is best**: OAuth 2.0/OIDC provide robust, interoperable solutions
3. **Use libraries**: Don't implement authentication protocols manually
4. **Security first**: Always HTTPS, short token lifetimes, PKCE for public clients
5. **Modern alternatives**: Prefer Authorization Code Flow + PKCE over older flows

**Modern Authentication Hierarchy** (2025):
1. **Best**: OAuth 2.0 Authorization Code + PKCE (with MFA/conditional access)
2. **Good**: OAuth 2.0 with Token Binding or Request Signing (AWS SigV4)
3. **Acceptable**: OAuth 2.0 Bearer Token (with short lifetimes, HTTPS)
4. **Legacy**: SPNEGO (enterprise only), HTTP Basic Auth (internal only, with HTTPS)
5. **Avoid**: Implicit Flow, ROPC Flow, credentials in URLs

This summary and associated documentation serve as a comprehensive reference for authentication system design and implementation.
