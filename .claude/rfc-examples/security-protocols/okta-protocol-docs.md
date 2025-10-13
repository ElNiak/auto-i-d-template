# Okta Protocol Documentation

**Source:** https://developer.okta.com/docs/concepts/oauth-openid/

## Protocol Overview

Okta implements industry-standard authentication and authorization protocols:
- **OAuth 2.0**: Authorization framework
- **OpenID Connect (OIDC)**: Authentication layer on top of OAuth 2.0
- **SAML 2.0**: Enterprise federation protocol

## OAuth 2.0 and OpenID Connect Implementation

### Core OAuth 2.0 Concepts

#### Roles in OAuth 2.0:
1. **Resource Owner**: End-user who owns the data
2. **Client**: Application requesting access to resources
3. **Resource Server**: API hosting protected resources
4. **Authorization Server**: Okta's service issuing tokens

#### Grant Types Supported:
- Authorization Code Grant
- Authorization Code with PKCE (Proof Key for Code Exchange)
- Implicit Grant (deprecated)
- Resource Owner Password Grant (limited use)
- Client Credentials Grant
- Device Authorization Grant
- Token Exchange Grant

### OpenID Connect (OIDC) Extensions

**Purpose:** Adds authentication layer on top of OAuth 2.0 authorization

**Additional Features:**
- **ID Token**: JWT containing user identity information
- **UserInfo Endpoint**: Retrieve user profile data
- **Standard Scopes**: openid, profile, email, address, phone
- **Authentication Methods**: Multiple authentication factors

## Recommended Authentication Flows

### Selection Criteria:
Choose authentication flow based on:
- **Application type**: Web, mobile, single-page, service
- **Client characteristics**: Public (cannot keep secrets) or confidential (can keep secrets)
- **Authentication model**: Redirect-based or embedded
- **User interaction**: With user or machine-to-machine

### 1. Authorization Code with PKCE (Recommended)

**Use Case:** Most secure flow for all application types

**Client Types:**
- Single-page applications (SPAs)
- Mobile applications
- Native applications
- Web applications

**Flow Steps:**
1. Client generates code verifier and challenge
2. User redirected to Okta authorization endpoint with code challenge
3. User authenticates and authorizes
4. Authorization code returned to client
5. Client exchanges code + code verifier for tokens

**Security Features:**
- Protection against authorization code interception
- No client secret required (suitable for public clients)
- PKCE prevents CSRF and authorization code injection attacks

**Code Challenge Methods:**
- `S256` (SHA-256): Recommended
- `plain`: Not recommended (use only if SHA-256 unavailable)

**PKCE Components:**
```
Code Verifier: High-entropy random string (43-128 characters)
Code Challenge: Base64URL(SHA256(code_verifier))
Code Challenge Method: S256
```

### 2. Interaction Code Flow (Okta Identity Engine)

**Use Case:** Next-generation authentication for Okta Identity Engine

**Features:**
- Enhanced security
- Step-up authentication
- Progressive enrollment
- Risk-based authentication
- Multi-factor authentication orchestration

**Benefits:**
- Granular control over authentication steps
- Dynamic authentication requirements
- Passwordless authentication support
- Device trust integration

### 3. Client Credentials Flow

**Use Case:** Machine-to-machine (M2M) authentication

**Client Type:** Confidential clients only

**Characteristics:**
- No user interaction
- Client authenticates with its own credentials
- Access token represents client, not user
- Used for backend services, APIs, daemons

**Flow Steps:**
1. Client sends client credentials to token endpoint
2. Okta validates credentials
3. Access token issued to client

**Security Considerations:**
- Client secret must be protected
- Store secrets in secure vaults
- Rotate credentials regularly
- Use service accounts with minimal privileges

### 4. Resource Owner Password Grant (Legacy)

**Use Case:** Highly trusted applications only (migration scenarios)

**Status:** Not recommended for new applications

**Limitations:**
- Requires sharing user credentials with client
- Breaks single sign-on (SSO)
- Limited MFA support
- Poor user experience

**When to Use:**
- Legacy application migration
- First-party applications only
- Short-term transitional use

**Recommendation:** Migrate to Authorization Code with PKCE

## Security Best Practices

### 1. Use Authorization Code with PKCE

**Recommendation:**
> "Okta recommends using the authorization code flow with PKCE for most clients"

**Benefits:**
- Most secure flow available
- Works for all client types
- Protection against multiple attack vectors
- Industry best practice (OAuth 2.1 requirement)

### 2. Prefer Redirect Authentication Model

**Redirect Model (Recommended):**
- User redirected to Okta for authentication
- Credentials never touch client application
- Centralized security controls
- Consistent authentication experience

**Embedded Model (Not Recommended):**
- Authentication UI embedded in application
- Increased security responsibility
- Custom implementation required
- Limited security features

### 3. Protect Code Verifiers and Challenges

**Requirements:**
- **Code Verifier**:
  - Cryptographically random string
  - Minimum 43 characters, maximum 128 characters
  - Allowed characters: [A-Z], [a-z], [0-9], "-", ".", "_", "~"

- **Code Challenge Generation**:
  - Use SHA-256 hash of code verifier
  - Base64URL encode the hash
  - Never reuse code verifiers

**Security:**
- Code verifier must be stored securely (client-side memory)
- Code verifier must be single-use
- Code challenge transmitted in authorization request

### 4. Use Cryptographically Secure Random Generators

**Requirement:** Generate code verifiers using cryptographically secure random number generators (CSPRNG)

**Platform Recommendations:**
- **JavaScript**: `crypto.getRandomValues()`
- **Java**: `java.security.SecureRandom`
- **Python**: `secrets` module
- **.NET**: `System.Security.Cryptography.RandomNumberGenerator`
- **iOS**: `SecRandomCopyBytes`
- **Android**: `java.security.SecureRandom`

### 5. Validate Token Signatures

**ID Token Validation:**
1. Verify signature using Okta's public keys
2. Validate issuer (`iss` claim)
3. Validate audience (`aud` claim)
4. Check expiration (`exp` claim)
5. Validate issued-at time (`iat` claim)
6. Check nonce (if used in request)

**Access Token Validation:**
1. Validate signature (if JWT format)
2. Check expiration
3. Validate audience
4. Validate issuer
5. Check scopes

### 6. Implement Proper Token Lifecycle Management

**Access Tokens:**
- **Lifetime**: Short-lived (default: 1 hour)
- **Storage**: Memory (SPAs), secure storage (mobile)
- **Transmission**: HTTPS only, Authorization header
- **Revocation**: Server-side validation

**Refresh Tokens:**
- **Lifetime**: Long-lived (days to months)
- **Storage**: Secure storage only (never localStorage)
- **Rotation**: Issue new refresh token on each use
- **Revocation**: Support explicit revocation

**ID Tokens:**
- **Purpose**: User identity information
- **Validation**: Always validate signature and claims
- **Usage**: Not for API authorization (use access tokens)

### 7. Use HTTPS for All Token Exchanges

**Requirement:** All OAuth/OIDC communications must use HTTPS (TLS 1.2+)

**Endpoints Protected:**
- Authorization endpoint
- Token endpoint
- UserInfo endpoint
- Revocation endpoint
- Introspection endpoint

## Okta-Specific Security Features

### 1. Token Management

**Token Inline Hooks:**
- Customize token claims
- Add custom claims
- Modify token content
- Integrate external systems

**Token Rotation:**
- Automatic refresh token rotation
- Configurable rotation policies
- Prevent token replay attacks

### 2. Security Policies

**Authentication Policies:**
- Multi-factor authentication requirements
- Network-based access control
- Device trust policies
- Risk-based authentication

**Authorization Policies:**
- Scope-based access control
- Conditional access rules
- Step-up authentication
- Context-aware authorization

### 3. API Access Management

**OAuth 2.0 Scopes:**
- Fine-grained access control
- Custom scope definitions
- Scope-based authorization
- Consent management

**Custom Authorization Servers:**
- Dedicated token issuance
- Isolated scope management
- Resource-specific policies
- Multi-tenant support

### 4. Threat Detection

**Suspicious Activity Detection:**
- Anomalous location detection
- Velocity checks
- Device fingerprinting
- Bot detection

**Automated Response:**
- Block suspicious requests
- Require step-up authentication
- Alert administrators
- Log security events

## Protocol Flow Examples

### Authorization Code with PKCE Flow (Detailed)

#### Step 1: Prepare PKCE Parameters
```
code_verifier = generateRandomString(64)
code_challenge = base64url(sha256(code_verifier))
code_challenge_method = "S256"
```

#### Step 2: Authorization Request
```
GET /oauth2/v1/authorize?
  client_id={client_id}
  &response_type=code
  &scope=openid profile email
  &redirect_uri={redirect_uri}
  &state={state}
  &code_challenge={code_challenge}
  &code_challenge_method=S256
```

#### Step 3: User Authentication
- User redirected to Okta
- User authenticates (username/password, MFA, etc.)
- User grants consent (if required)

#### Step 4: Authorization Response
```
HTTP/1.1 302 Found
Location: {redirect_uri}?
  code={authorization_code}
  &state={state}
```

#### Step 5: Token Request
```
POST /oauth2/v1/token
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code
&code={authorization_code}
&redirect_uri={redirect_uri}
&client_id={client_id}
&code_verifier={code_verifier}
```

#### Step 6: Token Response
```json
{
  "access_token": "eyJhbG...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "openid profile email",
  "refresh_token": "v2.loc...",
  "id_token": "eyJhbG..."
}
```

### Client Credentials Flow (Detailed)

#### Step 1: Token Request
```
POST /oauth2/v1/token
Authorization: Basic {base64(client_id:client_secret)}
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials
&scope={scopes}
```

#### Step 2: Token Response
```json
{
  "access_token": "eyJhbG...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "api:read api:write"
}
```

## Implementation Best Practices by Application Type

### Single-Page Applications (SPAs)

**Recommended Flow:** Authorization Code with PKCE

**Best Practices:**
- Store tokens in memory (JavaScript variables)
- Avoid localStorage (XSS vulnerability)
- Use sessionStorage as alternative (with caveats)
- Implement silent authentication for token renewal
- Use secure same-site cookies for session management
- Implement Content Security Policy (CSP)

### Mobile Applications

**Recommended Flow:** Authorization Code with PKCE

**Best Practices:**
- Use platform keychain/keystore for token storage
- Implement certificate pinning
- Use system browser for authentication (not WebView)
- Handle deep links securely
- Implement biometric authentication
- Protect against reverse engineering

### Web Applications

**Recommended Flow:** Authorization Code with PKCE or traditional Authorization Code

**Best Practices:**
- Store tokens server-side
- Use secure, httpOnly cookies for session
- Implement CSRF protection
- Validate tokens on every request
- Use short access token lifetimes
- Implement proper session management

### Backend Services / APIs

**Recommended Flow:** Client Credentials

**Best Practices:**
- Store client secrets in secure vaults (e.g., HashiCorp Vault, AWS Secrets Manager)
- Never commit secrets to version control
- Rotate credentials regularly
- Use service accounts with minimal privileges
- Implement circuit breakers for token refresh
- Monitor token usage for anomalies

## Security Checklist

### Authorization Configuration:
- [ ] Use Authorization Code with PKCE for all clients
- [ ] Implement HTTPS for all endpoints
- [ ] Configure appropriate redirect URIs
- [ ] Set minimal required scopes
- [ ] Enable refresh token rotation

### Token Management:
- [ ] Validate all token signatures
- [ ] Check token expiration on every use
- [ ] Store tokens securely based on client type
- [ ] Implement token refresh logic
- [ ] Support token revocation

### Authentication Policies:
- [ ] Require MFA for sensitive operations
- [ ] Configure session timeout policies
- [ ] Implement step-up authentication
- [ ] Enable risk-based authentication
- [ ] Configure network access restrictions

### Monitoring and Logging:
- [ ] Log all authentication events
- [ ] Monitor for suspicious activity
- [ ] Set up alerting for security events
- [ ] Implement audit logging
- [ ] Review logs regularly

## Key Takeaways

### Protocol Selection:
> "Okta recommends using one of its authentication deployment models for your app's authentication needs"

**Primary Recommendation:** Use Authorization Code with PKCE for maximum security

### Security Principles:
1. **Prefer redirect authentication**: Don't collect credentials in your app
2. **Use PKCE always**: Protection against authorization code interception
3. **Short-lived tokens**: Minimize impact of token compromise
4. **Secure storage**: Never store tokens in localStorage
5. **Validate everything**: Always verify signatures and claims

### Okta Advantages:
- Standards-compliant implementation
- Built-in security features
- Flexible authentication policies
- Comprehensive threat detection
- Enterprise-grade scalability

## Additional Resources

- **Okta Developer Documentation**: https://developer.okta.com/
- **OAuth 2.0 and OIDC**: https://developer.okta.com/docs/concepts/oauth-openid/
- **Authentication Guide**: https://developer.okta.com/docs/guides/implement-auth-code-pkce/
- **API Security**: https://developer.okta.com/docs/concepts/api-access-management/
