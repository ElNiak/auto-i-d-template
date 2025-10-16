---
description: Update existing RFC documentation after code changes
argument-hint: RFC_FILE [--dry-run] [--force]
---

Update an existing RFC document by detecting code changes and regenerating only affected sections while preserving manual edits.

## Arguments Provided

```
$ARGUMENTS
```

## Task

You will update IETF-compliant RFC documentation using incremental update workflow:

### 1. Parse Arguments and Validate Inputs

From `$ARGUMENTS`, extract and validate:
- **RFC_FILE**: Path to existing RFC document (required)
  - First positional argument (e.g., `docs/generated/draft-myapi-00.md`)
  - Must be a `.md` file in `docs/generated/`
  - File must exist or ERROR
- **--dry-run**: Show what would change without writing (optional)
  - If present, skip writing outputs in Step 7
  - Display change report only
- **--force**: Skip conflict validation prompts (optional)
  - If present, auto-resolve WARNING-level conflicts
  - ERROR-level conflicts still block update

**Example Parsing**:
- `/rfc-update docs/generated/draft-api-00.md` → update draft-api-00.md
- `/rfc-update draft-api-00.md --dry-run` → show changes only
- `/rfc-update draft-api-00.md --force` → auto-resolve warnings

### 2. Load Existing State (Step 1 of Incremental Workflow)

#### Step 2a: Validate Prerequisites
Check required files exist:
- ✅ RFC file: `{RFC_FILE}`
- ✅ rfc-map.json: `docs/rfc-map.json`
- ✅ Serena MCP: Test with `mcp__serena__list_dir` on "."

If any missing:
- ❌ RFC file not found: "Cannot update non-existent RFC. Run /rfc-generate first." → STOP
- ❌ rfc-map.json not found: "No traceability map found. Cannot determine changed sections." → STOP
- ❌ Serena MCP unavailable: "Serena MCP required for code analysis." → STOP

#### Step 2b: Load RFC Content
Read existing RFC file:
```python
with open(RFC_FILE, 'r') as f:
    existing_rfc_content = f.read()
```

#### Step 2c: Extract Preserve Blocks
Use `.claude/lib/preserve_edits.py`:
```python
from lib.preserve_edits import extract_preserve_blocks

preserve_blocks = extract_preserve_blocks(existing_rfc_content)
# Returns: List[PreserveBlock] with start_line, end_line, content, marker_id
```

Log preserve blocks found:
```
📝 Found {len(preserve_blocks)} preserve blocks:
  - Line 45-52: @preserve-start id:security-notes
  - Line 87-95: @preserve-start id:custom-behavior
```

#### Step 2d: Load RFC Map
Use `.claude/lib/rfc_mapper.py`:
```python
from lib.rfc_mapper import load_rfc_map

mapper = load_rfc_map("docs/rfc-map.json")
if not mapper:
    print("❌ Failed to load rfc-map.json")
    STOP
```

### 3. Detect Changed Code (Step 2 of Incremental Workflow)

Use `.claude/lib/impact_analyzer.py` to detect changed files and affected RFC sections:

```python
from lib.impact_analyzer import detect_affected_sections

# Detect changes since last RFC update (use git diff)
affected_sections = detect_affected_sections(
    file_paths=None,  # None = auto-detect from git status
    rfc_map_path="docs/rfc-map.json",
    base_ref="HEAD~1",  # Compare with previous commit
    target_ref="HEAD",
    repo_root="."
)

# Filter by severity: BREAKING or COMPATIBLE changes only
changed_sections = [
    s for s in affected_sections
    if s.severity in ['BREAKING', 'COMPATIBLE']
]
```

**Change Report**:
```
📊 Change Detection Report:
  - Files modified: 3 (src/auth.py, src/api.py, src/utils.py)
  - Affected RFC sections: 2 (§3.1, §4.2)
  - Severity: 1 BREAKING, 1 COMPATIBLE, 0 MINOR
  - Unchanged sections: 8 (will be preserved)

Affected Sections:
  § 3.1 Authentication Interface - BREAKING
    - src/auth.py:AuthService.authenticate (line 45)
    - Change: Method signature modified

  § 4.2 Token Validation - COMPATIBLE
    - src/api.py:validate_token (line 123)
    - Change: Implementation updated
```

If no changes detected:
```
✅ No code changes detected. RFC is up-to-date.
```
→ STOP (no update needed)

### 4. Validate Preserve Blocks (Step 3 of Incremental Workflow)

Use `.claude/lib/preserve_edits.py`:
```python
from lib.preserve_edits import validate_preserve_blocks, detect_content_conflicts

# Check for overlapping or nested preserve blocks
conflicts = validate_preserve_blocks(preserve_blocks)

# ERROR-level conflicts: overlapping preserve blocks
error_conflicts = [c for c in conflicts if c.severity == 'ERROR']
if error_conflicts:
    print("❌ Preserve block conflicts detected:")
    for c in error_conflicts:
        print(f"  - {c.description}")
    print("\nFix preserve blocks and try again.")
    STOP

# WARNING-level conflicts: preserve blocks overlap with changed sections
warning_conflicts = [c for c in conflicts if c.severity == 'WARNING']
if warning_conflicts and '--force' not in arguments:
    print("⚠️  Preserve block warnings:")
    for c in warning_conflicts:
        print(f"  - {c.description}")
    print("\nContinue anyway? Preserve blocks will take precedence. (Use --force to skip)")
    # In Claude Code, display warning and let user decide
```

### 5. Spawn Agents for Changed Sections Only (Step 4 of Incremental Workflow)

Extract section IDs from `changed_sections`:
```python
section_filter = [s.section for s in changed_sections]
# Example: ["3.1", "4.2"]
```

#### Step 5a: Spawn Parser Agent (Filtered)
Use Task tool to spawn `.claude/agents/parser.md`:

```
INCREMENTAL UPDATE MODE - Parse only changed files:

Changed files: {list of changed files from impact analysis}

Use Serena MCP tools to extract current state of changed code:
- mcp__serena__get_symbols_overview (for changed files only)
- mcp__serena__find_symbol (for affected symbols)

Return JSON with extracted code elements for CHANGED FILES ONLY.
```

**CHECKPOINT**: Write to `.claude/.checkpoints/parser-update-{timestamp}.json`

#### Step 5b: Spawn Analyzer Agent (Filtered)
Use Task tool to spawn `.claude/agents/analyzer.md`:

```
INCREMENTAL UPDATE MODE - Analyze only changed symbols:

Parser output: {filtered parser results}

Use Serena MCP tools to analyze changed symbols:
- mcp__serena__find_referencing_symbols (impact analysis)
- Cross-reference with unchanged code for dependencies

Return JSON with analysis results for CHANGED SYMBOLS ONLY.
```

**CHECKPOINT**: Write to `.claude/.checkpoints/analyzer-update-{timestamp}.json`

#### Step 5c: Spawn Formatter Agent (Filtered)
Use Task tool to spawn `.claude/agents/formatter.md`:

```
INCREMENTAL UPDATE MODE - Generate only changed sections:

Section filter: {section_filter}  (e.g., ["3.1", "4.2"])

Parser output: {filtered parser results}
Analyzer output: {filtered analyzer results}

Existing preserve blocks:
{JSON.stringify(preserve_blocks)}

Instructions:
- Generate ONLY sections: {section_filter}
- Flag any overlaps with preserve blocks
- Return partial RFC content (coordinator will merge)
- Use specification language and RFC 2119 keywords

Output format:
{
  "rfc_content": "...only regenerated sections...",
  "mappings": [...only for regenerated sections...],
  "updated_sections": ["3.1", "4.2"],
  "warnings": ["Section 3.1 may overlap with preserve block at lines 45-52"]
}
```

**CHECKPOINT**: Write to `.claude/.checkpoints/formatter-update-{timestamp}.json`

### 6. Merge with Preserved Content (Step 5 of Incremental Workflow)

Use `.claude/lib/preserve_edits.py`:
```python
from lib.preserve_edits import merge_with_preserved, apply_preservation_priority

# Get new content from formatter
new_sections_content = formatter_output['rfc_content']

# Replace changed sections in existing RFC
# (Keep frontmatter, unchanged sections, and preserve blocks)
merged_content = merge_with_preserved(
    generated_content=new_sections_content,
    preserve_blocks=preserve_blocks,
    existing_content=existing_rfc_content,
    updated_sections=formatter_output['updated_sections']
)

# Safety check: ensure preserve blocks weren't lost
final_content = apply_preservation_priority(merged_content, preserve_blocks)
```

**Merge Report**:
```
🔀 Merge Summary:
  - Sections updated: 2 (§3.1, §4.2)
  - Sections preserved: 8
  - Preserve blocks honored: 2
  - Conflicts resolved: 0 (preservation priority applied)
```

### 7. Update RFC Map Timestamps (Step 6 of Incremental Workflow)

Use `.claude/lib/rfc_mapper.py`:
```python
# Update timestamps for changed files
for file_path in changed_files:
    mapper.update_timestamp(file_path, symbol="*", timestamp=datetime.now().isoformat())

# Update mappings for new sections
for mapping_data in formatter_output['mappings']:
    mapper.add_mapping(
        code_file=mapping_data['file'],
        code_symbol=mapping_data['symbol'],
        code_line=mapping_data['line'],
        rfc_section=mapping_data['section'],
        rfc_heading=mapping_data['heading'],
        relationship=mapping_data['relationship']
    )

# Save updated map
mapper.save()
```

### 8. Write Outputs (Step 7 of Incremental Workflow)

If `--dry-run` flag present:
```
🔍 DRY RUN - No files modified

Would update:
  📄 {RFC_FILE}
  🔗 docs/rfc-map.json

Changes:
  - Section 3.1 Authentication Interface: REGENERATED
  - Section 4.2 Token Validation: REGENERATED
  - 2 preserve blocks honored
  - 8 sections unchanged

To apply changes, run: /rfc-update {RFC_FILE}
```
→ STOP (don't write files)

Otherwise, write updated files:
```python
# Write updated RFC
with open(RFC_FILE, 'w') as f:
    f.write(final_content)

# rfc-map.json already saved in Step 7
```

### 9. Report Success

```
✅ RFC Updated Successfully

Files Updated:
  📄 {RFC_FILE}
  🔗 docs/rfc-map.json
  📊 .claude/.checkpoints/ (parser-update, analyzer-update, formatter-update)

Changes:
  - Sections regenerated: 2 (§3.1, §4.2)
  - Sections preserved: 8
  - Preserve blocks honored: 2
  - Manual edits retained: ✅

Impact Summary:
  - BREAKING changes: 1 (§3.1 Authentication Interface)
  - COMPATIBLE changes: 1 (§4.2 Token Validation)

Validation:
  ⚠️  Run `make lint` to validate kramdown syntax
  ⚠️  Run `make txt` to validate XML2RFC schema
  ⚠️  Review regenerated sections for accuracy

Next Steps:
  1. Review regenerated sections: §3.1, §4.2
  2. Validate: `make txt html`
  3. Compare: `git diff {RFC_FILE}`
  4. Commit: `git add docs/ && git commit -m "Update RFC after code changes"`
```

### Recovery from Failure

If any step fails:
1. Check for checkpoint files in `.claude/.checkpoints/`
2. Load last successful checkpoint (parser-update, analyzer-update, formatter-update)
3. Display: "⚠️  Update failed. Resuming from checkpoint: {checkpoint_file}"
4. Rollback RFC changes if merge fails (restore from backup)
5. Display full error report

## Error Handling

- **RFC file not found**: Error + exit (run /rfc-generate first)
- **rfc-map.json missing**: Error + exit (no traceability data)
- **No changes detected**: Success + exit (RFC already up-to-date)
- **Preserve block conflicts (ERROR)**: Error + exit (fix overlapping blocks)
- **Preserve block warnings (WARNING)**: Warn + prompt (or --force to continue)
- **Parser fails**: Error + exit with checkpoint
- **Analyzer fails**: Continue with structure only + warn user
- **Formatter fails**: Error + exit with checkpoint
- **Merge fails**: Rollback + error + exit

## Example Usage

```
/rfc-update docs/generated/draft-myapi-00.md
/rfc-update draft-myapi-00.md --dry-run
/rfc-update draft-myapi-00.md --force
```

## Workflow Integration

This command implements the **Incremental Update Workflow** defined in `.claude/instructions/coordinator.md` (lines 842-979):

1. Load existing state (RFC + rfc-map.json + preserve blocks)
2. Detect changed code (impact_analyzer)
3. Validate preserve blocks (preserve_edits)
4. Spawn agents for changed sections only
5. Merge with preserved content (preservation priority)
6. Update timestamps (rfc_mapper)
7. Write updated RFC

**Preservation Priority Rule**: `@preserve` blocks ALWAYS take precedence over generated content in case of conflicts.
