# Google API Design Guide

**Source:** Google Cloud
**URL:** https://cloud.google.com/apis/design
**Type:** Corporate API Design Standard
**In Use Since:** 2014 (internally), Public since 2016

## Overview

The Google API Design Guide is a comprehensive set of guidelines for designing APIs that are consistent with Google API Improvement Proposals (AIPs). Used internally at Google since 2014, this guide represents Google's extensive experience in designing Cloud APIs and other Google APIs.

## Applicability

- **Target APIs**: Both REST APIs and RPC APIs (gRPC focus)
- **Scope**: Cloud APIs, Google APIs, third-party APIs on Google Cloud
- **Adoption**: Strongly recommended for Cloud Endpoints developers
- **Nature**: Living document that evolves with new patterns

## Core Principles

### Resource-Oriented Design

The foundational principle of Google's API design is resource-oriented architecture.

**Key Concepts:**
- APIs should be designed around resources (nouns) not actions (verbs)
- Resources are identified by resource names
- Operations on resources use standard methods
- Custom methods available for operations that don't fit standard patterns

**Reference:** [AIP-121: Resource-oriented design](https://google.aip.dev/121)

### Resource Names

Structured naming convention for resources:

**Format:**
```
//service.googleapis.com/collection/resource-id/collection/resource-id
```

**Examples:**
```
//library.googleapis.com/shelves/shelf1/books/book2
//storage.googleapis.com/buckets/my-bucket/objects/my-object
```

**Characteristics:**
- Hierarchical structure
- Globally unique identifiers
- URL-safe components
- Predictable patterns

**Reference:** [AIP-122: Resource names](https://google.aip.dev/122)

## Standard Methods

Google APIs use five standard methods that map to HTTP verbs:

### List

**Purpose:** Retrieve a collection of resources

**HTTP Mapping:**
```
GET /v1/publishers/123/books
```

**Characteristics:**
- Returns multiple resources
- Supports pagination
- Supports filtering and sorting
- May return partial resources

**Reference:** [AIP-132: List](https://google.aip.dev/132)

### Get

**Purpose:** Retrieve a single resource

**HTTP Mapping:**
```
GET /v1/publishers/123/books/456
```

**Characteristics:**
- Returns complete resource
- Idempotent operation
- Uses resource name as identifier

**Reference:** [AIP-131: Get](https://google.aip.dev/131)

### Create

**Purpose:** Create a new resource

**HTTP Mapping:**
```
POST /v1/publishers/123/books
```

**Request Body:** Resource representation

**Response:** Created resource with generated ID

**Characteristics:**
- Non-idempotent by default
- Server assigns resource ID (usually)
- Returns complete created resource

**Reference:** [AIP-133: Create](https://google.aip.dev/133)

### Update

**Purpose:** Modify an existing resource

**HTTP Mapping:**
```
PATCH /v1/publishers/123/books/456
```

**Request Body:** Fields to update

**Characteristics:**
- Partial updates with field masks
- Idempotent operation
- Returns updated resource

**Reference:** [AIP-134: Update](https://google.aip.dev/134)

### Delete

**Purpose:** Remove a resource

**HTTP Mapping:**
```
DELETE /v1/publishers/123/books/456
```

**Characteristics:**
- Idempotent operation
- May return empty response or deleted resource
- Supports soft delete and cascade delete

**Reference:** [AIP-135: Delete](https://google.aip.dev/135)

## Custom Methods

For operations that don't fit standard methods:

**HTTP Mapping:**
```
POST /v1/publishers/123/books/456:publish
```

**Format:** `:customVerb` suffix on resource name

**Guidelines:**
- Use only when standard methods are insufficient
- Use descriptive, action-oriented names
- Document clearly in API specification
- Prefer POST for custom methods

**Common Examples:**
- `:cancel` - Cancel a long-running operation
- `:publish` - Publish content
- `:archive` - Archive a resource
- `:undelete` - Restore a deleted resource

**Reference:** [AIP-136: Custom methods](https://google.aip.dev/136)

## Common Design Patterns

### Pagination

**List Pagination:**
```
GET /v1/books?page_size=10&page_token=abc123
```

**Response:**
```json
{
  "books": [...],
  "next_page_token": "def456"
}
```

**Reference:** [AIP-158: Pagination](https://google.aip.dev/158)

### Filtering

**Field-level filtering:**
```
GET /v1/books?filter=genre='fiction' AND publish_year>2020
```

**Reference:** [AIP-160: Filtering](https://google.aip.dev/160)

### Field Masks

**Update with field mask:**
```
PATCH /v1/books/123?update_mask=title,description
```

**Purpose:** Specify exactly which fields to update

**Reference:** [AIP-161: Field masks](https://google.aip.dev/161)

### Long-Running Operations

**Pattern for operations that take significant time:**

**Start operation:**
```
POST /v1/books:import
```

**Response:**
```json
{
  "name": "operations/abc123",
  "metadata": {...},
  "done": false
}
```

**Check status:**
```
GET /v1/operations/abc123
```

**Reference:** [AIP-151: Long-running operations](https://google.aip.dev/151)

### Batch Operations

**Batch get:**
```
POST /v1/books:batchGet
Body: {"names": [...]}
```

**Batch create:**
```
POST /v1/books:batchCreate
Body: {"requests": [...]}
```

**Reference:** [AIP-159: Batch operations](https://google.aip.dev/159)

## Error Handling

### Error Response Format

```json
{
  "error": {
    "code": 404,
    "message": "Resource not found",
    "status": "NOT_FOUND",
    "details": [...]
  }
}
```

### Standard Error Codes

Map HTTP status codes to canonical error codes:

- `OK` (200): Success
- `INVALID_ARGUMENT` (400): Invalid request
- `UNAUTHENTICATED` (401): Authentication required
- `PERMISSION_DENIED` (403): Authorization failed
- `NOT_FOUND` (404): Resource not found
- `ALREADY_EXISTS` (409): Resource already exists
- `RESOURCE_EXHAUSTED` (429): Quota exceeded
- `INTERNAL` (500): Server error

**Reference:** [AIP-193: Errors](https://google.aip.dev/193)

## Versioning

### Version in URL Path

```
https://library.googleapis.com/v1/publishers/123/books
https://library.googleapis.com/v2/publishers/123/books
```

### Version Stability

- **Alpha:** Experimental, may break at any time
- **Beta:** Pre-release, avoid breaking changes
- **GA (General Availability):** Stable, backward compatible

### Breaking Changes

- Removing or renaming fields
- Changing field types
- Changing resource names
- Changing error codes

**Reference:** [AIP-180: Versioning](https://google.aip.dev/180)

## Documentation

### Inline Documentation

**Resource documentation:**
```protobuf
// A representation of a book in the library.
message Book {
  // The resource name of the book.
  // Format: publishers/{publisher}/books/{book}
  string name = 1;

  // The title of the book.
  string title = 2;

  // The author of the book.
  string author = 3;
}
```

### API Documentation Structure

1. **Overview:** High-level API description
2. **Quickstart:** Getting started guide
3. **Resources:** Documentation for each resource type
4. **Methods:** Documentation for each method
5. **Error handling:** Error codes and messages
6. **Authentication:** How to authenticate
7. **Examples:** Code samples in multiple languages

**Reference:** [AIP-192: Documentation](https://google.aip.dev/192)

## Standard Fields

### Common Fields Across Resources

- `name` (string): Resource name
- `uid` (string): Globally unique immutable ID
- `create_time` (Timestamp): Creation timestamp
- `update_time` (Timestamp): Last modification timestamp
- `delete_time` (Timestamp): Deletion timestamp (for soft delete)
- `etag` (string): Entity tag for concurrency control
- `display_name` (string): Human-readable name

**Reference:** [AIP-142: Standard fields](https://google.aip.dev/142)

## Request and Response Patterns

### List Request

```json
{
  "page_size": 10,
  "page_token": "abc123",
  "filter": "status='ACTIVE'",
  "order_by": "create_time desc"
}
```

### List Response

```json
{
  "resources": [...],
  "next_page_token": "def456",
  "total_size": 42
}
```

### Create Request

```json
{
  "resource_id": "custom-id",
  "resource": {
    "field1": "value1",
    "field2": "value2"
  }
}
```

### Update Request

```json
{
  "resource": {
    "name": "resources/123",
    "field1": "new_value"
  },
  "update_mask": "field1"
}
```

## Design for Consistency

### Naming Conventions

**Resource Names:**
- Use plural for collections: `/books`, `/authors`
- Use singular for resource: `/books/123`
- Use lowercase with hyphens: `/book-reviews`

**Field Names:**
- Use lowercase with underscores: `publish_date`
- Use clear, descriptive names: `author_name` not `an`
- Boolean fields start with verb: `is_published`, `has_cover`

**Method Names:**
- Standard methods: `List`, `Get`, `Create`, `Update`, `Delete`
- Custom methods: Use verb form: `Cancel`, `Publish`, `Archive`

### HTTP Mapping

**Standard method mapping:**
- `List` → `GET /collection`
- `Get` → `GET /collection/resource-id`
- `Create` → `POST /collection`
- `Update` → `PATCH /collection/resource-id`
- `Delete` → `DELETE /collection/resource-id`

**Custom method mapping:**
- `POST /collection/resource-id:customVerb`
- `POST /collection:customVerb` (for collection-level operations)

## Protocol Buffers

### Why Protocol Buffers

- **Strongly typed:** Type safety at compile time
- **Language agnostic:** Generate code for multiple languages
- **Forward/backward compatible:** Easy to evolve
- **Efficient:** Binary serialization

### API Definition Example

```protobuf
syntax = "proto3";

package library.v1;

import "google/api/annotations.proto";
import "google/api/resource.proto";

service Library {
  rpc ListBooks(ListBooksRequest) returns (ListBooksResponse) {
    option (google.api.http) = {
      get: "/v1/{parent=publishers/*}/books"
    };
  }

  rpc GetBook(GetBookRequest) returns (Book) {
    option (google.api.http) = {
      get: "/v1/{name=publishers/*/books/*}"
    };
  }
}

message Book {
  option (google.api.resource) = {
    type: "library.googleapis.com/Book"
    pattern: "publishers/{publisher}/books/{book}"
  };

  string name = 1;
  string title = 2;
  string author = 3;
}
```

## JSON/HTTP Transcoding

Google APIs support automatic transcoding between:
- **gRPC** (Protocol Buffers over HTTP/2)
- **REST** (JSON over HTTP/1.1)

This allows clients to use either protocol to access the same API.

## Best Practices Summary

1. **Design around resources:** Use resource-oriented design
2. **Use standard methods:** Prefer standard CRUD operations
3. **Follow naming conventions:** Consistent, predictable names
4. **Provide clear documentation:** Inline and external docs
5. **Version appropriately:** Use URL path versioning
6. **Handle errors consistently:** Use standard error format
7. **Support pagination:** Always paginate list operations
8. **Use field masks:** Allow partial updates
9. **Consider long-running ops:** For time-consuming operations
10. **Think about evolution:** Design for backward compatibility

## Key Differences from Other REST Approaches

1. **Resource names vs. URLs:** Emphasis on logical resource names
2. **Standard methods:** Fixed set of standard operations
3. **Custom methods:** Explicit pattern for non-CRUD operations
4. **Protocol Buffers:** Strong typing with HTTP/JSON transcoding
5. **Versioning:** Major versions in URL, minor versions transparent
6. **Filtering:** Structured filtering language
7. **Field masks:** Explicit field selection for updates

## References

- Main guide: https://cloud.google.com/apis/design
- AIP site: https://google.aip.dev/
- Changelog: https://cloud.google.com/apis/design/changelog
- Resource-oriented design: https://cloud.google.com/apis/design/resources

---

**Key Takeaways:**

1. Resource-oriented design is the foundation of Google's API philosophy
2. Standard methods (List, Get, Create, Update, Delete) cover most use cases
3. Custom methods provide escape hatch for non-standard operations
4. Protocol Buffers enable strong typing with JSON/HTTP compatibility
5. Consistency through naming conventions and standard patterns
6. Comprehensive documentation is essential for API adoption
7. Design for evolution with versioning and backward compatibility
