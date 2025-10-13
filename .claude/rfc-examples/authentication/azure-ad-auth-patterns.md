# Azure AD Authentication Patterns (Microsoft Identity Platform)

**Source**: Microsoft Documentation
**Category**: Company Authentication Pattern
**URL**: https://learn.microsoft.com/en-us/azure/active-directory/develop/

## Overview

Azure AD (now Microsoft Entra ID) provides a comprehensive identity platform built on industry-standard protocols (OAuth 2.0 and OpenID Connect). It supports multiple authentication flows for various application types, from single-page apps to daemon services.

**Core Principle**: All architectures based on OAuth 2.0 and OpenID Connect standards.

## Authentication Flows

### 1. Authorization Code Flow

**Use Case**: Web applications with backend server

**Characteristics**:
- Most secure flow
- Uses PKCE for public clients
- Supports refresh tokens
- Recommended for most scenarios

#### Flow Diagram

```
User Agent          Client App       Azure AD           Resource API
    |                   |                |                    |
    |---(1) Login------>|                |                    |
    |                   |                |                    |
    |                   |---(2) Authorize|                    |
    |                   |    Request---->|                    |
    |                   |                |                    |
    |<-----------(3) Consent Page--------|                    |
    |                   |                |                    |
    |---(4) Grant------>|--------------->|                    |
    |    Consent        |                |                    |
    |                   |                |                    |
    |<---(5) Auth code--|----------------|                    |
    |                   |                |                    |
    |---(6) Send code-->|                |                    |
    |                   |                |                    |
    |                   |---(7) Exchange |                    |
    |                   |    code+PKCE-->|                    |
    |                   |                |                    |
    |                   |<--(8) Tokens---|                    |
    |                   |                |                    |
    |                   |---(9) API req with token---------->|
    |                   |                |                    |
    |                   |<--(10) Protected resource----------|
    |                   |                |                    |
```

#### Implementation Steps

**Step 1: Authorization Request**
```http
GET https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize?
  client_id=<client-id>
  &response_type=code
  &redirect_uri=https://app.example.com/callback
  &response_mode=query
  &scope=openid%20profile%20email%20https://graph.microsoft.com/.default
  &state=<state-value>
  &code_challenge=<pkce-challenge>
  &code_challenge_method=S256
```

**Parameters**:
- `client_id`: Application (client) ID from Azure AD registration
- `response_type`: `code` for authorization code
- `redirect_uri`: Registered callback URL
- `scope`: Space-delimited permissions (OpenID + resource scopes)
- `state`: CSRF protection token
- `code_challenge`: PKCE challenge (SHA256 hash of verifier)
- `code_challenge_method`: `S256` (SHA256) or `plain`

**Step 2: User Consent**
Azure AD displays consent screen if needed (first time or new permissions)

**Step 3: Authorization Code Response**
```http
HTTP/1.1 302 Found
Location: https://app.example.com/callback?
  code=0.AQEAYoC...authorization-code...qKxw
  &state=<state-value>
```

**Step 4: Token Exchange**
```http
POST https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token
Content-Type: application/x-www-form-urlencoded

client_id=<client-id>
&scope=https://graph.microsoft.com/.default
&code=0.AQEAYoC...authorization-code...qKxw
&redirect_uri=https://app.example.com/callback
&grant_type=authorization_code
&code_verifier=<pkce-verifier>
&client_secret=<client-secret>  // Only for confidential clients
```

**Step 5: Token Response**
```json
{
  "token_type": "Bearer",
  "scope": "User.Read profile openid email",
  "expires_in": 3599,
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "0.AQEAYoC8taZ...",
  "id_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### 2. Implicit Flow (Deprecated)

**Status**: Deprecated - DO NOT USE for new applications

**Use Case**: Previously for SPAs (now use Auth Code + PKCE)

**Why Deprecated**:
- Tokens exposed in URL fragment
- No refresh token support
- Security risks with XSS attacks

**Migration**: Use Authorization Code Flow with PKCE

### 3. Client Credentials Flow

**Use Case**: Daemon services, background jobs, server-to-server

**Characteristics**:
- No user context
- App-only authentication
- Uses client secret or certificate
- No interactive login

#### Flow Diagram

```
Client App                     Azure AD
    |                              |
    |---(1) Token Request--------->|
    |     (client_id + secret)     |
    |                              |
    |     [Azure AD validates]     |
    |     [Checks app permissions] |
    |                              |
    |<---(2) Access Token----------|
    |                              |
    |---(3) API Request----------->|
    |     with access token        |
    |                              |
```

#### Implementation

**Token Request**:
```http
POST https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token
Content-Type: application/x-www-form-urlencoded

client_id=<client-id>
&scope=https://graph.microsoft.com/.default
&client_secret=<client-secret>
&grant_type=client_credentials
```

**Response**:
```json
{
  "token_type": "Bearer",
  "expires_in": 3599,
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Note**: No `refresh_token` or `id_token` (app-only context)

### 4. Device Code Flow

**Use Case**: Input-constrained devices (IoT, CLI tools, smart TVs)

**Characteristics**:
- Two-device authentication
- User authenticates on separate device
- Polling mechanism for token

#### Flow Diagram

```
Device              Azure AD           User Browser
  |                     |                    |
  |---(1) Device------->|                    |
  |     code request    |                    |
  |                     |                    |
  |<---(2) Device code--|                    |
  |     + User code     |                    |
  |                     |                    |
  |---(3) Display------>|---(4) Navigate---->|
  |     to user         |     to URL         |
  |     "Visit URL,     |                    |
  |      enter code"    |                    |
  |                     |                    |
  |                     |<---(5) Enter code--|
  |                     |     and sign in    |
  |                     |                    |
  |---(6) Poll--------->|                    |
  |     for token       |                    |
  |                     |                    |
  |<---(7) Pending------|                    |
  |     (retry)         |                    |
  |                     |                    |
  |---(8) Poll--------->|                    |
  |                     |                    |
  |<---(9) Access token-|                    |
  |                     |                    |
```

#### Implementation

**Step 1: Request Device Code**
```http
POST https://login.microsoftonline.com/{tenant}/oauth2/v2.0/devicecode
Content-Type: application/x-www-form-urlencoded

client_id=<client-id>
&scope=https://graph.microsoft.com/.default
```

**Response**:
```json
{
  "user_code": "CNGBK-QFT7N",
  "device_code": "CAQABAAEAAADCoMpjJX...",
  "verification_uri": "https://microsoft.com/devicelogin",
  "expires_in": 900,
  "interval": 5,
  "message": "To sign in, use a web browser to open the page https://microsoft.com/devicelogin and enter the code CNGBK-QFT7N to authenticate."
}
```

**Step 2: Poll for Token**
```http
POST https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token
Content-Type: application/x-www-form-urlencoded

grant_type=urn:ietf:params:oauth:grant-type:device_code
&client_id=<client-id>
&device_code=CAQABAAEAAADCoMpjJX...
```

**Polling Responses**:

*Still waiting*:
```json
{
  "error": "authorization_pending",
  "error_description": "AADSTS70016: Pending end-user authorization..."
}
```

*Success*:
```json
{
  "token_type": "Bearer",
  "scope": "User.Read",
  "expires_in": 3599,
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "0.AQEAYoC8taZ...",
  "id_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### 5. Resource Owner Password Credentials (ROPC) Flow

**Status**: Not Recommended

**Use Case**: Legacy applications, migration scenarios only

**Characteristics**:
- User provides username/password to app
- App sends credentials to Azure AD
- No MFA or conditional access support
- Security risks

**Why Not Recommended**:
- Violates OAuth 2.0 security principles
- No modern authentication features (MFA, conditional access)
- Credentials exposed to application
- Limited to work/school accounts

**Implementation** (for reference only):
```http
POST https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token
Content-Type: application/x-www-form-urlencoded

client_id=<client-id>
&scope=https://graph.microsoft.com/.default
&username=user@example.com
&password=<password>
&grant_type=password
```

**Recommendation**: Migrate to Authorization Code Flow or Device Flow

### 6. On-Behalf-Of (OBO) Flow

**Use Case**: Middle-tier service calling another API on behalf of user

**Characteristics**:
- Preserves user identity across services
- Token exchange mechanism
- Maintains consent and permissions

#### Flow Diagram

```
Client          Web API              Azure AD         Backend API
  |                |                    |                   |
  |---(1) Request->|                    |                   |
  |    + token     |                    |                   |
  |                |                    |                   |
  |                |---(2) Exchange---->|                   |
  |                |    user token      |                   |
  |                |    for new token   |                   |
  |                |                    |                   |
  |                |<---(3) New token---|                   |
  |                |                    |                   |
  |                |---(4) Call Backend------------------->|
  |                |    with new token  |                   |
  |                |                    |                   |
  |                |<---(5) Response---------------------|
  |                |                    |                   |
  |<---(6) Result--|                    |                   |
  |                |                    |                   |
```

#### Implementation

**Token Exchange Request**:
```http
POST https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token
Content-Type: application/x-www-form-urlencoded

grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer
&client_id=<web-api-client-id>
&client_secret=<web-api-secret>
&assertion=<access-token-from-client>
&scope=https://backend-api.example.com/.default
&requested_token_use=on_behalf_of
```

**Response**:
```json
{
  "token_type": "Bearer",
  "scope": "https://backend-api.example.com/.default",
  "expires_in": 3599,
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "0.AQEAYoC8taZ..."
}
```

## Token Types

### 1. Access Token

**Purpose**: Authorization for API access

**Format**: JWT (JSON Web Token)

**Structure**:
```json
{
  "header": {
    "typ": "JWT",
    "alg": "RS256",
    "kid": "key-id"
  },
  "payload": {
    "aud": "https://graph.microsoft.com",
    "iss": "https://sts.windows.net/{tenant-id}/",
    "iat": 1516239022,
    "exp": 1516242622,
    "sub": "user-object-id",
    "scp": "User.Read Mail.Read",
    "roles": ["Admin"],
    "appid": "client-id",
    "ver": "2.0"
  },
  "signature": "..."
}
```

**Key Claims**:
- `aud`: Audience (intended recipient)
- `iss`: Issuer (Azure AD)
- `exp`: Expiration time (Unix timestamp)
- `scp`: Scopes (delegated permissions)
- `roles`: App roles (application permissions)
- `sub`: Subject (user identifier)

**Lifetime**: Default 1 hour (configurable)

### 2. ID Token

**Purpose**: User identity information (OpenID Connect)

**Format**: JWT

**Structure**:
```json
{
  "header": {...},
  "payload": {
    "aud": "client-id",
    "iss": "https://login.microsoftonline.com/{tenant-id}/v2.0",
    "iat": 1516239022,
    "exp": 1516242622,
    "sub": "user-object-id",
    "name": "John Doe",
    "preferred_username": "john@example.com",
    "email": "john@example.com",
    "oid": "user-object-id",
    "tid": "tenant-id",
    "ver": "2.0"
  },
  "signature": "..."
}
```

**Key Claims**:
- `name`: User's display name
- `preferred_username`: Primary identifier (email)
- `oid`: User's object ID in Azure AD
- `tid`: Tenant ID

**Usage**: Client-side user info display (DO NOT use for authorization)

### 3. Refresh Token

**Purpose**: Obtain new access tokens without user interaction

**Format**: Opaque string (not JWT)

**Characteristics**:
- Long-lived (90 days default, can be extended)
- Single-use (new refresh token issued with each use)
- Revocable by admin
- Requires secure storage

**Usage**:
```http
POST https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token
Content-Type: application/x-www-form-urlencoded

client_id=<client-id>
&scope=https://graph.microsoft.com/.default
&refresh_token=0.AQEAYoC8taZ...
&grant_type=refresh_token
&client_secret=<client-secret>  // Only for confidential clients
```

**Response**:
```json
{
  "token_type": "Bearer",
  "scope": "User.Read Mail.Read",
  "expires_in": 3599,
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "0.AQEAYoC8taZ..."  // New refresh token
}
```

## Security Best Practices

### 1. Use PKCE for Public Clients

**Requirement**: All public clients MUST use PKCE

**Implementation**:
```javascript
// Generate code verifier (43-128 characters)
const codeVerifier = generateRandomString(128);

// Generate code challenge (SHA256 hash)
const codeChallenge = base64url(sha256(codeVerifier));

// Authorization request
const authUrl = `https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize?` +
  `client_id=${clientId}&` +
  `response_type=code&` +
  `redirect_uri=${redirectUri}&` +
  `scope=${scopes}&` +
  `code_challenge=${codeChallenge}&` +
  `code_challenge_method=S256`;

// Token exchange (include verifier)
const tokenRequest = {
  client_id: clientId,
  code: authorizationCode,
  redirect_uri: redirectUri,
  grant_type: 'authorization_code',
  code_verifier: codeVerifier
};
```

### 2. Token Storage

**Recommendations**:
- **Backend**: Encrypted database, Azure Key Vault
- **SPA**: Memory only (no localStorage/sessionStorage)
- **Native App**: OS-provided secure storage (Keychain, Credential Manager)
- **Never**: Plain text, client-side storage for confidential data

**Example** (Node.js backend):
```javascript
// Store tokens server-side in encrypted session
app.post('/callback', async (req, res) => {
  const tokens = await exchangeCodeForTokens(req.body.code);

  // Store in encrypted session
  req.session.accessToken = encrypt(tokens.access_token);
  req.session.refreshToken = encrypt(tokens.refresh_token);

  res.redirect('/dashboard');
});
```

### 3. Token Validation

**Access Token Validation**:
```javascript
const jwt = require('jsonwebtoken');
const jwksClient = require('jwks-rsa');

// Configure JWKS client
const client = jwksClient({
  jwksUri: 'https://login.microsoftonline.com/{tenant}/discovery/v2.0/keys'
});

// Get signing key
function getKey(header, callback) {
  client.getSigningKey(header.kid, (err, key) => {
    const signingKey = key.publicKey || key.rsaPublicKey;
    callback(null, signingKey);
  });
}

// Validate token
function validateAccessToken(token) {
  return new Promise((resolve, reject) => {
    jwt.verify(token, getKey, {
      audience: 'https://graph.microsoft.com',
      issuer: `https://sts.windows.net/{tenant-id}/`,
      algorithms: ['RS256']
    }, (err, decoded) => {
      if (err) reject(err);
      else resolve(decoded);
    });
  });
}
```

**Validation Checklist**:
- [ ] Signature valid (using public key from JWKS)
- [ ] `iss` matches Azure AD issuer
- [ ] `aud` matches expected audience
- [ ] `exp` not expired
- [ ] `nbf` (not before) time passed
- [ ] Scopes/roles sufficient for operation

### 4. Least Privilege Principle

**Scope Selection**:
```javascript
// BAD - Requesting too many permissions
const scopes = ['https://graph.microsoft.com/.default'];

// GOOD - Specific permissions only
const scopes = ['User.Read', 'Mail.Send'];
```

**Dynamic Consent**:
```javascript
// Request additional scopes when needed
async function sendEmail() {
  try {
    // Try with existing token
    await callGraphAPI(currentToken);
  } catch (error) {
    if (error.status === 403) {
      // Request additional permission
      const newToken = await acquireTokenInteractive(['Mail.Send']);
      await callGraphAPI(newToken);
    }
  }
}
```

### 5. Conditional Access and MFA Support

**Implementation**:
- Use Authorization Code Flow (supports modern auth)
- Avoid ROPC flow (no MFA support)
- Handle authentication challenges

**Challenge Handling**:
```javascript
async function callAPI(token) {
  const response = await fetch(apiUrl, {
    headers: { 'Authorization': `Bearer ${token}` }
  });

  if (response.status === 401) {
    const authHeader = response.headers.get('WWW-Authenticate');
    if (authHeader.includes('claims=')) {
      // Extract claims challenge
      const claims = extractClaims(authHeader);

      // Reacquire token with claims
      const newToken = await acquireToken({
        scopes: ['User.Read'],
        claims: claims
      });

      return callAPI(newToken);
    }
  }

  return response;
}
```

## Microsoft Authentication Library (MSAL)

### Why Use MSAL

**Benefits**:
- Automatic token caching
- Automatic token refresh
- PKCE implementation
- Error handling
- Cross-platform support

**Supported Platforms**:
- JavaScript/TypeScript (MSAL.js)
- .NET (MSAL.NET)
- Python (MSAL Python)
- Java (MSAL Java)
- iOS (MSAL iOS)
- Android (MSAL Android)
- Node.js (MSAL Node)

### MSAL.js Example (SPA)

**Installation**:
```bash
npm install @azure/msal-browser
```

**Configuration**:
```javascript
import { PublicClientApplication } from '@azure/msal-browser';

const msalConfig = {
  auth: {
    clientId: '<client-id>',
    authority: 'https://login.microsoftonline.com/<tenant-id>',
    redirectUri: 'https://app.example.com'
  },
  cache: {
    cacheLocation: 'sessionStorage',
    storeAuthStateInCookie: false
  }
};

const msalInstance = new PublicClientApplication(msalConfig);
await msalInstance.initialize();
```

**Login**:
```javascript
// Interactive login
const loginRequest = {
  scopes: ['User.Read', 'Mail.Read']
};

try {
  const loginResponse = await msalInstance.loginPopup(loginRequest);
  console.log('Access Token:', loginResponse.accessToken);
} catch (error) {
  console.error('Login failed:', error);
}
```

**Acquire Token Silently**:
```javascript
// Try silent token acquisition first
const tokenRequest = {
  scopes: ['User.Read'],
  account: msalInstance.getAllAccounts()[0]
};

try {
  const response = await msalInstance.acquireTokenSilent(tokenRequest);
  return response.accessToken;
} catch (error) {
  if (error instanceof InteractionRequiredAuthError) {
    // Fall back to interactive
    const response = await msalInstance.acquireTokenPopup(tokenRequest);
    return response.accessToken;
  }
  throw error;
}
```

### MSAL.NET Example (Web App)

**Installation**:
```bash
dotnet add package Microsoft.Identity.Web
```

**Configuration** (Program.cs):
```csharp
using Microsoft.Identity.Web;

var builder = WebApplication.CreateBuilder(args);

// Add authentication
builder.Services.AddAuthentication(OpenIdConnectDefaults.AuthenticationScheme)
    .AddMicrosoftIdentityWebApp(builder.Configuration.GetSection("AzureAd"));

// Add authorization
builder.Services.AddAuthorization();

var app = builder.Build();

app.UseAuthentication();
app.UseAuthorization();
```

**Configuration** (appsettings.json):
```json
{
  "AzureAd": {
    "Instance": "https://login.microsoftonline.com/",
    "TenantId": "<tenant-id>",
    "ClientId": "<client-id>",
    "ClientSecret": "<client-secret>",
    "CallbackPath": "/signin-oidc"
  }
}
```

**Protected Controller**:
```csharp
[Authorize]
public class ProfileController : Controller
{
    private readonly ITokenAcquisition _tokenAcquisition;

    public ProfileController(ITokenAcquisition tokenAcquisition)
    {
        _tokenAcquisition = tokenAcquisition;
    }

    public async Task<IActionResult> Index()
    {
        // Acquire token for Microsoft Graph
        string[] scopes = new[] { "User.Read" };
        string accessToken = await _tokenAcquisition.GetAccessTokenForUserAsync(scopes);

        // Call Microsoft Graph
        var graphClient = new GraphServiceClient(
            new DelegateAuthenticationProvider((requestMessage) =>
            {
                requestMessage.Headers.Authorization =
                    new AuthenticationHeaderValue("Bearer", accessToken);
                return Task.CompletedTask;
            }));

        var user = await graphClient.Me.Request().GetAsync();
        return View(user);
    }
}
```

## Common Patterns

### Pattern 1: SPA + Web API

**Architecture**:
```
Browser (SPA) → Azure AD (login) → Browser gets token
Browser → Web API (with token) → API validates token
```

**Implementation**:
- SPA uses MSAL.js with Authorization Code + PKCE
- API validates JWT tokens
- Token caching in memory (SPA) and backend (API)

### Pattern 2: Web App (Server-Side)

**Architecture**:
```
User → Web App → Azure AD (login redirect)
Azure AD → Web App (callback with code)
Web App → Azure AD (exchange code for token)
Web App stores token server-side
```

**Implementation**:
- ASP.NET Core with Microsoft.Identity.Web
- Server-side session for tokens
- Automatic token refresh

### Pattern 3: Daemon/Background Service

**Architecture**:
```
Service → Azure AD (client credentials)
Azure AD → Service (access token)
Service → Microsoft Graph/API (with token)
```

**Implementation**:
- Client credentials flow
- Certificate-based authentication (preferred)
- Token caching with expiration

### Pattern 4: Mobile App

**Architecture**:
```
Mobile App → System Browser (Azure AD login)
System Browser → Mobile App (callback with code)
Mobile App → Azure AD (exchange code for token)
Mobile App stores token in secure storage
```

**Implementation**:
- MSAL for iOS/Android
- System browser for authentication (not WebView)
- Secure storage (Keychain/Keystore)

## Summary

Azure AD (Microsoft Entra ID) provides a comprehensive, standards-based authentication platform with multiple flows for diverse application scenarios.

**Key Strengths**:
- Standards-based (OAuth 2.0, OpenID Connect)
- Rich MSAL library support across platforms
- Enterprise features (conditional access, MFA, SSO)
- Fine-grained permissions (scopes and roles)
- Comprehensive token management

**Recommended Flows by Scenario**:
- **Web Apps**: Authorization Code Flow
- **SPAs**: Authorization Code Flow + PKCE
- **Mobile Apps**: Authorization Code Flow + PKCE (system browser)
- **Desktop Apps**: Authorization Code Flow + PKCE or Device Flow
- **Daemons**: Client Credentials Flow
- **APIs calling APIs**: On-Behalf-Of Flow

**Security Checklist**:
- [ ] Always use PKCE for public clients
- [ ] Validate all tokens (signature, issuer, audience, expiration)
- [ ] Use MSAL libraries (don't implement OAuth manually)
- [ ] Store tokens securely (never in localStorage for SPAs)
- [ ] Request minimal necessary scopes
- [ ] Implement proper error handling
- [ ] Support conditional access and MFA
- [ ] Avoid deprecated flows (Implicit, ROPC)
- [ ] Use refresh tokens for long-lived sessions
- [ ] Implement token caching to reduce auth requests

**Recommendation**: Use MSAL libraries for all Azure AD integrations. They handle complex scenarios (token caching, refresh, PKCE, error handling) automatically and are maintained by Microsoft with security updates.
