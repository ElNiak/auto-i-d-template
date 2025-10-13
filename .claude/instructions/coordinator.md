# RFC Documentation Workflow Coordination

**Purpose**: This document provides workflow orchestration instructions for generating and maintaining IETF-compliant RFC documentation from source code. Slash commands reference these instructions when coordinating specialized subagents.

**Architecture**: The main Claude Code agent reads slash commands (e.g., `/rfc-generate`) which reference this document for workflow logic. The main agent then spawns specialized subagents using the Task tool.

---

## Standard Workflow: Initial RFC Generation

### Overview
When `/rfc-generate` is invoked, follow this sequence:

```
1. Parse command arguments
   ↓
2. Spawn Parser Agent → Extract code structure
   ↓
3. Spawn Analyzer Agent → Semantic analysis
   ↓
4. Spawn Formatter Agent → Generate RFC sections
   ↓
5. Aggregate results → Assemble RFC document
   ↓
6. Build cross-references → Use rfc_mapper library
   ↓
7. Spawn Validator Agent → IETF compliance check
   ↓
8. Write output files (RFC draft + rfc-map.json)
```

### Step-by-Step Instructions

#### Step 1: Parse Command Arguments

Extract from user command:
- **Target paths**: Which directories/files to analyze (default: current directory)
- **Output file**: Where to write RFC draft (default: `docs/generated/draft-{project}-spec-latest.md`)
- **Section filter**: Which sections to generate (default: all)
- **Options**: Additional flags (e.g., `--verbose`, `--skip-validation`)

#### Step 2: Spawn Parser Agent

**Prompt for Task tool**:
```
Analyze code structure from the following paths: {paths}

Use Serena MCP tools exclusively:
- mcp__serena__get_symbols_overview for file-level structure
- mcp__serena__find_symbol for detailed extraction
- mcp__serena__search_for_pattern for content search

Extract:
- Public functions and methods
- Class definitions
- Type definitions
- Constants and enums
- Docstrings

Return JSON format:
{
  "files": [
    {
      "path": "src/api.py",
      "symbols": [
        {
          "name": "authenticate",
          "type": "function",
          "line": 42,
          "signature": "def authenticate(user: str, password: str) -> bool",
          "visibility": "public",
          "docstring": "Authenticates a user..."
        }
      ]
    }
  ]
}
```

**Wait for parser agent completion**. Log progress: "✅ Parser completed: {count} symbols extracted"

#### Step 3: Spawn Analyzer Agent

**Prompt for Task tool**:
```
Analyze the following code elements for semantic relationships and behaviors:

{parser_results}

Use Serena MCP tools:
- mcp__serena__find_referencing_symbols for call graphs
- mcp__serena__search_for_pattern for protocol detection

Detect:
- Function call relationships
- Data flow patterns
- State machines and behaviors
- External standard references (look for RFC citations, protocol implementations)

Return JSON format:
{
  "relationships": [
    {
      "from": "authenticate",
      "to": "validate_token",
      "type": "calls"
    }
  ],
  "behaviors": [
    {
      "name": "Authentication Flow",
      "steps": ["validate credentials", "generate token", "store session"]
    }
  ],
  "standards": [
    {
      "id": "RFC6749",
      "title": "OAuth 2.0",
      "confidence": 0.9,
      "detection_method": "comment"
    }
  ]
}
```

**Wait for analyzer agent completion**. Log: "✅ Analyzer completed: {relationships_count} relationships, {standards_count} standards detected"

#### Step 4: Spawn Formatter Agent

**Prompt for Task tool**:
```
Generate RFC sections from the analyzed code:

Parser results: {parser_results}
Analyzer results: {analyzer_results}

Generate these sections in kramdown-rfc format:

1. **Terminology**: Extract from type definitions, constants, enums
2. **Interfaces**: Document public APIs, function signatures, parameters
3. **Behavior**: Describe workflows, state machines, data flows

Use templates from .claude/templates/sections/ as reference.

Include cross-reference markers: {{xref:src/api.py:authenticate:42}}

Return markdown text with sections clearly marked:
```markdown
## Terminology
...

## Interfaces
...

## Behavior
...
```

**Wait for formatter agent completion**. Log: "✅ Formatter completed: {section_count} sections generated"

#### Step 5: Aggregate Results

Combine outputs from all agents:

```python
aggregated_data = {
    "parsed_symbols": parser_results,
    "relationships": analyzer_results["relationships"],
    "behaviors": analyzer_results["behaviors"],
    "standards": analyzer_results["standards"],
    "rfc_sections": formatter_results
}
```

#### Step 6: Build Cross-References

Use the `rfc_mapper.py` library:

```python
import sys
sys.path.insert(0, '.claude/lib')
from rfc_mapper import RFCMapper

# Create new mapper
mapper = RFCMapper("docs/rfc-map.json")

# Add mappings from parser results
for file in parser_results["files"]:
    for symbol in file["symbols"]:
        # Determine RFC section based on symbol type
        if symbol["type"] in ["class", "interface"]:
            section = "2"  # Terminology
        elif symbol["type"] in ["function", "method"]:
            section = "3"  # Interfaces

        mapper.add_mapping(
            code_file=file["path"],
            code_symbol=symbol["name"],
            code_line=symbol["line"],
            rfc_section=section,
            rfc_heading=determine_heading(section),
            relationship="describes",
            confidence=1.0
        )

# Save mappings
mapper.save()
```

Log: "✅ Created {mapping_count} cross-references in rfc-map.json"

#### Step 7: Spawn Validator Agent (Optional)

**Prompt for Task tool**:
```
Validate the following RFC document for IETF compliance:

{complete_rfc_draft}

Use Make targets for validation:
- Execute: make lint
- Execute: make idnits

Check for:
- kramdown-rfc syntax errors
- Required sections present (Abstract, Introduction, Terminology, Interfaces, Behavior)
- Cross-reference integrity
- Proper frontmatter

Return validation report:
{
  "errors": ["list of blocking errors"],
  "warnings": ["list of non-blocking warnings"],
  "passed": true/false
}
```

**Non-blocking**: Continue even if warnings found. Log: "⚠️ Validator found {warning_count} warnings"

#### Step 8: Write Output Files

1. **Generate RFC frontmatter**:
```markdown
---
docname: draft-{project}-spec-latest
title: {Project} Specification
category: info
ipr: trust200902

author:
 -
    name: {extracted from git config or default}
    email: {extracted from git config or default}
---
```

2. **Assemble complete RFC**:
   - Frontmatter
   - Abstract (auto-generated summary)
   - Introduction (template-based)
   - Terminology (from formatter)
   - Interfaces (from formatter)
   - Behavior (from formatter)
   - Security Considerations (template if needed)
   - References (from analyzer's standards)

3. **Write files**:
   - RFC document to specified output path
   - rfc-map.json to `docs/rfc-map.json`

Log: "✅ RFC document written to: {output_path}"

---

## Incremental Update Workflow

### Overview
When `/rfc-update` is invoked for existing RFC:

```
1. Load existing state
   ↓
2. Detect changed code → Use impact_analyzer
   ↓
3. Extract preserve blocks → Use preserve_edits
   ↓
4. Spawn agents for changed sections only
   ↓
5. Merge with preserved content
   ↓
6. Update timestamps in rfc-map.json
   ↓
7. Write updated RFC
```

### Step-by-Step Instructions

#### Step 1: Load Existing State

```python
import sys
sys.path.insert(0, '.claude/lib')
from rfc_mapper import RFCMapper
from preserve_edits import extract_preserve_blocks

# Load existing RFC
with open(rfc_path, 'r') as f:
    existing_rfc = f.read()

# Load mappings
mapper = RFCMapper("docs/rfc-map.json")
mapper.load()

# Extract preserve blocks
preserve_blocks = extract_preserve_blocks(existing_rfc)
```

Log: "📖 Loaded existing RFC with {len(preserve_blocks)} preserved sections"

#### Step 2: Detect Changed Code

```python
from impact_analyzer import detect_affected_sections

# Analyze changes since last update
impacts = detect_affected_sections(
    rfc_map_path="docs/rfc-map.json",
    base_ref="HEAD~1",
    target_ref="HEAD"
)

# Filter by severity
must_update = [i for i in impacts if i.severity == 'MUST_UPDATE']
should_review = [i for i in impacts if i.severity == 'SHOULD_REVIEW']
```

Log impact report to user. If no impacts, exit early: "✅ No changes detected, RFC is up to date"

#### Step 3: Validate Preserve Blocks

```python
from preserve_edits import validate_preserve_blocks, generate_conflict_log

# Check for conflicts
conflicts = validate_preserve_blocks(preserve_blocks)

# Handle ERROR-level conflicts (overlapping blocks)
error_conflicts = [c for c in conflicts if c.severity == 'ERROR']
if error_conflicts:
    generate_conflict_log(conflicts, ".claude/.preserve-conflicts.log")
    # ABORT: Report to user
    print("❌ ERROR: Overlapping @preserve blocks detected")
    print("See .claude/.preserve-conflicts.log for details")
    exit(1)

# Warn about content overlaps (non-blocking)
warning_conflicts = [c for c in conflicts if c.severity == 'WARNING']
if warning_conflicts:
    generate_conflict_log(conflicts, ".claude/.preserve-conflicts.log")
    print("⚠️  WARNING: Preserved content overlaps with generated sections")
```

#### Step 4: Incremental Agent Spawning

Only spawn agents for **changed files/sections**:

```python
changed_files = [impact.affected_code_elements for impact in must_update + should_review]
changed_sections = [impact.section_number for impact in must_update + should_review]
```

**Spawn Parser Agent** with filtered paths:
- Only analyze changed_files
- Prompt: "Parse code structure from these changed files: {changed_files}"

**Spawn Analyzer Agent** with context:
- Include previous analysis results for context
- Focus on changed elements

**Spawn Formatter Agent** with section filter:
- Only regenerate changed_sections
- Preserve existing content for unchanged sections

#### Step 5: Merge with Preserved Content

```python
from preserve_edits import merge_with_preserved, apply_preservation_priority

# Merge new sections with preserved blocks
merged_content = merge_with_preserved(new_generated_content, preserve_blocks)

# Safety check
final_content = apply_preservation_priority(merged_content, preserve_blocks)
```

Log: "✅ Merged with {len(preserve_blocks)} preserved sections"

#### Step 6: Update Timestamps

```python
# Mark changed files as recently synced
for file in changed_files:
    mapper.update_timestamp(file, symbol, timestamp=None)  # Uses current time

# Save updated mappings
mapper.save()
```

#### Step 7: Write Updated RFC

Write final_content to RFC file. Log: "✅ Updated RFC written to: {rfc_path}"

---

## Error Handling Strategy

### Critical Errors (Abort Workflow)

Stop execution and report clearly:

1. **Parser fails completely**
   - Error: "Code parsing failed. Check that paths are valid and accessible."
   - Check: Are paths correct? Is Serena MCP running?

2. **Serena MCP unavailable**
   - Error: "Serena MCP required for code analysis. Ensure MCP server is running."
   - Check: MCP server status

3. **Output path unwritable**
   - Error: "Cannot write to {path}. Check directory exists and has write permissions."

4. **Overlapping @preserve blocks**
   - Error: "ERROR: Preserve blocks conflict at lines {lines}. See .claude/.preserve-conflicts.log"
   - Resolution: User must manually fix preserve markers

### Non-Critical Errors (Continue with Warning)

Log warning and continue:

1. **Analyzer partially fails**
   - Warning: "Semantic analysis incomplete. Continuing with parser results only."
   - Impact: May miss some relationships

2. **External standards not detected**
   - Warning: "No external standards detected. References section will be skipped."
   - Impact: No References section

3. **Validator warnings**
   - Warning: "IETF compliance check found {count} warnings (non-blocking)"
   - Impact: RFC may need manual review

4. **@preserve content overlaps generated**
   - Warning: "Preserved content overlaps with section {section}. Preservation priority applied."
   - Impact: Generated content in overlap area will be discarded

### Logging

All errors and warnings should be logged to:
- Console: For immediate user feedback
- `.claude/.coordinator-errors.log`: For debugging and audit trail

Format:
```
[2025-10-13T12:00:00] ERROR: Parser agent failed: ...
[2025-10-13T12:00:05] WARNING: Analyzer partial failure: ...
```

---

## Result Aggregation Patterns

### Combining Parser and Analyzer Results

```python
# Enrich parser results with analyzer insights
for file in parser_results["files"]:
    for symbol in file["symbols"]:
        # Add relationships
        symbol["calls"] = [
            r["to"] for r in analyzer_results["relationships"]
            if r["from"] == symbol["name"]
        ]

        # Add behavior context
        symbol["behaviors"] = [
            b for b in analyzer_results["behaviors"]
            if symbol["name"] in b["steps"]
        ]
```

### Mapping to RFC Sections

| Code Element Type | RFC Section | Heading Example |
|-------------------|-------------|-----------------|
| Type definitions, enums, constants | 2 | Terminology |
| Public functions, classes | 3 | Interfaces |
| Implementation logic, state machines | 4 | Behavior |
| External protocols, standards | 5 | References |

### Handling Multiple Agents

If processing large codebases in chunks:

```python
chunk_results = []

for chunk in chunks:
    # Spawn agents for chunk
    parser_result = spawn_parser(chunk)
    analyzer_result = spawn_analyzer(parser_result)
    formatter_result = spawn_formatter(analyzer_result)

    chunk_results.append({
        "parser": parser_result,
        "analyzer": analyzer_result,
        "formatter": formatter_result
    })

# Aggregate all chunks
final_result = aggregate_chunks(chunk_results)
```

---

## Foundational Libraries Usage

### rfc_mapper.py

**Purpose**: Manage bidirectional mappings between code and RFC sections

**Key Operations**:
```python
from rfc_mapper import RFCMapper

# Create/load
mapper = RFCMapper("docs/rfc-map.json")
mapper.load()  # Load existing or start empty

# Add mapping
mapper.add_mapping(
    code_file="src/api.py",
    code_symbol="authenticate",
    code_line=42,
    rfc_section="3.2",
    rfc_heading="Authentication Interface",
    relationship="implements"
)

# Query
file_mappings = mapper.find_mappings_by_file("src/api.py")
section_mappings = mapper.find_mappings_by_section("3.2")

# Update
mapper.update_timestamp("src/api.py", "authenticate")

# Validate
errors = mapper.validate_integrity()

# Save
mapper.save()
```

### preserve_edits.py

**Purpose**: Handle manual edits marked with @preserve blocks

**Key Operations**:
```python
from preserve_edits import (
    extract_preserve_blocks,
    validate_preserve_blocks,
    merge_with_preserved,
    generate_conflict_log
)

# Extract
blocks = extract_preserve_blocks(rfc_content)

# Validate
conflicts = validate_preserve_blocks(blocks)
if conflicts:
    generate_conflict_log(conflicts, ".claude/.preserve-conflicts.log")

# Merge
merged = merge_with_preserved(new_content, blocks)
```

### impact_analyzer.py

**Purpose**: Detect which RFC sections are affected by code changes

**Key Operations**:
```python
from impact_analyzer import detect_affected_sections, format_impact_report

# Detect impacts
impacts = detect_affected_sections(
    file_paths=None,  # Analyzes all changed files
    rfc_map_path="docs/rfc-map.json",
    base_ref="HEAD~1",
    target_ref="HEAD"
)

# Report
if impacts:
    report = format_impact_report(impacts)
    print(report)

    # Filter by severity
    critical = [i for i in impacts if i.severity == 'MUST_UPDATE']
```

---

## Progress Reporting

Keep user informed throughout workflow with clear, emoji-enhanced messages:

**Initial Generation**:
```
🔍 Parsing code structure from 3 paths...
✅ Parser completed: 45 symbols extracted

🔬 Analyzing semantic relationships...
✅ Analyzer completed: 12 relationships, 3 standards detected

📝 Generating RFC sections...
✅ Formatter completed: 4 sections generated

🔒 Creating cross-references...
✅ Added 23 mappings to rfc-map.json

✅ Validating IETF compliance...
⚠️  Validator found 2 warnings (non-blocking)

✅ RFC document written to: draft-myproject-spec-00.md
```

**Incremental Update**:
```
📖 Loading existing RFC and mappings...
✅ Loaded 23 existing mappings

🔍 Detecting code changes...
✅ Found 3 affected sections (2 MUST_UPDATE, 1 SHOULD_REVIEW)

🔒 Validating preserve blocks...
✅ No conflicts detected

🔄 Updating affected sections...
✅ Updated 3 sections

✅ RFC updated: draft-myproject-spec-00.md
```

---

## Configuration and Defaults

### Default Paths

- **RFC output**: `docs/generated/draft-{project}-spec-latest.md`
- **rfc-map.json**: `docs/rfc-map.json`
- **Templates**: `.claude/templates/`
- **Logs**: `.claude/.coordinator-errors.log`
- **Conflict logs**: `.claude/.preserve-conflicts.log`

### Mandatory Sections

From plugin.json configuration:
- Abstract
- Introduction
- Terminology
- Interfaces
- Behavior

### Optional Sections

- Security Considerations
- IANA Considerations
- References (if standards detected)

### Chunk Processing

For codebases >10K lines:
- Chunk size: 10,000 lines
- Overlap: 500 lines
- Process sequentially with context passing

---

## Notes and Best Practices

- ✅ **Always use Serena MCP** for code analysis (never custom parsing)
- ✅ **Always use Make targets** for RFC validation (never direct xml2rfc/idnits calls)
- ✅ **Always preserve @preserve blocks** - They take absolute priority
- ✅ **Always log errors** to .coordinator-errors.log
- ✅ **Never execute user code** - Static analysis only
- ✅ **Report progress frequently** - Users appreciate visibility
- ✅ **Handle failures gracefully** - Partial results better than complete failure

---

## References

- Slash commands: `.claude/commands/rfc-generate.md`, `.claude/commands/rfc-update.md`
- Subagents: `.claude/agents/parser.md`, `.claude/agents/analyzer.md`, `.claude/agents/formatter.md`, `.claude/agents/validator.md`
- Libraries: `.claude/lib/rfc_mapper.py`, `.claude/lib/preserve_edits.py`, `.claude/lib/impact_analyzer.py`
- Templates: `.claude/templates/`
- Data model: `specs/002-build-a-claude/data-model.md`
- Quickstart guide: `specs/002-build-a-claude/quickstart.md`
