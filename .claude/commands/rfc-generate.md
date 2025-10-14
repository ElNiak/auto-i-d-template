---
description: Generate RFC-style documentation from source code
argument-hint: [paths] [--output FILENAME] [--sections SECTION1,SECTION2]
---

Generate RFC-style documentation from the specified source code paths.

## Arguments Provided

```
$ARGUMENTS
```

## Task

You will generate IETF-compliant RFC documentation by orchestrating specialized agents:

### 1. Parse Arguments and Filter Paths (T021)

From `$ARGUMENTS`, extract and validate:
- **Paths**: Directories/files to document (default: `.`)
  - Parse positional arguments (those without `--` prefix)
  - If no paths specified, default to `.` (current directory)
  - Validate each path exists, skip non-existent paths with warning
  - Store as `target_paths` for filtering
- **--output**: Output filename (default: `draft-generated-latest.md`)
  - Extract value after `--output` flag
- **--sections**: Sections to generate (default: all)
  - Extract value after `--sections` flag
  - Split by comma if multiple sections specified

**Path Filtering Strategy**:
When scouting and analyzing code:
1. Only process files under the specified `target_paths`
2. Pass `target_paths` to parser agent as `relative_path` parameter
3. Exclude files outside `target_paths` from analysis
4. Log which paths are being processed

**Example Parsing**:
- `/rfc-generate` → paths: [`.`], output: `draft-generated-latest.md`
- `/rfc-generate src/ lib/` → paths: [`src/`, `lib/`], output: `draft-generated-latest.md`
- `/rfc-generate src/ --output draft-api-00.md` → paths: [`src/`], output: `draft-api-00.md`
- `/rfc-generate --sections interfaces,terminology` → paths: [`.`], sections: [`interfaces`, `terminology`]

### 2. Validate Prerequisites (REVISED - Added Scout Phase)

#### Step 2a: Basic Validation
Check Serena MCP availability with `mcp__serena__list_dir` on ".":
- ❌ If unavailable: Display "Serena MCP required. Check MCP server status." and STOP
- ✅ If available: Continue to scout phase

#### Step 2b: Scout Phase (Pre-Processing with Path Filtering)
Use `mcp__serena__list_dir` to discover code files **within target_paths only**:
- For each path in `target_paths`, call `mcp__serena__list_dir(relative_path=path, recursive=true)`
- Combine results from all target paths
- Filter out non-code files (skip .md, .txt, .json, .yaml, .gitignore, .DS_Store)
- Identify code files by extension (.py, .js, .ts, .go, .rs, .java, .cpp, .h, etc.)
- **Exclude** files outside `target_paths` (path filtering applied here)
- Use `mcp__serena__get_symbols_overview` on 1-2 sample files to test parsability
- Count total lines of code for progress estimation

**Scout Report**:
```
📊 Scout Report:
- Total files: 247
- Code files: 189 (.py: 145, .js: 44)
- Non-code files: 58 (skipped)
- Estimated LOC: 45,230
- Estimated time: ~5 minutes
- Sample parse: ✅ 2/2 files parsed successfully
```

#### Step 2c: Create Output Directory
`!mkdir -p docs/generated/`
`!mkdir -p .claude/.checkpoints/`

- ❌ If no code found: Display "No analyzable code in paths" and STOP
- ❌ If sample parse fails: Display "Code parsing failed. Check Serena MCP configuration" and STOP
- ✅ If all checks pass: Continue to parser agent

### 3. Spawn Parser Agent (WITH CHECKPOINTING and Path Filtering)

Use Task tool to spawn `.claude/agents/parser.md`:

```
Analyze code ONLY in these filtered paths: {target_paths}

IMPORTANT: Only analyze files under the specified paths. Ignore files outside these directories.

Extract public APIs, types, and structure using Serena MCP tools:
- mcp__serena__get_symbols_overview (Phase 1: lightweight indexing)
- mcp__serena__find_symbol (Phase 2: detailed extraction for public APIs only)
- mcp__serena__search_for_pattern

Use two-phase extraction approach:
1. Phase 1: Build lightweight symbol index (files in target_paths only, include_body: false)
2. Phase 2: Extract details for public APIs only (include_body: true)

For each path in target_paths, use relative_path parameter to scope analysis.

Return JSON with extracted code elements.
```

**CHECKPOINT**: Write parser output to `.claude/.checkpoints/parser-{timestamp}.json`
- Calculate SHA256 hash of output for integrity
- Log completion: "✅ Parser checkpoint saved: .claude/.checkpoints/parser-1234567890.json"
- **Schema Validation**: Validate parser output against expected JSON schema before proceeding
- If validation fails: Display schema errors, save to .claude/.checkpoints/parser-invalid.json, STOP

### 4. Spawn Analyzer Agent (WITH CHECKPOINTING)

Use Task tool to spawn `.claude/agents/analyzer.md`:

```
Analyze parsed code for:
- Semantic relationships (project-wide, not file-scope)
- Behavioral patterns (cross-language patterns)
- External standard references (3-layer hierarchical detection)

Establish project-level context FIRST using Serena's index.

Use:
- mcp__serena__find_referencing_symbols (project scope)
- mcp__serena__search_for_pattern (config files, comments, protocol signatures)
- mcp__serena__read_file (dependency files: requirements.txt, package.json, etc.)

Return JSON with analysis results including confidence scores.
```

**CHECKPOINT**: Write analyzer output to `.claude/.checkpoints/analyzer-{timestamp}.json`
- Calculate SHA256 hash of output for integrity
- Log completion: "✅ Analyzer checkpoint saved: .claude/.checkpoints/analyzer-1234567890.json"
- **Schema Validation**: Validate analyzer output against expected JSON schema
- If validation fails: Display schema errors, save to .claude/.checkpoints/analyzer-invalid.json, STOP

### 5. Spawn Formatter Agent (WITH CHECKPOINTING)

Use Task tool to spawn `.claude/agents/formatter.md`:

```
Generate RFC from analysis in kramdown-rfc format:
- Frontmatter (docname, title, author)
- Sections: abstract, terminology, interfaces, behavior, security, references
- Optional sections: use_cases, change_log, implementation_status, design_rationale
- Cross-reference markers using kramdown anchors ({: #anchor})
- Mandatory review markers ([NEEDS MANUAL REVIEW]) for security/design sections

CRITICAL GUIDELINES:
- Use specification language (abstraction, not implementation)
- Use RFC 2119 keywords correctly (MUST, SHOULD, MAY in ALL CAPS)
- Include design rationale (WHY, not just WHAT)
- ALWAYS mark security sections for manual review

Output: RFC content + mappings for rfc-map.json
```

**CHECKPOINT**: Write formatter output to `.claude/.checkpoints/formatter-{timestamp}.json`
- Calculate SHA256 hash of output for integrity
- Log completion: "✅ Formatter checkpoint saved: .claude/.checkpoints/formatter-1234567890.json"
- **Schema Validation**: Validate formatter output against expected JSON schema
- If validation fails: Display schema errors, save to .claude/.checkpoints/formatter-invalid.json, STOP

### 6. Post-Processing Lint Phase (NEW - Validation Before Writing)

Validate generated RFC using Make targets:

#### Step 6a: Kramdown Syntax Validation
- Write RFC content to temporary file: `.claude/.temp-rfc.md`
- Run: `!make lint RFC_FILE=.claude/.temp-rfc.md` (dry-run validation)
- Parse Make output for syntax errors
- If errors: Display validation failures, mark affected sections `[SYNTAX ERROR]`

#### Step 6b: XML2RFC Schema Validation
- Run: `!make txt RFC_FILE=.claude/.temp-rfc.md` (generate XML, validate)
- If errors: Display schema violations with line numbers

#### Step 6c: Quality Gates
- Check: All required sections present (abstract, intro, terminology, interfaces, behavior)
- Check: Cross-references resolve (no broken `{{anchor}}` links)
- Check: RFC 2119 keywords used correctly (MUST/SHOULD/MAY all caps, not lowercase)
- Check: No empty sections (all sections have content)
- Check: Security section has manual review marker

**Validation Report**:
```
✅ Kramdown Syntax: PASS
✅ XML2RFC Schema: PASS
⚠️  Quality Gates:
    - ✅ All required sections present
    - ⚠️  Broken reference: {{#token-validation}} (anchor not found) → Line 145
    - ⚠️  RFC keyword error: Line 145 uses "must" (should be "MUST")
    - ✅ Security section has review marker
```

- If critical errors (syntax/schema): STOP, display errors, save draft to `.claude/.draft-failed.md`
- If warnings only: Continue, but include warnings in final report
- If all pass: Continue to write outputs

### 7. Write Outputs (After Validation)

Write RFC to `docs/generated/{output_file}`

Create `docs/rfc-map.json` with code ↔ RFC mappings (with staleness detection):
```json
{
  "version": "1.0.0",
  "mappings": [{
    "code": {"file": "...", "symbol": "...", "line": 42},
    "rfc": {"section": "3.1", "heading": "..."},
    "relationship": "implements",
    "last_synced": "2025-10-13T...",
    "file_checksum": "abc123...",
    "git_commit": "def456...",
    "staleness_status": "fresh"
  }]
}
```

### 8. Report Success

```
✅ RFC Generated Successfully

Files:
  📄 docs/generated/{output_file}
  🔗 docs/rfc-map.json
  📊 .claude/.checkpoints/ (parser, analyzer, formatter)

Validation:
  ✅ Kramdown syntax valid
  ✅ XML2RFC schema valid
  ⚠️  2 quality warnings (see report above)

Statistics:
  - Files analyzed: 189
  - Public APIs documented: 45
  - External standards detected: 3 (OAuth 2.0, TLS 1.3, HTTP/2)
  - Cross-references generated: 127
  - Sections with manual review markers: 5

Next Steps:
  1. Review validation warnings (if any)
  2. Review sections marked [NEEDS MANUAL REVIEW]
  3. Add @preserve blocks for manual content
  4. Build and validate: `make txt html`
  5. Commit: `git add docs/ && git commit -m "Generate RFC documentation"`
```

### Recovery from Failure

If any agent fails:
1. Check for checkpoint files in `.claude/.checkpoints/`
2. Load last successful checkpoint
3. Display: "⚠️  Agent failed. Resuming from checkpoint: parser-1234567890.json"
4. Skip completed agents, restart from failed agent
5. If all agents fail, display full error report and save partial results

## Error Handling

- **Serena MCP unavailable**: Error + exit
- **No code found**: Warning + exit
- **Parser fails**: Error + exit
- **Analyzer fails**: Continue with structure only (warn user)
- **Formatter fails**: Error + exit

## Example Usage

```
/rfc-generate
/rfc-generate src/ lib/
/rfc-generate src/ --output draft-myapi-00.md
/rfc-generate --sections interfaces,terminology
```
