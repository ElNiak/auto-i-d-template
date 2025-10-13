# Microsoft Identity Platform Protocol Specifications

**Source:** https://learn.microsoft.com/en-us/entra/identity-platform/v2-protocols

## Platform Overview

The Microsoft identity platform (formerly Azure AD v2.0) provides authentication and authorization services for modern applications using industry-standard protocols.

**Core Service:** Microsoft Entra ID (formerly Azure Active Directory)

## Protocol Support

### 1. OAuth 2.0
**Specification:** Standards-compliant implementation of OAuth 2.0

**Purpose:** Authorization framework for delegated access to APIs and resources

**Key Statement:**
> "Standards-compliant implementations" of authentication protocols

### 2. OpenID Connect (OIDC) 1.0
**Specification:** OIDC 1.0 built on OAuth 2.0

**Purpose:** Authentication layer providing user sign-in and identity information

**Integration:** Works seamlessly with OAuth 2.0 for combined authentication and authorization

### 3. SAML 2.0 (Enterprise)
**Purpose:** Enterprise federation protocol for SSO

**Use Case:** Legacy enterprise application integration

## Architecture Components

### Four Primary Roles in OAuth 2.0:

#### 1. Authorization Server
**Identity:** Microsoft Identity Platform / Entra ID

**Responsibilities:**
- User authentication
- Token issuance (access tokens, ID tokens, refresh tokens)
- Token validation
- User consent management
- Security policy enforcement

**Endpoints:**
- Authorization endpoint: `/authorize`
- Token endpoint: `/token`
- UserInfo endpoint: `/userinfo`
- Discovery endpoint: `/.well-known/openid-configuration`

#### 2. Client (Application)
**Identity:** Application requesting access

**Types:**
- Web applications (confidential client)
- Single-page applications (public client)
- Mobile applications (public client)
- Daemon/service applications (confidential client)

**Requirements:**
- Register in Microsoft Entra admin center
- Obtain client ID (application ID)
- Configure redirect URIs
- Manage client secrets (confidential clients only)

#### 3. Resource Owner
**Identity:** End-user or entity owning the data

**Responsibilities:**
- Authenticate to authorization server
- Grant consent to client applications
- Control access to protected resources

#### 4. Resource Server
**Identity:** API or data provider (e.g., Microsoft Graph, custom APIs)

**Responsibilities:**
- Validate access tokens
- Enforce authorization policies
- Serve protected resources
- Apply scope-based access control

## Token Types

### 1. Access Tokens

**Format:** JSON Web Tokens (JWTs)

**Purpose:** Represent permissions granted by authorization server

**Key Statement:**
> "Bearer tokens are JSON Web Tokens (JWTs)"

**Characteristics:**
- Short-lived (default: 1 hour)
- Used to access protected APIs
- Include scopes/permissions
- Must be validated by resource server

**Token Structure:**
```json
{
  "header": {
    "alg": "RS256",
    "typ": "JWT",
    "kid": "key-id"
  },
  "payload": {
    "aud": "api://resource-id",
    "iss": "https://login.microsoftonline.com/{tenant}/v2.0",
    "iat": 1234567890,
    "exp": 1234571490,
    "scp": "user.read mail.send",
    "sub": "user-id",
    "tid": "tenant-id"
  }
}
```

**Validation Requirements:**
- Verify signature using Microsoft's public keys
- Check expiration (`exp` claim)
- Validate audience (`aud` claim)
- Validate issuer (`iss` claim)
- Verify required scopes

### 2. ID Tokens

**Format:** JSON Web Tokens (JWTs)

**Purpose:** User sign-in and basic identity information

**Characteristics:**
- OIDC-compliant
- Contains user profile claims
- Used for authentication, not authorization
- Must be validated by client

**Common Claims:**
- `sub`: Subject (unique user identifier)
- `name`: User's display name
- `email`: User's email address
- `preferred_username`: Username
- `oid`: Object ID (immutable identifier)
- `tid`: Tenant ID

**Important:**
- ID tokens are for client consumption only
- Never use ID tokens to authorize API access (use access tokens)

### 3. Refresh Tokens

**Format:** Opaque tokens (not JWTs)

**Purpose:** Request new access/ID tokens without re-authentication

**Characteristics:**
- Long-lived (days to months)
- Single-use or rotated on use
- Revocable
- Stored securely

**Security Considerations:**
> "Protect refresh tokens as sensitive data"

**Best Practices:**
- Store in secure storage (never localStorage)
- Implement refresh token rotation
- Support revocation
- Encrypt at rest
- Use bound to device/client

## Authentication Flows

### 1. Authorization Code Grant Flow

**Use Case:** Web applications (confidential clients)

**Security:** Most secure flow for server-side applications

**Flow Steps:**
1. Client initiates authorization request
2. User authenticates and grants consent
3. Authorization code returned to client
4. Client exchanges code for tokens (includes client secret)
5. Tokens issued (access token, ID token, refresh token)

**Client Authentication:** Client secret required

**Benefits:**
- Access token never exposed to user agent
- Client authentication at token endpoint
- Support for refresh tokens
- Suitable for confidential clients

### 2. Authorization Code Flow with PKCE

**Use Case:** Single-page applications and mobile apps (public clients)

**Security:** Recommended for all public clients

**Flow Steps:**
1. Client generates code verifier and challenge
2. Client initiates authorization request with code challenge
3. User authenticates and grants consent
4. Authorization code returned to client
5. Client exchanges code + code verifier for tokens
6. Tokens issued

**Client Authentication:** Code verifier instead of client secret

**Benefits:**
- Protection against authorization code interception
- No client secret required
- Suitable for public clients
- Mitigates CSRF and code injection attacks

### 3. Client Credentials Flow

**Use Case:** Daemon applications, backend services (machine-to-machine)

**Security:** For confidential clients only

**Flow Steps:**
1. Client authenticates with client credentials
2. Access token issued (no user context)
3. Client uses token to access resources

**Characteristics:**
- No user interaction
- Client acts on its own behalf
- No refresh tokens
- Application permissions (not delegated)

**Authentication Methods:**
- Client secret
- Certificate
- Federated credentials (workload identity)

### 4. On-Behalf-Of (OBO) Flow

**Use Case:** Middle-tier services calling downstream APIs on behalf of user

**Security:** Maintains user context through service chain

**Flow Steps:**
1. Client gets access token for middle-tier service
2. Middle-tier service receives access token
3. Middle-tier exchanges token for downstream API token
4. Middle-tier calls downstream API with new token

**Benefits:**
- Preserves user identity
- Implements least privilege
- Enables audit trails
- Supports consent management

### 5. Device Code Flow

**Use Case:** Input-constrained devices (IoT, CLIs)

**Flow Steps:**
1. Device requests device code
2. User navigates to verification URL on another device
3. User enters code and authenticates
4. Device polls for token
5. Tokens issued after user completes authentication

**Benefits:**
- No input required on constrained device
- Secure authentication on capable device
- User-friendly for devices without keyboards

## Security Recommendations

### 1. Use Microsoft Authentication Libraries (MSAL)

**Key Recommendation:**
> "Strongly advise against crafting your own library or raw HTTP calls"

**Benefits of MSAL:**
- Handles token acquisition and renewal
- Implements security best practices
- Manages token caching
- Provides error handling
- Receives security updates
- Cross-platform support

**Available MSAL Libraries:**
- MSAL.NET (.NET applications)
- MSAL.js (JavaScript/TypeScript SPAs)
- MSAL Node (Node.js applications)
- MSAL Python
- MSAL Java
- MSAL for iOS/macOS
- MSAL for Android

### 2. Register Applications Properly

**Requirements:**
1. Register in Microsoft Entra admin center
2. Configure platform (web, SPA, mobile)
3. Set redirect URIs (exact match required)
4. Configure permissions (API permissions)
5. Generate client secrets (confidential clients)
6. Set up authentication settings

**Redirect URI Security:**
- Use HTTPS (except localhost for development)
- Exact match validation (no wildcards)
- Register all valid redirect URIs
- Avoid overly permissive URIs

### 3. Use Predefined Endpoints

**Authorization Endpoint:**
```
https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize
```

**Token Endpoint:**
```
https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token
```

**Discovery Endpoint (OpenID Configuration):**
```
https://login.microsoftonline.com/{tenant}/v2.0/.well-known/openid-configuration
```

**Multi-Tenant Applications:**
Use `common`, `organizations`, or `consumers` instead of `{tenant}`

### 4. Implement Proper Redirect URI Configuration

**Web Applications:**
- Use HTTPS redirect URIs
- Configure explicit paths
- Avoid wildcards

**Single-Page Applications:**
- Register as SPA platform type
- Use Authorization Code Flow with PKCE
- No client secret

**Mobile Applications:**
- Use platform-specific redirect URI schemes
- iOS: Custom URL schemes or Universal Links
- Android: App Links or custom schemes

### 5. Protect Client Secrets

**Confidential Clients Only:**
- Web applications
- Daemon/service applications

**Security Requirements:**
- Never embed in client-side code
- Store in secure configuration (Azure Key Vault, environment variables)
- Never commit to source control
- Rotate regularly
- Use certificate-based authentication when possible

**Certificate Authentication (Preferred):**
- More secure than client secrets
- Shorter-lived credentials
- Hardware-backed options (HSM)

### 6. Validate Tokens on Every Request

**Access Token Validation (Resource Server):**
1. Validate signature (use Microsoft public keys)
2. Check issuer (`iss` claim)
3. Validate audience (`aud` claim)
4. Check expiration (`exp` claim)
5. Verify not-before (`nbf` claim)
6. Validate scopes for authorization

**ID Token Validation (Client):**
1. Validate signature
2. Check issuer
3. Validate audience (must be client ID)
4. Check expiration
5. Verify nonce (if used in request)
6. Validate `c_hash` or `at_hash` (if present)

### 7. Implement Minimal Privilege Principle

**Scope Requests:**
- Request only necessary scopes
- Use incremental consent
- Separate admin consent from user consent

**API Permissions:**
- **Delegated permissions**: User context required
- **Application permissions**: No user context (admin consent required)

**Best Practice:**
Request permissions dynamically based on feature usage

## Microsoft-Specific Security Features

### 1. Conditional Access

**Purpose:** Risk-based access control policies

**Policies Can Enforce:**
- Multi-factor authentication
- Device compliance
- Location restrictions
- Risk-based authentication
- Session controls

**Integration:**
- Claims challenges
- Step-up authentication
- Continuous access evaluation

### 2. Continuous Access Evaluation (CAE)

**Purpose:** Near real-time token revocation

**Benefits:**
- Immediate response to security events
- Reduced token lifetime risks
- User revocation enforcement
- Location policy enforcement

**Events Triggering CAE:**
- User account disabled
- Password changed
- MFA state changed
- Location policy violation

### 3. Token Lifetime Policies

**Configurable Lifetimes:**
- Access tokens (default: 1 hour)
- ID tokens (default: 1 hour)
- Refresh tokens (default: 90 days)
- Session tokens (default: 24 hours)

**Recommendations:**
- Short access token lifetimes (1 hour or less)
- Longer refresh tokens with rotation
- Conditional refresh token lifetime based on risk

### 4. Multi-Factor Authentication (MFA)

**Methods Supported:**
- Microsoft Authenticator app
- SMS text message
- Voice call
- FIDO2 security keys
- Certificate-based authentication
- Windows Hello

**Enforcement:**
- Per-user MFA
- Conditional Access policies
- Risk-based MFA
- Step-up authentication

### 5. Identity Protection

**Risk Detection:**
- Anonymous IP usage
- Atypical travel
- Malware-linked IP
- Password spray
- Leaked credentials

**Risk Levels:**
- Low
- Medium
- High

**Automated Responses:**
- Require MFA
- Require password change
- Block access
- Alert administrators

## Best Practices by Application Type

### Web Applications

**Recommended Flow:** Authorization Code Flow

**Implementation:**
- Use MSAL.NET or MSAL Node
- Store tokens server-side
- Use secure session cookies (httpOnly, Secure, SameSite)
- Implement CSRF protection
- Validate state parameter
- Use short access token lifetimes

### Single-Page Applications

**Recommended Flow:** Authorization Code Flow with PKCE

**Implementation:**
- Use MSAL.js 2.x
- Store tokens in memory (not localStorage)
- Implement silent token renewal
- Use popup or redirect for authentication
- Enable CORS for token endpoint
- Implement Content Security Policy

### Mobile Applications

**Recommended Flow:** Authorization Code Flow with PKCE

**Implementation:**
- Use MSAL for iOS/Android
- Use system browser (not WebView)
- Store tokens in platform keychain
- Implement token caching
- Handle redirect URIs securely
- Support biometric authentication

### Daemon/Service Applications

**Recommended Flow:** Client Credentials Flow

**Implementation:**
- Use MSAL.NET or language-specific MSAL
- Use certificate authentication (preferred over secrets)
- Store credentials in Azure Key Vault
- Implement token caching
- Use application permissions
- Monitor token usage

## Security Checklist

### Application Registration:
- [ ] Register application in Microsoft Entra admin center
- [ ] Configure appropriate platform type
- [ ] Set exact redirect URIs (HTTPS for production)
- [ ] Request minimal required permissions
- [ ] Generate and secure client secrets (if confidential client)

### Authentication Implementation:
- [ ] Use MSAL libraries (don't build custom)
- [ ] Implement Authorization Code with PKCE for public clients
- [ ] Validate state parameter (CSRF protection)
- [ ] Use HTTPS for all endpoints
- [ ] Handle errors gracefully

### Token Management:
- [ ] Validate all token signatures
- [ ] Check token expiration on every use
- [ ] Validate issuer and audience
- [ ] Store tokens securely based on client type
- [ ] Implement token refresh logic
- [ ] Support token revocation

### API Security:
- [ ] Validate access tokens on every API call
- [ ] Check required scopes
- [ ] Implement least privilege
- [ ] Return appropriate error codes
- [ ] Log security events

### Conditional Access:
- [ ] Handle claims challenges
- [ ] Implement step-up authentication
- [ ] Support MFA requirements
- [ ] Handle location restrictions
- [ ] Enable continuous access evaluation

## Common Security Pitfalls

### 1. Client Secret Exposure
**Problem:** Client secrets committed to source control or embedded in code

**Solution:**
- Use environment variables or Azure Key Vault
- Never commit secrets to version control
- Use certificate-based authentication
- Rotate secrets regularly

### 2. Improper Token Storage (SPAs)
**Problem:** Tokens stored in localStorage (vulnerable to XSS)

**Solution:**
- Store tokens in memory only
- Use MSAL.js with proper configuration
- Implement token renewal
- Consider backend-for-frontend pattern

### 3. Missing Token Validation
**Problem:** APIs not validating access tokens properly

**Solution:**
- Validate signature, issuer, audience, expiration
- Use middleware for automatic validation
- Check scopes for authorization
- Log validation failures

### 4. Overly Broad Permissions
**Problem:** Requesting unnecessary API permissions

**Solution:**
- Request minimal required scopes
- Use incremental consent
- Implement feature-based permission requests
- Regular permission audits

### 5. Not Handling Conditional Access
**Problem:** Applications fail when Conditional Access policies applied

**Solution:**
- Implement claims challenge handling
- Support step-up authentication
- Handle MFA requirements
- Test with various CA policies

## Key Takeaways

### Protocol Implementation:
> "Strongly advise against crafting your own library or raw HTTP calls"

**Use MSAL libraries for all authentication scenarios**

### Security Principles:
1. **Standards compliance**: OAuth 2.0 and OIDC certified
2. **Use proven libraries**: MSAL provides security and updates
3. **Validate everything**: Tokens, redirects, claims
4. **Least privilege**: Minimal permissions required
5. **Defense in depth**: Multiple security layers

### Microsoft Identity Platform Advantages:
- Enterprise-grade security
- Built-in threat protection
- Conditional Access integration
- Continuous Access Evaluation
- Comprehensive monitoring and logging

### Migration Path:
- Legacy apps: SAML 2.0 support
- Modern apps: OAuth 2.0 / OIDC
- Gradual migration supported
- Backward compatibility maintained

## Additional Resources

- **Microsoft Identity Platform Documentation**: https://learn.microsoft.com/en-us/entra/identity-platform/
- **MSAL Libraries**: https://learn.microsoft.com/en-us/entra/msal/
- **OAuth 2.0 and OIDC**: https://learn.microsoft.com/en-us/entra/identity-platform/v2-protocols
- **Security Best Practices**: https://learn.microsoft.com/en-us/entra/identity-platform/security-best-practices
- **Microsoft Graph API**: https://learn.microsoft.com/en-us/graph/
