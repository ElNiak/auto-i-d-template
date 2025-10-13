# Data Formats Application Profile

This directory contains comprehensive reference examples for data serialization format specifications.

## Quick Navigation

### IETF RFCs
1. **[RFC 8259 - JSON](rfc8259-json.md)** - JavaScript Object Notation
2. **[RFC 7049 - CBOR](rfc7049-cbor.md)** - Concise Binary Object Representation
3. **[RFC 4506 - XDR](rfc4506-xdr.md)** - External Data Representation Standard
4. **[RFC 7464 - JSON Text Sequences](rfc7464-json-text-sequences.md)** - Streaming JSON format

### Industry Specifications
5. **[Protocol Buffers](protobuf-spec.md)** - Google's binary serialization format
6. **[Apache Avro](avro-spec.md)** - Big data serialization system
7. **[MessagePack](messagepack-spec.md)** - Efficient binary format

### Reference Documents
- **[Summary and Analysis](summary.md)** - Comprehensive guide with comparative analysis, patterns, and recommendations

## Document Structure

Each specification includes:
- Overview and purpose
- Type system definition
- Syntax rules and grammar
- Encoding rules (byte-level detail)
- Representative examples
- Security considerations
- Implementation guidance
- Use cases and comparisons

## Use This Collection For

### Specification Authors
- Study syntax definition patterns
- Learn encoding rule documentation
- Understand security consideration formats
- See example quality standards
- Design extensibility mechanisms

### Protocol Designers
- Choose appropriate format for use case
- Understand trade-offs between formats
- Plan for schema evolution
- Design binary vs. text formats

### Implementers
- Understand format specifications
- Find test vectors and examples
- Learn security mitigations
- Review implementation best practices

## Quick Reference by Need

| Need | Recommended Format |
|------|-------------------|
| Human-readable API | JSON (RFC 8259) |
| Efficient binary | CBOR or MessagePack |
| Schema evolution | Avro or Protocol Buffers |
| Streaming logs | JSON Text Sequences |
| IoT/Constrained | CBOR or MessagePack |
| RPC systems | Protocol Buffers or Avro |
| Big data | Avro |
| Legacy systems | XDR |

## File Sizes
- RFC 8259 (JSON): 3.5 KB
- RFC 7049 (CBOR): 5.5 KB
- RFC 4506 (XDR): 8.3 KB
- RFC 7464 (JSON Sequences): 8.8 KB
- Protocol Buffers: 12 KB
- Apache Avro: 14 KB
- MessagePack: 13 KB
- **Summary**: 16 KB (comprehensive analysis)

**Total Collection Size:** ~80 KB

## Sources

All content extracted from official specifications:
- IETF RFCs: https://www.rfc-editor.org/
- Protocol Buffers: https://protobuf.dev/
- Apache Avro: https://avro.apache.org/
- MessagePack: https://msgpack.org/

## Last Updated
2025-10-13
