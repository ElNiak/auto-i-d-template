# Data Formats Application Profile - RFC Examples Summary

## Overview

This directory contains comprehensive reference documentation for data serialization formats, including IETF RFCs and industry-standard specifications. These examples provide patterns for writing data format specifications with syntax definitions, encoding rules, and implementation guidance.

## Collection Contents

### IETF RFCs

#### 1. RFC 8259 - JSON (JavaScript Object Notation)
**File:** `rfc8259-json.md`

**Key Characteristics:**
- Text-based, human-readable format
- Language-independent data interchange
- UTF-8 encoding required
- Six data types: object, array, string, number, boolean, null

**Specification Highlights:**
- Clear ABNF grammar definitions
- Encoding rules (UTF-8 mandatory)
- Comprehensive examples (objects, arrays, primitives)
- Security considerations (parser vulnerabilities, resource limits)

**When to Reference:**
- Writing text-based format specifications
- Defining simple, human-readable formats
- Syntax grammar examples
- Interoperability considerations

---

#### 2. RFC 7049 - CBOR (Concise Binary Object Representation)
**File:** `rfc7049-cbor.md`

**Key Characteristics:**
- Binary format optimized for small code size
- Self-describing without external schema
- Extensible through semantic tags
- Supports both definite and indefinite-length encoding

**Specification Highlights:**
- Initial byte structure (3-bit major type + 5-bit additional info)
- 8 major types with clear encoding rules
- Extensive encoding examples with hexadecimal
- Security guidance (resource exhaustion, integer overflow)
- Canonical encoding for cryptographic use

**When to Reference:**
- Binary format specifications
- Encoding rule definitions with bit-level detail
- Extensibility mechanisms (semantic tags)
- Constrained environment considerations
- Security-focused specifications

---

#### 3. RFC 4506 - XDR (External Data Representation)
**File:** `rfc4506-xdr.md`

**Key Characteristics:**
- Data description language and encoding standard
- 4-byte alignment requirement
- Big-endian byte order
- Supports complex types (structs, unions, arrays)

**Specification Highlights:**
- Type system with C-like syntax
- Detailed encoding rules (4-byte blocks, padding)
- Variable-length and fixed-length data
- Discriminated unions
- Security considerations (buffer overflow, validation)

**When to Reference:**
- Cross-platform binary data exchange
- Alignment requirements
- Type description languages
- RPC protocol data formats
- Structured binary encoding

---

#### 4. RFC 7464 - JSON Text Sequences
**File:** `rfc7464-json-text-sequences.md`

**Key Characteristics:**
- Streaming format for multiple JSON texts
- Record Separator (0x1E) prefix, Line Feed (0x0A) suffix
- Error recovery (skip invalid entries)
- Incremental parsing without streaming parser

**Specification Highlights:**
- Dual ABNF grammars (parsing vs. encoding)
- Delimiter rationale and design decisions
- Truncation detection mechanisms
- Security considerations (untrusted input, data smuggling)

**When to Reference:**
- Streaming data format specifications
- Delimiter design and rationale
- Error recovery mechanisms
- Incremental processing formats
- Log/event stream specifications

---

### Company Specifications

#### 5. Protocol Buffers (Google)
**File:** `protobuf-spec.md`

**Key Characteristics:**
- Schema-based binary serialization
- Code generation for multiple languages
- Compact varint encoding
- Strong backward/forward compatibility

**Specification Highlights:**
- Proto3 syntax with message definitions
- Wire format (key-value pairs with field numbers)
- Varint encoding examples
- Schema evolution rules
- Field numbering best practices (1-15 for frequent fields)
- Optimization options (SPEED, CODE_SIZE, LITE_RUNTIME)

**When to Reference:**
- Schema-based format specifications
- Code generation approaches
- Field numbering systems
- Backward compatibility strategies
- Performance optimization options
- Type system design

---

#### 6. Apache Avro
**File:** `avro-spec.md`

**Key Characteristics:**
- JSON schema definition
- Compact binary encoding without field names
- Dynamic typing support
- Rich schema evolution (aliases, defaults)

**Specification Highlights:**
- JSON schema syntax for complex types
- Zig-zag encoding for signed integers
- Logical types (date, timestamp, decimal, UUID)
- Schema resolution for evolution
- Data file format with compression
- RPC protocol definition

**When to Reference:**
- JSON-based schema languages
- Schema evolution mechanisms
- Logical type extensions
- Data file format specifications
- Compression integration
- Big data serialization

---

#### 7. MessagePack
**File:** `messagepack-spec.md`

**Key Characteristics:**
- Self-describing binary format (no schema)
- Optimized for compact size
- Similar to JSON but binary
- Extension type system

**Specification Highlights:**
- First-byte marker system
- Format family hierarchy (fix, 8, 16, 32)
- Encoding optimization rules ("use smallest representation")
- Extension type for custom types
- Comprehensive encoding examples with hexadecimal

**When to Reference:**
- Schema-less binary formats
- Size optimization strategies
- First-byte marker design patterns
- Extension mechanisms
- Simple binary encoding rules

---

## Comparative Analysis

### Format Characteristics Matrix

| Format | Type | Schema | Size | Speed | Human-Readable | Evolution |
|--------|------|--------|------|-------|----------------|-----------|
| JSON | Text | No | Large | Medium | Yes | Good |
| CBOR | Binary | No | Small | Fast | No | Excellent |
| XDR | Binary | Yes | Medium | Fast | No | Limited |
| JSON Seq | Text | No | Large | Medium | Partial | Good |
| Protobuf | Binary | Yes | Very Small | Very Fast | No | Excellent |
| Avro | Binary | Yes | Very Small | Very Fast | No | Excellent |
| MessagePack | Binary | No | Small | Very Fast | No | Good |

### Use Case Recommendations

**Human-Readable Formats:**
- JSON (RFC 8259) - APIs, configuration files, web services

**Constrained Environments (IoT, Embedded):**
- CBOR (RFC 7049) - Small code size, efficient encoding
- MessagePack - Minimal overhead, simple implementation

**Streaming/Logging:**
- JSON Text Sequences (RFC 7464) - Log files, event streams
- MessagePack - High-throughput message queues

**Big Data/Analytics:**
- Avro - Hadoop, Spark, data lakes
- Protobuf - Large-scale data pipelines

**RPC/Microservices:**
- Protobuf - gRPC, internal service APIs
- Avro - Schema registry, cross-language RPC
- XDR - Legacy RPC systems (Sun RPC, NFS)

**General Purpose:**
- JSON - Maximum interoperability
- MessagePack - Efficient, no schema overhead
- CBOR - Flexible, extensible, binary

---

## Specification Writing Patterns

### Common Structure Elements

All specifications in this collection follow these patterns:

#### 1. Abstract/Overview
- Purpose and design goals
- Target use cases
- Key differentiators

#### 2. Type System
- Primitive types
- Composite/complex types
- Type hierarchy or categorization

#### 3. Syntax Rules
- Grammar definitions (ABNF, BNF, or prose)
- Naming conventions
- Structural constraints

#### 4. Encoding Rules
- Binary or text representation
- Byte order, alignment
- Length encoding
- Delimiter or framing

#### 5. Examples
- Simple values
- Complex nested structures
- Edge cases
- Both conceptual and hexadecimal/byte-level

#### 6. Security Considerations
- Parser vulnerabilities
- Resource exhaustion
- Validation requirements
- Integrity protection

#### 7. Implementation Guidance
- Best practices
- Performance tips
- Common patterns
- Pitfalls to avoid

---

## Key Lessons for Specification Authors

### 1. Grammar Definition Clarity

**Best Examples:**
- **JSON (RFC 8259):** Clean ABNF grammar with prose explanations
- **XDR (RFC 4506):** C-like syntax for familiarity
- **Avro:** JSON schema format (self-describing)

**Key Takeaway:** Use formal grammars (ABNF, BNF) supplemented with examples. Choose syntax notation that fits your audience.

---

### 2. Encoding Rule Precision

**Best Examples:**
- **CBOR (RFC 7049):** Bit-level encoding with explicit byte layouts
- **MessagePack:** First-byte marker system with clear format families
- **XDR (RFC 4506):** Alignment and padding rules explicitly stated

**Key Takeaway:** Specify encoding at the byte (or bit) level. Show hexadecimal examples for binary formats. Include edge cases (empty, maximum size, negative numbers).

---

### 3. Extensibility Mechanisms

**Best Examples:**
- **CBOR:** Semantic tags (open-ended type system)
- **Protobuf:** Reserved field numbers and field options
- **Avro:** Schema evolution with aliases and defaults
- **MessagePack:** Extension types with application codes

**Key Takeaway:** Plan for evolution from day one. Provide clear rules for adding types, fields, or features without breaking compatibility.

---

### 4. Security Guidance

**Common Themes:**
- **Parser robustness:** Validate lengths before allocation
- **Resource limits:** Maximum message size, nesting depth, array lengths
- **Integer overflow:** Check calculations before allocation
- **Input validation:** Treat all input as untrusted
- **Canonical encoding:** Define one correct encoding for security-critical uses

**Best Examples:**
- **CBOR (RFC 7049):** Comprehensive security section covering all major attack vectors
- **JSON Text Sequences (RFC 7464):** Explicit threat model discussion

**Key Takeaway:** Include dedicated security considerations section. Address parser vulnerabilities, resource exhaustion, and validation requirements.

---

### 5. Example Quality

**Best Practices Observed:**
- **Progression:** Simple → Complex → Edge cases
- **Multiple Representations:** Conceptual, hexadecimal, ASCII art
- **Real-World:** Realistic examples (Person, AddressBook, not Foo/Bar)
- **Annotated:** Explain each byte or field

**Best Examples:**
- **CBOR:** Extensive encoding tables with multiple representations
- **Protobuf:** Realistic message definitions with best practices
- **MessagePack:** Byte-by-byte breakdowns

---

### 6. Implementation Guidance

**Valuable Sections:**
- **Best Practices:** Field numbering (Protobuf), format selection (MessagePack)
- **Common Patterns:** Optional fields, versioning, pagination
- **Performance Tips:** Encoding choices, buffer reuse, batch operations
- **Pitfalls:** What not to do (required fields, field reuse, etc.)

**Best Examples:**
- **Protobuf:** Comprehensive best practices section
- **Avro:** Schema evolution patterns with examples
- **MessagePack:** Encoding optimization guidelines

---

## Format Selection Decision Tree

```
Need human-readable?
├─ YES → JSON (RFC 8259)
│   └─ Streaming? → JSON Text Sequences (RFC 7464)
└─ NO (binary) → Need schema?
    ├─ YES → Need evolution?
    │   ├─ Strong → Avro or Protobuf
    │   │   ├─ Code generation → Protobuf
    │   │   └─ Dynamic typing → Avro
    │   └─ Limited → XDR (RPC legacy)
    └─ NO (schema-less) → Need extensibility?
        ├─ YES → CBOR (semantic tags)
        └─ NO → MessagePack (simplicity)
```

---

## Cross-Cutting Concerns

### Interoperability Considerations

**Lessons from RFCs:**
1. **UTF-8 preference:** JSON, JSON Seq, CBOR all mandate or prefer UTF-8
2. **Byte order:** Specify explicitly (big-endian preferred for network)
3. **Number precision:** Document limitations (JSON's number ambiguity)
4. **Duplicate keys:** Define behavior (reject, first-wins, last-wins)

---

### Versioning Strategies

**Observed Patterns:**

1. **Field Numbers (Protobuf):**
   - Never reuse numbers
   - Reserve deleted fields
   - Low numbers for frequent fields

2. **Defaults and Optional (Avro):**
   - All fields have defaults
   - Aliases for renames
   - Schema resolution rules

3. **Extension Types (CBOR, MessagePack):**
   - Application-specific type codes
   - Ignore unknown extensions
   - Standard types in reserved range

4. **Version Field:**
   - Explicit version in message
   - Discriminated union of versions

---

### Performance Optimization

**Size Efficiency:**
- **Varint encoding:** Protobuf, MessagePack (common case optimization)
- **Packed repeated fields:** Protobuf
- **Compression:** Avro data files (deflate, snappy, zstandard)
- **Fixed vs. variable length:** Trade-offs documented

**Speed Efficiency:**
- **Simple parsing:** MessagePack (first-byte markers)
- **Indexed fields:** Protobuf (field numbers)
- **Streaming:** JSON Sequences, CBOR indefinite-length
- **Code generation:** Protobuf (type-safe, no reflection)

---

## Specification Authoring Checklist

Based on this collection, a complete data format specification should include:

### Essential Sections
- [ ] Abstract/Overview with design goals
- [ ] Type system definition (primitive and complex types)
- [ ] Grammar or syntax rules (formal notation)
- [ ] Encoding rules (byte-level precision)
- [ ] Comprehensive examples (simple to complex)
- [ ] Security considerations
- [ ] Implementation guidance

### Recommended Sections
- [ ] Comparison with related formats
- [ ] Use case recommendations
- [ ] Performance characteristics
- [ ] Schema evolution rules (if applicable)
- [ ] Extension mechanisms
- [ ] Error handling guidance
- [ ] Test vectors

### Optional but Valuable
- [ ] RPC protocol definition (if applicable)
- [ ] File format specification (if applicable)
- [ ] Compression integration
- [ ] Language bindings guidance
- [ ] Canonical encoding rules
- [ ] IANA considerations (type registries, etc.)

---

## Usage Recommendations

### For Specification Authors

1. **Starting a New Format:**
   - Review all seven specifications
   - Choose 2-3 similar to your goals
   - Extract patterns and structure
   - Adapt to your needs

2. **Binary Format:**
   - Study CBOR and MessagePack for encoding patterns
   - Reference Protobuf for schema-based approaches
   - Use XDR for alignment/padding considerations

3. **Text Format:**
   - Use JSON as baseline
   - Add JSON Text Sequences for streaming
   - Consider hybrid approaches (JSON schema like Avro)

4. **Schema Evolution:**
   - Study Avro's resolution rules
   - Learn from Protobuf's field numbering
   - Understand CBOR's extensibility

### For Implementers

1. **Understanding a Format:**
   - Read encoding rules first
   - Study examples with hex/byte breakdowns
   - Review security considerations
   - Check implementation guidance

2. **Testing Implementation:**
   - Use examples as test vectors
   - Test edge cases mentioned in specs
   - Validate security mitigations
   - Cross-reference with other implementations

### For Protocol Designers

1. **Choosing a Format:**
   - Use decision tree above
   - Consider ecosystem and tooling
   - Evaluate performance requirements
   - Plan for evolution

2. **Extending a Format:**
   - Follow extensibility mechanisms
   - Document extensions clearly
   - Maintain backward compatibility
   - Consider interoperability

---

## References and Standards Bodies

### IETF RFCs
- **JSON:** RFC 8259 (STD 90)
- **CBOR:** RFC 8949 (STD 94) [updates RFC 7049]
- **XDR:** RFC 4506 (STD 67)
- **JSON Text Sequences:** RFC 7464

### Company/Community Specifications
- **Protocol Buffers:** Google, https://protobuf.dev/
- **Apache Avro:** Apache Software Foundation, https://avro.apache.org/
- **MessagePack:** Community, https://msgpack.org/

### Related Standards
- **ABNF:** RFC 5234 (grammar notation used in RFCs)
- **UTF-8:** RFC 3629 (character encoding)
- **IEEE 754:** Floating-point standard
- **ISO 8601:** Date/time format (referenced by logical types)

---

## Document Metadata

**Created:** 2025-10-13

**Purpose:** Reference collection for data format specification authoring

**Scope:** Serialization formats (excludes wire protocols, database formats, media codecs)

**Coverage:**
- 4 IETF RFCs (JSON, CBOR, XDR, JSON Sequences)
- 3 Industry specifications (Protobuf, Avro, MessagePack)

**Maintenance:** Update when new major format specifications are published or when existing specs receive significant updates.

---

## Appendix: Format Timeline

Understanding the evolution of data formats:

- **1987:** XDR (RFC 1014, updated 1995 as RFC 1832, 2006 as RFC 4506)
- **1999:** XML 1.0 (W3C, not included in collection)
- **2006:** JSON (RFC 4627, updated 2013 as RFC 7159, 2017 as RFC 8259)
- **2008:** Protocol Buffers open-sourced by Google
- **2009:** Apache Avro 1.0
- **2010:** MessagePack initial release
- **2013:** CBOR (RFC 7049, updated 2020 as RFC 8949)
- **2015:** JSON Text Sequences (RFC 7464)

**Key Trend:** Evolution from text (JSON) to optimized binary formats (CBOR, MessagePack) while maintaining different approaches to schemas (required vs. optional vs. none).
