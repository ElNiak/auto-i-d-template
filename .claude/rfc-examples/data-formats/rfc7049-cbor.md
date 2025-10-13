# RFC 7049: Concise Binary Object Representation (CBOR)

## Overview

**Title:** Concise Binary Object Representation (CBOR)

**RFC Number:** 7049

**Status:** Standards Track

**Abstract:** A data format designed for extremely small code size, fairly small message size, and extensibility without version negotiation.

## Key Syntax Rules and Grammar

### Initial Byte Structure

CBOR uses an **8-bit initial byte** with:
- **3-bit major type** (bits 5-7)
- **5-bit additional information** (bits 0-4)

### Major Types

| Major Type | Description |
|------------|-------------|
| 0 | Unsigned integers |
| 1 | Negative integers |
| 2 | Byte strings |
| 3 | UTF-8 text strings |
| 4 | Arrays |
| 5 | Maps (key/value pairs) |
| 6 | Semantic tags |
| 7 | Floating-point and simple values |

### Data Item Structure

```
+---+---+---+---+---+---+---+---+
| Major type  | Additional info |
+---+---+---+---+---+---+---+---+
  bits 5-7        bits 0-4
```

**Additional Information Values:**
- 0-23: Direct value
- 24: 1-byte value follows
- 25: 2-byte value follows
- 26: 4-byte value follows
- 27: 8-byte value follows
- 28-30: Reserved
- 31: Indefinite length

## Encoding Rules

### Length Encoding

**Definite Length:**
- Short values (0-23) encoded directly in initial byte
- Longer values use additional bytes (1, 2, 4, or 8 bytes)

**Indefinite Length:**
- Used for streaming data
- Terminated with a "break" marker (0xFF)

### Integer Encoding

**Unsigned Integers (Major Type 0):**
- Direct encoding for 0-23
- Extended encoding for larger values

**Negative Integers (Major Type 1):**
- Encoded as -1 - n
- Example: -500 encoded as unsigned 499 with major type 1

### String Encoding

**Byte Strings (Major Type 2):**
- Raw binary data
- Length followed by bytes

**Text Strings (Major Type 3):**
- UTF-8 encoded text
- Length followed by UTF-8 bytes

### Semantic Tags

Optional tags provide additional meaning:
- Tag 0: Standard date/time string
- Tag 1: Epoch-based date/time
- Tag 2: Positive bignum
- Tag 3: Negative bignum
- Tag 32: URI
- Tag 33: base64url
- Tag 34: base64

## Examples

### Integer Encodings

| Value | Hexadecimal | Description |
|-------|-------------|-------------|
| 0 | 0x00 | Direct encoding |
| 1 | 0x01 | Direct encoding |
| 10 | 0x0A | Direct encoding |
| 23 | 0x17 | Direct encoding |
| 24 | 0x18 0x18 | 1-byte follows |
| 100 | 0x18 0x64 | 1-byte follows |
| 1000 | 0x19 0x03 0xE8 | 2-bytes follow |
| 1000000 | 0x1A 0x00 0x0F 0x42 0x40 | 4-bytes follow |

### Negative Integer Encodings

| Value | Hexadecimal | Description |
|-------|-------------|-------------|
| -1 | 0x20 | Encoded as 0 with major type 1 |
| -10 | 0x29 | Encoded as 9 with major type 1 |
| -100 | 0x38 0x63 | Encoded as 99 with major type 1 |
| -1000 | 0x39 0x03 0xE7 | Encoded as 999 with major type 1 |

### Floating-Point Encodings

| Value | Hexadecimal | Format |
|-------|-------------|--------|
| 0.0 | 0xF9 0x00 0x00 | Half-precision |
| 1.1 | 0xFB 0x3F 0xF1 0x99... | Double-precision |
| 1.5 | 0xF9 0x3E 0x00 | Half-precision |
| Infinity | 0xF9 0x7C 0x00 | Half-precision |
| NaN | 0xF9 0x7E 0x00 | Half-precision |

### Array Encoding

**Definite-length array [1, 2, 3]:**
```
0x83 0x01 0x02 0x03
```
- 0x83: Array of length 3 (major type 4, additional info 3)
- 0x01, 0x02, 0x03: Elements

**Indefinite-length array [1, 2, 3]:**
```
0x9F 0x01 0x02 0x03 0xFF
```
- 0x9F: Start indefinite array
- 0xFF: Break marker

### Map Encoding

**Map {"a": 1, "b": [2, 3]}:**
```
0xA2 0x61 0x61 0x01 0x61 0x62 0x82 0x02 0x03
```
- 0xA2: Map of 2 pairs
- 0x61 0x61: Text string "a" (length 1)
- 0x01: Integer 1
- 0x61 0x62: Text string "b" (length 1)
- 0x82 0x02 0x03: Array [2, 3]

## Security Considerations

### Primary Concerns

1. **Resource Exhaustion:**
   - Malicious data items with extremely long lengths
   - Deeply nested arrays/maps causing stack overflow
   - Implementations must enforce resource limits

2. **Parser Complexity:**
   - CBOR reduces parser complexity compared to text formats
   - Simpler parsers have fewer vulnerabilities

3. **Strict Mode:**
   - Prevents multiple interpretations of data
   - Rejects duplicate keys in maps
   - Ensures canonical encoding

4. **Integer Overflow:**
   - Protect against integer overflow in length calculations
   - Validate array/map sizes before allocation

5. **Stack Depth:**
   - Limit nesting depth to prevent stack exhaustion
   - Use iterative parsing for deeply nested structures

### Recommended Practices

- Implement resource management (memory, CPU time)
- Use strict mode for security-critical applications
- Validate all length fields before allocation
- Set maximum nesting depth
- Reject non-canonical encodings when appropriate

## Key Design Goals

1. **Compact:** Small message size
2. **Minimal Code Size:** Simple encoder/decoder implementation
3. **Self-Describing:** No external schema required
4. **Extensible:** Semantic tags for custom types
5. **Efficient:** Fast encoding/decoding
6. **No Versioning:** Extensions don't require version negotiation

## Use Cases

- IoT and constrained devices
- Binary web APIs
- High-volume data interchange
- Protocol buffers alternative
- Database storage format
- Blockchain data structures

## Comparison with JSON

**Advantages over JSON:**
- More compact binary format
- Native support for binary data
- Efficient number representations
- Indefinite-length streaming
- Extensible type system

**Trade-offs:**
- Not human-readable
- Requires binary-safe transport
- More complex than JSON (but still simple)

## References

- **Source:** https://www.rfc-editor.org/rfc/rfc7049.txt
- **Updated By:** RFC 8949 (CBOR STD 94)
