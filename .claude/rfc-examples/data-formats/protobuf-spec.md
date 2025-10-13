# Protocol Buffers (Protobuf) Specification

## Overview

**Name:** Protocol Buffers (Protobuf)

**Organization:** Google

**Current Version:** Proto3

**Purpose:** Language-agnostic, platform-neutral, extensible mechanism for serializing structured data

**Abstract:** Protocol Buffers is a data serialization format designed for efficient, structured data exchange between different programming languages and systems. It generates type-safe code from a single `.proto` definition file.

## Key Syntax Rules and Message Definitions

### Proto File Structure

**Basic Syntax:**
```proto
syntax = "proto3";

package example;

import "other.proto";

message MessageName {
  // field definitions
}

enum EnumName {
  // enum values
}

service ServiceName {
  // RPC methods
}
```

### Message Definition

**Syntax:**
```proto
message MessageName {
  field_type field_name = field_number;
}
```

**Example:**
```proto
message SearchRequest {
  string query = 1;
  int32 page_number = 2;
  int32 results_per_page = 3;
}
```

### Field Rules

**Field Components:**
1. **Type:** Scalar type, enum, or message type
2. **Name:** Lowercase with underscores
3. **Field Number:** Unique identifier (1-536,870,911)

**Field Number Ranges:**
- 1-15: Single-byte encoding (use for frequent fields)
- 16-2047: Two-byte encoding
- 19000-19999: Reserved by Protocol Buffers
- 536,870,912-max: Not allowed

### Scalar Types

| Proto Type | C++ Type | Java Type | Python Type | Go Type | Notes |
|------------|----------|-----------|-------------|---------|-------|
| double | double | double | float | float64 | |
| float | float | float | float | float32 | |
| int32 | int32 | int | int | int32 | Variable-length |
| int64 | int64 | long | int/long | int64 | Variable-length |
| uint32 | uint32 | int | int/long | uint32 | Variable-length |
| uint64 | uint64 | long | int/long | uint64 | Variable-length |
| sint32 | int32 | int | int | int32 | Efficient negative |
| sint64 | int64 | long | int/long | int64 | Efficient negative |
| fixed32 | uint32 | int | int/long | uint32 | Always 4 bytes |
| fixed64 | uint64 | long | int/long | uint64 | Always 8 bytes |
| sfixed32 | int32 | int | int | int32 | Always 4 bytes |
| sfixed64 | int64 | long | int/long | int64 | Always 8 bytes |
| bool | bool | boolean | bool | bool | |
| string | string | String | str/unicode | string | UTF-8 or 7-bit ASCII |
| bytes | string | ByteString | bytes | []byte | Arbitrary bytes |

### Field Cardinality

**Singular (default in proto3):**
```proto
message Example {
  string field = 1;  // Zero or one value
}
```

**Repeated (arrays/lists):**
```proto
message Example {
  repeated int32 numbers = 1;  // Zero or more values
}
```

**Optional (proto3):**
```proto
message Example {
  optional string field = 1;  // Explicitly optional
}
```

**Map:**
```proto
message Example {
  map<string, int32> counts = 1;
}
```

### Enum Definition

**Syntax:**
```proto
enum EnumName {
  ENUM_VALUE_UNSPECIFIED = 0;  // First value must be 0
  ENUM_VALUE_ONE = 1;
  ENUM_VALUE_TWO = 2;
}
```

**Example:**
```proto
enum PhoneType {
  PHONE_TYPE_UNSPECIFIED = 0;
  PHONE_TYPE_MOBILE = 1;
  PHONE_TYPE_HOME = 2;
  PHONE_TYPE_WORK = 3;
}

message PhoneNumber {
  string number = 1;
  PhoneType type = 2;
}
```

### Nested Types

**Nested Messages:**
```proto
message Person {
  string name = 1;

  message Address {
    string street = 1;
    string city = 2;
    string country = 3;
  }

  Address address = 2;
}
```

**Usage outside:**
```proto
message Company {
  Person.Address headquarters = 1;
}
```

### Oneof (Union)

**Syntax:**
```proto
message SampleMessage {
  oneof test_oneof {
    string name = 1;
    int32 id = 2;
  }
}
```

**Only one field can be set at a time**

## Encoding Rules and Wire Format

### Wire Format Basics

**Key-Value Pairs:**
Each field encoded as key-value pair:
```
key = (field_number << 3) | wire_type
```

**Wire Types:**
| Type | Meaning | Used For |
|------|---------|----------|
| 0 | Varint | int32, int64, uint32, uint64, sint32, sint64, bool, enum |
| 1 | 64-bit | fixed64, sfixed64, double |
| 2 | Length-delimited | string, bytes, embedded messages, repeated fields |
| 5 | 32-bit | fixed32, sfixed32, float |

### Varint Encoding

**Variable-length integer encoding:**
- 7 bits per byte for value
- MSB indicates continuation (1 = more bytes follow)

**Example: 300**
```
Binary: 100101100
Varint: 10101100 00000010
Hex: 0xAC 0x02
```

**Example: 1**
```
Binary: 00000001
Varint: 00000001
Hex: 0x01
```

### Message Encoding Example

**Message:**
```proto
message Test1 {
  int32 a = 1;
}
```

**Setting a = 150:**
```
Field number: 1
Wire type: 0 (varint)
Key: (1 << 3) | 0 = 0x08

Value (150 as varint): 0x96 0x01

Encoded: 0x08 0x96 0x01
```

### String Encoding

**Message:**
```proto
message Test2 {
  string b = 2;
}
```

**Setting b = "testing":**
```
Key: (2 << 3) | 2 = 0x12
Length: 7
Value: "testing" (UTF-8 bytes)

Encoded: 0x12 0x07 74 65 73 74 69 6E 67
```

### Embedded Message Encoding

**Definition:**
```proto
message Test3 {
  Test1 c = 3;
}
```

**Setting c.a = 150:**
```
Outer key: (3 << 3) | 2 = 0x1A
Length: 3 (bytes in embedded message)
Embedded message: 0x08 0x96 0x01

Encoded: 0x1A 0x03 0x08 0x96 0x01
```

### Repeated Fields

**Packed encoding (default for repeated numeric types):**
```proto
message Test4 {
  repeated int32 d = 4;
}
```

**Setting d = [3, 270, 86942]:**
```
Key: (4 << 3) | 2 = 0x22
Length: 6
Values: 0x03 0x8E 0x02 0x9E 0xA7 0x05

Encoded: 0x22 0x06 0x03 0x8E 0x02 0x9E 0xA7 0x05
```

## Representative Examples

### Basic Message

```proto
syntax = "proto3";

package example;

message Person {
  string name = 1;
  int32 id = 2;
  string email = 3;

  enum PhoneType {
    PHONE_TYPE_UNSPECIFIED = 0;
    PHONE_TYPE_MOBILE = 1;
    PHONE_TYPE_HOME = 2;
    PHONE_TYPE_WORK = 3;
  }

  message PhoneNumber {
    string number = 1;
    PhoneType type = 2;
  }

  repeated PhoneNumber phones = 4;
}
```

### Address Book Example

```proto
syntax = "proto3";

package tutorial;

import "google/protobuf/timestamp.proto";

message Person {
  string name = 1;
  int32 id = 2;
  string email = 3;

  repeated PhoneNumber phones = 4;

  google.protobuf.Timestamp last_updated = 5;
}

message PhoneNumber {
  string number = 1;
  PhoneType type = 2;
}

enum PhoneType {
  PHONE_TYPE_UNSPECIFIED = 0;
  PHONE_TYPE_MOBILE = 1;
  PHONE_TYPE_HOME = 2;
  PHONE_TYPE_WORK = 3;
}

message AddressBook {
  repeated Person people = 1;
}
```

### Search Request/Response

```proto
syntax = "proto3";

package search;

message SearchRequest {
  string query = 1;
  int32 page_number = 2;
  int32 results_per_page = 3;

  enum SortOrder {
    SORT_ORDER_UNSPECIFIED = 0;
    SORT_ORDER_ASCENDING = 1;
    SORT_ORDER_DESCENDING = 2;
  }

  SortOrder sort = 4;
}

message SearchResponse {
  repeated Result results = 1;
  int32 total_results = 2;
  int32 page = 3;
}

message Result {
  string url = 1;
  string title = 2;
  repeated string snippets = 3;
}
```

### Complex Nested Example

```proto
syntax = "proto3";

package company;

message Company {
  string name = 1;
  repeated Department departments = 2;
  Address headquarters = 3;
}

message Department {
  string name = 1;
  repeated Employee employees = 2;
  Employee manager = 3;
}

message Employee {
  string name = 1;
  int32 id = 2;
  string email = 3;
  Address address = 4;

  message Salary {
    int32 amount = 1;
    string currency = 2;
  }

  Salary salary = 5;
}

message Address {
  string street = 1;
  string city = 2;
  string state = 3;
  string postal_code = 4;
  string country = 5;
}
```

### Map Example

```proto
syntax = "proto3";

message Config {
  map<string, string> settings = 1;
  map<string, int32> counters = 2;
  map<int32, Feature> features = 3;
}

message Feature {
  string name = 1;
  bool enabled = 2;
}
```

## Key Features and Best Practices

### Schema Evolution

**Backward Compatibility Rules:**
1. Don't change field numbers
2. New fields should be optional or repeated
3. Old fields can be deleted (but reserve the number)
4. Don't change field types

**Field Reservation:**
```proto
message Example {
  reserved 2, 15, 9 to 11;
  reserved "foo", "bar";

  string baz = 1;
  // field 2 is reserved
  string qux = 3;
}
```

### Optimization Options

**File-level options:**
```proto
syntax = "proto3";

option optimize_for = SPEED;  // Default
// option optimize_for = CODE_SIZE;
// option optimize_for = LITE_RUNTIME;
```

**Modes:**
- `SPEED`: Optimized for fast serialization/deserialization
- `CODE_SIZE`: Minimal generated code size
- `LITE_RUNTIME`: Smaller runtime library (mobile)

### Best Practices

**Field Numbers:**
1. Use 1-15 for frequently used fields (1-byte encoding)
2. Reserve numbers 1-15 for common fields
3. Leave gaps for future expansion
4. Never reuse field numbers

**Naming Conventions:**
```proto
// Message names: PascalCase
message PersonInfo { }

// Field names: snake_case
message Example {
  string first_name = 1;
  int32 user_id = 2;
}

// Enum names: UPPER_SNAKE_CASE
enum Status {
  STATUS_UNSPECIFIED = 0;
  STATUS_ACTIVE = 1;
}
```

**Required Fields (proto2 only):**
- Avoid `required` fields
- Use optional or repeated instead
- Required fields prevent schema evolution

**Default Values:**
- Proto3: All fields have default values
- Numbers: 0
- Bools: false
- Strings: ""
- Enums: First value (must be 0)
- Messages: null/not set

**Packages:**
```proto
syntax = "proto3";

package com.example.project;
```
- Prevents naming conflicts
- Generates namespaced code
- Use reverse domain notation

### Performance Tips

1. **Field Ordering:**
   - Put frequently accessed fields first
   - Group related fields together

2. **Message Size:**
   - Keep messages small and focused
   - Split large messages if possible

3. **Repeated Fields:**
   - Use packed encoding for primitives
   - Consider pagination for large lists

4. **String Pooling:**
   - Reuse identical strings when possible

5. **Lazy Parsing:**
   - Available in some language implementations
   - Defer parsing of large embedded messages

### Common Patterns

**Versioning:**
```proto
message Request {
  int32 version = 1;
  oneof payload {
    RequestV1 v1 = 2;
    RequestV2 v2 = 3;
  }
}
```

**Pagination:**
```proto
message ListRequest {
  int32 page_size = 1;
  string page_token = 2;
}

message ListResponse {
  repeated Item items = 1;
  string next_page_token = 2;
}
```

**Timestamps:**
```proto
import "google/protobuf/timestamp.proto";

message Event {
  string name = 1;
  google.protobuf.Timestamp created_at = 2;
}
```

**Any Type (Dynamic Types):**
```proto
import "google/protobuf/any.proto";

message ErrorInfo {
  string message = 1;
  google.protobuf.Any details = 2;
}
```

## Use Cases

### Ideal Applications

1. **Microservices Communication:**
   - gRPC services
   - Internal APIs
   - Service mesh data plane

2. **Data Storage:**
   - Database serialization
   - Cache storage
   - Log files

3. **Configuration Files:**
   - Application config
   - Feature flags
   - System settings

4. **Message Queues:**
   - Event streams
   - Command queues
   - Pub/sub messages

5. **Mobile Applications:**
   - Client-server communication
   - Offline data storage
   - Sync protocols

### Comparison with Other Formats

**vs. JSON:**
- Smaller size (binary)
- Faster serialization
- Type safety
- But: Not human-readable

**vs. XML:**
- Much more compact
- Simpler schema
- Faster parsing
- Better tooling

**vs. CBOR:**
- Requires schema
- Better tooling/ecosystem
- Type-safe code generation
- Similar performance

## Language Support

**Official Support:**
- C++
- Java
- Python
- Go
- C#
- Objective-C
- Ruby
- PHP
- Dart

**Community Support:**
- JavaScript/TypeScript
- Rust
- Swift
- Kotlin
- Scala
- And many more...

## References

- **Source:** https://protobuf.dev/
- **GitHub:** https://github.com/protocolbuffers/protobuf
- **gRPC:** https://grpc.io/
