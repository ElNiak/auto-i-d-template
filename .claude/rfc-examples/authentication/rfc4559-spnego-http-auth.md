# RFC 4559: SPNEGO-based HTTP Authentication (Negotiate)

**Status**: Informational
**Published**: June 2006
**Category**: HTTP Authentication
**URL**: https://www.rfc-editor.org/rfc/rfc4559.txt

## Overview

RFC 4559 defines the "Negotiate" HTTP authentication scheme using SPNEGO (Simple and Protected GSS-API Negotiation Mechanism). It enables HTTP clients and servers to negotiate authentication mechanisms (primarily Kerberos and NTLM) through the GSS-API framework, providing single sign-on capabilities in enterprise environments.

## Authentication Flow

### Complete Negotiation Sequence

```
Client                                Server
  |                                      |
  |---(1) GET /resource ---------------->|
  |       (no credentials)               |
  |                                      |
  |<--(2) 401 Unauthorized --------------|
  |       WWW-Authenticate: Negotiate    |
  |                                      |
  |---(3) GET /resource ---------------->|
  |       Authorization: Negotiate       |
  |       <base64-InitialContextToken>   |
  |                                      |
  |       [Server calls gss_accept]      |
  |       [Security context incomplete]  |
  |                                      |
  |<--(4) 401 Unauthorized --------------|
  |       WWW-Authenticate: Negotiate    |
  |       <base64-OutputToken>           |
  |                                      |
  |---(5) GET /resource ---------------->|
  |       Authorization: Negotiate       |
  |       <base64-ContextToken>          |
  |                                      |
  |       [Context established]          |
  |                                      |
  |<--(6) 200 OK + Resource -------------|
  |       WWW-Authenticate: Negotiate    |
  |       <base64-FinalToken> (optional) |
  |                                      |
```

### Flow Steps Explained

#### Step 1: Initial Request
Client requests protected resource without credentials

#### Step 2: Authentication Challenge
Server responds with `WWW-Authenticate: Negotiate` to initiate SPNEGO negotiation

#### Step 3: Client Initiates Context
- Client calls `gss_init_sec_context()`
- Generates `InitialContextToken` (contains SPNEGO mechanism negotiation)
- Sends base64-encoded token in `Authorization: Negotiate` header

#### Step 4: Server Responds (if needed)
- Server calls `gss_accept_sec_context()`
- If context incomplete, returns output token
- Client must continue negotiation

#### Step 5: Context Completion
- Client sends final token
- Server validates and establishes security context
- Authentication complete

#### Step 6: Success Response
- Server grants access to resource
- Optional final token for mutual authentication

## Token Format

### Authorization Header Format
```http
Authorization: Negotiate <base64-encoded-gss-api-token>
```

### Challenge Header Format
```http
WWW-Authenticate: Negotiate [<base64-encoded-gss-api-token>]
```

### Token Structure (SPNEGO InitialContextToken)
The token is a GSS-API mechanism token containing SPNEGO negotiation data:

```asn1
InitialContextToken ::=
  [APPLICATION 0] IMPLICIT SEQUENCE {
    thisMech MechType,
    innerContextToken ANY DEFINED BY thisMech
      -- contents mechanism-specific
  }
```

**Components**:
- **thisMech**: OID identifying SPNEGO mechanism (1.3.6.1.5.5.2)
- **innerContextToken**: Mechanism-specific data (e.g., Kerberos ticket, NTLM challenge)

### Example Token Exchange

#### Client Initial Request
```http
GET /docs/protected HTTP/1.1
Host: server.example.com
Authorization: Negotiate YIGZBgkqhkiG9xIBAgICAG+BiTCBhqADAgEFoQMCAQ+ieDB2oAMC
AQWiLzAtoCswKaADAgESoSIEIE5UTE1TU1AAAwAAAAAAAAA4AAAAAAAAAAAAAAAAAAAAAAAA
```

#### Server Response Token
```http
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Negotiate oYGgMIGdoAMKAQChCwYJKoZIhvcSAQICooGEBIGBYIGBBgkqhkiG
9xIBAgICAG+BcTBvoAMKAQChCwYJKoZIhvcSAQICoi8wLaArMCmgAwIBEqEiBCBOVExNU1NA
AwAAAAAAAAA4AAAAAAAAAAAAAAAAAAAAAAAA
```

## Security Considerations

### Authentication Scope
**Important Limitation**:
> "The SPNEGO HTTP authentication facility is only used to provide authentication of a user to a server. It provides no facilities for protecting the HTTP headers or data including the Authorization and WWW-Authenticate headers."

### Security Properties

#### What It Provides
1. **User Authentication**: Verifies user identity to server
2. **Mutual Authentication**: Optional server-to-client verification
3. **Credential Delegation**: Optional (Kerberos only)
4. **Single Sign-On**: Transparent authentication using OS credentials

#### What It Does NOT Provide
1. **Data Confidentiality**: No encryption of HTTP content
2. **Data Integrity**: No protection against tampering
3. **Message Authentication**: Headers can be modified
4. **Replay Protection**: Limited (depends on underlying mechanism)

### Security Requirements

**MUST**:
- Use HTTPS/TLS for confidentiality and integrity
- Validate tokens through GSS-API validation functions
- Complete authentication before processing PUT/POST data
- Use mutual authentication for sensitive operations

**SHOULD**:
- Implement channel bindings to prevent MITM attacks
- Use constrained delegation when delegation is required
- Limit credential delegation scope
- Implement replay detection

**SHOULD NOT**:
- Use over unencrypted connections for sensitive data
- Trust authentication without additional transport security
- Allow delegation without user consent

### Known Vulnerabilities

#### 1. Credential Forwarding
**Risk**: Delegated credentials can be misused
**Mitigation**: Use constrained delegation, limit delegation scope

#### 2. Man-in-the-Middle
**Risk**: MITM can relay authentication
**Mitigation**: Use TLS with channel bindings (RFC 5929)

#### 3. Downgrade Attacks
**Risk**: SPNEGO can negotiate to weaker mechanism (e.g., NTLM)
**Mitigation**: Configure allowed mechanisms, prefer Kerberos

## Technical Requirements

### Server Requirements

#### HTTP Server Configuration
1. **Principal Name**: Server uses principal name format `HTTP/<hostname>`
   - Example: `HTTP/server.example.com`
   - Must match DNS hostname
   - Required for Kerberos authentication

2. **GSS-API Integration**:
   ```c
   // Server accepts security context
   gss_accept_sec_context(
       &min_stat,
       &context,
       server_creds,      // HTTP/hostname principal
       &input_token,      // From Authorization header
       GSS_C_NO_CHANNEL_BINDINGS,
       &client_name,      // Output: authenticated client identity
       &mech_type,        // Output: mechanism used
       &output_token,     // Output: token to return (if any)
       &ret_flags,        // Output: context flags
       &time_rec,         // Output: context lifetime
       &delegated_cred    // Output: delegated credentials (if any)
   );
   ```

3. **Token Handling**:
   - Extract base64 token from `Authorization: Negotiate` header
   - Decode base64 to binary
   - Pass to `gss_accept_sec_context()`
   - If output token generated, encode base64 and return in `WWW-Authenticate`

4. **Context Management**:
   - Maintain security context across multiple requests
   - Associate context with HTTP session
   - Clean up contexts on session termination

#### Authentication Flow Logic
```python
def handle_negotiate_auth(request):
    # Extract token from Authorization header
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Negotiate '):
        return 401, {'WWW-Authenticate': 'Negotiate'}

    input_token = base64_decode(auth_header[10:])

    # Accept security context
    context, output_token, client_name, complete = gss_accept_context(
        server_principal='HTTP/server.example.com',
        input_token=input_token
    )

    if not complete:
        # More tokens needed
        response_token = base64_encode(output_token)
        return 401, {'WWW-Authenticate': f'Negotiate {response_token}'}

    # Authentication complete
    request.user = client_name
    if output_token:
        # Include final token (for mutual auth)
        response_token = base64_encode(output_token)
        return 200, {'WWW-Authenticate': f'Negotiate {response_token}'}

    return 200, {}
```

### Client Requirements

#### GSS-API Integration
```c
// Client initiates security context
gss_init_sec_context(
    &min_stat,
    cred_handle,           // Client credentials (or GSS_C_NO_CREDENTIAL)
    &context,
    target_name,           // "HTTP@server.example.com"
    GSS_C_NO_OID,          // Let SPNEGO choose mechanism
    GSS_C_MUTUAL_FLAG | GSS_C_REPLAY_FLAG,
    0,                     // Default lifetime
    GSS_C_NO_CHANNEL_BINDINGS,
    &input_token,          // From server (or GSS_C_NO_BUFFER initially)
    &actual_mech,          // Output: mechanism used
    &output_token,         // Output: token to send
    &ret_flags,            // Output: context flags
    &time_rec              // Output: context lifetime
);
```

#### Client Flow Logic
```python
def negotiate_auth(url):
    # First request - no credentials
    response = http_get(url)

    if response.status == 401 and 'WWW-Authenticate: Negotiate' in response.headers:
        # Initialize security context
        target = f"HTTP@{parse_hostname(url)}"
        context, output_token, complete = gss_init_context(
            target_name=target,
            input_token=None
        )

        # Send initial token
        auth_header = f"Negotiate {base64_encode(output_token)}"
        response = http_get(url, headers={'Authorization': auth_header})

        # Handle multi-round negotiation
        while response.status == 401 and not complete:
            server_token = extract_negotiate_token(response)
            context, output_token, complete = gss_init_context(
                context=context,
                input_token=base64_decode(server_token)
            )

            auth_header = f"Negotiate {base64_encode(output_token)}"
            response = http_get(url, headers={'Authorization': auth_header})

        return response
```

### Proxy Authentication
**Note**: RFC 4559 explicitly states:
> "This mechanism is for authentication of users to origin servers. The use of this mechanism to authenticate to proxies is not specified by this document."

However, some implementations support proxy authentication using:
- `Proxy-Authenticate: Negotiate`
- `Proxy-Authorization: Negotiate <token>`

## Supported Mechanisms

### Primary: Kerberos (GSS-API Kerberos V5)
**OID**: 1.2.840.113554.1.2.2

**Characteristics**:
- Mutual authentication supported
- Ticket-based authentication
- No password transmission
- Supports credential delegation
- Requires KDC infrastructure

**Token Content**: Kerberos AP-REQ and AP-REP messages

### Secondary: NTLM
**OID**: 1.3.6.1.4.1.311.2.2.10

**Characteristics**:
- Challenge-response protocol
- Windows domain authentication
- No mutual authentication (NTLM v1)
- NTLMv2 provides improved security
- No delegation support

**Token Content**: NTLM NEGOTIATE, CHALLENGE, AUTHENTICATE messages

### Mechanism Negotiation
SPNEGO allows client and server to negotiate supported mechanisms:

1. Client proposes list of mechanisms in `InitialContextToken`
2. Server selects preferred mechanism from list
3. Server returns selected mechanism in response
4. Subsequent tokens use selected mechanism

**Example Preference Order**:
1. Kerberos (most secure)
2. NTLMv2
3. NTLMv1 (deprecated, avoid if possible)

## Use Cases

### 1. Enterprise Single Sign-On (SSO)
**Scenario**: Intranet web applications in Windows domain
**Implementation**:
- Client: Windows with Active Directory integration
- Server: IIS or Apache with Kerberos support
- User authenticates transparently using domain credentials
- No password prompt required

### 2. Cross-Platform Authentication
**Scenario**: Mixed Windows/Linux environment
**Implementation**:
- Kerberos realm spanning multiple platforms
- Linux clients with `kinit` for ticket acquisition
- Web applications use GSS-API for authentication
- Single identity across platforms

### 3. Cloud Service Integration
**Scenario**: Hybrid cloud with on-premises AD
**Implementation**:
- Azure AD Connect or AD FS integration
- SPNEGO for legacy application authentication
- Modern applications use OAuth/SAML federation

## Implementation Notes

### Browser Support
- **Internet Explorer/Edge**: Native support for Windows Integrated Authentication
- **Firefox**: Configure `network.negotiate-auth.trusted-uris`
- **Chrome**: Uses OS-level authentication (automatic on Windows)
- **Safari**: Supports Kerberos on macOS

### Server Implementation Examples

#### Apache (mod_auth_gssapi)
```apache
<Location "/protected">
    AuthType GSSAPI
    AuthName "Kerberos Login"
    GssapiCredStore keytab:/etc/httpd/http.keytab
    GssapiCredStore client_keytab:/etc/httpd/http.keytab
    Require valid-user
</Location>
```

#### IIS (Windows Integrated Authentication)
```xml
<system.webServer>
  <security>
    <authentication>
      <windowsAuthentication enabled="true">
        <providers>
          <add value="Negotiate" />
          <add value="NTLM" />
        </providers>
      </windowsAuthentication>
    </authentication>
  </security>
</system.webServer>
```

#### Nginx (via auth_request module)
```nginx
location /protected {
    auth_request /auth;
    error_page 401 = @error401;
}

location = /auth {
    internal;
    proxy_pass http://gssapi-auth-backend;
    proxy_pass_request_body off;
    proxy_set_header Content-Length "";
    proxy_set_header X-Original-URI $request_uri;
}
```

## Migration and Interoperability

### From Basic/Digest Authentication
1. Deploy SPNEGO alongside existing methods
2. Configure client browser support
3. Test with pilot user group
4. Gradually enforce SPNEGO for all clients
5. Deprecate Basic/Digest (with TLS still required)

### With Modern Protocols
- **OAuth 2.0**: Use SPNEGO for initial authentication, issue OAuth tokens
- **SAML**: SPNEGO as authentication method for SAML assertion generation
- **OpenID Connect**: SPNEGO as upstream authentication provider

## Related Specifications

- **RFC 4178**: SPNEGO (Simple and Protected GSS-API Negotiation Mechanism)
- **RFC 4120**: Kerberos V5
- **RFC 2743**: GSS-API (Generic Security Service Application Program Interface)
- **RFC 2744**: GSS-API C-bindings
- **RFC 5929**: Channel Bindings for TLS

## Summary

SPNEGO-based HTTP Authentication (Negotiate) provides enterprise-grade single sign-on capabilities for HTTP applications through GSS-API integration. It's particularly well-suited for corporate environments with existing Kerberos or Active Directory infrastructure.

**Key Strengths**:
- Transparent authentication (no password prompts)
- Strong security with Kerberos
- Multi-platform support via GSS-API
- Mutual authentication capability

**Key Limitations**:
- Authentication only (no data protection - use TLS)
- Requires infrastructure (KDC/AD)
- Complex deployment and troubleshooting
- Limited to enterprise environments

**Recommendation**: Ideal for intranet applications in enterprise environments with existing Kerberos/AD infrastructure. Always use with TLS for data protection. For internet-facing applications, consider OAuth 2.0 or OpenID Connect instead.
