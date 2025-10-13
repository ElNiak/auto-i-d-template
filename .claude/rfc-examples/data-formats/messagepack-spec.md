# MessagePack Specification

## Overview

**Name:** MessagePack

**Organization:** Community-driven open source project

**Purpose:** Efficient object serialization specification for converting data between application objects and compact binary format

**Abstract:** MessagePack is an efficient binary serialization format similar to JSON but more compact and faster. It enables data exchange between different programming languages using a simple binary format that's more space-efficient than JSON.

## Key Format Rules and Type System

### Type System Overview

MessagePack supports the following types:

**Integer Types:**
- Positive integers: 0 to (2^64)-1
- Negative integers: -(2^63) to -1

**Nil:**
- Represents absence of value

**Boolean:**
- true
- false

**Float:**
- IEEE 754 single precision (32-bit)
- IEEE 754 double precision (64-bit)

**Raw Types:**
- **String:** UTF-8 encoded text
- **Binary:** Arbitrary byte array

**Container Types:**
- **Array:** Ordered sequence of objects
- **Map:** Key-value pairs

**Extension Type:**
- Application-specific types with type code
- Used for custom serialization

### Type Hierarchy

```
MessagePack Object
├── Integer
│   ├── Positive (uint)
│   └── Negative (int)
├── Nil
├── Boolean
├── Float
│   ├── float 32
│   └── float 64
├── String (UTF-8)
├── Binary
├── Array
├── Map
└── Extension
    ├── Fixext 1/2/4/8/16
    └── Ext 8/16/32
```

## Encoding Rules and Binary Format

### Format Families

MessagePack uses **first-byte markers** to indicate type and sometimes length.

### Integer Encoding

**Positive Fixint (0x00 - 0x7f):**
```
Format: 0xxxxxxx
Range: 0 to 127
Example: 42 = 0x2A
```

**Negative Fixint (0xe0 - 0xff):**
```
Format: 111xxxxx
Range: -32 to -1
Example: -5 = 0xFB
```

**uint 8 (0xcc):**
```
Format: 0xCC + 1 byte
Range: 0 to 255
Example: 200 = 0xCC 0xC8
```

**uint 16 (0xcd):**
```
Format: 0xCD + 2 bytes (big-endian)
Range: 0 to 65535
Example: 1000 = 0xCD 0x03 0xE8
```

**uint 32 (0xce):**
```
Format: 0xCE + 4 bytes (big-endian)
Range: 0 to 2^32-1
```

**uint 64 (0xcf):**
```
Format: 0xCF + 8 bytes (big-endian)
Range: 0 to 2^64-1
```

**int 8 (0xd0):**
```
Format: 0xD0 + 1 byte (signed)
Range: -128 to 127
Example: -50 = 0xD0 0xCE
```

**int 16/32/64:** Similar with 0xD1, 0xD2, 0xD3

### Nil and Boolean

**nil (0xc0):**
```
Format: 0xC0
Size: 1 byte
```

**false (0xc2):**
```
Format: 0xC2
Size: 1 byte
```

**true (0xc3):**
```
Format: 0xC3
Size: 1 byte
```

### Float Encoding

**float 32 (0xca):**
```
Format: 0xCA + 4 bytes (IEEE 754 single, big-endian)
Example: 3.14 = 0xCA 0x40 0x48 0xF5 0xC3
```

**float 64 (0xcb):**
```
Format: 0xCB + 8 bytes (IEEE 754 double, big-endian)
Example: 3.14159 = 0xCB 0x40 0x09 0x21 0xF9...
```

### String Encoding

**fixstr (0xa0 - 0xbf):**
```
Format: 101xxxxx + UTF-8 bytes
Length: 0 to 31 bytes
Example: "hi" = 0xA2 'h' 'i'
         (0xA2 = 0b10100010, length = 2)
```

**str 8 (0xd9):**
```
Format: 0xD9 + 1 byte length + UTF-8 bytes
Length: 0 to 255 bytes
Example: "hello" = 0xD9 0x05 'h' 'e' 'l' 'l' 'o'
```

**str 16 (0xda):**
```
Format: 0xDA + 2 bytes length (big-endian) + UTF-8 bytes
Length: 0 to 65535 bytes
```

**str 32 (0xdb):**
```
Format: 0xDB + 4 bytes length (big-endian) + UTF-8 bytes
Length: 0 to 2^32-1 bytes
```

### Binary Encoding

**bin 8 (0xc4):**
```
Format: 0xC4 + 1 byte length + raw bytes
Length: 0 to 255 bytes
```

**bin 16 (0xc5):**
```
Format: 0xC5 + 2 bytes length (big-endian) + raw bytes
Length: 0 to 65535 bytes
```

**bin 32 (0xc6):**
```
Format: 0xC6 + 4 bytes length (big-endian) + raw bytes
Length: 0 to 2^32-1 bytes
```

### Array Encoding

**fixarray (0x90 - 0x9f):**
```
Format: 1001xxxx + objects
Length: 0 to 15 elements
Example: [1, 2, 3] = 0x93 0x01 0x02 0x03
         (0x93 = 0b10010011, count = 3)
```

**array 16 (0xdc):**
```
Format: 0xDC + 2 bytes count (big-endian) + objects
Length: 0 to 65535 elements
```

**array 32 (0xdd):**
```
Format: 0xDD + 4 bytes count (big-endian) + objects
Length: 0 to 2^32-1 elements
```

### Map Encoding

**fixmap (0x80 - 0x8f):**
```
Format: 1000xxxx + key-value pairs
Length: 0 to 15 pairs
Example: {"a":1} = 0x81 0xA1 'a' 0x01
         (0x81 = 0b10000001, count = 1)
```

**map 16 (0xde):**
```
Format: 0xDE + 2 bytes count (big-endian) + key-value pairs
Length: 0 to 65535 pairs
```

**map 32 (0xdf):**
```
Format: 0xDF + 4 bytes count (big-endian) + key-value pairs
Length: 0 to 2^32-1 pairs
```

### Extension Type Encoding

**fixext 1/2/4/8/16 (0xd4-0xd8):**
```
Format: 0xD4-0xD8 + 1 byte type code + data
Sizes: 1, 2, 4, 8, or 16 bytes
Example: fixext 1 = 0xD4 <type> <1 byte data>
```

**ext 8 (0xc7):**
```
Format: 0xC7 + 1 byte length + 1 byte type + data
Length: 0 to 255 bytes
```

**ext 16 (0xc8):**
```
Format: 0xC8 + 2 bytes length + 1 byte type + data
Length: 0 to 65535 bytes
```

**ext 32 (0xc9):**
```
Format: 0xC9 + 4 bytes length + 1 byte type + data
Length: 0 to 2^32-1 bytes
```

**Type Codes:**
- -1 to 127: Application-specific
- -128 to -1: Reserved by MessagePack

## Representative Examples

### Simple Values

**Integer 42:**
```
Hex: 2A
Binary: 00101010
Size: 1 byte
```

**Integer 300:**
```
Hex: CD 01 2C
Binary: 11001101 00000001 00101100
Size: 3 bytes (uint 16)
```

**Negative Integer -5:**
```
Hex: FB
Binary: 11111011
Size: 1 byte
```

**Float 3.14:**
```
Hex: CA 40 48 F5 C3
Size: 5 bytes (float 32)
```

**String "hello":**
```
Hex: A5 68 65 6C 6C 6F
ASCII: [fixstr len=5] 'h' 'e' 'l' 'l' 'o'
Size: 6 bytes
```

**nil:**
```
Hex: C0
Size: 1 byte
```

**true:**
```
Hex: C3
Size: 1 byte
```

**false:**
```
Hex: C2
Size: 1 byte
```

### Array Examples

**Array [1, 2, 3]:**
```
Hex: 93 01 02 03
Breakdown:
  0x93 = fixarray with 3 elements
  0x01 = integer 1
  0x02 = integer 2
  0x03 = integer 3
Size: 4 bytes
```

**Array ["a", "b", "c"]:**
```
Hex: 93 A1 61 A1 62 A1 63
Breakdown:
  0x93 = fixarray with 3 elements
  0xA1 'a' = string "a"
  0xA1 'b' = string "b"
  0xA1 'c' = string "c"
Size: 7 bytes
```

**Nested Array [[1, 2], [3, 4]]:**
```
Hex: 92 92 01 02 92 03 04
Breakdown:
  0x92 = fixarray with 2 elements
    0x92 = fixarray with 2 elements
      0x01, 0x02
    0x92 = fixarray with 2 elements
      0x03, 0x04
Size: 7 bytes
```

### Map Examples

**Map {"a": 1}:**
```
Hex: 81 A1 61 01
Breakdown:
  0x81 = fixmap with 1 pair
  0xA1 'a' = string key "a"
  0x01 = integer value 1
Size: 4 bytes
```

**Map {"name": "Alice", "age": 30}:**
```
Hex: 82 A4 6E 61 6D 65 A5 41 6C 69 63 65 A3 61 67 65 1E
Breakdown:
  0x82 = fixmap with 2 pairs
  0xA4 'name' = string "name"
  0xA5 'Alice' = string "Alice"
  0xA3 'age' = string "age"
  0x1E = integer 30
Size: 17 bytes
```

**Nested Map {"user": {"id": 1, "name": "Bob"}}:**
```
Hex: 81 A4 75 73 65 72 82 A2 69 64 01 A4 6E 61 6D 65 A3 42 6F 62
Breakdown:
  0x81 = fixmap with 1 pair
  0xA4 'user' = string "user"
    0x82 = fixmap with 2 pairs
    0xA2 'id' = string "id"
    0x01 = integer 1
    0xA4 'name' = string "name"
    0xA3 'Bob' = string "Bob"
Size: 20 bytes
```

### Complex Object Example

**JSON equivalent:**
```json
{
  "id": 42,
  "name": "Alice",
  "active": true,
  "scores": [95, 87, 92],
  "metadata": {
    "registered": "2023-01-15",
    "verified": true
  }
}
```

**MessagePack encoding (hex):**
```
85                          # fixmap with 5 pairs
A2 69 64                    # string "id"
2A                          # integer 42
A4 6E 61 6D 65              # string "name"
A5 41 6C 69 63 65           # string "Alice"
A6 61 63 74 69 76 65        # string "active"
C3                          # true
A6 73 63 6F 72 65 73        # string "scores"
93                          # fixarray with 3 elements
5F                          # integer 95
57                          # integer 87
5C                          # integer 92
A8 6D 65 74 61 64 61 74 61  # string "metadata"
82                          # fixmap with 2 pairs
AA 72 65 67 69 73 74 65 72 65 64  # string "registered"
AA 32 30 32 33 2D 30 31 2D 31 35  # string "2023-01-15"
A8 76 65 72 69 66 69 65 64  # string "verified"
C3                          # true
```

### Extension Type Example

**Timestamp Extension (type -1):**
```
Timestamp with seconds and nanoseconds:
D7 FF 00 00 00 00 63 E4 6B 80
Breakdown:
  0xD7 = fixext 8
  0xFF = type -1 (timestamp)
  [8 bytes] = timestamp data
```

**Custom Application Type:**
```
D4 05 42
Breakdown:
  0xD4 = fixext 1
  0x05 = application type 5
  0x42 = 1 byte of data
```

## Key Design Principles

### Efficiency Goals

1. **Compact Encoding:**
   - "Serializers SHOULD use the format which represents the data in the smallest number of bytes"
   - Optimized for common cases (small integers, short strings)

2. **Fast Serialization:**
   - Simple format rules
   - Minimal parsing overhead
   - Direct byte representation

3. **Streaming-Friendly:**
   - Self-delimiting types
   - No lookahead required
   - Can process incrementally

### Format Selection

**Encoding Guidelines:**
- Use smallest representation that fits the data
- Positive integers < 128: Use fixint (1 byte)
- Strings < 32 bytes: Use fixstr
- Arrays < 16 elements: Use fixarray
- Maps < 16 pairs: Use fixmap

**Example Integer Encoding Choices:**
| Value | Best Format | Size |
|-------|-------------|------|
| 0-127 | positive fixint | 1 byte |
| 128-255 | uint 8 | 2 bytes |
| 256-65535 | uint 16 | 3 bytes |
| -1 to -32 | negative fixint | 1 byte |
| -33 to -128 | int 8 | 2 bytes |

### Extensibility

**Extension Types:**
- Allow application-specific types
- Type codes -1 to 127 for applications
- Standard timestamp type defined (type -1)
- Preserve compatibility with future extensions

**Application Profiles:**
- Applications can restrict supported types
- Can define additional validation rules
- Can assign meaning to extension types

## Use Cases

### Ideal Applications

1. **Network Protocols:**
   - Binary API communication
   - RPC systems
   - WebSocket messages

2. **Data Serialization:**
   - Cache storage (Redis, Memcached)
   - Session storage
   - Inter-process communication

3. **Configuration Files:**
   - Binary config formats
   - Faster than JSON parsing
   - Smaller file sizes

4. **Message Queues:**
   - Job queues
   - Event streams
   - Log aggregation

5. **Embedded Systems:**
   - IoT devices
   - Limited bandwidth scenarios
   - Resource-constrained environments

### Comparison with Other Formats

**vs. JSON:**
- 20-50% smaller size
- Faster parsing/serialization
- Binary format (not human-readable)
- Preserves data types (no string/number ambiguity)

**vs. Protocol Buffers:**
- No schema required
- Simpler implementation
- Self-describing format
- Dynamic typing
- But: Larger than Protocol Buffers

**vs. CBOR:**
- Simpler specification
- Faster encoding/decoding
- Similar size efficiency
- Wider language support

**vs. Avro:**
- No schema required
- Smaller for small objects
- Simpler format
- But: Avro better for large datasets with schema

## Language Support

**Official Implementations:**
- C/C++
- Ruby
- Python
- Java
- JavaScript/Node.js
- C#
- PHP
- Perl
- Go
- Rust

**Community Implementations:**
- Nearly every major programming language
- Consistent behavior across implementations
- Active maintenance and testing

## Best Practices

### Encoding

1. **Use Appropriate Types:**
   - Use bin for binary data, str for text
   - Choose int/uint based on value range
   - Use smallest representation

2. **Map Key Guidelines:**
   - Use strings or integers as keys
   - Keep keys short for efficiency
   - Consider integer keys for internal protocols

3. **Backward Compatibility:**
   - Add new map keys (old code ignores them)
   - Don't change key meanings
   - Version your protocol if needed

### Decoding

1. **Validate Input:**
   - Check UTF-8 validity in strings
   - Enforce map key uniqueness if needed
   - Limit nesting depth

2. **Handle Unknown Types:**
   - Skip unknown extension types gracefully
   - Provide fallback for missing map keys

3. **Resource Limits:**
   - Set maximum message size
   - Limit string/array/map lengths
   - Prevent memory exhaustion

### Performance

1. **Reuse Buffers:**
   - Avoid frequent allocation
   - Use buffer pools

2. **Batch Operations:**
   - Serialize multiple objects together
   - Amortize overhead

3. **Profile Encoding Choices:**
   - Measure actual sizes
   - Optimize for your data patterns

## Security Considerations

1. **Input Validation:**
   - Validate lengths before allocation
   - Check for integer overflow
   - Enforce nesting limits

2. **UTF-8 Validation:**
   - Validate string encoding
   - Reject invalid sequences
   - Handle replacement characters

3. **Resource Exhaustion:**
   - Limit maximum message size
   - Timeout on large messages
   - Monitor memory usage

4. **Extension Type Handling:**
   - Validate custom types
   - Sanitize extension data
   - Don't blindly execute code

## References

- **Source:** https://github.com/msgpack/msgpack/blob/master/spec.md
- **Website:** https://msgpack.org/
- **Format Specification:** https://github.com/msgpack/msgpack/blob/master/spec.md
