# RFC 4506: XDR - External Data Representation Standard

## Overview

**Title:** XDR: External Data Representation Standard

**RFC Number:** 4506

**Status:** Standards Track

**Abstract:** XDR is a standard for the description and encoding of data designed to transfer data between different computer architectures, providing a language to describe data formats concisely.

## Key Syntax Rules and Grammar

### Basic Declaration Syntax

```c
type-specifier identifier
type-specifier identifier "[" value "]"        // Fixed-length array
type-specifier identifier "<" [ value ] ">"    // Variable-length array
```

### Supported Type Specifiers

**Basic Types:**
- `int` - 32-bit signed integer
- `unsigned int` - 32-bit unsigned integer
- `hyper` - 64-bit signed integer
- `unsigned hyper` - 64-bit unsigned integer
- `float` - 32-bit IEEE 754 floating point
- `double` - 64-bit IEEE 754 floating point
- `quadruple` - 128-bit floating point
- `bool` - Boolean (TRUE or FALSE)
- `enum` - Enumeration
- `opaque` - Uninterpreted data
- `string` - Character string

**Constructed Types:**
- `struct` - Structure (record)
- `union` - Discriminated union
- `void` - 0-byte quantity

### Declaration Examples

**Simple Declarations:**
```xdr
int count;
unsigned int maxvalue;
bool flag;
```

**Fixed-Length Array:**
```xdr
int vector[10];
```

**Variable-Length Array:**
```xdr
int data<100>;        // Maximum 100 elements
string name<255>;     // Maximum 255 characters
```

**Enumeration:**
```xdr
enum filetype {
   TEXT = 0,
   DATA = 1,
   EXEC = 2
};
```

**Structure:**
```xdr
struct file {
   string filename<MAXNAMELEN>;
   filetype type;
   string owner<MAXUSERNAME>;
   opaque data<MAXFILELEN>;
};
```

**Discriminated Union:**
```xdr
union switch (int version) {
   case 1:
      struct v1_data data_v1;
   case 2:
      struct v2_data data_v2;
   default:
      void;
};
```

## Encoding Rules

### Fundamental Encoding Principles

1. **Block Size:** All data encoded in multiples of 4 bytes (32 bits)
2. **Byte Order:** Big-endian (most significant byte first)
3. **Alignment:** All data items aligned on 4-byte boundaries
4. **Padding:** Zero bytes added to maintain alignment

### Integer Encoding

**Signed Integer (32-bit):**
- Encoded in 4 bytes
- Big-endian byte order
- Two's complement representation

**Example: Integer 42**
```
Hexadecimal: 0x00 0x00 0x00 0x2A
Bytes: [0, 0, 0, 42]
```

**Unsigned Integer (32-bit):**
- Same encoding as signed
- Interpreted as unsigned value

**Hyper/Unsigned Hyper (64-bit):**
- Encoded in 8 bytes
- Big-endian byte order

### Boolean Encoding

Encoded as integer:
- FALSE = 0
- TRUE = 1

### Enumeration Encoding

Encoded as signed integer using the enum value.

### Floating-Point Encoding

**Float (32-bit):**
- IEEE 754 single-precision format
- 1 sign bit, 8 exponent bits, 23 fraction bits

**Double (64-bit):**
- IEEE 754 double-precision format
- 1 sign bit, 11 exponent bits, 52 fraction bits

### Fixed-Length Opaque Data

**Encoding:**
1. Data bytes in order
2. Padding with zero bytes to 4-byte boundary

**Example: 5 bytes of data [1, 2, 3, 4, 5]**
```
Encoded: [1, 2, 3, 4, 5, 0, 0, 0]
Total: 8 bytes (padded to multiple of 4)
```

### Variable-Length Opaque Data

**Format:**
1. Unsigned integer length (4 bytes)
2. Data bytes
3. Padding to 4-byte boundary

**Example: 5 bytes of data**
```
Length: 0x00 0x00 0x00 0x05
Data: [data bytes]
Padding: [0, 0, 0] if needed
```

### String Encoding

**Format:**
- Same as variable-length opaque
- Must be valid ASCII
- No null terminator in encoding

**Example: String "hello"**
```
Length: 0x00 0x00 0x00 0x05
Data: 'h' 'e' 'l' 'l' 'o'
Padding: 0x00 0x00 0x00
Total: 12 bytes
```

### Fixed-Length Array

**Encoding:**
- Elements encoded sequentially
- No length prefix
- All elements must be present

### Variable-Length Array

**Format:**
1. Unsigned integer count (4 bytes)
2. Elements encoded sequentially

**Example: Array of 3 integers [1, 2, 3]**
```
Count: 0x00 0x00 0x00 0x03
Elements: [encoded 1] [encoded 2] [encoded 3]
```

### Structure Encoding

**Rules:**
- Members encoded in declaration order
- Each member follows its type's encoding rules
- No padding between members (already aligned)

### Discriminated Union Encoding

**Format:**
1. Discriminant (encoded as its type)
2. Selected arm data (if not void)

## Examples

### File Structure Example

**XDR Definition:**
```xdr
const MAXNAMELEN = 255;
const MAXFILELEN = 1024;
const MAXUSERNAME = 32;

enum filetype {
   TEXT = 0,
   DATA = 1,
   EXEC = 2
};

struct file {
   string filename<MAXNAMELEN>;
   filetype type;
   string owner<MAXUSERNAME>;
   opaque data<MAXFILELEN>;
};
```

**Example File (Conceptual):**
```
filename: "sillyprog"
type: EXEC
owner: "john"
data: [Lisp program bytes]
```

**Encoded Structure (Partial):**
1. Filename length: 9 bytes
2. Filename: "sillyprog" + padding
3. Type: 2 (EXEC)
4. Owner length: 4 bytes
5. Owner: "john"
6. Data length: [actual length]
7. Data bytes + padding

### Complex Type Example

**Linked List:**
```xdr
struct list_node {
   int value;
   list_node *next;
};

union list_node switch (bool has_value) {
   case TRUE:
      struct {
         int value;
         list_node next;
      };
   case FALSE:
      void;
};
```

### Optional Data Example

**Optional Integer:**
```xdr
union opt_int switch (bool present) {
   case TRUE:
      int value;
   case FALSE:
      void;
};
```

## Security Considerations

### Key Security Concerns

1. **Buffer Overflow Attacks:**
   - Variable-length arrays must validate length before allocation
   - String lengths must be checked against maximum values
   - Implementations must not trust length fields

2. **Embedded Null Octets:**
   - Strings may contain null bytes internally
   - Can cause issues with C-style null-terminated strings
   - Parsers must use explicit length, not null termination

3. **Illegal Character Handling:**
   - String data may contain non-ASCII characters
   - Must validate character set requirements

4. **Recursive Encoding/Decoding:**
   - Deeply nested structures can cause stack overflow
   - Circular references in optional pointers
   - Implementations should limit recursion depth

5. **Integer Overflow:**
   - Length fields can overflow when calculating buffer sizes
   - Example: length * element_size may overflow
   - Must validate before allocation

6. **Resource Exhaustion:**
   - Large length values can cause memory exhaustion
   - Implementations should impose reasonable limits

### Recommended Practices

- Validate all length fields before use
- Impose maximum limits on array/string sizes
- Check for integer overflow in size calculations
- Limit recursion depth in parsers
- Use safe memory allocation practices
- Validate discriminant values in unions

## Key Design Principles

1. **Portability:** Transfer data between different architectures
2. **Implicit Typing:** Type information in schema, not data
3. **Canonical Encoding:** One correct way to encode each value
4. **4-Byte Alignment:** Simplifies implementation on many platforms
5. **Concise Description:** Language for describing data formats

## Unique Features

1. **Data Description Language:**
   - Not a programming language
   - Describes data structure, not algorithms

2. **Standardized Encoding:**
   - Same data encodes identically on all platforms
   - Enables exact binary comparison

3. **Big-Endian Only:**
   - Single byte order simplifies specification
   - Decoding implementations handle conversion

4. **Self-Contained:**
   - No external dependencies
   - Simple to implement

## Limitations

1. **No Bit Fields:** Cannot encode data smaller than bytes
2. **No Packed Decimals:** Only binary number representations
3. **Fixed Byte Order:** Big-endian only
4. **No Versioning:** Schema changes require careful planning
5. **Limited String Support:** ASCII only in original spec

## Use Cases

- RPC (Remote Procedure Call) protocols
- Network file systems (NFS)
- Distributed systems communication
- Cross-platform data exchange
- Persistent data storage

## Comparison with Other Formats

**vs. JSON:**
- Binary vs. text
- Requires schema
- More efficient encoding
- Not human-readable

**vs. Protocol Buffers:**
- Simpler type system
- No field numbers
- 4-byte alignment requirement
- Older specification

**vs. CBOR:**
- Fixed alignment vs. variable length
- Requires external schema
- Simpler encoding rules

## References

- **Source:** https://www.rfc-editor.org/rfc/rfc4506.txt
- **Obsoletes:** RFC 1832
- **STD:** 67
