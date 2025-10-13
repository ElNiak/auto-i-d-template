# RFC 8259: The JavaScript Object Notation (JSON) Data Interchange Format

## Overview

**Title:** The JavaScript Object Notation (JSON) Data Interchange Format

**RFC Number:** 8259

**Status:** Standards Track

**Abstract:** JSON is a lightweight, text-based, language-independent data interchange format derived from the ECMAScript Programming Language Standard.

## Key Syntax Rules and Grammar

### Grammar Definition

```abnf
JSON-text = ws value ws
```

### Data Types

JSON supports **4 primitive types** and **2 structured types**:

**Primitive Types:**
- Strings
- Numbers
- Booleans (true/false)
- null

**Structured Types:**
- Objects: Enclosed in `{ }`, contain name/value pairs
- Arrays: Enclosed in `[ ]`, contain ordered sequence of values

### Detailed Grammar Rules

**Numbers:**
- Base 10 decimal format
- Optional minus sign
- Optional fraction part
- Optional exponent part

**Strings:**
- Enclosed in quotation marks
- Unicode characters with escape sequences
- Supports escape sequences: `\"`, `\\`, `\/`, `\b`, `\f`, `\n`, `\r`, `\t`, `\uXXXX`

## Encoding Rules

### Character Encoding

**Primary Rule:** JSON text exchanged between systems MUST be encoded using UTF-8

**Additional Requirements:**
- No byte order mark (U+FEFF) should be added
- Unicode characters recommended for interoperability
- Programs that parse JSON texts MAY ignore the presence of a byte order mark

### Whitespace

Insignificant whitespace is allowed before or after any token:
- Space (U+0020)
- Horizontal tab (U+0009)
- Line feed (U+000A)
- Carriage return (U+000D)

## Examples

### JSON Object Example

```json
{
  "Image": {
    "Width": 800,
    "Height": 600,
    "Title": "View from 15th Floor",
    "Thumbnail": {
      "Url": "http://www.example.com/image/481989943",
      "Height": 125,
      "Width": 100
    },
    "Animated": false,
    "IDs": [116, 943, 234, 38793]
  }
}
```

### JSON Array Example

```json
[
  {
    "precision": "zip",
    "Latitude": 37.7668,
    "Longitude": -122.3959,
    "City": "SAN FRANCISCO",
    "State": "CA"
  },
  {
    "precision": "zip",
    "Latitude": 37.371991,
    "Longitude": -122.026020,
    "City": "SUNNYVALE",
    "State": "CA"
  }
]
```

### Simple Values

```json
"Hello World"
```

```json
42
```

```json
true
```

```json
null
```

## Security Considerations

### Key Security Points

1. **JSON Parsers Must Accept All Valid Texts:** This requirement can result in significant memory and processing costs

2. **Interoperability Concerns:**
   - Implementations must be careful about accepting non-UTF-8 encodings
   - Duplicate object names can lead to unpredictable behavior

3. **Number Precision:**
   - Different implementations may handle large numbers differently
   - Software using JSON for interchange must be aware of number precision limits

4. **Recursive Structures:**
   - Parsers must protect against deeply nested structures that could cause stack overflow

5. **Character Encoding Issues:**
   - Invalid Unicode sequences
   - Byte order marks
   - Non-UTF-8 encodings

## Key Design Principles

1. **Simplicity:** Minimal syntax, easy to read and write
2. **Universality:** Language-independent
3. **Text-based:** Human-readable format
4. **Structured:** Supports hierarchical data
5. **Interoperability:** Widely supported across platforms and languages

## Use Cases

- Web APIs and REST services
- Configuration files
- Data exchange between applications
- Structured logging
- NoSQL database storage format

## References

- **Source:** https://www.rfc-editor.org/rfc/rfc8259.txt
- **Obsoletes:** RFC 7159
- **Updates:** RFC 4627
