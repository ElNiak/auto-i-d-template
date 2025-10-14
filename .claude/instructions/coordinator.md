# RFC Documentation Workflow Coordination

**Purpose**: This document provides workflow orchestration instructions for generating and maintaining IETF-compliant RFC documentation from source code. Slash commands reference these instructions when coordinating specialized subagents.

**Architecture**: The main Claude Code agent reads slash commands (e.g., `/rfc-generate`) which reference this document for workflow logic. The main agent then spawns specialized subagents using the Task tool.

---

## Standard Workflow: Initial RFC Generation

### Overview
When `/rfc-generate` is invoked, follow this sequence:

```
0. Check for existing checkpoints → Offer recovery (T020e)
   ↓
1. Parse command arguments
   ↓
1b. Scout phase → Validate prerequisites (T020c)
   ↓
2. Spawn Parser Agent → Extract code structure (T020a)
   ↓
2b. Checkpoint parser → Validate & save (T020b + T020e)
   ↓
3. Spawn Analyzer Agent → Semantic analysis
   ↓
3b. Checkpoint analyzer → Validate & save (T020b + T020e)
   ↓
4. Spawn Formatter Agent → Generate RFC sections
   ↓
4b. Checkpoint formatter → Validate & save (T020b + T020e)
   ↓
5. Aggregate results → Assemble RFC document
   ↓
6. Build cross-references → Use rfc_mapper library
   ↓
7. Spawn Validator Agent → IETF compliance check
   ↓
7b. Lint phase → Validate before writing (T020d)
   ↓
8. Write output files (RFC draft + rfc-map.json)
```

### Checkpoint Recovery (T020e)

**Purpose**: Enable recovery from failures using saved checkpoints

#### Step 0: Check for Existing Checkpoints

At the START of `/rfc-generate`, check for recent checkpoints:

```python
import os
import json
import glob
from datetime import datetime

# Check for checkpoint files (last 24 hours)
checkpoint_dir = ".claude/.checkpoints/"
recent_checkpoints = {}

if os.path.exists(checkpoint_dir):
    # Find recent checkpoints for each agent
    for agent_type in ["parser", "analyzer", "formatter"]:
        pattern = f"{checkpoint_dir}{agent_type}-*.json"
        checkpoints = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)

        if checkpoints:
            # Get most recent checkpoint
            latest_checkpoint = checkpoints[0]
            mtime = os.path.getmtime(latest_checkpoint)
            age_hours = (datetime.now().timestamp() - mtime) / 3600

            if age_hours < 24:  # Only consider recent checkpoints
                recent_checkpoints[agent_type] = {
                    "path": latest_checkpoint,
                    "age_hours": age_hours
                }

# Offer recovery if checkpoints found
if recent_checkpoints:
    print("\n🔍 Found recent checkpoints:")
    for agent, info in recent_checkpoints.items():
        print(f"   - {agent}: {info['path']} ({info['age_hours']:.1f}h ago)")

    print("\nOptions:")
    print("  1. Resume from checkpoints (skip completed agents)")
    print("  2. Start fresh (ignore checkpoints)")

    # In non-interactive mode, default to option 2
    use_checkpoints = False  # Set based on user input or flag

    if use_checkpoints:
        print("\n✅ Resuming from checkpoints...\n")
    else:
        print("\n✅ Starting fresh...\n")
else:
    use_checkpoints = False
```

#### Loading Checkpoint Data

When resuming from checkpoints:

```python
loaded_checkpoints = {}

if use_checkpoints:
    for agent_type, info in recent_checkpoints.items():
        with open(info['path'], 'r') as f:
            checkpoint_data = json.load(f)

        # Verify integrity
        results = checkpoint_data['results']
        results_json = json.dumps(results, sort_keys=True)
        computed_hash = hashlib.sha256(results_json.encode()).hexdigest()

        if computed_hash == checkpoint_data['hash']:
            loaded_checkpoints[agent_type] = results
            print(f"✅ Loaded {agent_type} checkpoint (hash verified)")
        else:
            print(f"⚠️  {agent_type} checkpoint hash mismatch - will regenerate")
            loaded_checkpoints.pop(agent_type, None)

# Skip completed agents
skip_parser = "parser" in loaded_checkpoints
skip_analyzer = "analyzer" in loaded_checkpoints
skip_formatter = "formatter" in loaded_checkpoints
```

#### Agent Skip Logic

When agents are skipped due to checkpoints:

```python
# In Step 2 (Parser)
if skip_parser:
    print("⏭️  Skipping parser (using checkpoint)")
    parser_results = loaded_checkpoints["parser"]
else:
    # Normal parser spawn logic
    ...

# In Step 3 (Analyzer)
if skip_analyzer:
    print("⏭️  Skipping analyzer (using checkpoint)")
    analyzer_results = loaded_checkpoints["analyzer"]
else:
    # Normal analyzer spawn logic
    ...

# In Step 4 (Formatter)
if skip_formatter:
    print("⏭️  Skipping formatter (using checkpoint)")
    formatter_results = loaded_checkpoints["formatter"]
else:
    # Normal formatter spawn logic
    ...
```

### Step-by-Step Instructions

#### Step 1: Parse Command Arguments

Extract from user command:
- **Target paths**: Which directories/files to analyze (default: current directory)
- **Output file**: Where to write RFC draft (default: `docs/generated/draft-{project}-spec-latest.md`)
- **Section filter**: Which sections to generate (default: all)
- **Options**: Additional flags (e.g., `--verbose`, `--skip-validation`)

#### Step 1b: Validate Prerequisites (T020c - Scout Phase)

**Purpose**: Fail fast by discovering and testing code before expensive operations

1. **Check Serena MCP Availability**:
```python
# Test Serena MCP with simple operation
try:
    mcp__serena__list_dir(relative_path=".", recursive=false)
    print("✅ Serena MCP available")
except:
    print("❌ Serena MCP required. Check MCP server status.")
    exit(1)
```

2. **Scout Phase - Discover Code Files**:
```python
# Discover all files recursively
all_files = mcp__serena__list_dir(
    relative_path=target_paths,
    recursive=true,
    skip_ignored_files=true
)

# Filter code files by extension
code_extensions = ['.py', '.js', '.ts', '.go', '.rs', '.java', '.cpp', '.h', '.c', '.cs', '.rb', '.php']
code_files = [f for f in all_files if any(f.endswith(ext) for ext in code_extensions)]
non_code_files = len(all_files) - len(code_files)

# Count by extension for report
extension_counts = {}
for f in code_files:
    ext = f.split('.')[-1]
    extension_counts[ext] = extension_counts.get(ext, 0) + 1

# Estimate LOC (rough estimate: 50 lines per file average)
estimated_loc = len(code_files) * 50

print(f"""
📊 Scout Report:
- Total files: {len(all_files)}
- Code files: {len(code_files)} ({', '.join(f'.{ext}: {count}' for ext, count in extension_counts.items())})
- Non-code files: {non_code_files} (skipped)
- Estimated LOC: {estimated_loc:,}
- Estimated time: ~{estimated_loc // 2000} minutes
""")
```

3. **Test Parsability** (sample 1-2 files):
```python
# Test with first 2 code files
sample_files = code_files[:2]
parse_success = 0

for sample_file in sample_files:
    try:
        overview = mcp__serena__get_symbols_overview(
            relative_path=sample_file,
            max_answer_chars=-1
        )
        if overview:
            parse_success += 1
    except Exception as e:
        print(f"⚠️  Sample parse failed for {sample_file}: {e}")

print(f"- Sample parse: ✅ {parse_success}/{len(sample_files)} files parsed successfully")
```

4. **Create Output Directories**:
```bash
mkdir -p docs/generated/
mkdir -p .claude/.checkpoints/
```

5. **Abort Conditions**:
```python
if len(code_files) == 0:
    print("❌ No analyzable code found in paths")
    exit(1)

if parse_success == 0:
    print("❌ Code parsing failed. Check Serena MCP configuration")
    exit(1)

print("✅ Scout phase complete - ready to generate RFC\n")
```

#### Step 2: Spawn Parser Agent (T020a - Two-Phase Orchestration)

**Prompt for Task tool**:
```
Analyze code structure from the following paths: {paths}

Use TWO-PHASE extraction approach for token efficiency:

Phase 1: Lightweight Symbol Index
- Use mcp__serena__get_symbols_overview with include_body=false
- Build index of ALL symbols with metadata (name, type, line, visibility)
- Filter for public APIs based on LSP visibility metadata
- Track phase_1_symbols count

Phase 2: Detailed Extraction (Public APIs Only)
- Use mcp__serena__find_symbol with include_body=true
- Extract ONLY public symbols identified in Phase 1
- Get full signatures, docstrings, parameters, constraints
- Track phase_2_symbols count
- Skip all private/protected symbols

Extract:
- Public functions and methods
- Class definitions and interfaces
- Type definitions
- Constants and enums
- Docstrings and signatures
- Dependencies and provenance
- Parameter constraints
- Deprecation information

Return JSON format matching parser schema:
{
  "summary": {
    "files_analyzed": 15,
    "public_apis": 23,
    "types": 8,
    "private_symbols_skipped": 47,
    "phase_1_symbols": 70,
    "phase_2_symbols": 23
  },
  "files": ["src/api.py", "src/types.ts"],
  "symbols": [...],
  "interfaces": [...],
  "types": [...],
  "errors": []
}
```

**Wait for parser agent completion**.

#### Step 2b: Checkpoint Parser Output (T020b + T020e)

**Purpose**: Save parser results for recovery and validation

```python
import sys
import json
import hashlib
from datetime import datetime

sys.path.insert(0, '.claude/lib')
from schema_validator import validate_agent_output

# Get parser results
parser_results = {agent_output}

# Validate against schema
is_valid, message, errors = validate_agent_output("parser", parser_results)

if not is_valid:
    # Save invalid output for debugging
    timestamp = int(datetime.now().timestamp())
    invalid_path = f".claude/.checkpoints/parser-invalid-{timestamp}.json"

    with open(invalid_path, 'w') as f:
        json.dump(parser_results, f, indent=2)

    print(f"❌ Parser output validation failed: {message}")
    for error in errors:
        print(f"  - {error}")
    print(f"\n Debug: Invalid output saved to {invalid_path}")
    exit(1)

# Calculate SHA256 hash for integrity
parser_json = json.dumps(parser_results, sort_keys=True)
parser_hash = hashlib.sha256(parser_json.encode()).hexdigest()

# Save checkpoint
timestamp = int(datetime.now().timestamp())
checkpoint_path = f".claude/.checkpoints/parser-{timestamp}.json"

checkpoint_data = {
    "timestamp": timestamp,
    "hash": parser_hash,
    "results": parser_results
}

with open(checkpoint_path, 'w') as f:
    json.dump(checkpoint_data, f, indent=2)

print(f"✅ Parser checkpoint saved: {checkpoint_path}")
print(f"✅ Parser completed: {parser_results['summary']['public_apis']} public APIs extracted")
print(f"   Phase 1: {parser_results['summary']['phase_1_symbols']} symbols indexed")
print(f"   Phase 2: {parser_results['summary']['phase_2_symbols']} symbols detailed")
print(f"   Private symbols skipped: {parser_results['summary']['private_symbols_skipped']}\n")
```

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

**Wait for analyzer agent completion**.

#### Step 3b: Checkpoint Analyzer Output (T020b + T020e)

**Purpose**: Save analyzer results for recovery and validation

```python
import sys
import json
import hashlib
from datetime import datetime

sys.path.insert(0, '.claude/lib')
from schema_validator import validate_agent_output

# Get analyzer results
analyzer_results = {agent_output}

# Validate against schema
is_valid, message, errors = validate_agent_output("analyzer", analyzer_results)

if not is_valid:
    # Save invalid output for debugging
    timestamp = int(datetime.now().timestamp())
    invalid_path = f".claude/.checkpoints/analyzer-invalid-{timestamp}.json"

    with open(invalid_path, 'w') as f:
        json.dump(analyzer_results, f, indent=2)

    print(f"❌ Analyzer output validation failed: {message}")
    for error in errors:
        print(f"  - {error}")
    print(f"\nDebug: Invalid output saved to {invalid_path}")
    exit(1)

# Calculate SHA256 hash for integrity
analyzer_json = json.dumps(analyzer_results, sort_keys=True)
analyzer_hash = hashlib.sha256(analyzer_json.encode()).hexdigest()

# Save checkpoint
timestamp = int(datetime.now().timestamp())
checkpoint_path = f".claude/.checkpoints/analyzer-{timestamp}.json"

checkpoint_data = {
    "timestamp": timestamp,
    "hash": analyzer_hash,
    "results": analyzer_results
}

with open(checkpoint_path, 'w') as f:
    json.dump(checkpoint_data, f, indent=2)

print(f"✅ Analyzer checkpoint saved: {checkpoint_path}")
print(f"✅ Analyzer completed:")
print(f"   Relationships: {len(analyzer_results['relationships'])}")
print(f"   Behaviors: {len(analyzer_results['behaviors'])}")
print(f"   External standards: {len(analyzer_results['external_standards'])}\n")
```

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

**Wait for formatter agent completion**.

#### Step 4b: Checkpoint Formatter Output (T020b + T020e)

**Purpose**: Save formatter results for recovery and validation

```python
import sys
import json
import hashlib
from datetime import datetime

sys.path.insert(0, '.claude/lib')
from schema_validator import validate_agent_output

# Get formatter results
formatter_results = {agent_output}

# Validate against schema
is_valid, message, errors = validate_agent_output("formatter", formatter_results)

if not is_valid:
    # Save invalid output for debugging
    timestamp = int(datetime.now().timestamp())
    invalid_path = f".claude/.checkpoints/formatter-invalid-{timestamp}.json"

    with open(invalid_path, 'w') as f:
        json.dump(formatter_results, f, indent=2)

    print(f"❌ Formatter output validation failed: {message}")
    for error in errors:
        print(f"  - {error}")
    print(f"\nDebug: Invalid output saved to {invalid_path}")
    exit(1)

# Calculate SHA256 hash for integrity
formatter_json = json.dumps(formatter_results, sort_keys=True)
formatter_hash = hashlib.sha256(formatter_json.encode()).hexdigest()

# Save checkpoint
timestamp = int(datetime.now().timestamp())
checkpoint_path = f".claude/.checkpoints/formatter-{timestamp}.json"

checkpoint_data = {
    "timestamp": timestamp,
    "hash": formatter_hash,
    "results": formatter_results
}

with open(checkpoint_path, 'w') as f:
    json.dump(checkpoint_data, f, indent=2)

print(f"✅ Formatter checkpoint saved: {checkpoint_path}")
print(f"✅ Formatter completed:")
print(f"   RFC content length: {len(formatter_results['rfc_content'])} chars")
print(f"   Cross-reference mappings: {len(formatter_results['mappings'])}\n")
```

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

# Add mappings from parser results using section mapping algorithm (T023)
for file in parser_results["files"]:
    for symbol in file["symbols"]:
        # Determine RFC section based on symbol type using comprehensive mapping algorithm
        section, heading = determine_rfc_section(symbol)

        mapper.add_mapping(
            code_file=file["path"],
            code_symbol=symbol["name"],
            code_line=symbol["line"],
            rfc_section=section,
            rfc_heading=heading,
            relationship="describes",
            confidence=1.0
        )

def determine_rfc_section(symbol):
    """
    Map code element types to RFC sections (T023 - Section Mapping Algorithm).

    Decision Tree:
    1. Types, Interfaces, Enums, Constants → Section 2 (Terminology)
    2. Public Functions, Methods, Classes → Section 3 (Interfaces)
    3. Internal Logic, State Machines → Section 4 (Behavior)
    4. Configuration, Patterns → Section 4 (Behavior)

    Returns: (section_number, section_heading)
    """
    symbol_type = symbol.get("type", "").lower()
    visibility = symbol.get("visibility", "public")
    name = symbol.get("name", "")

    # Section 2: Terminology - Types and Data Structures
    if symbol_type in ["interface", "type", "enum", "constant"]:
        return ("2", "Terminology")

    # Section 2: Terminology - Type Classes (data carriers)
    if symbol_type == "class" and ("Data" in name or "Model" in name or "Entity" in name):
        return ("2", "Terminology")

    # Section 3: Interfaces - Public APIs
    if visibility == "public":
        if symbol_type in ["function", "method"]:
            return ("3", "Interfaces")
        if symbol_type == "class":
            return ("3", "Interfaces")

    # Section 4: Behavior - Internal Logic
    if visibility in ["private", "protected"]:
        return ("4", "Behavior")

    # Section 4: Behavior - Configuration
    if symbol_type in ["variable", "config", "setting"]:
        return ("4", "Behavior")

    # Default: Section 3 (Interfaces) for ambiguous public symbols
    return ("3", "Interfaces")

# Save mappings
mapper.save()
```

Log: "✅ Created {mapping_count} cross-references in rfc-map.json"

**Bidirectional Cross-Reference Validation (T022)**:

After creating rfc-map.json, validate cross-references work in both directions:

```python
import re

# 1. Extract CODE_REF markers from RFC
code_ref_pattern = r'<!-- CODE_REF: ([^:]+):([^:]+):(\d+) -->'
rfc_markers = re.findall(code_ref_pattern, formatter_results['rfc_content'])

# 2. Extract mappings from rfc-map.json
map_entries = [(m.code.file, m.code.symbol, m.code.line) for m in mapper.mappings]

# 3. Check: All CODE_REF markers have corresponding rfc-map entries
missing_in_map = []
for file, symbol, line in rfc_markers:
    if (file, symbol, int(line)) not in map_entries:
        missing_in_map.append(f"{file}:{symbol}:{line}")

# 4. Check: All rfc-map entries appear as CODE_REF markers in RFC
missing_in_rfc = []
for file, symbol, line in map_entries:
    if (file, symbol, str(line)) not in rfc_markers:
        missing_in_rfc.append(f"{file}:{symbol}:{line}")

# 5. Report validation results
if missing_in_map:
    print("⚠️  Warning: CODE_REF markers without rfc-map entries:")
    for ref in missing_in_map:
        print(f"   - {ref}")

if missing_in_rfc:
    print("⚠️  Warning: rfc-map entries without CODE_REF markers:")
    for ref in missing_in_rfc:
        print(f"   - {ref}")

if not missing_in_map and not missing_in_rfc:
    print("✅ Cross-reference validation: All mappings bidirectional")
```

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

#### Step 7b: Post-Processing Lint Phase (T020d)

**Purpose**: Validate generated RFC before writing final output

1. **Write RFC to Temporary File**:
```python
import tempfile

# Create temp file for validation
temp_rfc_path = ".claude/.temp-rfc.md"

with open(temp_rfc_path, 'w') as f:
    f.write(complete_rfc_draft)

print("📝 Validating generated RFC...")
```

2. **Kramdown Syntax Validation**:
```bash
# Run kramdown-rfc lint (via Make)
make lint RFC_FILE=.claude/.temp-rfc.md 2>&1
```

Parse output for syntax errors. If errors found:
- Log errors with line numbers
- Mark affected sections with `[SYNTAX ERROR]`
- STOP execution (critical error)

3. **XML2RFC Schema Validation**:
```bash
# Generate XML and validate schema
make txt RFC_FILE=.claude/.temp-rfc.md 2>&1
```

If schema violations found:
- Log errors with context
- STOP execution (critical error)

4. **Quality Gates**:
```python
# Check required sections
required_sections = ["# Abstract", "# Introduction", "# Terminology", "# Interfaces", "# Behavior"]
missing_sections = [sec for sec in required_sections if sec not in complete_rfc_draft]

# Check RFC 2119 keyword usage
import re
lowercase_keywords = re.findall(r'\b(must|should|may)\b(?! [A-Z])', complete_rfc_draft)

# Check for broken cross-references
broken_refs = re.findall(r'\{\{#(\w+)\}\}', complete_rfc_draft)
defined_anchors = re.findall(r'\{: #(\w+)\}', complete_rfc_draft)
broken_refs = [ref for ref in broken_refs if ref not in defined_anchors]

# Check security section marker
has_security = "# Security Considerations" in complete_rfc_draft
security_has_review = "[NEEDS MANUAL REVIEW]" in complete_rfc_draft if has_security else True
```

5. **Generate Validation Report**:
```python
print("\n📊 Validation Report:")
print(f"  ✅ Kramdown Syntax: PASS" if kramdown_valid else f"  ❌ Kramdown Syntax: FAIL")
print(f"  ✅ XML2RFC Schema: PASS" if xml_valid else f"  ❌ XML2RFC Schema: FAIL")
print(f"  Quality Gates:")
print(f"    {'✅' if not missing_sections else '❌'} Required sections: {'All present' if not missing_sections else f'Missing: {missing_sections}'}")
print(f"    {'✅' if not broken_refs else '⚠️ '} Cross-references: {'All valid' if not broken_refs else f'Broken: {broken_refs}'}")
print(f"    {'✅' if not lowercase_keywords else '⚠️ '} RFC 2119 keywords: {'Correct' if not lowercase_keywords else f'Found lowercase: {lowercase_keywords}'}")
print(f"    {'✅' if security_has_review else '⚠️ '} Security review marker: {'Present' if security_has_review else 'Missing'}")
```

6. **Handle Errors**:
```python
# Critical errors (STOP)
if not kramdown_valid or not xml_valid or missing_sections:
    print("\n❌ CRITICAL ERRORS FOUND - Cannot proceed")
    print(f"   Draft saved to: .claude/.draft-failed.md")

    with open(".claude/.draft-failed.md", 'w') as f:
        f.write(complete_rfc_draft)

    exit(1)

# Warnings only (continue)
if broken_refs or lowercase_keywords or not security_has_review:
    print("\n⚠️  WARNINGS FOUND - Review recommended before publication")

# Clean up temp file
os.remove(temp_rfc_path)
```

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
