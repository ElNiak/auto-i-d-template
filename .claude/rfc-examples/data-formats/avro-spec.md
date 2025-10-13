# Apache Avro Specification

## Overview

**Name:** Apache Avro

**Organization:** Apache Software Foundation

**Current Version:** 1.11.1

**Purpose:** Data serialization system providing compact, fast, binary data format with rich data structures

**Abstract:** Avro is a data serialization framework that enables efficient data exchange across different programming languages and systems. It uses JSON for schema definition and provides compact binary encoding with strong schema evolution support.

## Key Syntax Rules and Schema Definitions

### Schema Types

**Primitive Types:**
- `null` - No value
- `boolean` - Binary value
- `int` - 32-bit signed integer
- `long` - 64-bit signed integer
- `float` - Single precision (32-bit) IEEE 754 floating-point
- `double` - Double precision (64-bit) IEEE 754 floating-point
- `bytes` - Sequence of 8-bit unsigned bytes
- `string` - Unicode character sequence

**Complex Types:**
- `record` - Named fields
- `enum` - Enumeration of strings
- `array` - Sequence of values
- `map` - Key-value pairs (string keys)
- `union` - One of several types
- `fixed` - Fixed-length byte sequence

### Record Schema

**Syntax:**
```json
{
  "type": "record",
  "name": "RecordName",
  "namespace": "com.example",
  "doc": "Documentation string",
  "fields": [
    {
      "name": "field_name",
      "type": "field_type",
      "doc": "Field documentation",
      "default": default_value
    }
  ]
}
```

**Example:**
```json
{
  "type": "record",
  "name": "User",
  "namespace": "com.example",
  "fields": [
    {"name": "name", "type": "string"},
    {"name": "age", "type": "int"},
    {"name": "email", "type": ["null", "string"], "default": null}
  ]
}
```

### Enum Schema

**Syntax:**
```json
{
  "type": "enum",
  "name": "EnumName",
  "namespace": "com.example",
  "symbols": ["SYMBOL1", "SYMBOL2", "SYMBOL3"]
}
```

**Example:**
```json
{
  "type": "enum",
  "name": "Suit",
  "symbols": ["SPADES", "HEARTS", "DIAMONDS", "CLUBS"]
}
```

### Array Schema

**Syntax:**
```json
{
  "type": "array",
  "items": "item_type"
}
```

**Example:**
```json
{
  "type": "array",
  "items": "string"
}
```

### Map Schema

**Syntax:**
```json
{
  "type": "map",
  "values": "value_type"
}
```

**Example:**
```json
{
  "type": "map",
  "values": "int"
}
```

### Union Schema

**Syntax:**
```json
["null", "string"]
```

**Example (optional field):**
```json
{
  "name": "middle_name",
  "type": ["null", "string"],
  "default": null
}
```

### Fixed Schema

**Syntax:**
```json
{
  "type": "fixed",
  "name": "FixedName",
  "size": byte_count
}
```

**Example:**
```json
{
  "type": "fixed",
  "name": "MD5",
  "size": 16
}
```

### Logical Types

**Enhanced primitive types:**

```json
{"type": "int", "logicalType": "date"}
{"type": "int", "logicalType": "time-millis"}
{"type": "long", "logicalType": "time-micros"}
{"type": "long", "logicalType": "timestamp-millis"}
{"type": "long", "logicalType": "timestamp-micros"}
{"type": "fixed", "name": "decimal", "size": 8, "logicalType": "decimal", "precision": 18, "scale": 2}
{"type": "string", "logicalType": "uuid"}
```

**Examples:**
```json
{
  "name": "birthday",
  "type": {"type": "int", "logicalType": "date"}
}

{
  "name": "price",
  "type": {
    "type": "bytes",
    "logicalType": "decimal",
    "precision": 10,
    "scale": 2
  }
}
```

## Encoding Rules and Binary Format

### Primitive Type Encoding

**null:**
- Zero bytes (no encoding)

**boolean:**
- 1 byte: 0x00 (false) or 0x01 (true)

**int and long:**
- Variable-length zig-zag encoding
- Efficient for small values

**Zig-zag Encoding Examples:**
| Value | Encoded | Hex |
|-------|---------|-----|
| 0 | 0 | 0x00 |
| -1 | 1 | 0x01 |
| 1 | 2 | 0x02 |
| -2 | 3 | 0x03 |
| 2 | 4 | 0x04 |

**float:**
- 4 bytes, IEEE 754 single-precision, little-endian

**double:**
- 8 bytes, IEEE 754 double-precision, little-endian

**bytes:**
- Long (length) followed by that many bytes

**string:**
- Long (length) followed by UTF-8 encoded bytes

### Complex Type Encoding

**record:**
- Fields encoded in declaration order
- No field names or type info in encoding (schema-dependent)

**enum:**
- Encoded as int (index of symbol in symbols array)

**array:**
```
series of blocks:
  long (block count)
  long (block size in bytes, optional)
  [items...]
  ...
  long (0 - end marker)
```

**map:**
```
series of blocks:
  long (block count)
  long (block size in bytes, optional)
  [string key, value...]
  ...
  long (0 - end marker)
```

**union:**
- Long (index of type in union schema)
- Value (encoded per its type)

**fixed:**
- Exactly size bytes

### Encoding Examples

**Simple Record:**
```json
Schema:
{
  "type": "record",
  "name": "Person",
  "fields": [
    {"name": "name", "type": "string"},
    {"name": "age", "type": "int"}
  ]
}

Data: {"name": "Alice", "age": 30}

Encoding:
- String length: 0x0A (5 * 2 = 10)
- String bytes: "Alice" (5 bytes)
- Int: 0x3C (30 * 2 = 60)
```

**Union Example:**
```json
Schema: ["null", "string"]

Data: "hello"

Encoding:
- Union index: 0x02 (index 1 * 2)
- String length: 0x0A (5 * 2)
- String bytes: "hello"
```

**Array Example:**
```json
Schema: {"type": "array", "items": "int"}

Data: [1, 2, 3]

Encoding:
- Block count: 0x06 (3 * 2)
- Item 1: 0x02 (1 * 2)
- Item 2: 0x04 (2 * 2)
- Item 3: 0x06 (3 * 2)
- End marker: 0x00
```

### Data File Format

**Structure:**
```
magic bytes: 'O' 'b' 'j' 0x01
file metadata:
  - codec (compression)
  - schema (JSON string)
  - custom metadata
sync marker (16 bytes)
data blocks:
  - object count
  - compressed block size
  - serialized objects
  - sync marker
```

**Compression Codecs:**
- `null` - No compression
- `deflate` - DEFLATE compression
- `snappy` - Snappy compression
- `bzip2` - bzip2 compression
- `zstandard` - Zstandard compression

## Representative Examples

### Simple User Record

```json
{
  "type": "record",
  "name": "User",
  "namespace": "com.example",
  "fields": [
    {"name": "id", "type": "long"},
    {"name": "username", "type": "string"},
    {"name": "email", "type": "string"},
    {"name": "age", "type": "int"}
  ]
}
```

### Complex Employee Record

```json
{
  "type": "record",
  "name": "Employee",
  "namespace": "com.company.hr",
  "fields": [
    {"name": "id", "type": "long"},
    {"name": "name", "type": "string"},
    {"name": "email", "type": ["null", "string"], "default": null},
    {
      "name": "department",
      "type": {
        "type": "enum",
        "name": "Department",
        "symbols": ["ENGINEERING", "SALES", "MARKETING", "HR"]
      }
    },
    {
      "name": "salary",
      "type": {
        "type": "bytes",
        "logicalType": "decimal",
        "precision": 10,
        "scale": 2
      }
    },
    {
      "name": "hire_date",
      "type": {"type": "int", "logicalType": "date"}
    },
    {
      "name": "skills",
      "type": {"type": "array", "items": "string"},
      "default": []
    },
    {
      "name": "metadata",
      "type": {"type": "map", "values": "string"},
      "default": {}
    }
  ]
}
```

### Address Book

```json
{
  "type": "record",
  "name": "AddressBook",
  "namespace": "com.example.contacts",
  "fields": [
    {
      "name": "contacts",
      "type": {
        "type": "array",
        "items": {
          "type": "record",
          "name": "Contact",
          "fields": [
            {"name": "name", "type": "string"},
            {
              "name": "phone",
              "type": {
                "type": "record",
                "name": "PhoneNumber",
                "fields": [
                  {"name": "number", "type": "string"},
                  {
                    "name": "type",
                    "type": {
                      "type": "enum",
                      "name": "PhoneType",
                      "symbols": ["MOBILE", "HOME", "WORK"]
                    }
                  }
                ]
              }
            },
            {
              "name": "addresses",
              "type": {
                "type": "array",
                "items": {
                  "type": "record",
                  "name": "Address",
                  "fields": [
                    {"name": "street", "type": "string"},
                    {"name": "city", "type": "string"},
                    {"name": "state", "type": "string"},
                    {"name": "zip", "type": "string"}
                  ]
                }
              }
            }
          ]
        }
      }
    }
  ]
}
```

### Event Log with Union

```json
{
  "type": "record",
  "name": "Event",
  "namespace": "com.example.logging",
  "fields": [
    {"name": "timestamp", "type": {"type": "long", "logicalType": "timestamp-millis"}},
    {"name": "event_id", "type": "string"},
    {
      "name": "payload",
      "type": [
        {
          "type": "record",
          "name": "UserLogin",
          "fields": [
            {"name": "user_id", "type": "long"},
            {"name": "ip_address", "type": "string"}
          ]
        },
        {
          "type": "record",
          "name": "PageView",
          "fields": [
            {"name": "user_id", "type": "long"},
            {"name": "url", "type": "string"}
          ]
        },
        {
          "type": "record",
          "name": "Purchase",
          "fields": [
            {"name": "user_id", "type": "long"},
            {"name": "product_id", "type": "string"},
            {"name": "amount", "type": "double"}
          ]
        }
      ]
    }
  ]
}
```

## Key Features and Best Practices

### Schema Evolution

**Compatible Changes (Reader can read Writer's data):**

**Forward Compatibility (new schema reads old data):**
- Add fields with defaults
- Delete fields

**Backward Compatibility (old schema reads new data):**
- Add fields with defaults
- Delete fields

**Full Compatibility (both directions):**
- Add fields with defaults only

**Schema Resolution Rules:**
1. Field ordering doesn't matter
2. Extra fields in writer ignored by reader
3. Missing fields in writer filled with defaults
4. Type promotion allowed (int to long, float to double)
5. Union resolution by type matching

**Example Evolution:**
```json
// Version 1
{
  "type": "record",
  "name": "User",
  "fields": [
    {"name": "name", "type": "string"},
    {"name": "age", "type": "int"}
  ]
}

// Version 2 (backward compatible)
{
  "type": "record",
  "name": "User",
  "fields": [
    {"name": "name", "type": "string"},
    {"name": "age", "type": "int"},
    {"name": "email", "type": "string", "default": ""}
  ]
}
```

### Aliases

**Support schema evolution:**
```json
{
  "type": "record",
  "name": "User",
  "aliases": ["Person"],
  "fields": [
    {
      "name": "full_name",
      "type": "string",
      "aliases": ["name", "username"]
    }
  ]
}
```

### Best Practices

**Schema Design:**
1. Always include namespace
2. Provide documentation strings
3. Use logical types for dates, decimals, UUIDs
4. Provide defaults for optional fields
5. Use unions for nullable fields: `["null", "type"]`

**Naming Conventions:**
```json
{
  "type": "record",
  "name": "MyRecord",        // PascalCase
  "namespace": "com.example", // Reverse domain
  "fields": [
    {"name": "field_name", "type": "string"}  // snake_case
  ]
}
```

**Field Ordering:**
- Put frequently accessed fields first
- Group related fields together
- Put optional fields last

**Default Values:**
- Always provide defaults for optional fields
- Makes schema evolution easier
- Enables backward compatibility

**Union Best Practices:**
- Put `null` first in unions for optional fields
- Limit union complexity (avoid deeply nested unions)
- Document union usage clearly

**Performance Tips:**
1. Use `fixed` for known-size binary data
2. Enable compression for file storage
3. Use schema fingerprints for caching
4. Batch writes to data files
5. Use appropriate codec (snappy for speed, zstandard for size)

### Common Patterns

**Optional Fields:**
```json
{
  "name": "optional_field",
  "type": ["null", "string"],
  "default": null
}
```

**Timestamps:**
```json
{
  "name": "created_at",
  "type": {"type": "long", "logicalType": "timestamp-millis"}
}
```

**Decimal Money:**
```json
{
  "name": "price",
  "type": {
    "type": "bytes",
    "logicalType": "decimal",
    "precision": 10,
    "scale": 2
  }
}
```

**UUID:**
```json
{
  "name": "id",
  "type": {"type": "string", "logicalType": "uuid"}
}
```

**Versioning:**
```json
{
  "type": "record",
  "name": "Message",
  "fields": [
    {"name": "version", "type": "int", "default": 1},
    {"name": "payload", "type": "bytes"}
  ]
}
```

## Use Cases

### Ideal Applications

1. **Big Data Processing:**
   - Hadoop data storage
   - Spark data exchange
   - Data lake storage format

2. **Streaming Systems:**
   - Kafka messages
   - Event sourcing
   - Change data capture (CDC)

3. **Data Serialization:**
   - Microservices communication
   - API data exchange
   - Database serialization

4. **Data Archival:**
   - Long-term storage
   - Historical data
   - Backup systems

5. **Schema Registry:**
   - Confluent Schema Registry
   - Schema evolution management
   - Version control for schemas

### Comparison with Other Formats

**vs. Protocol Buffers:**
- No code generation required
- Dynamic typing support
- Better schema evolution
- JSON schema definition
- Similar performance

**vs. JSON:**
- Much more compact (binary)
- Faster serialization
- Schema enforcement
- But: Not human-readable

**vs. Parquet:**
- Row-oriented vs. column-oriented
- Better for streaming
- Simpler format
- Parquet better for analytics

**vs. Thrift:**
- Simpler schema evolution
- No IDL compiler needed
- Better documentation
- Similar performance

## RPC Protocol

**Avro RPC features:**
- Bidirectional message passing
- Schema-based protocol definition
- Stateful connections
- Multiple transports (HTTP, Netty, local)

**Protocol Example:**
```json
{
  "protocol": "HelloWorld",
  "namespace": "com.example",
  "types": [
    {
      "type": "record",
      "name": "Greeting",
      "fields": [
        {"name": "message", "type": "string"}
      ]
    }
  ],
  "messages": {
    "hello": {
      "request": [{"name": "greeting", "type": "Greeting"}],
      "response": "Greeting"
    }
  }
}
```

## Language Support

**Official Implementations:**
- C
- C++
- C#
- Java
- Python
- Ruby
- PHP
- Perl

**Community Implementations:**
- JavaScript/Node.js
- Go
- Rust
- Scala

## References

- **Source:** https://avro.apache.org/docs/1.11.1/specification/
- **Website:** https://avro.apache.org/
- **GitHub:** https://github.com/apache/avro
- **Format Comparison:** https://avro.apache.org/docs/current/spec.html#Comparison+with+other+systems
