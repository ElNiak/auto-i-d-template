# RFC 7519 - JSON Web Token (JWT)

**Source:** https://www.rfc-editor.org/rfc/rfc7519.txt

## Specification Purpose and JWT Structure

### Purpose:
JWT is a "compact claims representation format" for transmitting claims between parties in a cryptographically secure manner.

### Design Goal:
Designed for "space constrained environments such as HTTP Authorization headers" and URL query parameters.

### JWT Structure:
Three base64url-encoded parts separated by periods (`.`):
1. **Header**: Metadata about the token (algorithm, type)
2. **Payload**: Claims (statements about an entity and additional data)
3. **Signature**: Cryptographic signature or Message Authentication Code (MAC)

**Format:** `xxxxx.yyyyy.zzzzz`

### Security Variants:
- **JWS (JSON Web Signature)**: Signed JWT for integrity and authenticity
- **JWE (JSON Web Encryption)**: Encrypted JWT for confidentiality

## Key Security Considerations

### Fundamental Security Principle:
> "Contents of a JWT cannot be relied upon in a trust decision unless cryptographically secured"

### Cryptographic Validation:
- **Mandatory signature verification**: Always validate signatures before trusting claims
- **Algorithm validation**: Verify algorithm matches expected algorithm (prevent algorithm confusion)
- **Key validation**: Ensure signing/encryption keys are from trusted sources

### Signature and Encryption Order:
**Recommended approach:**
> "Sign the message and then encrypt the result"

This provides both authenticity (signature) and confidentiality (encryption).

### Algorithm Support:
- **Mandatory-to-implement**: Support for specific algorithms ensures interoperability
- **Algorithm negotiation**: Header specifies algorithm used
- **Algorithm security**: Use strong, modern cryptographic algorithms

## Claims and Their Security Implications

### Registered Claims (Standardized):

#### 1. `iss` (Issuer)
- **Purpose**: Identifies who issued the token
- **Security**: Validate against trusted issuer list
- **Format**: String or URI
- **Validation**: Essential for trust decisions

#### 2. `sub` (Subject)
- **Purpose**: Identifies principal being described
- **Security**: Must be unique within issuer context
- **Format**: String or URI
- **Use**: Often user ID or entity identifier

#### 3. `aud` (Audience)
- **Purpose**: Specifies intended recipients
- **Security**: Reject tokens not intended for your service
- **Format**: String, URI, or array
- **Validation**: Critical for preventing token misuse

#### 4. `exp` (Expiration Time)
- **Purpose**: Sets token validity period
- **Security**: Enforces time-limited access
- **Format**: NumericDate (seconds since epoch)
- **Validation**: Reject expired tokens
- **Best Practice**: Short expiration times reduce risk

#### 5. `nbf` (Not Before)
- **Purpose**: Defines earliest valid usage time
- **Security**: Prevents premature token use
- **Format**: NumericDate
- **Validation**: Reject tokens used too early

#### 6. `iat` (Issued At)
- **Purpose**: Records token creation time
- **Security**: Helps detect token replay and age
- **Format**: NumericDate
- **Use**: Audit logging and replay prevention

#### 7. `jti` (JWT ID)
- **Purpose**: Unique identifier for token
- **Security**: Enables token revocation tracking
- **Format**: Case-sensitive string
- **Use**: Prevent replay attacks via token blacklisting

### Private Claims:
- **Custom claims**: Application-specific data
- **Collision avoidance**: Use namespaced names or collision-resistant names
- **Privacy**: Encrypt sensitive private claims

## Best Practices for JWT Usage

### 1. Signature Validation:
- Always verify signature before processing claims
- Use approved cryptographic libraries
- Validate algorithm matches expected algorithm
- Check key validity and expiration

### 2. Claims Validation:
```
Required Validations:
- iss: Verify issuer is trusted
- aud: Confirm token intended for your service
- exp: Check token not expired
- nbf: Verify token validity period started
- iat: Validate token age is reasonable
```

### 3. Clock Skew Tolerance:
- Implement small tolerances for exp/nbf checks (e.g., 60 seconds)
- Account for clock synchronization issues
- Don't make tolerance too large (security risk)

### 4. Token Transmission Security:
- **Use TLS/HTTPS**: Always transmit tokens over encrypted channels
- **Avoid URL parameters**: Tokens in URLs can leak via logs/referers
- **Prefer headers**: Use Authorization header with Bearer scheme
- **Short-lived tokens**: Minimize exposure window

### 5. Privacy Protection:
- **Encrypt sensitive data**: Use JWE for confidential information
- **Minimal claims**: Include only necessary information
- **Avoid PII in public claims**: Personal data should be encrypted
- **Base64 is not encryption**: JWS only provides integrity, not confidentiality

### 6. Token Lifecycle:
- **Short expiration**: Minutes to hours for access tokens
- **Refresh mechanism**: Use refresh tokens for long-lived sessions
- **Revocation support**: Implement jti-based blacklisting
- **Rotation**: Issue new tokens regularly

### 7. Algorithm Security:
- **Avoid "none" algorithm**: Disable unsigned JWTs
- **Use RS256 or ES256**: For distributed systems
- **Use HS256**: Only when sharing secret is secure
- **Validate alg header**: Prevent algorithm substitution attacks

## Threat Models and Attack Vectors

### 1. Token Replay Attacks:
**Attack**: Reuse intercepted token multiple times
**Mitigations:**
- Short expiration times
- One-time use tokens (jti + blacklist)
- Token binding to client
- Audience validation

### 2. Signature Stripping:
**Attack**: Remove signature and set alg to "none"
**Mitigations:**
- Reject "none" algorithm
- Strict algorithm validation
- Whitelist allowed algorithms

### 3. Algorithm Confusion:
**Attack**: Change RS256 to HS256, use public key as HMAC secret
**Mitigations:**
- Explicitly specify expected algorithm
- Never use public key as HMAC secret
- Validate algorithm before verification

### 4. Claims Manipulation:
**Attack**: Modify claims in unsigned or weakly signed tokens
**Mitigations:**
- Always verify signatures
- Use strong cryptographic algorithms
- Validate all critical claims

### 5. Token Leakage:
**Attack**: Token exposure via logs, URLs, XSS, or storage
**Mitigations:**
- Use secure storage (httpOnly cookies or memory)
- Avoid URL parameters
- Implement XSS protection
- Clear tokens on logout

### 6. Expired Token Usage:
**Attack**: Use expired tokens to gain unauthorized access
**Mitigations:**
- Strict expiration validation
- No excessive clock skew tolerance
- Server-side expiration enforcement

### 7. Unintended Information Disclosure:
**Attack**: Extract sensitive data from JWT payload
**Mitigations:**
- Encrypt sensitive claims (use JWE)
- Minimize payload size
- Avoid including PII
- Remember: Base64 encoding is not encryption

### 8. Cross-Service Token Misuse:
**Attack**: Use token intended for service A to access service B
**Mitigations:**
- Validate audience (aud) claim
- Service-specific token validation
- Token binding to client instance

## Implementation Security Checklist

### Token Creation:
- [ ] Use secure random number generator for IDs (jti)
- [ ] Set appropriate expiration (exp)
- [ ] Include issuer (iss) and audience (aud)
- [ ] Use strong signing algorithm (RS256, ES256)
- [ ] Encrypt sensitive claims
- [ ] Minimize token size

### Token Validation:
- [ ] Verify signature/MAC before processing
- [ ] Validate algorithm matches expected
- [ ] Check issuer (iss) is trusted
- [ ] Verify audience (aud) matches
- [ ] Enforce expiration (exp)
- [ ] Check not-before (nbf) if present
- [ ] Validate token age (iat)
- [ ] Check jti for revocation if applicable

### Storage and Transmission:
- [ ] Transmit only over TLS
- [ ] Store securely (httpOnly cookies or secure storage)
- [ ] Never log full tokens
- [ ] Clear on logout
- [ ] Use Authorization header, not URL params

### Error Handling:
- [ ] Fail closed on validation errors
- [ ] Log validation failures
- [ ] Don't leak information in error messages
- [ ] Return generic errors to clients

## Key Takeaways for Token-Based Security

1. **Cryptographic security is mandatory**: Unsigned JWTs are not secure
2. **Validate everything**: Never trust claims without signature verification
3. **Short-lived tokens**: Minimize exposure window with short expiration
4. **Encrypt sensitive data**: JWS provides integrity, not confidentiality
5. **Audience validation**: Prevent cross-service token misuse
6. **Algorithm specification**: Explicitly validate expected algorithms
7. **Defense in depth**: Combine JWT security with TLS, secure storage, and proper validation
8. **Minimal claims**: Include only necessary information to reduce risk
9. **Proper revocation**: Implement token blacklisting for immediate revocation
10. **Regular rotation**: Issue new tokens frequently to limit compromise impact

## Comparison with Other Token Formats

| Feature | JWT | Opaque Token |
|---------|-----|--------------|
| **Structure** | Self-contained (claims in token) | Reference (requires lookup) |
| **Stateless** | Yes (no server-side storage needed) | No (requires token store) |
| **Revocation** | Complex (requires blacklist or short exp) | Simple (delete from store) |
| **Size** | Larger (base64-encoded JSON) | Smaller (random string) |
| **Performance** | Faster (no DB lookup) | Slower (requires lookup) |
| **Security** | Requires careful validation | Simpler security model |
| **Use Case** | Distributed systems, microservices | Centralized systems |

## Related Standards

- **RFC 7515**: JWS (JSON Web Signature) - signature format
- **RFC 7516**: JWE (JSON Web Encryption) - encryption format
- **RFC 7517**: JWK (JSON Web Key) - key representation
- **RFC 7518**: JWA (JSON Web Algorithms) - cryptographic algorithms
- **RFC 8725**: JWT Best Current Practices - updated security guidance
