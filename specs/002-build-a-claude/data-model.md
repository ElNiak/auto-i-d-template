# Data Model: RFC-Style Documentation Generator

**Date**: 2025-10-13
**Feature**: RFC-Style Documentation Generator

## Entity Definitions

### 1. RFC Document

**Description**: The generated specification document containing all sections, cross-references, and metadata about the analyzed codebase.

**Fields**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `docname` | string | Yes | RFC document identifier | Pattern: `draft-[a-z0-9-]+-latest` |
| `title` | string | Yes | Full document title | Max 100 chars |
| `abbrev` | string | No | Abbreviated title | Max 40 chars |
| `category` | enum | Yes | Document category | Values: info, std, bcp, exp, historic |
| `version` | string | Yes | Document version | Pattern: `\d{2}` |
| `authors` | Author[] | Yes | Document authors | Min 1 author |
| `abstract` | string | Yes | Document abstract | Max 500 words |
| `sections` | Section[] | Yes | Document sections | Min required sections |
| `references` | Reference[] | No | External references | Valid URLs/RFCs |
| `metadata` | Metadata | Yes | Generation metadata | Valid timestamps |
| `status` | enum | Yes | Document status | Values: draft, review, published |

**Relationships**:
- Contains multiple `Documentation Sections`
- References multiple `External Standards`
- Maps to multiple `Code Elements` via `Cross-References`

### 2. Code Element

**Description**: A discrete unit of source code (function, class, module) that gets documented with its interfaces, behavior, and relationships.

**Fields**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `id` | string | Yes | Unique identifier | UUID format |
| `type` | enum | Yes | Element type | Values: class, function, module, interface, constant |
| `name` | string | Yes | Element name | Valid identifier |
| `file_path` | string | Yes | Source file path | Valid path |
| `line_start` | integer | Yes | Starting line number | > 0 |
| `line_end` | integer | Yes | Ending line number | >= line_start |
| `signature` | string | No | Function/class signature | Language-specific |
| `docstring` | string | No | Documentation string | Extracted from code |
| `visibility` | enum | Yes | Access level (from LSP) | Values: public, private, protected |
| `language` | string | Yes | Programming language | Supported languages |
| `dependencies` | string[] | No | Imported symbols/modules | Valid symbol IDs or paths |
| `provenance` | enum | Yes | Definition source | Values: defined_here, re_exported, inherited |
| `parameter_constraints` | Constraint[] | No | API validation rules | Type/range constraints |
| `deprecation_info` | Deprecation | No | Deprecation status | Version, reason, alternative |
| `usage_examples` | string[] | No | Example code snippets | From docstrings/tests |

**Sub-Entities**:

#### Constraint
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `parameter_name` | string | Yes | Parameter being constrained |
| `constraint_type` | enum | Yes | Type of constraint |
| `constraint_value` | string | Yes | Constraint specification |
| `error_message` | string | No | Validation error message |

**Constraint Types**: type_check, range, regex, custom

#### Deprecation
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `is_deprecated` | boolean | Yes | Deprecation status |
| `since_version` | string | No | Version when deprecated |
| `reason` | string | No | Deprecation reason |
| `alternative` | string | No | Recommended replacement |

**Relationships**:
- Referenced by multiple `Cross-References`
- Analyzed by `Parser Agent` and `Analyzer Agent`
- May reference other `Code Elements` (dependencies)

### 3. Cross-Reference

**Description**: A bidirectional link between documentation sections and source code locations, maintaining line numbers and file paths with staleness detection.

**Fields**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `id` | string | Yes | Unique identifier | UUID format |
| `rfc_section` | string | Yes | RFC section number | Pattern: `\d+(\.\d+)*` |
| `code_element_id` | string | Yes | Referenced code element | Valid Code Element ID |
| `relationship_type` | enum | Yes | Type of relationship | Values: describes, implements, references, example |
| `confidence` | float | Yes | Confidence score | 0.0 - 1.0 |
| `last_synced` | timestamp | Yes | Last synchronization time | ISO 8601 format |
| `file_checksum` | string | Yes | SHA256 of source file | 64 hex chars |
| `git_commit` | string | No | Git commit hash at creation | Valid git hash (40 hex chars) |
| `staleness_status` | enum | Yes | Reference validity | Values: fresh, stale, unknown |

**Relationships**:
- Links `RFC Document` sections to `Code Elements`
- Stored in `rfc-map.json` for persistence
- Used by `Impact Analyzer` for change detection
- Staleness detected by comparing file_checksum with current file state

### 4. Documentation Section

**Description**: A structured part of the RFC document (Abstract, Introduction, Terminology, Interfaces, Behavior, Security Considerations, etc.)

**Fields**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `id` | string | Yes | Section identifier | Pattern: `\d+(\.\d+)*` |
| `title` | string | Yes | Section title | Max 100 chars |
| `content` | string | Yes | Section content | Markdown format |
| `type` | enum | Yes | Section type | Values: abstract, intro, terminology, interfaces, behavior, security, iana, references, use_cases, change_log, implementation_status, design_rationale |
| `required` | boolean | Yes | Is mandatory section | Based on config |
| `generated` | boolean | Yes | Auto-generated flag | true/false |
| `preserve_blocks` | PreserveBlock[] | No | Manual edit blocks | Valid markers |
| `order` | integer | Yes | Display order | > 0 |

**Section Types**:
- **Standard IETF**: abstract, intro, terminology, interfaces, behavior, security, iana, references
- **Enhanced** (optional): use_cases, change_log, implementation_status, design_rationale

**Relationships**:
- Part of `RFC Document`
- Contains `Cross-References` to code
- May reference `External Standards`

### 5. External Standard

**Description**: A referenced specification (IETF RFC, W3C standard, etc.) that the codebase implements or conforms to.

**Fields**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `id` | string | Yes | Standard identifier | e.g., "RFC8446", "W3C-HTML5" |
| `title` | string | Yes | Standard title | Official title |
| `url` | string | Yes | Standard URL | Valid URL |
| `type` | enum | Yes | Standard type | Values: RFC, W3C, ECMA, ISO, IEEE |
| `version` | string | No | Standard version | Version string |
| `detection_method` | enum | Yes | How detected | Values: config, comment, signature |
| `confidence` | float | Yes | Detection confidence | 0.0 - 1.0 |

**Relationships**:
- Referenced by `RFC Document`
- Detected from `Code Elements`

### 6. Change Set

**Description**: A collection of code modifications that trigger documentation updates, tracked to prevent redundant regeneration.

**Fields**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `id` | string | Yes | Change set ID | UUID format |
| `commit_hash` | string | No | Git commit hash | Valid git hash |
| `timestamp` | timestamp | Yes | Change time | ISO 8601 format |
| `changed_files` | string[] | Yes | Modified file paths | Valid paths |
| `affected_elements` | string[] | Yes | Affected Code Element IDs | Valid IDs |
| `affected_sections` | string[] | Yes | RFC sections to update | Section numbers |
| `change_type` | enum | Yes | Type of change | Values: add, modify, delete |
| `severity` | enum | Yes | Impact severity | Values: must_update, should_review, may_ignore |

**Relationships**:
- Affects multiple `Code Elements`
- Triggers updates to `Documentation Sections`
- Analyzed by `Impact Analyzer`

## Agent Entities

### 7. Parser Agent

**Description**: Specialized agent that analyzes source code structure and extracts syntactic information.

**State**:
| Field | Type | Description |
|-------|------|-------------|
| `session_id` | string | Unique session identifier |
| `target_paths` | string[] | Paths to analyze |
| `processed_files` | string[] | Already processed files |
| `extracted_elements` | CodeElement[] | Extracted code elements |
| `status` | enum | Current status: idle, parsing, complete, error |

**Capabilities**:
- Uses SerenaMCP for code analysis
- Extracts functions, classes, interfaces
- Identifies public APIs
- Detects language and structure

### 8. Analyzer Agent

**Description**: Specialized agent that extracts semantic meaning, relationships, and behavioral patterns from parsed code.

**State**:
| Field | Type | Description |
|-------|------|-------------|
| `session_id` | string | Unique session identifier |
| `code_elements` | CodeElement[] | Elements to analyze |
| `relationships` | Relationship[] | Detected relationships |
| `behaviors` | Behavior[] | Extracted behaviors |
| `external_refs` | ExternalStandard[] | Detected standards |
| `status` | enum | Current status |

**Capabilities**:
- Semantic relationship analysis
- Protocol detection
- State machine extraction
- External standard identification

### 9. Formatter Agent

**Description**: Specialized agent that generates RFC-compliant documentation sections from analyzed data.

**State**:
| Field | Type | Description |
|-------|------|-------------|
| `session_id` | string | Unique session identifier |
| `template` | string | RFC template to use |
| `sections` | DocumentationSection[] | Generated sections |
| `preserve_blocks` | PreserveBlock[] | Manual edits to preserve |
| `status` | enum | Current status |

**Capabilities**:
- Generates kramdown-rfc format
- Creates cross-references
- Preserves manual edits
- Formats to IETF conventions

### 10. Validator Agent

**Description**: Specialized agent that ensures IETF standards compliance and documentation completeness.

**State**:
| Field | Type | Description |
|-------|------|-------------|
| `session_id` | string | Unique session identifier |
| `document` | RFCDocument | Document to validate |
| `validation_errors` | ValidationError[] | Found errors |
| `warnings` | Warning[] | Found warnings |
| `status` | enum | Current status |

**Capabilities**:
- IETF compliance checking
- Cross-reference validation
- Completeness verification
- Quality gate enforcement

### 11. Coordinator/Orchestrator

**Description**: Central agent that manages workflow, balances load, and ensures context consistency across all specialized agents.

**State**:
| Field | Type | Description |
|-------|------|-------------|
| `session_id` | string | Unique session identifier |
| `command` | string | User command |
| `agents` | Agent[] | Spawned agents |
| `progress` | Progress | Overall progress |
| `final_document` | RFCDocument | Assembled document |
| `status` | enum | Current status |

**Capabilities**:
- Spawns specialized agents
- Manages chunked processing
- Aggregates results
- Handles failures gracefully

## Data Storage

### rfc-map.json Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["version", "mappings"],
  "properties": {
    "version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+\\.\\d+$"
    },
    "mappings": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["code", "rfc", "relationship", "last_synced", "file_checksum", "staleness_status"],
        "properties": {
          "code": {
            "type": "object",
            "required": ["file", "symbol", "line"],
            "properties": {
              "file": {"type": "string"},
              "symbol": {"type": "string"},
              "line": {"type": "integer", "minimum": 1}
            }
          },
          "rfc": {
            "type": "object",
            "required": ["section", "heading"],
            "properties": {
              "section": {"type": "string", "pattern": "^\\d+(\\.\\d+)*$"},
              "heading": {"type": "string"}
            }
          },
          "relationship": {
            "type": "string",
            "enum": ["describes", "implements", "references", "example"]
          },
          "last_synced": {
            "type": "string",
            "format": "date-time"
          },
          "file_checksum": {
            "type": "string",
            "pattern": "^[a-f0-9]{64}$",
            "description": "SHA256 hash of source file"
          },
          "git_commit": {
            "type": "string",
            "pattern": "^[a-f0-9]{40}$",
            "description": "Git commit hash at creation"
          },
          "staleness_status": {
            "type": "string",
            "enum": ["fresh", "stale", "unknown"],
            "description": "Whether cross-reference is still valid"
          }
        }
      }
    }
  }
}
```

## State Transitions

### Document Generation Workflow

```
IDLE → PARSING → ANALYZING → FORMATTING → VALIDATING → COMPLETE
         ↓           ↓            ↓            ↓
       ERROR      ERROR        ERROR        ERROR
```

### Incremental Update Workflow

```
IDLE → DETECTING_CHANGES → UPDATING_SECTIONS → VALIDATING → COMPLETE
              ↓                    ↓                ↓
           NO_CHANGES           ERROR            ERROR
```

## Validation Rules

### Cross-Entity Validation

1. **Code Coverage**: Every public API must have a documentation section
2. **Reference Integrity**: All cross-references must point to valid entities
3. **Section Completeness**: All required sections must be present
4. **Preserve Block Integrity**: Manual edits must not conflict
5. **Standard References**: All cited standards must be in references section

### Data Integrity Rules

1. **Unique IDs**: All entity IDs must be globally unique
2. **Path Validity**: All file paths must exist in the repository
3. **Line Number Consistency**: line_end >= line_start for all code elements
4. **Section Ordering**: Section numbers must be sequential
5. **Timestamp Validity**: All timestamps must be valid ISO 8601

## Performance Considerations

### Indexing Strategy

- Code elements indexed by file path for quick lookup
- Cross-references indexed by both RFC section and code element
- Change sets indexed by timestamp for incremental processing

### Caching Strategy

- Parser results cached per file hash
- Analysis results cached per code element
- Generated sections cached with preserve blocks intact

### Chunk Processing

- Maximum 10,000 lines per chunk
- 500 line overlap between chunks
- Results aggregated after all chunks complete