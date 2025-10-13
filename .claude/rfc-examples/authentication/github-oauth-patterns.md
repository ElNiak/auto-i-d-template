# GitHub OAuth Implementation Patterns

**Source**: GitHub Documentation
**Category**: Company Authentication Pattern
**URL**: https://docs.github.com/en/apps/oauth-apps

## Overview

GitHub's OAuth 2.0 implementation provides secure authentication for web applications, device flows, and command-line tools. It follows RFC 6749 (OAuth 2.0) with GitHub-specific extensions and best practices for API access.

## Authentication Flows

### 1. Web Application Flow (Authorization Code)

**Use Case**: Web applications with server-side components

#### Flow Steps

```
User                  Client App              GitHub
  |                       |                      |
  |---(1) Click Login---->|                      |
  |                       |                      |
  |                       |---(2) Redirect------>|
  |                       |    to authorize      |
  |                       |                      |
  |<----------------(3) Login Page---------------|
  |                       |                      |
  |---(4) Authorize------>|-------------------->|
  |                       |                      |
  |<---(5) Redirect with code--------------------|
  |       to client app   |                      |
  |                       |                      |
  |---(6) Send code------>|                      |
  |                       |                      |
  |                       |---(7) Exchange------>|
  |                       |    code for token    |
  |                       |                      |
  |                       |<---(8) Access token--|
  |                       |                      |
  |<---(9) Logged in------|                      |
  |                       |                      |
```

#### Step-by-Step Implementation

**Step 1: Request GitHub Identity**
```http
GET https://github.com/login/oauth/authorize
```

**Parameters**:
- `client_id` (required): The client ID from GitHub app registration
- `redirect_uri` (optional): URL to redirect after authorization
- `state` (recommended): Unguessable random string to prevent CSRF
- `scope` (optional): Space-delimited list of scopes (e.g., `user repo`)
- `allow_signup` (optional): Whether to show signup option

**Example URL**:
```
https://github.com/login/oauth/authorize?
  client_id=abc123&
  redirect_uri=https://example.com/callback&
  state=random-state-string&
  scope=user%20repo
```

**Step 2: User Authorizes Application**
User logs in (if needed) and grants requested permissions

**Step 3: GitHub Redirects with Code**
```http
GET https://example.com/callback?code=abc123xyz&state=random-state-string
```

**Client must**:
- Verify `state` matches original value (CSRF protection)
- Extract authorization `code`

**Step 4: Exchange Code for Access Token**
```http
POST https://github.com/login/oauth/access_token
Content-Type: application/json
Accept: application/json

{
  "client_id": "abc123",
  "client_secret": "secret456",
  "code": "abc123xyz",
  "redirect_uri": "https://example.com/callback"
}
```

**Response**:
```json
{
  "access_token": "gho_16C7e42F292c6912E7710c838347Ae178B4a",
  "token_type": "bearer",
  "scope": "user,repo"
}
```

**Step 5: Use Access Token**
```http
GET https://api.github.com/user
Authorization: Bearer gho_16C7e42F292c6912E7710c838347Ae178B4a
```

### 2. Device Flow

**Use Case**: CLI tools, headless devices, limited input devices

#### Flow Steps

```
Device/CLI              GitHub
    |                      |
    |---(1) Request------->|
    |    device code       |
    |                      |
    |<---(2) Device code---|
    |    + User code       |
    |    + Verification URI|
    |                      |
    |---(3) Display------->|
    |    code to user      |
    |                      |
    |    [User visits URI  |
    |     and enters code] |
    |                      |
    |---(4) Poll---------->|
    |    for token         |
    |                      |
    |<---(5) Pending-------|
    |    (continue polling)|
    |                      |
    |---(6) Poll---------->|
    |    for token         |
    |                      |
    |<---(7) Access token--|
    |                      |
```

#### Implementation

**Step 1: Request Device and User Codes**
```http
POST https://github.com/login/device/code
Accept: application/json
Content-Type: application/json

{
  "client_id": "abc123",
  "scope": "repo user"
}
```

**Response**:
```json
{
  "device_code": "3584d83530557fdd1f46af8289938c8ef79f9dc5",
  "user_code": "WDJB-MJHT",
  "verification_uri": "https://github.com/login/device",
  "expires_in": 900,
  "interval": 5
}
```

**Step 2: Display User Code**
```
Please visit: https://github.com/login/device
Enter code: WDJB-MJHT
```

**Step 3: Poll for Access Token**
```http
POST https://github.com/login/oauth/access_token
Accept: application/json
Content-Type: application/json

{
  "client_id": "abc123",
  "device_code": "3584d83530557fdd1f46af8289938c8ef79f9dc5",
  "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
}
```

**Polling Responses**:

*Still waiting*:
```json
{
  "error": "authorization_pending",
  "error_description": "The authorization request is still pending."
}
```

*Success*:
```json
{
  "access_token": "gho_16C7e42F292c6912E7710c838347Ae178B4a",
  "token_type": "bearer",
  "scope": "repo,user"
}
```

*Expired*:
```json
{
  "error": "expired_token",
  "error_description": "The device code has expired."
}
```

**Polling Logic**:
- Poll every `interval` seconds (from response)
- Respect rate limits (typically 5 seconds minimum)
- Stop polling on success, expiration, or user denial
- Maximum 900 seconds (15 minutes) expiration

### 3. Non-Web Application Flow

**Use Case**: Desktop applications, mobile apps (deprecated - use device flow instead)

**Note**: GitHub recommends using Device Flow for non-web applications. This flow is maintained for backward compatibility.

## Token Format and Usage

### Access Token Characteristics

**Token Prefix**: `gho_` (for OAuth apps)
- `gho_`: OAuth app token
- `ghp_`: Personal access token
- `ghs_`: Server-to-server token
- `ghu_`: User access token for GitHub App

**Token Properties**:
- **Length**: Typically 40-45 characters
- **Lifetime**: No expiration by default (until revoked)
- **Format**: Random alphanumeric string
- **Scope**: Permissions granted by user

**Example Token**:
```
gho_16C7e42F292c6912E7710c838347Ae178B4a
```

### Token Usage in API Requests

#### Authorization Header (Recommended)
```http
GET https://api.github.com/user
Authorization: Bearer gho_16C7e42F292c6912E7710c838347Ae178B4a
Accept: application/vnd.github+json
X-GitHub-Api-Version: 2022-11-28
```

#### Alternative: Authorization Header (token prefix)
```http
GET https://api.github.com/user
Authorization: token gho_16C7e42F292c6912E7710c838347Ae178B4a
```

#### Query Parameter (Not Recommended)
```http
GET https://api.github.com/user?access_token=gho_16C7e42F292c6912E7710c838347Ae178B4a
```
**Warning**: Tokens in URLs may be logged in server logs and browser history

### Token Introspection

**Check Token Validity**:
```http
GET https://api.github.com/user
Authorization: Bearer gho_16C7e42F292c6912E7710c838347Ae178B4a
```

**Response includes**:
```json
{
  "login": "octocat",
  "id": 1,
  "type": "User",
  "site_admin": false
}
```

**Check Token Scopes**:
```http
GET https://api.github.com/user
Authorization: Bearer gho_16C7e42F292c6912E7710c838347Ae178B4a
```

Response headers include:
```http
X-OAuth-Scopes: repo, user
X-Accepted-OAuth-Scopes: user
```

## Scopes (Permissions)

### Common Scopes

| Scope | Description | Access |
|-------|-------------|--------|
| `(no scope)` | Public read-only | Public info, public repos |
| `repo` | Full repo access | Read/write public/private repos |
| `repo:status` | Commit status | Read/write commit status |
| `repo_deployment` | Deployment status | Read/write deployment status |
| `public_repo` | Public repos | Read/write public repos only |
| `repo:invite` | Repository invitations | Accept/decline invitations |
| `user` | User profile | Read/write user profile |
| `read:user` | User profile (read) | Read user profile |
| `user:email` | Email addresses | Access email addresses |
| `user:follow` | Follow users | Follow/unfollow users |
| `admin:org` | Full org access | Full organization access |
| `write:org` | Org access | Read/write org membership |
| `read:org` | Org access (read) | Read org membership |
| `workflow` | GitHub Actions | Update workflow files |
| `delete_repo` | Delete repos | Delete repositories |

### Scope Best Practices

1. **Principle of Least Privilege**: Request only scopes needed
2. **Granular Scopes**: Use most specific scope (e.g., `public_repo` instead of `repo`)
3. **Dynamic Scopes**: Request additional scopes only when needed
4. **User Education**: Explain why each scope is needed

**Example**: For a CI/CD app that only needs to update commit status:
```
scope=repo:status
```
Not:
```
scope=repo  # Too broad!
```

## Security Considerations

### CSRF Protection (State Parameter)

**Always use state parameter**:
```javascript
// Generate random state
const state = crypto.randomBytes(16).toString('hex');

// Store in session
session.oauthState = state;

// Include in authorization URL
const authUrl = `https://github.com/login/oauth/authorize?` +
  `client_id=${clientId}&` +
  `redirect_uri=${redirectUri}&` +
  `state=${state}&` +
  `scope=${scopes}`;

// Validate on callback
app.get('/callback', (req, res) => {
  if (req.query.state !== req.session.oauthState) {
    return res.status(403).send('Invalid state');
  }
  // Proceed with code exchange
});
```

### Token Security

**Storage**:
- **Server-side**: Store in encrypted database or secure key management system
- **Client-side**: Use secure storage mechanisms (Keychain, Credential Manager)
- **Never**: Store in localStorage, cookies without HttpOnly/Secure flags

**Transmission**:
- **Always**: Use HTTPS for all OAuth flows
- **Never**: Send tokens in URL parameters (prefer headers)
- **Rotate**: Implement token rotation where possible

**Validation**:
```javascript
// Verify token on each request
async function validateToken(token) {
  try {
    const response = await fetch('https://api.github.com/user', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Accept': 'application/vnd.github+json'
      }
    });

    if (!response.ok) {
      throw new Error('Invalid token');
    }

    return await response.json();
  } catch (error) {
    // Token invalid or expired
    return null;
  }
}
```

### Authorization Code Security

**10-Minute Expiration**:
- Authorization codes expire after 10 minutes
- Use immediately after receiving
- Single-use only (cannot be reused)

**PKCE Support** (Proof Key for Code Exchange):
While not explicitly required by GitHub OAuth Apps, GitHub Apps support PKCE:

```javascript
// Generate code verifier
const codeVerifier = crypto.randomBytes(32).toString('base64url');

// Generate code challenge
const codeChallenge = crypto
  .createHash('sha256')
  .update(codeVerifier)
  .digest('base64url');

// Authorization request
const authUrl = `https://github.com/login/oauth/authorize?` +
  `client_id=${clientId}&` +
  `code_challenge=${codeChallenge}&` +
  `code_challenge_method=S256`;

// Token exchange
const tokenRequest = {
  client_id: clientId,
  code: authCode,
  code_verifier: codeVerifier
};
```

## Rate Limiting

### OAuth API Rate Limits

**Authenticated Requests**:
- **Primary Rate Limit**: 5,000 requests per hour
- **Secondary Rate Limit**: No more than 100 concurrent requests
- **GraphQL**: 5,000 points per hour

**Rate Limit Headers**:
```http
X-RateLimit-Limit: 5000
X-RateLimit-Remaining: 4999
X-RateLimit-Reset: 1372700873
X-RateLimit-Used: 1
X-RateLimit-Resource: core
```

**Handling Rate Limits**:
```javascript
async function makeGitHubRequest(url, token) {
  const response = await fetch(url, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Accept': 'application/vnd.github+json'
    }
  });

  if (response.status === 403) {
    const rateLimitRemaining = response.headers.get('X-RateLimit-Remaining');
    if (rateLimitRemaining === '0') {
      const resetTime = response.headers.get('X-RateLimit-Reset');
      const waitTime = (resetTime * 1000) - Date.now();
      console.log(`Rate limited. Retry after ${waitTime}ms`);
      throw new Error('Rate limit exceeded');
    }
  }

  return response;
}
```

## Best Practices

### 1. Validate User Identity with Each Token

**Why**: Tokens can be reused; verify user hasn't changed permissions
```javascript
// On each significant operation
const user = await validateToken(accessToken);
if (!user || user.login !== expectedUser) {
  throw new Error('Token validation failed');
}
```

### 2. Use Short-Lived Tokens (GitHub Apps)

**Recommendation**: Use GitHub Apps instead of OAuth Apps for:
- Fine-grained permissions
- Short-lived tokens (1 hour expiration)
- Automated workflows

### 3. Implement Token Revocation

**User-Initiated Revocation**:
```http
DELETE https://api.github.com/applications/{client_id}/token
Authorization: Basic {base64(client_id:client_secret)}
Content-Type: application/json

{
  "access_token": "gho_16C7e42F292c6912E7710c838347Ae178B4a"
}
```

**Check Revocation**:
```javascript
app.get('/logout', async (req, res) => {
  await revokeToken(req.session.accessToken);
  req.session.destroy();
  res.redirect('/');
});
```

### 4. Monitor Token Usage

**Logging**:
- Log token creation events
- Log API requests with token IDs (not token values)
- Monitor for unusual patterns
- Alert on high-privilege operations

**Audit**:
```javascript
// Log token usage
function logTokenUsage(tokenId, endpoint, status) {
  auditLog.info({
    tokenId: hashToken(tokenId),  // Never log full token
    endpoint,
    status,
    timestamp: new Date()
  });
}
```

### 5. Handle Token Errors Gracefully

**Error Codes**:
- `401 Unauthorized`: Token invalid or expired
- `403 Forbidden`: Token lacks required scope
- `404 Not Found`: Resource doesn't exist or token lacks access

**Error Handling**:
```javascript
async function githubRequest(endpoint, token) {
  try {
    const response = await fetch(endpoint, {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (response.status === 401) {
      // Token invalid - require re-authentication
      throw new Error('REAUTH_REQUIRED');
    }

    if (response.status === 403) {
      // Check if it's a scope issue
      const scopes = response.headers.get('X-OAuth-Scopes');
      const required = response.headers.get('X-Accepted-OAuth-Scopes');
      throw new Error(`Insufficient scope. Has: ${scopes}, Needs: ${required}`);
    }

    return response;
  } catch (error) {
    console.error('GitHub API error:', error);
    throw error;
  }
}
```

## Comparison: OAuth Apps vs GitHub Apps

| Feature | OAuth Apps | GitHub Apps |
|---------|-----------|-------------|
| **Permissions** | Broad scopes | Fine-grained |
| **Token Lifetime** | No expiration | 1 hour |
| **User Context** | User authorization | App installation |
| **Rate Limits** | 5,000/hour | 5,000/hour per installation |
| **Webhooks** | Limited | Rich webhook support |
| **Best For** | User-centric apps | Automation, CI/CD |

**Recommendation**: Use GitHub Apps for new applications unless you specifically need user-context operations.

## Summary

GitHub's OAuth implementation provides a robust, standards-based authentication system with multiple flows for different use cases.

**Key Takeaways**:
- Use web application flow for server-side apps
- Use device flow for CLI tools and headless devices
- Always use state parameter for CSRF protection
- Request minimal scopes necessary
- Use Authorization header (not URL parameters)
- Consider GitHub Apps for fine-grained permissions

**Security Checklist**:
- [ ] Use HTTPS for all OAuth flows
- [ ] Validate state parameter
- [ ] Request minimal necessary scopes
- [ ] Store tokens securely (never in localStorage)
- [ ] Validate tokens on each significant operation
- [ ] Implement token revocation
- [ ] Handle rate limiting gracefully
- [ ] Log token usage (not token values)
- [ ] Use GitHub Apps for automation (not OAuth Apps)

**Recommendation**: GitHub's OAuth implementation is excellent for user-centric applications. For automation and CI/CD, prefer GitHub Apps with their fine-grained permissions and short-lived tokens.
