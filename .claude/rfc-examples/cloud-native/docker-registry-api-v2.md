# Docker Registry HTTP API V2 Specification

**Source**: https://distribution.github.io/distribution/spec/api/
**Source**: https://docs.docker.com/registry/spec/api/
**Type**: CNCF-standardized (OCI Distribution Specification)
**Domain**: Container image distribution

## Overview

The Docker Registry HTTP API V2 is the protocol that facilitates distribution of container images to Docker engines. It provides a standardized way to interact with Docker registry services for managing information about Docker images and enabling their distribution.

### Core Design Principles

1. **Content Addressable Storage**: All content identified by cryptographic digest
2. **Namespace-Oriented**: Rich authentication/authorization through namespace structure
3. **HTTP Semantic Leverage**: Uses standard HTTP methods and status codes
4. **Resumable Operations**: Support for resumable uploads and downloads
5. **Layered Architecture**: Separates manifest and blob operations

### Standardization Status

The Docker Registry HTTP API V2 has been adopted by the **Open Container Initiative (OCI)** as the OCI Distribution Specification, making it the de facto industry standard for container image distribution.

## Base URL and Versioning

All API endpoints are prefixed with the API version:

```
<scheme>://<registry-host>[:<port>]/v2/
```

### API Version Check

**Endpoint**: `GET /v2/`

**Purpose**: Check API availability and authentication

**Success Response**:
```http
HTTP/1.1 200 OK
Content-Type: application/json
```

**Authentication Required Response**:
```http
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Bearer realm="https://auth.example.com/token",service="registry.example.com"
```

## Authentication and Authorization

### Authentication Flow

1. **Anonymous Request**: Try accessing resource without credentials
2. **Challenge Response**: Server returns `401` with `WWW-Authenticate` header
3. **Token Request**: Client requests token from auth service
4. **Authenticated Request**: Client retries with `Authorization: Bearer <token>` header

### Authorization Scopes

Tokens include scopes defining permitted operations:

```
repository:samalba/my-app:pull,push
repository:library/ubuntu:pull
```

**Scope Format**: `repository:<name>:<action>[,<action>...]`

**Actions**:
- `pull`: Download operations (GET manifest, GET blob)
- `push`: Upload operations (PUT manifest, POST/PUT blob)
- `delete`: Deletion operations
- `*`: All operations

### WWW-Authenticate Header

```http
WWW-Authenticate: Bearer realm="<auth-service-url>",
                         service="<registry-service-name>",
                         scope="<requested-scope>"
```

## Content Digests

### Digest Format

A content digest uniquely identifies content:

```
<algorithm>:<encoded>
```

**Example**:
```
sha256:6c3c624b58dbbcd3c0dd82b4c53f04194d1247c6eebdaab7c610cf7d66709b3b
```

### Supported Algorithms

- **sha256**: Required, primary algorithm
- **sha512**: Optional, additional security
- Algorithm identifier must match regex: `[a-z0-9]+([+._-][a-z0-9]+)*`

### Digest Verification

Clients MUST verify content matches digest after download:

1. Download content
2. Compute digest using specified algorithm
3. Compare computed digest with provided digest
4. Reject if mismatch

## Manifest Operations

Manifests describe the structure of container images.

### Manifest Types

**Image Manifest** (Media Type: `application/vnd.docker.distribution.manifest.v2+json`):
- Single-architecture image
- References configuration blob and layer blobs

**Manifest List** (Media Type: `application/vnd.docker.distribution.manifest.list.v2+json`):
- Multi-architecture image
- References multiple image manifests for different platforms

**OCI Image Manifest** (Media Type: `application/vnd.oci.image.manifest.v1+json`):
- OCI standard format
- Compatible with Docker V2 schema 2

### Pull Manifest

**Endpoint**: `GET /v2/<name>/manifests/<reference>`

**Parameters**:
- `<name>`: Repository name (may include multiple path segments)
- `<reference>`: Tag name or digest

**Request Headers**:
```http
Accept: application/vnd.docker.distribution.manifest.v2+json
Accept: application/vnd.docker.distribution.manifest.list.v2+json
Accept: application/vnd.oci.image.manifest.v1+json
```

**Success Response**:
```http
HTTP/1.1 200 OK
Content-Type: application/vnd.docker.distribution.manifest.v2+json
Docker-Content-Digest: sha256:6c3c624b58dbbcd3c0dd82b4c53f04194d1247c6eebdaab7c610cf7d66709b3b
Content-Length: 1234

{
  "schemaVersion": 2,
  "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
  "config": {
    "mediaType": "application/vnd.docker.container.image.v1+json",
    "size": 7023,
    "digest": "sha256:b5b2b2c50720..."
  },
  "layers": [
    {
      "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
      "size": 32654,
      "digest": "sha256:e692418e3570..."
    }
  ]
}
```

**Error Responses**:
- `404 Not Found`: Manifest does not exist
- `401 Unauthorized`: Authentication required

### Push Manifest

**Endpoint**: `PUT /v2/<name>/manifests/<reference>`

**Request Headers**:
```http
Content-Type: application/vnd.docker.distribution.manifest.v2+json
Content-Length: 1234
```

**Request Body**: JSON manifest

**Success Response**:
```http
HTTP/1.1 201 Created
Location: https://registry.example.com/v2/<name>/manifests/sha256:6c3c624b...
Docker-Content-Digest: sha256:6c3c624b58dbbcd3c0dd82b4c53f04194d1247c6eebdaab7c610cf7d66709b3b
```

**Preconditions**:
- All referenced blobs must already exist in registry
- Manifest must be valid JSON
- All digests must be correctly formatted

**Error Responses**:
- `400 Bad Request`: Invalid manifest
- `404 Not Found`: Referenced blob doesn't exist (MANIFEST_BLOB_UNKNOWN)

### Delete Manifest

**Endpoint**: `DELETE /v2/<name>/manifests/<reference>`

**Important**: `<reference>` MUST be a digest, not a tag

**Success Response**:
```http
HTTP/1.1 202 Accepted
```

**Error Responses**:
- `404 Not Found`: Manifest does not exist
- `405 Method Not Allowed`: Deletion not supported

## Blob Operations

Blobs store actual content: configuration objects and layer tarballs.

### Check Blob Existence

**Endpoint**: `HEAD /v2/<name>/blobs/<digest>`

**Success Response**:
```http
HTTP/1.1 200 OK
Content-Length: 1234567
Docker-Content-Digest: sha256:6c3c624b58dbbcd3c0dd82b4c53f04194d1247c6eebdaab7c610cf7d66709b3b
```

### Pull Blob

**Endpoint**: `GET /v2/<name>/blobs/<digest>`

**Success Response**:
```http
HTTP/1.1 200 OK
Content-Type: application/octet-stream
Content-Length: 1234567
Docker-Content-Digest: sha256:6c3c624b58dbbcd3c0dd82b4c53f04194d1247c6eebdaab7c610cf7d66709b3b

<binary data>
```

**Range Requests**: Supported via standard HTTP Range header

```http
GET /v2/<name>/blobs/<digest>
Range: bytes=0-1023
```

### Initiate Blob Upload

**Endpoint**: `POST /v2/<name>/blobs/uploads/`

**Success Response**:
```http
HTTP/1.1 202 Accepted
Location: https://registry.example.com/v2/<name>/blobs/uploads/<uuid>
Range: 0-0
Docker-Upload-UUID: <uuid>
```

The `Location` header contains the URL for continuing the upload.

### Upload Blob Chunk

**Endpoint**: `PATCH /v2/<name>/blobs/uploads/<uuid>`

**Request Headers**:
```http
Content-Type: application/octet-stream
Content-Length: 1024
Content-Range: 0-1023
```

**Request Body**: Binary chunk data

**Success Response**:
```http
HTTP/1.1 202 Accepted
Location: https://registry.example.com/v2/<name>/blobs/uploads/<uuid>
Range: 0-1023
Docker-Upload-UUID: <uuid>
```

**Resumption**: Client can resume using `Range` header value from response

### Complete Blob Upload

**Endpoint**: `PUT /v2/<name>/blobs/uploads/<uuid>?digest=<digest>`

**Query Parameters**:
- `digest`: Expected digest of the complete blob (required)

**Request Body**: Final chunk (may be empty if all data uploaded via PATCH)

**Success Response**:
```http
HTTP/1.1 201 Created
Location: https://registry.example.com/v2/<name>/blobs/<digest>
Docker-Content-Digest: sha256:6c3c624b58dbbcd3c0dd82b4c53f04194d1247c6eebdaab7c610cf7d66709b3b
```

**Verification**: Registry computes digest and compares with provided digest

**Error Responses**:
- `400 Bad Request`: Digest mismatch (DIGEST_INVALID)

### Cancel Blob Upload

**Endpoint**: `DELETE /v2/<name>/blobs/uploads/<uuid>`

**Success Response**:
```http
HTTP/1.1 204 No Content
```

### Monolithic Blob Upload

Single request upload for smaller blobs:

**Endpoint**: `POST /v2/<name>/blobs/uploads/?digest=<digest>`

**Request Headers**:
```http
Content-Type: application/octet-stream
Content-Length: 1234
```

**Request Body**: Complete blob data

**Success Response**:
```http
HTTP/1.1 201 Created
Location: https://registry.example.com/v2/<name>/blobs/<digest>
Docker-Content-Digest: sha256:6c3c624b58dbbcd3c0dd82b4c53f04194d1247c6eebdaab7c610cf7d66709b3b
```

### Mount Blob

Copy blob from another repository (same registry):

**Endpoint**: `POST /v2/<name>/blobs/uploads/?mount=<digest>&from=<source-repo>`

**Query Parameters**:
- `mount`: Digest of blob to mount
- `from`: Source repository name

**Success Response** (blob already exists):
```http
HTTP/1.1 201 Created
Location: https://registry.example.com/v2/<name>/blobs/<digest>
Docker-Content-Digest: sha256:6c3c624b58dbbcd3c0dd82b4c53f04194d1247c6eebdaab7c610cf7d66709b3b
```

**Fallback Response** (blob needs uploading):
```http
HTTP/1.1 202 Accepted
Location: https://registry.example.com/v2/<name>/blobs/uploads/<uuid>
```

### Delete Blob

**Endpoint**: `DELETE /v2/<name>/blobs/<digest>`

**Success Response**:
```http
HTTP/1.1 202 Accepted
```

**Note**: Blob may not be immediately deleted (garbage collection scheduled)

## Catalog Operations

### List Repositories

**Endpoint**: `GET /v2/_catalog`

**Query Parameters**:
- `n`: Maximum number of results (pagination limit)
- `last`: Last repository name from previous response (pagination marker)

**Success Response**:
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "repositories": [
    "library/ubuntu",
    "library/nginx",
    "myorg/myapp"
  ]
}
```

**Pagination Example**:
1. `GET /v2/_catalog?n=100`
2. `GET /v2/_catalog?n=100&last=library/nginx`

### List Tags

**Endpoint**: `GET /v2/<name>/tags/list`

**Query Parameters**:
- `n`: Maximum number of results
- `last`: Last tag name from previous response

**Success Response**:
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "name": "library/ubuntu",
  "tags": [
    "latest",
    "22.04",
    "20.04",
    "18.04"
  ]
}
```

**Pagination**: Same as catalog (use `n` and `last` parameters)

## Error Response Format

All errors follow consistent JSON structure:

```json
{
  "errors": [
    {
      "code": "MANIFEST_UNKNOWN",
      "message": "manifest unknown",
      "detail": "The manifest identified by the digest is unknown to the registry"
    }
  ]
}
```

### Error Structure

- **code**: Machine-readable error identifier (uppercase with underscores)
- **message**: Human-readable short description
- **detail**: Optional detailed explanation or additional context

### Standard Error Codes

| Error Code | HTTP Status | Description |
|------------|-------------|-------------|
| BLOB_UNKNOWN | 404 | Blob not found in registry |
| BLOB_UPLOAD_INVALID | 400 | Blob upload invalid |
| BLOB_UPLOAD_UNKNOWN | 404 | Upload session not found |
| DIGEST_INVALID | 400 | Digest format invalid or mismatch |
| MANIFEST_BLOB_UNKNOWN | 404 | Manifest references unknown blob |
| MANIFEST_INVALID | 400 | Manifest is invalid |
| MANIFEST_UNKNOWN | 404 | Manifest not found |
| MANIFEST_UNVERIFIED | 400 | Manifest verification failed |
| NAME_INVALID | 400 | Repository name invalid |
| NAME_UNKNOWN | 404 | Repository name not found |
| SIZE_INVALID | 400 | Size mismatch |
| TAG_INVALID | 400 | Tag name invalid |
| UNAUTHORIZED | 401 | Authentication required |
| DENIED | 403 | Access denied |
| UNSUPPORTED | 400 | Operation not supported |

## Content Negotiation

### Media Types

Clients use `Accept` header to specify preferred manifest formats:

```http
Accept: application/vnd.docker.distribution.manifest.v2+json,
        application/vnd.docker.distribution.manifest.list.v2+json;q=0.9,
        application/vnd.oci.image.manifest.v1+json;q=0.8
```

**Quality Values**: Indicate preference order (higher values preferred)

### Manifest Schema Versions

**Schema 1** (deprecated):
- Media Type: `application/vnd.docker.distribution.manifest.v1+json`
- No longer recommended
- Lacks multi-architecture support

**Schema 2**:
- Media Type: `application/vnd.docker.distribution.manifest.v2+json`
- Current Docker standard
- Supports multi-architecture via manifest lists

**OCI Image Manifest**:
- Media Type: `application/vnd.oci.image.manifest.v1+json`
- OCI standard
- Interoperable with Docker

### Content-Type Response

Server indicates format in `Content-Type` header:

```http
Content-Type: application/vnd.docker.distribution.manifest.v2+json
```

## Namespace Structure

Repository names follow hierarchical structure:

```
<namespace>/<repository>
<organization>/<project>/<component>
```

**Rules**:
- Components separated by `/`
- Each component must match: `[a-z0-9]+([._-][a-z0-9]+)*`
- Total length: 2-255 characters
- Minimum 2 characters per component

**Examples**:
- `library/ubuntu` (official image)
- `myorg/myapp` (organization image)
- `myorg/team/project/service` (deep hierarchy)

## Push Workflow

Typical sequence for pushing an image:

1. **Authentication**: Obtain token with `push` scope
2. **Upload Configuration Blob**:
   - POST to initiate upload
   - PATCH to upload data (or skip for small blobs)
   - PUT to complete with digest
3. **Upload Layer Blobs** (for each layer):
   - Same upload sequence as config
   - May use mount if layer exists in another repo
4. **Push Manifest**:
   - PUT manifest referencing all uploaded blobs
   - Registry validates all blobs exist

## Pull Workflow

Typical sequence for pulling an image:

1. **Authentication**: Obtain token with `pull` scope
2. **Pull Manifest**:
   - GET manifest by tag or digest
   - If manifest list, select appropriate platform manifest
3. **Pull Configuration Blob**:
   - GET blob using digest from manifest
4. **Pull Layer Blobs** (for each layer):
   - GET blob using digest from manifest
   - May use range requests for resumption
   - Verify digest after download

## Cross-Repository Blob Mounting

Optimization for sharing layers between repositories:

**Use Case**: Copy image from `source/app:v1` to `dest/app:v2`

**Process**:
1. Pull manifest from `source/app:v1`
2. For each blob in manifest:
   - Attempt mount: `POST /v2/dest/app/blobs/uploads/?mount=<digest>&from=source/app`
   - If `201 Created`: Blob mounted successfully
   - If `202 Accepted`: Blob needs uploading
3. Push new manifest to `dest/app:v2`

**Benefits**:
- No network transfer for shared layers
- Instant "copy" operation
- Efficient registry storage

## Resumable Uploads

Support for interrupted uploads:

1. **Initiate Upload**: `POST /v2/<name>/blobs/uploads/`
2. **Upload Chunks**: Multiple `PATCH` requests
3. **Check Progress**: `GET` to upload URL returns `Range` header
4. **Resume**: Continue from last byte in `Range`
5. **Complete**: `PUT` with digest

**Range Header Format**:
```http
Range: 0-1234567
```

Indicates bytes 0 through 1234567 successfully received.

## Garbage Collection

Registries may implement garbage collection:

- **Mark Phase**: Identify all reachable blobs (referenced by manifests)
- **Sweep Phase**: Delete unreferenced blobs
- **Tombstones**: Deleted manifests may remain briefly for consistency

**Implications**:
- Deleted blobs/manifests may not disappear immediately
- Unreferenced blobs eventually removed
- Storage reclaimed asynchronously

## API Extensions

Registry implementations may provide extensions:

- Additional endpoints (prefixed with `_`)
- Custom authentication mechanisms
- Enhanced search capabilities
- Replication APIs

**Discovery**: Extensions not standardized, consult registry documentation

## Cloud-Native Design Patterns

### 1. Content Addressability
- All content identified by cryptographic digest
- Immutable content (digest never changes)
- Verifiable integrity

### 2. Layer Deduplication
- Shared layers stored once
- Cross-repository mounting
- Efficient storage utilization

### 3. Resumable Operations
- Upload/download resumption
- Chunked transfers
- Network resilience

### 4. Namespace-Based Authorization
- Hierarchical repository names
- Scoped access tokens
- Fine-grained permissions

### 5. Stateless Protocol
- Each request self-contained
- No session state on server
- Horizontal scalability

### 6. Standard HTTP Semantics
- Uses HTTP status codes appropriately
- Leverages HTTP caching
- Follows REST principles

### 7. Multi-Platform Support
- Manifest lists for architecture selection
- Client-side platform matching
- Transparent multi-arch images

### 8. Backward Compatibility
- Multiple manifest schema versions
- Content negotiation
- Gradual migration path

## Performance Considerations

### Caching

Registries should leverage HTTP caching:

- **ETag**: Manifest digest serves as ETag
- **Cache-Control**: Blobs are immutable (long cache times)
- **If-None-Match**: Avoid re-downloading unchanged manifests

### Parallel Downloads

Clients should parallelize:

- Multiple layer downloads simultaneously
- Chunked downloads for large layers
- Independent verification per blob

### Compression

Layers typically compressed:

- `application/vnd.docker.image.rootfs.diff.tar.gzip` (gzip)
- `application/vnd.docker.image.rootfs.diff.tar.zstd` (zstd)
- Client decompresses after download

### CDN Integration

Registry APIs designed for CDN fronting:

- Blob URLs cacheable by path
- Immutable content (digests)
- GET-heavy workload (pulls >> pushes)

## Security Considerations

### Authentication

- Bearer token authentication standard
- Tokens scoped to specific operations
- Short token lifetimes recommended

### Authorization

- Repository-level access control
- Separate push/pull permissions
- Namespace-based hierarchies

### Content Trust

Docker Content Trust (Notary):

- Cryptographic signatures on manifests
- Publisher verification
- Not part of core Registry API (layered on top)

### Vulnerability Scanning

- Not part of Registry API
- Implemented by higher-layer services
- Scan blobs after upload

## Compatibility Notes

### Docker Engine

Docker Engine uses this API for:

- `docker pull`
- `docker push`
- `docker search` (limited support)

### OCI Clients

OCI-compliant tools (e.g., Podman, Buildah, Skopeo) use this API with OCI media types.

### Kubernetes

Kubernetes uses this API via:

- Container runtime (containerd, CRI-O)
- Image pull from kubelets
- Private registry integration

## Summary of Key Patterns

1. **Content-addressable storage** with cryptographic digests
2. **Resumable chunked uploads** for large blobs
3. **Namespace-based authorization** scopes
4. **Layered architecture** (manifest + blobs)
5. **Multi-platform support** via manifest lists
6. **Standard HTTP semantics** (status codes, headers)
7. **Consistent error response** format
8. **Pagination for large collections**
9. **Cross-repository blob mounting** for efficiency
10. **Stateless RESTful protocol** for scalability

These patterns make the Docker Registry API a robust, scalable, and interoperable foundation for container image distribution in cloud-native environments.
