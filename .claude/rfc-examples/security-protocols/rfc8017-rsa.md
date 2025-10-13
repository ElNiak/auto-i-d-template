# RFC 8017 - PKCS #1: RSA Cryptography Specifications Version 2.2

**Source:** https://www.rfc-editor.org/rfc/rfc8017.txt

## Specification Purpose and RSA Overview

### Purpose:
Provides comprehensive recommendations for implementing RSA public-key cryptography, covering:
- Cryptographic primitives (low-level operations)
- Encryption schemes (secure data encryption)
- Signature schemes (digital signatures)
- Key representation (encoding formats)

### RSA Foundation:
- **Mathematical basis**: Difficulty of computing e-th roots modulo n
- **Key components**: Public key (n, e), Private key (n, d)
- **Multi-prime support**: More than two prime factors for improved performance

### Design Goals:
- Improve computational efficiency
- Support modern cryptographic practices
- Maintain backward compatibility
- Enable secure implementations

## Key Security Considerations and Cryptographic Requirements

### Fundamental Security Assumptions:

#### 1. RSA Problem Hardness:
- **Assumption**: Computing e-th roots modulo n is computationally infeasible
- **Requirement**: Sufficiently large key sizes (2048+ bits recommended)
- **Threat**: Quantum computing will break RSA (requires post-quantum alternatives)

#### 2. Key Separation:
**Critical Requirement:**
> "It is recommended that one use only one scheme per RSA key pair to avoid potential vulnerabilities"

**Rationale:**
- Prevents cross-protocol attacks
- Reduces attack surface
- Simplifies security analysis

#### 3. Key Validation:
- **Public key validation**: Check n is composite, e is appropriate
- **Private key validation**: Verify consistency of key components
- **Parameter constraints**: Enforce minimum key sizes and valid exponents

### Security Implementation Requirements:

#### Random Number Generation:
- **Quality**: Cryptographically secure random number generator (CSPRNG)
- **Purpose**: Used in padding schemes (OAEP, PSS)
- **Requirement**: Sufficient entropy for security

#### Side-Channel Protection:
- **Timing attacks**: Constant-time implementations
- **Power analysis**: Countermeasures in hardware implementations
- **Fault attacks**: Proper error handling without leaking information

#### Error Handling:
- **Consistent behavior**: Don't leak information via error messages
- **Timing uniformity**: All error paths should take similar time
- **No partial results**: Never return partial decryption/signature data on errors

## Encryption and Signature Schemes

### Encryption Schemes

#### 1. RSAES-OAEP (Optimal Asymmetric Encryption Padding)
**Status:** Recommended for new applications

**Properties:**
- **Security**: Provably secure against adaptive chosen-ciphertext attacks (IND-CCA2)
- **Padding**: Optimal Asymmetric Encryption Padding
- **Randomization**: Includes random oracle hash function
- **Message limit**: Depends on key size and hash function

**Algorithm Components:**
1. Message encoding with OAEP padding
2. RSA encryption primitive (RSAEP)
3. Ciphertext output

**Padding Structure:**
```
OAEP Padding:
- Random seed
- Hash of label
- Padding string
- Message
- Mask generation function (MGF)
```

**Security Features:**
- Probabilistic encryption (different ciphertexts for same message)
- Protection against chosen-ciphertext attacks
- Semantic security (no information leakage)

#### 2. RSAES-PKCS1-v1_5
**Status:** Included for compatibility with existing systems

**Properties:**
- **Security**: Weaker than OAEP (vulnerable to adaptive chosen-ciphertext attacks)
- **Padding**: PKCS #1 v1.5 padding scheme
- **Deterministic**: Fixed padding structure
- **Legacy**: Widely deployed but not recommended for new applications

**Vulnerabilities:**
- **Bleichenbacher attack**: Padding oracle attack via error messages
- **Timing attacks**: Implementation must be careful about error handling

**Mitigation Required:**
- Constant-time decryption error handling
- No distinguishable error messages
- Consider migrating to OAEP

### Signature Schemes

#### 1. RSASSA-PSS (Probabilistic Signature Scheme)
**Status:** Required for new applications

**Properties:**
- **Security**: Provably secure in random oracle model
- **Randomization**: Probabilistic (different signatures for same message)
- **Salt**: Includes random salt value
- **Verification**: Deterministic verification process

**Algorithm Components:**
1. Message encoding with PSS padding
2. RSA signature primitive (RSASP1)
3. Signature output

**Security Features:**
- **Probabilistic**: Different signatures for same message
- **Tight security reduction**: Strong provable security guarantees
- **Resistance to existential forgery**: Cannot forge signatures
- **Modern**: Designed with current cryptographic knowledge

**Padding Structure:**
```
PSS Padding:
- Hash of message
- Random salt
- Padding string
- Mask generation function (MGF)
```

#### 2. RSASSA-PKCS1-v1_5
**Status:** Included for compatibility

**Properties:**
- **Security**: Secure in practice but lacks proof
- **Deterministic**: Same message produces same signature
- **Legacy**: Widely used but PSS preferred
- **Simpler**: Less complex than PSS

**Use Cases:**
- Legacy system compatibility
- Protocols requiring deterministic signatures
- Performance-critical scenarios (marginally faster)

**Recommendation:** Migrate to PSS for new systems

## Security Recommendations and Constraints

### 1. Key Size Recommendations:

| Key Size | Security Level | Status |
|----------|---------------|---------|
| 1024 bits | 80-bit security | Deprecated (broken) |
| 2048 bits | 112-bit security | Minimum recommended |
| 3072 bits | 128-bit security | Recommended |
| 4096 bits | 152-bit security | High security applications |

**Considerations:**
- Larger keys = better security but slower operations
- Balance security needs with performance requirements
- Plan for key size increases over time

### 2. Hash Function Selection:

**Requirement:** Match hash function security level to key size

| Key Size | Recommended Hash |
|----------|------------------|
| 2048 bits | SHA-256 |
| 3072 bits | SHA-256 or SHA-384 |
| 4096 bits | SHA-384 or SHA-512 |

**Recommendation:**
> "Match hash functions in mask generation for enhanced security"

### 3. Mask Generation Function (MGF):

**MGF1 Requirements:**
- Use with OAEP and PSS schemes
- Based on hash function (e.g., MGF1-SHA256)
- Generates pseudo-random output of desired length
- Security depends on underlying hash function

### 4. Implementation Security:

#### Randomization:
- Use cryptographically secure random number generator
- Generate independent random octets for each operation
- Never reuse randomness

#### Message Handling:
- Implement rigorous message checking
- Avoid encryption of similar messages with same key
- Use proper encoding before cryptographic operations

#### Error Handling:
- Implement countermeasures against side-channel attacks
- Uniform timing for all code paths
- Generic error messages (no information leakage)

### 5. Operational Security:

#### Key Management:
- Secure key generation
- Proper key storage (hardware security modules)
- Regular key rotation
- Secure key destruction

#### Certificate Validation:
- Verify certificate chains
- Check certificate revocation status
- Validate certificate constraints

## Known Vulnerabilities and Mitigations

### 1. Chosen Ciphertext Attacks

#### Bleichenbacher Attack (PKCS#1 v1.5):
**Attack:** Padding oracle attack using error messages
**Target:** RSAES-PKCS1-v1_5 encryption

**Mitigation:**
- Use RSAES-OAEP instead
- If PKCS#1 v1.5 required: implement constant-time decryption
- No distinguishable error messages
- No timing differences between error cases

#### Adaptive Chosen Ciphertext:
**Attack:** Use decryption oracle to decrypt ciphertexts
**Target:** Schemes without IND-CCA2 security

**Mitigation:**
- Use RSAES-OAEP (provably IND-CCA2 secure)
- Proper implementation of padding verification
- No partial result disclosure on errors

### 2. Message Representative Manipulation

#### Attack Vector:
Manipulate message encoding to forge signatures or decrypt messages

**Mitigations:**
- Strict encoding format verification
- Hash function domain separation
- Proper padding validation

### 3. Low-Exponent RSA Attacks

#### Small Public Exponent (e=3):
**Risk:** Faster encryption but potential vulnerabilities if not properly padded

**Mitigations:**
- Always use proper padding (OAEP, PSS)
- Never encrypt raw messages
- Ensure message space is large enough

#### Small Private Exponent:
**Risk:** Faster decryption but cryptanalytic vulnerabilities

**Mitigation:** Use full-size private exponent d

### 4. Timing Attacks

#### Attack Vector:
Analyze timing variations to extract key information

**Mitigations:**
- Constant-time implementations
- Blinding during private key operations
- Uniform error handling timing

### 5. Fault Attacks

#### Attack Vector:
Induce computational errors to extract key information

**Mitigations:**
- Verify computation results
- Use redundant computations
- Hardware countermeasures

### 6. Cross-Protocol Attacks

#### Attack Vector:
Use key from one protocol in another to break security

**Mitigation:**
> "Use only one scheme per RSA key pair"

- Separate keys for encryption and signing
- Include protocol identifier in message encoding
- Domain separation in hash inputs

### 7. Common Implementation Pitfalls:

#### Padding Validation:
- ❌ **Wrong**: Check padding byte-by-byte with early exit
- ✅ **Correct**: Constant-time full padding verification

#### Random Number Generation:
- ❌ **Wrong**: Use system time or predictable seeds
- ✅ **Correct**: Use CSPRNG with sufficient entropy

#### Error Messages:
- ❌ **Wrong**: "Invalid padding" vs "Decryption failed"
- ✅ **Correct**: Generic "Decryption error" for all failures

## Comparison of Schemes

### Encryption Schemes:

| Feature | RSAES-OAEP | RSAES-PKCS1-v1_5 |
|---------|------------|------------------|
| **Security** | IND-CCA2 (provable) | Vulnerable to CCA |
| **Randomization** | Yes | Yes (but weak) |
| **Ciphertext Size** | Same as modulus | Same as modulus |
| **Performance** | Slightly slower | Slightly faster |
| **Recommendation** | Use for new apps | Legacy only |

### Signature Schemes:

| Feature | RSASSA-PSS | RSASSA-PKCS1-v1_5 |
|---------|------------|-------------------|
| **Security** | Provably secure | Secure in practice |
| **Randomization** | Yes | No |
| **Signature Size** | Same as modulus | Same as modulus |
| **Performance** | Comparable | Slightly faster |
| **Recommendation** | Use for new apps | Legacy/compatibility |

## Implementation Checklist

### Key Generation:
- [ ] Use cryptographically secure random number generator
- [ ] Generate keys of sufficient size (2048+ bits)
- [ ] Verify key consistency (mathematical relationships)
- [ ] Use appropriate public exponent (e.g., 65537)
- [ ] Store private keys securely

### Encryption:
- [ ] Use RSAES-OAEP for new applications
- [ ] Select appropriate hash function
- [ ] Generate fresh random seed for each encryption
- [ ] Check message length constraints
- [ ] Implement constant-time operations

### Decryption:
- [ ] Validate ciphertext length
- [ ] Implement constant-time padding verification
- [ ] Use uniform error handling
- [ ] No information leakage in errors
- [ ] Consider blinding against timing attacks

### Signing:
- [ ] Use RSASSA-PSS for new applications
- [ ] Select appropriate hash function and salt length
- [ ] Generate fresh random salt for PSS
- [ ] Hash message before signing
- [ ] Protect private key during signing operation

### Verification:
- [ ] Validate signature length
- [ ] Use same hash function as signing
- [ ] Verify padding structure (PSS or PKCS1-v1_5)
- [ ] Compare hash values securely
- [ ] Return boolean result (valid/invalid)

## Key Takeaways for Cryptographic Protocol Design

1. **Use modern schemes**: RSAES-OAEP and RSASSA-PSS provide stronger security guarantees
2. **Proper padding is essential**: Never use raw RSA operations
3. **One key, one purpose**: Don't reuse keys for encryption and signing
4. **Randomization matters**: Probabilistic schemes provide better security
5. **Implementation security**: Side-channel protection is critical
6. **Error handling**: Constant-time operations and uniform error messages
7. **Key size planning**: Use 2048+ bits, plan for increases
8. **Hash function matching**: Match hash strength to key size
9. **Legacy migration**: Phase out PKCS#1 v1.5 schemes
10. **Post-quantum awareness**: RSA will be broken by quantum computers, plan transitions

## Future Considerations

### Post-Quantum Cryptography:
- RSA vulnerable to quantum computers (Shor's algorithm)
- NIST post-quantum standardization process
- Hybrid approaches during transition
- Plan migration strategies now

### Algorithm Agility:
- Support multiple algorithm versions
- Enable smooth algorithm transitions
- Version negotiation in protocols
- Backward compatibility considerations
