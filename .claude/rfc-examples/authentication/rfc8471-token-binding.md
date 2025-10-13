# RFC 8471: Token Binding over HTTP

**Status**: Standards Track
**Published**: October 2018
**Category**: Security
**URL**: https://www.rfc-editor.org/rfc/rfc8471.txt

## Overview

Token Binding is a security mechanism that cryptographically binds security tokens (like cookies and OAuth tokens) to the TLS layer, preventing token export and replay attacks. It ensures that even if a token is stolen, it cannot be used from a different TLS connection.

## Authentication Flow

### Initial Setup
1. **Key Generation**: Client generates cryptographic key pair for target server
2. **TLS Negotiation**: Client and server negotiate token binding support during TLS handshake
3. **Token Binding Establishment**: Client proves possession of private key

### Per-Request Flow
1. **TLS Connection**: Client establishes TLS connection to server
2. **Key Proof**: Client generates signature over Exported Keying Material (EKM) from TLS
3. **Token Binding Message**: Client includes Token Binding message in HTTP request
4. **Validation**: Server validates signature and binds tokens to this key
5. **Token Issuance**: Server issues tokens bound to client's Token Binding ID

```
Client                                Server
  |                                      |
  |---(1) TLS Handshake + Token -------->|
  |       Binding negotiation            |
  |                                      |
  |<--(2) TLS + Token Binding params ----|
  |                                      |
  |---(3) HTTP + Sec-Token-Binding ----->|
  |       Header (signed proof)          |
  |                                      |
  |       [Server validates signature]   |
  |       [Server binds tokens to key]   |
  |                                      |
  |<--(4) HTTP Response + Token ---------|
  |       (bound to Token Binding ID)    |
  |                                      |
```

## Token Binding Format

### HTTP Header Structure
```http
Sec-Token-Binding: <base64-encoded-token-binding-message>
```

### Token Binding Message Structure
```
struct {
    TokenBinding tokenbindings<132..2^16-1>;
} TokenBindingMessage;

struct {
    TokenBindingType tokenbinding_type;
    TokenBindingID tokenbindingid;
    opaque signature<64..2^16-1>;
    Extension extensions<0..2^16-1>;
} TokenBinding;
```

### Token Binding Types

#### 1. provided_token_binding (0)
- Used for establishing binding with the server receiving the token
- Most common type for direct authentication

#### 2. referred_token_binding (1)
- Used when client is obtaining token from one server to use at another
- Enables federated authentication scenarios
- Example: Client gets token from IdP to use at Service Provider

### Token Binding ID Structure
```
struct {
    TokenBindingKeyParameters key_parameters;
    uint16 key_length;
    opaque public_key<1..2^16-1>;
} TokenBindingID;
```

**Key Components**:
- **key_parameters**: Identifies the signature algorithm (e.g., `ecdsap256`, `rsa2048_pss`)
- **key_length**: Length of public key in bytes
- **public_key**: The client's public key in raw format

### Example Token Binding Header
```http
Sec-Token-Binding: AIkAAgBBQLTsvK4....base64data....DsH2
```

Decoded structure:
- Token Binding Type: `provided_token_binding`
- Key Parameters: `ecdsap256`
- Public Key: [256-bit EC public key]
- Signature: [ECDSA signature over EKM]

## Cryptographic Details

### Signature Calculation
1. **Extract EKM**: Get Exported Keying Material from TLS connection
   - Length: 32 bytes
   - Label: "EXPORTER-Token-Binding"
   - Context: Empty string

2. **Construct Message**: Create signing input
   ```
   SignedData = key_parameters || key_length || public_key || EKM
   ```

3. **Generate Signature**: Sign with client's private key
   - Algorithm: As negotiated in TLS (e.g., ECDSA with P-256)
   - Output: Signature over SignedData

### Supported Key Parameters
- `rsa2048_pkcs1.5` (0)
- `rsa2048_pss` (1)
- `ecdsap256` (2) - RECOMMENDED

## Security Considerations

### Threat Mitigation

#### 1. Token Export Prevention
**Problem**: Attacker steals token and uses it from different connection
**Solution**: Token cryptographically bound to specific TLS connection
**Result**: Stolen token unusable without private key

#### 2. Token Replay Prevention
**Problem**: Attacker replays captured token
**Solution**: Each TLS connection has unique EKM; signature includes EKM
**Result**: Replayed tokens fail validation due to EKM mismatch

#### 3. Man-in-the-Middle Prevention
**Problem**: MITM intercepts and attempts to use token
**Solution**: Token bound to client's key pair; MITM lacks private key
**Result**: MITM cannot prove key possession

### Security Requirements

**Token Binding Key Protection**:
- Private keys MUST be protected with same or stronger security as TLS keys
- Private keys SHOULD NOT be exportable
- RECOMMENDED: Use hardware security modules (HSM) or TPM

**Key Scope**:
- Keys SHOULD be scoped per origin (scheme + host + port)
- Key scope MUST NOT exceed token scope
- Single key MAY be used for multiple tokens on same origin

**Validation Requirements**:
- Server MUST validate signature algorithm matches negotiated parameters
- Server MUST verify signature is valid
- Server MUST verify Token Binding ID matches established binding
- Server MUST reject tokens not bound to current Token Binding ID

### Security Limitations
- Does not protect against token theft on client device
- Does not prevent malware with access to private keys
- Requires both client and server support
- TLS session resumption requires careful handling

## Technical Requirements

### Client Requirements

**Implementation**:
1. Generate and securely store key pairs per origin
2. Negotiate Token Binding support in TLS
3. Generate signatures over EKM for each request
4. Include `Sec-Token-Binding` header in HTTP requests
5. Handle Token Binding negotiation failure gracefully

**Key Management**:
- Generate keys on-demand or during first connection
- Store keys securely (non-exportable preferred)
- Support key rotation
- Clean up keys for removed origins

### Server Requirements

**Implementation**:
1. Negotiate Token Binding support in TLS
2. Extract and validate `Sec-Token-Binding` header
3. Verify signature using provided public key
4. Bind issued tokens to Token Binding ID
5. Validate Token Binding ID on subsequent requests

**Token Management**:
- Store Token Binding ID with each token
- Validate Token Binding ID matches on token use
- Reject tokens without proper binding in binding-enforced context
- Support optional binding for transition period

### TLS Extension
Token Binding requires TLS extension (RFC 8472):
- Extension Type: `token_binding` (24)
- Negotiates key parameters
- Must be negotiated on each connection (no resumption)

## Use Cases

### 1. Cookie Security Enhancement
**Scenario**: Protect session cookies from theft
**Implementation**:
- Server issues cookie with Token Binding ID
- Browser includes Token Binding proof with each request
- Server validates binding before accepting cookie

### 2. OAuth Token Protection
**Scenario**: Bind OAuth access tokens to client
**Implementation**:
- Authorization server includes Token Binding ID in token
- Client proves possession when using token
- Resource server validates binding

### 3. Federated Authentication
**Scenario**: SSO token protection across domains
**Implementation**:
- Use `referred_token_binding` for cross-domain tokens
- Identity Provider binds token to client's referred Token Binding ID
- Service Provider validates referred binding

## Implementation Example

### Client Request
```http
POST /api/resource HTTP/1.1
Host: example.com
Sec-Token-Binding: AIkAAgBBQLTsvK4dN_7g...base64...DsH2
Authorization: Bearer eyJhbGc...token...xyz
Cookie: session=abc123
```

### Server Validation Process
1. Extract `Sec-Token-Binding` header
2. Decode Token Binding message
3. Extract Token Binding ID and signature
4. Retrieve EKM from TLS connection
5. Verify signature over EKM
6. Check if tokens (Bearer/Cookie) are bound to this Token Binding ID
7. If valid, process request; otherwise return 401

### Token Binding ID Storage
Server stores with each token:
```json
{
  "token": "eyJhbGc...token...xyz",
  "token_binding_id": {
    "key_parameters": "ecdsap256",
    "public_key": "BASQf2...base64..."
  },
  "issued_at": "2025-10-13T12:00:00Z",
  "expires_at": "2025-10-13T13:00:00Z"
}
```

## Deployment Considerations

### Client-Side Deployment
- Browser support required (native or extension)
- Key storage mechanism (browser profile, OS keychain)
- Performance impact: ~10-20ms per request for signature generation

### Server-Side Deployment
- TLS termination point must support Token Binding extension
- Load balancers must preserve Token Binding data
- Session store must accommodate Token Binding IDs
- Validation performance: ~5-10ms per request

### Transition Strategy
1. Deploy with optional binding (accept both bound and unbound tokens)
2. Monitor adoption rates
3. Gradually enforce binding for sensitive operations
4. Eventually require binding for all authenticated requests

## Related Specifications

- **RFC 8472**: TLS Extension for Token Binding Protocol Negotiation
- **RFC 8473**: Token Binding over HTTP (this document)
- **RFC 8474**: OIDC Token Bound Authentication
- **RFC 5705**: Keying Material Exporters for TLS

## Summary

Token Binding provides strong cryptographic protection against token theft and replay attacks by binding security tokens to TLS connections. It represents a significant security improvement over bearer tokens alone.

**Key Benefits**:
- Cryptographic binding prevents token export
- Protection against token theft (without private key)
- Works with existing token types (cookies, OAuth, etc.)
- Minimal performance impact

**Key Challenges**:
- Requires client and server support
- Complex key management
- Limited browser adoption as of 2025
- Deployment complexity with load balancers

**Recommendation**: Consider for high-security applications where token theft is a significant threat. Evaluate client support availability and deployment complexity. May be superseded by newer protocols like OAuth 2.0 DPoP (RFC 9449).
