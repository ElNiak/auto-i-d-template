# RFC 7464: JavaScript Object Notation (JSON) Text Sequences

## Overview

**Title:** JavaScript Object Notation (JSON) Text Sequences

**RFC Number:** 7464

**Status:** Standards Track

**Abstract:** Describes a format for JSON text sequences, where multiple JSON texts are encoded in UTF-8, each prefixed by an ASCII Record Separator (0x1E) and ending with a Line Feed (0x0A).

## Key Syntax Rules and Format Specifications

### ABNF Grammar

**Parsing ABNF (Loose):**
```abnf
input-JSON-sequence = *(1*RS possible-JSON)
RS = %x1E                 ; Record Separator
possible-JSON = UTF8-text
```

**Encoding ABNF (Strict):**
```abnf
JSON-sequence = *(RS JSON-text LF)
RS = %x1E                 ; Record Separator (ASCII 0x1E)
LF = %x0A                 ; Line Feed (ASCII 0x0A)
JSON-text = <per RFC 7159>
```

### Format Structure

Each JSON text in a sequence:
1. **Begins with RS (Record Separator, 0x1E)**
2. **Contains valid JSON text**
3. **Ends with LF (Line Feed, 0x0A)**

### Key Characteristics

1. **UTF-8 Only:** All JSON texts must be UTF-8 encoded
2. **No Encoding Declaration:** Character encoding is fixed
3. **Incremental Parsing:** Can be parsed without streaming JSON parser
4. **Error Recovery:** Invalid JSON texts can be skipped
5. **Self-Delimiting:** RS character unambiguously marks boundaries

## Encoding Rules and Sequence Delimiters

### Record Separator (RS)

**Character:** ASCII 0x1E (decimal 30)

**Purpose:**
- Marks the start of each JSON text
- Unambiguously delimits sequence elements
- Not a valid character in JSON texts
- Allows parsers to resynchronize after errors

**Key Property:** RS does not appear in valid JSON texts encoded in UTF-8

### Line Feed (LF)

**Character:** ASCII 0x0A (decimal 10)

**Purpose:**
- Marks the end of each JSON text
- Helps detect truncated JSON values
- Enables line-oriented processing tools
- Improves human readability in some cases

**Rationale:** Without LF, truncated numbers are ambiguous:
```
<RS>123<RS>  Could be: 123 or 1234 or 123456...
<RS>123<LF><RS>  Clearly: 123 (complete)
```

### Encoding Process

**Step-by-Step:**
1. Generate valid JSON text
2. Ensure UTF-8 encoding
3. Prepend RS character (0x1E)
4. Append LF character (0x0A)
5. Repeat for each JSON text

**Pseudocode:**
```
for each json_object:
    json_text = encode_json(json_object)
    output RS
    output json_text
    output LF
```

### Parsing Process

**Step-by-Step:**
1. Read input until RS found
2. Read until LF found
3. Extract text between RS and LF
4. Attempt to parse as JSON
5. If valid, process; if invalid, skip
6. Repeat from step 1

**Pseudocode:**
```
while input_available:
    skip_until(RS)
    text = read_until(LF)
    try:
        json_obj = parse_json(text)
        process(json_obj)
    except:
        continue  # Skip invalid JSON
```

## Examples

### Simple Sequence

**Three JSON objects:**
```
<RS>{"id":1,"name":"Alice"}<LF>
<RS>{"id":2,"name":"Bob"}<LF>
<RS>{"id":3,"name":"Carol"}<LF>
```

**Hexadecimal representation:**
```
1E 7B 22 69 64 22 3A 31 2C 22 6E 61 6D 65 22 3A 22 41 6C 69 63 65 22 7D 0A
1E 7B 22 69 64 22 3A 32 2C 22 6E 61 6D 65 22 3A 22 42 6F 62 22 7D 0A
1E 7B 22 69 64 22 3A 33 2C 22 6E 61 6D 65 22 3A 22 43 61 72 6F 6C 22 7D 0A
```

### Truncated Sequence (mentioned in RFC)

**Incomplete number:**
```
<RS>123<RS>
```
**Problem:** Ambiguous - could be 123, 1234, 123456...

**Complete number:**
```
<RS>123<LF><RS>
```
**Clear:** The number is 123 (LF indicates completion)

### Sequence with Invalid Entry

**Mixed valid/invalid:**
```
<RS>{"valid":true}<LF>
<RS>{invalid json}<LF>
<RS>{"also":"valid"}<LF>
```

**Parser behavior:**
- Parse first object successfully
- Skip second object (invalid)
- Parse third object successfully

### Array of Values

**Sequence of simple values:**
```
<RS>true<LF>
<RS>false<LF>
<RS>null<LF>
<RS>42<LF>
<RS>"hello"<LF>
```

### Nested Objects

**Complex objects:**
```
<RS>{"user":{"id":1,"profile":{"name":"Alice","age":30}}}<LF>
<RS>{"user":{"id":2,"profile":{"name":"Bob","age":25}}}<LF>
```

## Security Considerations

### Threat Model

**Assumption:** All input is untrusted and potentially malicious

### Key Security Issues

1. **Malicious Input Handling:**
   - Parsers must fail gracefully with invalid input
   - Must not crash, hang, or consume excessive resources
   - Invalid JSON texts should be skipped, not cause errors

2. **Partial Parsing:**
   - Truncated sequences are valid
   - Parsers must handle incomplete sequences gracefully
   - No guarantee of receiving complete data

3. **Data Modification Through Re-encoding:**
   - Parsing and re-encoding may modify sequence elements
   - JSON text canonicalization is not standardized
   - Repeated parse/encode cycles can change data

4. **No Integrity Protection:**
   - Format provides no cryptographic integrity
   - Cannot detect tampering or corruption
   - Applications requiring integrity must add their own protection

5. **Data Smuggling:**
   - Different parsers may interpret JSON differently
   - Ambiguities in JSON spec can be exploited
   - Example: Duplicate object keys, number precision

6. **Resource Exhaustion:**
   - Large JSON texts can consume memory
   - Many small texts can consume CPU
   - Implementations should impose limits

7. **Injection Attacks:**
   - RS/LF characters could be used for injection
   - Proper escaping required when embedding sequences
   - Care needed in protocol design

### Recommended Practices

1. **Robust Parsing:**
   - Handle all invalid input gracefully
   - Implement timeouts for parsing
   - Limit maximum JSON text size
   - Limit maximum sequence length

2. **Validation:**
   - Validate JSON structure after parsing
   - Check for expected schema
   - Reject unexpected data types

3. **Resource Limits:**
   - Set maximum memory usage
   - Limit parsing time
   - Implement rate limiting in network scenarios

4. **Integrity Protection:**
   - Use HMAC or digital signatures if needed
   - Consider encrypting sensitive sequences
   - Validate sequence completeness if required

## Key Unique Aspects

### Design Goals

1. **Streaming Support:** Process large sequences incrementally
2. **Error Tolerance:** Continue processing after encountering invalid texts
3. **Simplicity:** Easy to implement and understand
4. **Line-Oriented:** Compatible with line-based tools
5. **Unambiguous:** Clear boundaries between texts

### Advantages

**Over JSON Arrays:**
- Incremental processing without streaming parser
- Error recovery (skip invalid elements)
- No need to parse entire array into memory
- Better for infinite/unbounded sequences

**Over Newline-Delimited JSON:**
- Unambiguous delimiters (RS not in JSON)
- Truncation detection (via LF)
- Better error recovery

### Trade-offs

**Benefits:**
- Simple incremental parsing
- Error resilience
- No schema required
- Backward compatible with JSON

**Limitations:**
- Not human-readable (RS is control character)
- Slightly larger than bare JSON array
- Requires UTF-8 encoding
- No random access

## Use Cases

### Ideal Applications

1. **Log Streaming:**
   - Application logs as JSON objects
   - Real-time log processing
   - Error recovery from corrupted entries

2. **Data Pipelines:**
   - ETL processes
   - Stream processing
   - Map-reduce inputs

3. **Database Dumps:**
   - Incremental exports
   - Large dataset transfers
   - Resumable downloads

4. **Message Queues:**
   - Event streams
   - Pub/sub systems
   - Command sequences

5. **API Responses:**
   - Paginated results
   - Server-sent events
   - Long-polling responses

### Not Recommended For

- Small datasets (JSON array is simpler)
- Human-readable output
- Random access required
- Strict ordering guarantees needed

## Implementation Guidance

### Encoder Implementation

```python
def encode_json_sequence(objects):
    for obj in objects:
        json_text = json.dumps(obj)
        yield '\x1e' + json_text + '\n'
```

### Decoder Implementation

```python
def decode_json_sequence(stream):
    buffer = ''
    for chunk in stream:
        buffer += chunk
        while '\x1e' in buffer:
            # Find RS
            rs_pos = buffer.index('\x1e')
            # Look for LF after RS
            lf_pos = buffer.find('\n', rs_pos)
            if lf_pos == -1:
                break  # Need more data
            # Extract JSON text
            json_text = buffer[rs_pos+1:lf_pos]
            buffer = buffer[lf_pos+1:]
            # Parse JSON
            try:
                obj = json.loads(json_text)
                yield obj
            except:
                # Skip invalid JSON
                continue
```

### Testing Considerations

1. Test with valid sequences
2. Test with invalid JSON texts
3. Test with truncated sequences
4. Test with empty sequences
5. Test with very large texts
6. Test with missing RS or LF
7. Test with nested RS characters (shouldn't occur)

## References

- **Source:** https://www.rfc-editor.org/rfc/rfc7464.txt
- **Depends On:** RFC 7159 (JSON)
- **Related:** RFC 8259 (JSON update)
