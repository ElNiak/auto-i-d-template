# RFC 8446 - The Transport Layer Security (TLS) Protocol Version 1.3

**Source:** IETF RFC 8446
**URL:** https://www.rfc-editor.org/rfc/rfc8446.txt
**Category:** Network Protocol - Security Layer

## Protocol Overview

The Transport Layer Security (TLS) Protocol version 1.3 provides secure communication over insecure networks by enabling authentication, confidentiality, and integrity protection. TLS 1.3 represents a major redesign of the protocol with enhanced security, improved performance, and simplified design compared to TLS 1.2.

## Key Characteristics

- **Authentication:** Verifies identity of communicating parties
- **Confidentiality:** Encrypts application data to prevent eavesdropping
- **Integrity:** Detects message tampering through cryptographic MACs/AEAD
- **Forward Secrecy:** Compromising long-term keys doesn't compromise past sessions
- **Low Latency:** Reduced handshake round trips (1-RTT, 0-RTT)
- **Simplified Design:** Removed legacy cryptographic algorithms and modes

## Protocol Architecture

TLS consists of two primary layers:

### 1. Handshake Protocol

Negotiates cryptographic parameters and establishes shared secrets:
- Key exchange
- Server authentication
- Optional client authentication
- Session establishment

### 2. Record Protocol

Provides secure channel for application data:
- Fragmentation
- Encryption
- Authentication (AEAD)
- Reassembly and delivery

## TLS 1.3 Handshake Modes

### Full (1-RTT) Handshake

```
Client                                           Server

Key  ^ ClientHello
Exch | + key_share*
     | + signature_algorithms*
     | + psk_key_exchange_modes*
     v + pre_shared_key*       -------->
                                                  ServerHello  ^ Key
                                                 + key_share*  | Exch
                                            + pre_shared_key*  v
                                        {EncryptedExtensions}  ^  Server
                                        {CertificateRequest*}  v  Params
                                               {Certificate*}  ^
                                         {CertificateVerify*}  | Auth
                                                   {Finished}  v
                               <--------  [Application Data*]
     ^ {Certificate*}
Auth | {CertificateVerify*}
     v {Finished}              -------->
       [Application Data]      <------->  [Application Data]
```

**Key Points:**
- **1 Round Trip:** Client and server exchange hellos, then encrypted data
- **Encrypted After ServerHello:** All subsequent handshake messages encrypted
- **Authentication:** Server always authenticated, client optionally
- **Application Data:** Can be sent immediately after Finished

### 0-RTT (Zero Round Trip) Resumption

```
Client                                           Server

     {ClientHello}
     + early_data
     + key_share*
     + psk_key_exchange_modes
     + pre_shared_key
     (Application Data*)      -------->
                                                  ServerHello
                                             + pre_shared_key
                                                 + key_share*
                                        {EncryptedExtensions}
                                                   {Finished}
                              <--------  [Application Data*]
     {Finished}               -------->
     [Application Data]       <------->  [Application Data]
```

**Key Points:**
- **Zero Round Trips:** Client sends data immediately with ClientHello
- **Resumption Only:** Requires previously established session
- **Replay Risk:** Early data not replay-protected (application must handle)
- **Fast Resumption:** Ideal for frequently reconnecting clients

### PSK-Based Handshake

Uses pre-shared key (from previous session or out-of-band) instead of certificates:
- Reduces computational cost
- Enables resumption without full handshake
- Can combine with key exchange for forward secrecy

## Handshake Messages

### ClientHello

```
struct {
    ProtocolVersion legacy_version = 0x0303;  /* TLS 1.2 */
    Random random;
    opaque legacy_session_id<0..32>;
    CipherSuite cipher_suites<2..2^16-2>;
    opaque legacy_compression_methods<1..2^8-1>;
    Extension extensions<8..2^16-1>;
} ClientHello;
```

**Key Extensions:**
- **supported_versions:** Indicates TLS 1.3 support
- **supported_groups:** Elliptic curves or finite field groups
- **signature_algorithms:** Acceptable signature algorithms
- **key_share:** Client's public key(s) for key exchange
- **psk_key_exchange_modes:** PSK exchange modes supported
- **pre_shared_key:** PSK identities and binders

### ServerHello

```
struct {
    ProtocolVersion legacy_version = 0x0303;  /* TLS 1.2 */
    Random random;
    opaque legacy_session_id_echo<0..32>;
    CipherSuite cipher_suite;
    uint8 legacy_compression_method = 0;
    Extension extensions<6..2^16-1>;
} ServerHello;
```

**Key Extensions:**
- **supported_versions:** Selected TLS version
- **key_share:** Server's public key for key exchange
- **pre_shared_key:** Selected PSK identity (if using PSK)

### EncryptedExtensions

Contains extensions that are not needed for cryptographic parameter negotiation:
- Server name indication (SNI)
- Application-layer protocol negotiation (ALPN)
- Maximum fragment length
- Early data indication

### Certificate

```
struct {
    opaque cert_data<1..2^24-1>;
    Extension extensions<0..2^16-1>;
} CertificateEntry;

struct {
    opaque certificate_request_context<0..2^8-1>;
    CertificateEntry certificate_list<0..2^24-1>;
} Certificate;
```

**Certificate Chain:**
- End-entity certificate first
- Each subsequent certificate certifies previous
- Root CA certificate may be omitted

**Extensions:**
- OCSP Status Request
- Signed Certificate Timestamp

### CertificateVerify

Proves possession of private key corresponding to certificate:

```
struct {
    SignatureScheme algorithm;
    opaque signature<0..2^16-1>;
} CertificateVerify;
```

**Signature Covers:**
- Transcript of all prior handshake messages
- Context string distinguishing client/server
- Prevents cross-protocol attacks

### Finished

Cryptographic verification of entire handshake:

```
struct {
    opaque verify_data[Hash.length];
} Finished;
```

**verify_data = HMAC(finished_key, Transcript-Hash(Handshake Context))**

- Ensures handshake hasn't been tampered with
- Confirms both parties computed same keys
- First message that can be authenticated

## Key Derivation

TLS 1.3 uses HKDF (HMAC-based Key Derivation Function) for all key derivation:

```
             0
             |
             v
   PSK ->  HKDF-Extract = Early Secret
             |
             +-----> Derive-Secret(., "ext binder" | "res binder")
             |                     = binder_key
             |
             +-----> Derive-Secret(., "c e traffic")
             |                     = client_early_traffic_secret
             |
             +-----> Derive-Secret(., "e exp master")
             |                     = early_exporter_master_secret
             v
       Derive-Secret(., "derived")
             |
             v
   (EC)DHE -> HKDF-Extract = Handshake Secret
             |
             +-----> Derive-Secret(., "c hs traffic")
             |                     = client_handshake_traffic_secret
             |
             +-----> Derive-Secret(., "s hs traffic")
             |                     = server_handshake_traffic_secret
             v
       Derive-Secret(., "derived")
             |
             v
   0 -> HKDF-Extract = Master Secret
             |
             +-----> Derive-Secret(., "c ap traffic")
             |                     = client_application_traffic_secret_0
             |
             +-----> Derive-Secret(., "s ap traffic")
             |                     = server_application_traffic_secret_0
             |
             +-----> Derive-Secret(., "exp master")
             |                     = exporter_master_secret
             |
             +-----> Derive-Secret(., "res master")
                                   = resumption_master_secret
```

**Key Stages:**
1. **Early Secret:** Derived from PSK (or zero if no PSK)
2. **Handshake Secret:** Incorporates (EC)DHE shared secret
3. **Master Secret:** Final stage, derives application secrets

**Key Separation:**
- Each stage has distinct purpose
- Compromise of one stage doesn't compromise others
- Forward secrecy through ephemeral key exchange

## Cryptographic Operations

### Cipher Suites

TLS 1.3 dramatically simplified cipher suite specification:

```
CipherSuite TLS_AES_128_GCM_SHA256       = {0x13,0x01};
CipherSuite TLS_AES_256_GCM_SHA384       = {0x13,0x02};
CipherSuite TLS_CHACHA20_POLY1305_SHA256 = {0x13,0x03};
CipherSuite TLS_AES_128_CCM_SHA256       = {0x13,0x04};
CipherSuite TLS_AES_128_CCM_8_SHA256     = {0x13,0x05};
```

**Components:**
- **AEAD Algorithm:** AES-GCM, ChaCha20-Poly1305, AES-CCM
- **Hash Algorithm:** SHA-256, SHA-384

**Note:** Key exchange and signature algorithms negotiated separately through extensions, not in cipher suite.

### Key Exchange Methods

**Supported Groups (Elliptic Curves and Finite Fields):**
- secp256r1, secp384r1, secp521r1 (NIST curves)
- x25519, x448 (Curve25519/448)
- ffdhe2048, ffdhe3072, ffdhe4096, ffdhe6144, ffdhe8192 (Finite field DH)

**Ephemeral Key Exchange:**
- (EC)DHE: Elliptic Curve or Finite Field Diffie-Hellman Ephemeral
- Provides forward secrecy
- Static RSA key exchange removed in TLS 1.3

### Signature Algorithms

```
enum {
    /* RSASSA-PKCS1-v1_5 algorithms */
    rsa_pkcs1_sha256(0x0401),
    rsa_pkcs1_sha384(0x0501),
    rsa_pkcs1_sha512(0x0601),

    /* ECDSA algorithms */
    ecdsa_secp256r1_sha256(0x0403),
    ecdsa_secp384r1_sha384(0x0503),
    ecdsa_secp521r1_sha512(0x0603),

    /* RSASSA-PSS algorithms */
    rsa_pss_rsae_sha256(0x0804),
    rsa_pss_rsae_sha384(0x0805),
    rsa_pss_rsae_sha512(0x0806),

    /* EdDSA algorithms */
    ed25519(0x0807),
    ed448(0x0808),

    (0xFFFF)
} SignatureScheme;
```

## Record Protocol

### Record Layer Structure

```
struct {
    ContentType type;
    ProtocolVersion legacy_record_version;
    uint16 length;
    opaque fragment[TLSPlaintext.length];
} TLSPlaintext;

struct {
    opaque content[TLSPlaintext.length];
    ContentType type;
    uint8 zeros[length_of_padding];
} TLSInnerPlaintext;

struct {
    ContentType opaque_type = application_data; /* 23 */
    ProtocolVersion legacy_record_version = 0x0303; /* TLS 1.2 */
    uint16 length;
    opaque encrypted_record[TLSCiphertext.length];
} TLSCiphertext;
```

**Record Types:**
- **alert (21):** Error conditions and connection closure
- **handshake (22):** Handshake protocol messages
- **application_data (23):** Application-layer data

**Encryption:**
- All records after ServerHello are encrypted
- AEAD provides confidentiality and integrity
- Content type encrypted inside AEAD

### AEAD Encryption

**Structure:**
```
additional_data = TLSCiphertext.opaque_type ||
                  TLSCiphertext.legacy_record_version ||
                  TLSCiphertext.length

plaintext = TLSInnerPlaintext

encrypted_record = AEAD-Encrypt(write_key, nonce, additional_data, plaintext)
```

**Nonce Construction:**
- Per-record nonce XORed with IV
- Sequence number ensures unique nonce per record
- Prevents nonce reuse attacks

### Record Size Limits

- **Maximum Fragment Length:** 2^14 bytes (16384)
- **Maximum Encrypted Length:** 2^14 + 256 bytes
- **Padding:** Allowed but not required (for traffic analysis mitigation)

## Alert Protocol

### Alert Levels

- **warning (1):** Non-fatal issues (deprecated in TLS 1.3, rarely used)
- **fatal (2):** Connection must be terminated immediately

### Alert Descriptions

```
enum {
    close_notify(0),
    unexpected_message(10),
    bad_record_mac(20),
    record_overflow(22),
    handshake_failure(40),
    bad_certificate(42),
    unsupported_certificate(43),
    certificate_revoked(44),
    certificate_expired(45),
    certificate_unknown(46),
    illegal_parameter(47),
    unknown_ca(48),
    access_denied(49),
    decode_error(50),
    decrypt_error(51),
    protocol_version(70),
    insufficient_security(71),
    internal_error(80),
    inappropriate_fallback(86),
    user_canceled(90),
    missing_extension(109),
    unsupported_extension(110),
    unrecognized_name(112),
    bad_certificate_status_response(113),
    unknown_psk_identity(115),
    certificate_required(116),
    no_application_protocol(120),
    (255)
} AlertDescription;
```

### Connection Closure

**close_notify:**
- Either party can initiate graceful shutdown
- Prevents truncation attacks
- Receiver must close after sending its close_notify

## Major Changes from TLS 1.2

### Removed Features

- **Static RSA Key Exchange:** All key exchanges provide forward secrecy
- **CBC Mode Ciphers:** Only AEAD ciphers supported
- **SHA-1:** Removed for signatures
- **MD5:** Completely removed
- **Compression:** Removed due to CRIME attack
- **Renegotiation:** Removed, replaced with key update
- **Custom DHE Groups:** Only named groups allowed
- **ChangeCipherSpec:** Implicit from handshake state

### Added Features

- **0-RTT Mode:** Early data in first flight
- **Post-Handshake Authentication:** Client certificate after handshake
- **Key Update:** Refresh traffic keys without full handshake
- **HelloRetryRequest:** Server can request new ClientHello with different parameters
- **Encrypted Certificates:** Server certificate encrypted
- **PSK Resumption:** Cleaner resumption mechanism

### Security Improvements

- **Downgrade Protection:** Random field includes TLS 1.3 sentinel
- **Signature Covers Context:** Prevents cross-protocol attacks
- **Key Separation:** Distinct keys for different purposes
- **Simplified State Machine:** Fewer states reduce attack surface
- **Removed Weak Algorithms:** RSA PKCS#1v1.5 encryption, DSA, RC4, 3DES, etc.

## State Machine

### Simplified Client State Machine

```
                              START <----+
               Send ClientHello |        | Recv HelloRetryRequest
          [K_send = early data] |        |
                                v        |
           /                 WAIT_SH ----+
           |                    | Recv ServerHello
           |                    | K_recv = handshake
       Can |                    V
      send |                 WAIT_EE
     early |                    | Recv EncryptedExtensions
      data |           +--------+--------+
           |     Using |                 | Using certificate
           |       PSK |                 v
           |           |            WAIT_CERT_CR
           |           |        Recv |       | Recv CertificateRequest
           |           | Certificate |       v
           |           |             |    WAIT_CERT
           |           |             |       | Recv Certificate
           |           |             v       v
           |           |              WAIT_CV
           |           |                 | Recv CertificateVerify
           |           +> WAIT_FINISHED <+
           |                  | Recv Finished
           \                  | [Send EndOfEarlyData]
                              | K_send = handshake
                              | [Send Certificate [+ CertificateVerify]]
    K_send = K_recv = application
                              v
                          CONNECTED
```

### Simplified Server State Machine

```
                              START <-----+
               Recv ClientHello |         | Send HelloRetryRequest
                                v         |
                             RECVD_CH ----+
                                | Select parameters
                                v
                             NEGOTIATED
                                | Send ServerHello
                                | K_send = handshake
                                | Send EncryptedExtensions
                                | [Send CertificateRequest]
                 Can send       | [Send Certificate + CertificateVerify]
                 app data       | Send Finished
                 after   -->    | K_send = application
                 here           v
                             WAIT_EOED <-+
                                | Recv |  | Recv EndOfEarlyData
                                | End  |  +
                                | of   |
                                | Early|
                                | Data |
                                |      v
                                +-> WAIT_FLIGHT2
                                       |
                           +-----------+
                   No auth |           | Client auth
                           |           |
                           |           v
                           |       WAIT_CERT
                           |           | Recv Certificate
                           |           v
                           |       WAIT_CV
                           |           | Recv CertificateVerify
                           v           v
                             WAIT_FINISHED
                                | Recv Finished
                                | K_recv = application
                                v
                            CONNECTED
```

## Security Considerations

### Cryptographic Security

- **AEAD Only:** Provides both confidentiality and integrity
- **Forward Secrecy:** Ephemeral key exchange protects past sessions
- **Key Separation:** Different keys for different purposes prevents cross-protocol attacks
- **Strong Algorithms:** Weak ciphers and hash functions removed

### Protocol Security

- **Downgrade Protection:** Prevents forcing TLS 1.2 or lower
- **Transcript Hash:** All messages authenticated via Finished
- **Certificate Transparency:** SCT extension enables public logging
- **OCSP Stapling:** Reduces privacy leaks from OCSP queries

### Implementation Security

- **Constant-Time Operations:** Required for cryptographic operations
- **Side-Channel Resistance:** Implementations must avoid timing attacks
- **Key Erasure:** Ephemeral secrets should be erased after use
- **Random Number Generation:** Critical for security, must be cryptographically secure

### Known Limitations

- **0-RTT Replay:** Early data not replay-protected
- **Traffic Analysis:** Encrypted traffic still reveals patterns
- **Certificate Validation:** Complex process prone to implementation errors
- **Cryptographic Agility:** Algorithm migration challenging in practice

## Performance Characteristics

### Latency

- **1-RTT Handshake:** Full handshake completes in one round trip
- **0-RTT Resumption:** Data can be sent immediately
- **Reduced Computational Cost:** Fewer cryptographic operations than TLS 1.2

### Throughput

- **AEAD Efficiency:** Hardware acceleration widely available
- **Pipelining:** Can send application data sooner
- **Record Coalescing:** Multiple messages in single record

### Resource Usage

- **Memory:** Moderate for connection state and buffers
- **CPU:** Cryptographic operations dominate cost
- **Network:** Overhead approximately 40-60 bytes per record

## Implementation Considerations

### Mandatory Features

- At least one cipher suite (TLS_AES_128_GCM_SHA256 recommended)
- DHE or ECDHE key exchange
- Digital signatures for authentication
- Proper random number generation
- Certificate validation

### Optional Features

- 0-RTT mode
- Post-handshake authentication
- Client authentication
- Session tickets (resumption)
- PSK modes

### Testing and Validation

- Interoperability testing essential
- Negative testing for error handling
- Cryptographic correctness verification
- Performance benchmarking under load

## Related Specifications

- **RFC 5246:** TLS 1.2 (obsoleted by TLS 1.3)
- **RFC 8447:** IANA Registry Updates for TLS and DTLS
- **RFC 8448:** Example Handshake Traces for TLS 1.3
- **RFC 8449:** Record Size Limit Extension
- **RFC 8451:** Token Binding for HTTP/2 over TLS 1.3
- **RFC 9150:** TLS 1.3 Authentication and Integrity-Only Cipher Suites

## Summary

TLS 1.3 represents a fundamental redesign of the TLS protocol with an emphasis on:

1. **Enhanced Security:** Removal of weak algorithms, mandatory forward secrecy, simplified state machine
2. **Improved Performance:** 1-RTT handshake, 0-RTT resumption, reduced computational overhead
3. **Cleaner Design:** Removal of legacy features, simplified cipher suite specification, better key derivation

The protocol achieves these goals through:
- Encrypting more of the handshake
- Restricting cryptographic agility to secure algorithms
- Simplifying the protocol state machine
- Improving forward secrecy guarantees
- Better separation of concerns between protocol layers

TLS 1.3 has been widely adopted as the modern standard for secure Internet communication, providing the security foundation for HTTP/3, QUIC, and many other application protocols.
