# AWS Signature Version 4 (SigV4) Signing Process

**Source**: AWS Documentation
**Category**: Company Authentication Pattern
**URL**: https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_aws-signing.html

## Overview

AWS Signature Version 4 (SigV4) is a cryptographic signing protocol used to authenticate API requests to AWS services. Unlike bearer tokens, SigV4 requires signing each request with a derived key, providing proof of identity and request integrity without transmitting the secret key.

## Core Concepts

### Authentication vs Authorization
- **Authentication**: SigV4 verifies WHO is making the request (identity)
- **Authorization**: IAM policies determine WHAT the authenticated identity can do

### Key Terminology
- **Access Key ID**: Public identifier for AWS credentials (e.g., `AKIAIOSFODNN7EXAMPLE`)
- **Secret Access Key**: Secret key used for signing (never transmitted)
- **Signing Key**: Derived key scoped to service, region, and date
- **Signature**: HMAC-SHA256 cryptographic signature proving request authenticity
- **Canonical Request**: Normalized representation of HTTP request

## Authentication Flow

### High-Level Process

```
Client                           AWS Service
  |                                  |
  |--(1) Prepare request parameters--|
  |     (method, headers, payload)   |
  |                                  |
  |--(2) Create canonical request----|
  |     (normalize request details)  |
  |                                  |
  |--(3) Create string to sign-------|
  |     (hash canonical request)     |
  |                                  |
  |--(4) Calculate signature---------|
  |     (HMAC with derived key)      |
  |                                  |
  |--(5) Add auth header------------>|
  |     Authorization: AWS4-HMAC-... |
  |                                  |
  |     [Service recreates signature]|
  |     [Compares with request sig]  |
  |                                  |
  |<-(6) Response if signatures match|
  |     (or 403 if mismatch)         |
  |                                  |
```

### Detailed Signing Steps

#### Step 1: Create Canonical Request

**Purpose**: Normalize HTTP request into standard format for signing

**Components**:
1. HTTP method (GET, POST, PUT, etc.)
2. Canonical URI (URL-encoded path)
3. Canonical query string (sorted, URL-encoded parameters)
4. Canonical headers (lowercase, sorted, trimmed)
5. Signed headers list (which headers are included)
6. Hashed payload (SHA256 hex of body)

**Format**:
```
<HTTPMethod>\n
<CanonicalURI>\n
<CanonicalQueryString>\n
<CanonicalHeaders>\n
<SignedHeaders>\n
<HashedPayload>
```

**Example**:
```
GET
/
Action=ListUsers&Version=2010-05-08
content-type:application/x-www-form-urlencoded; charset=utf-8
host:iam.amazonaws.com
x-amz-date:20150830T123600Z

content-type;host;x-amz-date
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

**Pseudo-code**:
```python
def create_canonical_request(method, uri, query_params, headers, payload):
    # 1. HTTP method
    canonical_method = method.upper()

    # 2. Canonical URI (URL-encode path)
    canonical_uri = url_encode(uri) if uri else '/'

    # 3. Canonical query string (sorted, encoded)
    canonical_query = '&'.join(sorted([
        f"{url_encode(k)}={url_encode(v)}"
        for k, v in query_params.items()
    ]))

    # 4. Canonical headers (lowercase, sorted, trimmed)
    canonical_headers = '\n'.join([
        f"{k.lower().strip()}:{v.strip()}"
        for k, v in sorted(headers.items())
    ]) + '\n'

    # 5. Signed headers (semicolon-separated list)
    signed_headers = ';'.join(sorted([k.lower() for k in headers.keys()]))

    # 6. Hashed payload
    hashed_payload = sha256_hex(payload)

    return f"{canonical_method}\n{canonical_uri}\n{canonical_query}\n" \
           f"{canonical_headers}\n{signed_headers}\n{hashed_payload}"
```

#### Step 2: Create String to Sign

**Purpose**: Create string that will be cryptographically signed

**Format**:
```
AWS4-HMAC-SHA256\n
<Timestamp>\n
<Credential Scope>\n
<Hashed Canonical Request>
```

**Components**:
- **Algorithm**: Always "AWS4-HMAC-SHA256"
- **Timestamp**: ISO 8601 format (e.g., "20150830T123600Z")
- **Credential Scope**: `<date>/<region>/<service>/aws4_request`
- **Hashed Canonical Request**: SHA256 hex of canonical request

**Example**:
```
AWS4-HMAC-SHA256
20150830T123600Z
20150830/us-east-1/iam/aws4_request
f536975d06c0309214f805bb90ccff089219ecd68b2577efef23edd43b7e1a59
```

**Pseudo-code**:
```python
def create_string_to_sign(timestamp, credential_scope, canonical_request):
    algorithm = "AWS4-HMAC-SHA256"
    hashed_request = sha256_hex(canonical_request)

    return f"{algorithm}\n{timestamp}\n{credential_scope}\n{hashed_request}"
```

#### Step 3: Calculate Signing Key

**Purpose**: Derive service-specific, date-scoped signing key

**Derivation Process** (nested HMAC):
```
kSecret = AWS Secret Access Key
kDate = HMAC("AWS4" + kSecret, Date)
kRegion = HMAC(kDate, Region)
kService = HMAC(kRegion, Service)
kSigning = HMAC(kService, "aws4_request")
```

**Pseudo-code**:
```python
def get_signature_key(key, date_stamp, region, service):
    k_date = hmac_sha256(("AWS4" + key).encode('utf-8'), date_stamp.encode('utf-8'))
    k_region = hmac_sha256(k_date, region.encode('utf-8'))
    k_service = hmac_sha256(k_region, service.encode('utf-8'))
    k_signing = hmac_sha256(k_service, b"aws4_request")
    return k_signing
```

**Example**:
```python
secret_key = "wJalrXUtnFEMI/K7MDENG+bPxRfiCYEXAMPLEKEY"
date_stamp = "20150830"  # YYYYMMDD
region = "us-east-1"
service = "iam"

signing_key = get_signature_key(secret_key, date_stamp, region, service)
# Result: binary key (not displayed)
```

#### Step 4: Calculate Signature

**Purpose**: Create signature by signing the string-to-sign

**Process**:
```
Signature = Hex(HMAC-SHA256(SigningKey, StringToSign))
```

**Pseudo-code**:
```python
def calculate_signature(signing_key, string_to_sign):
    signature = hmac_sha256(signing_key, string_to_sign.encode('utf-8'))
    return signature.hex()
```

**Example**:
```python
string_to_sign = "AWS4-HMAC-SHA256\n20150830T123600Z\n..."
signing_key = get_signature_key(...)  # From step 3

signature = calculate_signature(signing_key, string_to_sign)
# Result: "5d672d79c15b13162d9279b0855cfba6789a8edb4c82c400e06b5924a6f2b5d7"
```

#### Step 5: Add Authorization Header

**Format**:
```
Authorization: AWS4-HMAC-SHA256
  Credential=<AccessKeyId>/<CredentialScope>,
  SignedHeaders=<SignedHeaders>,
  Signature=<Signature>
```

**Example**:
```http
Authorization: AWS4-HMAC-SHA256
  Credential=AKIAIOSFODNN7EXAMPLE/20150830/us-east-1/iam/aws4_request,
  SignedHeaders=content-type;host;x-amz-date,
  Signature=5d672d79c15b13162d9279b0855cfba6789a8edb4c82c400e06b5924a6f2b5d7
```

## Request Format

### Required Headers

#### 1. Host Header
```http
Host: <service>.<region>.amazonaws.com
```
Example: `Host: iam.amazonaws.com`

#### 2. X-Amz-Date Header
```http
X-Amz-Date: <ISO8601 timestamp>
```
Example: `X-Amz-Date: 20150830T123600Z`
Format: `YYYYMMDDTHHmmssZ` (UTC)

#### 3. Authorization Header
```http
Authorization: AWS4-HMAC-SHA256
  Credential=<AccessKeyId>/<Scope>,
  SignedHeaders=<Headers>,
  Signature=<Signature>
```

### Optional but Common Headers

#### X-Amz-Content-Sha256
```http
X-Amz-Content-Sha256: <hex-encoded-sha256-of-payload>
```
- Required for S3
- Optional for other services
- Use `UNSIGNED-PAYLOAD` for unsigned payloads (not recommended)

#### X-Amz-Security-Token
```http
X-Amz-Security-Token: <session-token>
```
- Required when using temporary credentials (STS)
- Obtained from AssumeRole, GetSessionToken, etc.

### Complete Request Example

```http
GET /?Action=ListUsers&Version=2010-05-08 HTTP/1.1
Host: iam.amazonaws.com
Content-Type: application/x-www-form-urlencoded; charset=utf-8
X-Amz-Date: 20150830T123600Z
Authorization: AWS4-HMAC-SHA256
  Credential=AKIAIOSFODNN7EXAMPLE/20150830/us-east-1/iam/aws4_request,
  SignedHeaders=content-type;host;x-amz-date,
  Signature=5d672d79c15b13162d9279b0855cfba6789a8edb4c82c400e06b5924a6f2b5d7
```

## Signature Variants

### Symmetric SigV4 (Standard)

**Characteristics**:
- Signing key scoped to single service, region, and date
- Most common variant
- Used by default

**Key Derivation**: `AWS4 + SecretKey → Date → Region → Service → aws4_request`

**Use Case**: Standard API requests to single-region services

### Asymmetric SigV4a (Multi-Region)

**Characteristics**:
- Uses ECDSA (Elliptic Curve Digital Signature Algorithm)
- Supports multi-region signatures
- Single signature valid across multiple regions

**Key Differences**:
- Algorithm: `AWS4-ECDSA-P256-SHA256` (instead of `AWS4-HMAC-SHA256`)
- Signing Key: ECDSA private key (instead of derived HMAC key)
- Signature: ECDSA signature (instead of HMAC signature)

**Use Case**: S3 Multi-Region Access Points, EventBridge global endpoints

**Example Authorization Header**:
```http
Authorization: AWS4-ECDSA-P256-SHA256
  Credential=AKIAIOSFODNN7EXAMPLE/20150830/s3/aws4_request,
  SignedHeaders=host;x-amz-date,
  Signature=<ecdsa-signature>
```

### Query String Authentication (Presigned URLs)

**Characteristics**:
- Signature in URL query parameters (not header)
- Time-limited access (expiration)
- Shareable URLs (no authentication required)

**Format**:
```
https://<service>.<region>.amazonaws.com/<path>?
  X-Amz-Algorithm=AWS4-HMAC-SHA256&
  X-Amz-Credential=<AccessKeyId>/<Scope>&
  X-Amz-Date=<Timestamp>&
  X-Amz-Expires=<Seconds>&
  X-Amz-SignedHeaders=<Headers>&
  X-Amz-Signature=<Signature>
```

**Example** (S3 presigned URL):
```
https://s3.amazonaws.com/mybucket/photo.jpg?
  X-Amz-Algorithm=AWS4-HMAC-SHA256&
  X-Amz-Credential=AKIAIOSFODNN7EXAMPLE/20150830/us-east-1/s3/aws4_request&
  X-Amz-Date=20150830T123600Z&
  X-Amz-Expires=3600&
  X-Amz-SignedHeaders=host&
  X-Amz-Signature=<signature>
```

**Use Case**: Shareable download links, browser uploads, temporary access

## Security Considerations

### Request Timestamp Validation

**Requirement**: Request must reach AWS within 5 minutes of timestamp
- Prevents replay attacks
- Uses X-Amz-Date header
- Service compares request time with current time

**Error Response**:
```http
HTTP/1.1 403 Forbidden
Content-Type: application/json

{
  "Code": "SignatureDoesNotMatch",
  "Message": "The request signature we calculated does not match the signature you provided. Check your AWS Secret Access Key and signing method."
}
```

### Signature Scope Restrictions

**Service Scoped**: Signature valid only for specific:
- Date (YYYYMMDD format)
- Region (e.g., us-east-1)
- Service (e.g., s3, iam)

**Benefits**:
- Limits blast radius of compromised signature
- Requires deriving new key daily
- Prevents cross-service attacks

### Credential Protection

**Secret Key Security**:
- NEVER transmit secret access key
- NEVER include in requests
- NEVER log secret key
- Rotate regularly

**Derived Key Security**:
- Signing key derived fresh for each day
- Old signing keys unusable after date change
- Compromised signing key has limited lifetime

### Payload Integrity

**Hashed Payload**:
- SHA256 hash of request body included in signature
- Prevents payload tampering
- Ensures request integrity

**Verification**:
1. Client calculates payload hash
2. Client includes hash in canonical request
3. Service recalculates payload hash
4. Service verifies hash matches

### Common Attack Mitigations

#### 1. Replay Attack Prevention
**Mitigation**: Timestamp validation (5-minute window)
**How**: Old requests rejected by timestamp check

#### 2. Request Tampering Prevention
**Mitigation**: Payload hashing, canonical request normalization
**How**: Any modification invalidates signature

#### 3. Credential Theft
**Mitigation**: Secret key never transmitted
**How**: Only signature sent; secret key stays on client

#### 4. Cross-Service Access
**Mitigation**: Service-scoped signatures
**How**: Signature for S3 can't be used for IAM

## Technical Requirements

### Client Implementation

**Minimum Requirements**:
1. HTTP client library
2. SHA256 hashing capability
3. HMAC-SHA256 signing capability
4. URL encoding functions
5. ISO 8601 timestamp generation

**Recommended Approach**: Use AWS SDK
```python
# Python example using boto3 (AWS SDK)
import boto3

# SDK handles all signing automatically
iam = boto3.client('iam')
users = iam.list_users()
```

**Manual Signing** (not recommended):
```python
# Python example of manual signing
import hashlib
import hmac
from datetime import datetime
from urllib.parse import quote

def sign_request(method, url, headers, payload, access_key, secret_key, region, service):
    # Step 1: Create canonical request
    canonical_request = create_canonical_request(method, url, headers, payload)

    # Step 2: Create string to sign
    timestamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    date_stamp = datetime.utcnow().strftime('%Y%m%d')
    credential_scope = f"{date_stamp}/{region}/{service}/aws4_request"
    string_to_sign = create_string_to_sign(timestamp, credential_scope, canonical_request)

    # Step 3: Calculate signing key
    signing_key = get_signature_key(secret_key, date_stamp, region, service)

    # Step 4: Calculate signature
    signature = hmac.new(signing_key, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()

    # Step 5: Add authorization header
    authorization_header = (
        f"AWS4-HMAC-SHA256 "
        f"Credential={access_key}/{credential_scope}, "
        f"SignedHeaders={';'.join(sorted(headers.keys()))}, "
        f"Signature={signature}"
    )

    return authorization_header
```

### Server (AWS Service) Validation

**Validation Steps**:
1. Extract authorization header components
2. Retrieve secret key for access key ID
3. Recreate canonical request from incoming request
4. Recreate string to sign
5. Calculate expected signature
6. Compare signatures (constant-time comparison)
7. Validate timestamp (within 5 minutes)
8. Check IAM permissions (authorization)

**Validation Pseudo-code**:
```python
def validate_signature(request):
    # Extract authorization header
    auth_header = request.headers['Authorization']
    access_key_id, credential_scope, signed_headers, client_signature = parse_auth_header(auth_header)

    # Retrieve secret key
    secret_key = get_secret_key(access_key_id)

    # Recreate canonical request
    canonical_request = create_canonical_request_from_request(request, signed_headers)

    # Recreate string to sign
    timestamp = request.headers['X-Amz-Date']
    string_to_sign = create_string_to_sign(timestamp, credential_scope, canonical_request)

    # Calculate expected signature
    date_stamp, region, service = parse_credential_scope(credential_scope)
    signing_key = get_signature_key(secret_key, date_stamp, region, service)
    expected_signature = calculate_signature(signing_key, string_to_sign)

    # Compare signatures (constant-time)
    if not constant_time_compare(client_signature, expected_signature):
        return 403, "SignatureDoesNotMatch"

    # Validate timestamp
    request_time = parse_iso8601(timestamp)
    if abs(current_time() - request_time) > 300:  # 5 minutes
        return 403, "RequestExpired"

    # Check IAM permissions (authorization)
    if not check_iam_permissions(access_key_id, request.action):
        return 403, "AccessDenied"

    return 200, "OK"
```

## Implementation Best Practices

### 1. Always Use SDK When Possible

**Recommendation**: Use AWS SDKs (boto3, AWS SDK for JavaScript, etc.)

**Why**:
- Automatic signing (no manual implementation)
- Handles edge cases (URL encoding, header normalization)
- Maintained by AWS (security updates)
- Reduced error potential

**Quote from AWS**:
> "Unless you have a good reason not to, we recommend that you always use an SDK or the CLI."

### 2. Credential Management

**Best Practices**:
- Use IAM roles for EC2/Lambda (no long-term credentials)
- Use temporary credentials (STS) when possible
- Rotate access keys regularly (90 days recommended)
- Use AWS Secrets Manager or Parameter Store for storage
- Never hardcode credentials in source code

**Example** (IAM role):
```python
# Credentials automatically provided by IAM role
import boto3

# No need to specify credentials
s3 = boto3.client('s3')
s3.list_buckets()
```

### 3. Signature Debugging

**Common Issues**:
- Incorrect canonical request (whitespace, encoding)
- Wrong timestamp format
- Incorrect header ordering
- Missing required headers

**Debugging Tips**:
1. Compare canonical request with AWS examples
2. Verify timestamp is ISO 8601 format
3. Check header normalization (lowercase, trimmed)
4. Enable SDK debug logging

**SDK Debug Logging**:
```python
import boto3
import logging

# Enable debug logging
boto3.set_stream_logger('', logging.DEBUG)
```

### 4. Performance Optimization

**Caching**:
- Cache signing keys (valid for 24 hours)
- Reuse HTTP connections
- Batch requests when possible

**Example** (key caching):
```python
from functools import lru_cache
from datetime import datetime

@lru_cache(maxsize=10)
def get_cached_signing_key(secret_key, date_stamp, region, service):
    return get_signature_key(secret_key, date_stamp, region, service)

# Use cached key
date_stamp = datetime.utcnow().strftime('%Y%m%d')
signing_key = get_cached_signing_key(secret_key, date_stamp, region, service)
```

### 5. Error Handling

**Common Errors**:
- `SignatureDoesNotMatch`: Signature calculation error
- `RequestExpired`: Timestamp outside 5-minute window
- `AccessDenied`: Valid signature but no IAM permission
- `InvalidAccessKeyId`: Access key doesn't exist

**Error Handling Pattern**:
```python
try:
    response = client.list_users()
except client.exceptions.SignatureDoesNotMatch as e:
    # Signature error - check signing logic
    logger.error("Signature error", exc_info=True)
except client.exceptions.RequestExpired as e:
    # Clock skew - sync system time
    logger.error("Request expired - check system clock")
except client.exceptions.AccessDenied as e:
    # Permission error - check IAM policies
    logger.error("Access denied - insufficient permissions")
```

## Use Cases

### 1. API Request Signing
**Scenario**: Application makes AWS API calls
**Implementation**: Use SDK with IAM role credentials

### 2. Presigned URLs
**Scenario**: Temporary access to S3 objects
**Implementation**: Generate presigned URLs with expiration

### 3. Third-Party Service Integration
**Scenario**: External service needs AWS access
**Implementation**: Provide access key/secret key, service signs requests

### 4. Custom API Gateway Authentication
**Scenario**: API Gateway with IAM authentication
**Implementation**: Client signs requests, API Gateway validates via IAM

## Related AWS Services

- **AWS STS**: Temporary credentials (AssumeRole, GetSessionToken)
- **IAM**: User/role management, policies
- **AWS Secrets Manager**: Credential storage
- **API Gateway**: IAM-authenticated APIs
- **S3**: Presigned URLs, bucket policies
- **CloudFront**: Signed URLs/cookies

## Summary

AWS Signature Version 4 provides robust, cryptographic authentication for AWS API requests through request signing rather than token transmission.

**Key Strengths**:
- Secret key never transmitted
- Request integrity protection (payload hashing)
- Replay attack prevention (timestamp validation)
- Service/region scoped signatures
- Daily key derivation limits exposure

**Key Requirements**:
- Accurate system clock (5-minute tolerance)
- Correct canonical request generation
- Proper URL encoding and header normalization
- Secure credential storage

**Recommendation**: Always use AWS SDKs for automatic signing. Manual implementation is error-prone and should only be used when SDK is unavailable. For sharing temporary access, use presigned URLs or STS temporary credentials instead of sharing long-term access keys.
