# RFC Impact Analysis Command

Perform deep semantic analysis of code changes and their impact on RFC documentation.

## User Intent

When the user runs `/rfc-analyze-impact`, spawn an analyzer agent that uses Serena MCP tools to:
1. Analyze changed code with full semantic understanding
2. Identify affected RFC sections with high precision
3. Detect breaking changes and API modifications
4. Generate comprehensive impact report with migration guidance

## Prerequisites

- Serena MCP server must be available
- rfc-map.json must exist (run /rfc-generate first)
- Git repository with at least one commit

## Command Execution

### Phase 1: Change Detection

Use lib/impact_analyzer.py for initial change detection:

```python
from lib.impact_analyzer import detect_affected_sections, get_changed_files

# Get changed files since last commit
changed_files = get_changed_files(base_ref="HEAD~1", target_ref="HEAD")

if not changed_files:
    print("✅ No code changes detected")
    exit(0)

# Get affected sections (git diff + line tracking)
impacts = detect_affected_sections(
    file_paths=changed_files,
    rfc_map_path="docs/rfc-map.json",
    base_ref="HEAD~1",
    target_ref="HEAD"
)
```

### Phase 2: Semantic Analysis (Serena MCP)

For each affected file, use Serena MCP tools for deep analysis:

```python
# Get full symbol information with context
for file_path in changed_files:
    # Get symbols overview
    symbols_overview = mcp__serena__get_symbols_overview(
        relative_path=file_path,
        max_answer_chars=50000
    )

    # For each public symbol, get detailed information
    for symbol in symbols_overview['symbols']:
        if symbol['visibility'] == 'public':
            # Get full symbol details with body
            symbol_details = mcp__serena__find_symbol(
                name_path=symbol['name_path'],
                relative_path=file_path,
                include_body=True,
                depth=1  # Include nested symbols
            )

            # Find all references to this symbol
            references = mcp__serena__find_referencing_symbols(
                name_path=symbol['name_path'],
                relative_path=file_path
            )

            # Analyze: breaking change if signature changed
            check_for_breaking_changes(symbol_details, references)
```

### Phase 3: RFC Cross-Reference

Match analyzed symbols to RFC sections:

```python
import json

# Load rfc-map.json
with open('docs/rfc-map.json', 'r') as f:
    rfc_map = json.load(f)

# For each changed symbol, find corresponding RFC section
affected_sections_detailed = []

for symbol in changed_symbols:
    for mapping in rfc_map['mappings']:
        if (mapping['code']['file'] == symbol['file'] and
            mapping['code']['symbol'] == symbol['name']):

            affected_sections_detailed.append({
                'section': mapping['rfc']['section'],
                'heading': mapping['rfc']['heading'],
                'symbol': symbol,
                'change_type': classify_change(symbol),
                'breaking': is_breaking_change(symbol),
                'migration_notes': generate_migration_notes(symbol)
            })
```

### Phase 4: Report Generation

Generate comprehensive markdown report:

```markdown
# RFC Documentation Impact Report

**Analysis Date**: {datetime.now().isoformat()}
**Base Commit**: {base_ref}
**Target Commit**: {target_ref}
**Files Changed**: {len(changed_files)}

---

## Executive Summary

- **🔴 Breaking Changes**: {breaking_count}
- **🟡 API Modifications**: {api_changes_count}
- **🟢 Internal Changes**: {internal_changes_count}
- **📝 RFC Sections Affected**: {len(affected_sections)}

---

## Affected RFC Sections

### Section 3.2: Authentication Interface

**Severity**: 🔴 MUST_UPDATE (Breaking Change)

**Changed Symbols**:
- `authenticate(username: str, password: str) -> Token`
  - **Change Type**: Signature modification
  - **Breaking**: Yes - removed `remember_me` parameter
  - **References**: 15 call sites across 8 files

**Migration Guidance**:
```python
# OLD (no longer supported)
token = authenticate(username, password, remember_me=True)

# NEW (required update)
token = authenticate(username, password)
if remember_me:
    token.extend_session()
```

**Required RFC Updates**:
1. Update interface signature in §3.2.1
2. Add migration note in §3.2.3
3. Update examples in §3.2.4
4. Add backward compatibility note in Appendix A

---

## Detailed Changes

### src/api.py

**Line 42-58**: `authenticate()` function signature changed

**Old Signature**:
```python
def authenticate(
    username: str,
    password: str,
    remember_me: bool = False
) -> Token:
    ...
```

**New Signature**:
```python
def authenticate(
    username: str,
    password: str
) -> Token:
    ...
```

**Impact Assessment**:
- **Visibility**: Public API (exported in `__init__.py`)
- **Call Graph**: 15 references in:
  - `tests/test_auth.py` (8 calls)
  - `src/middleware.py` (4 calls)
  - `src/cli.py` (3 calls)
- **Breaking**: YES - parameter removed without deprecation period
- **Recommended Action**: Add deprecation warning, maintain compatibility for 2 versions

---

## Recommendations

### Immediate Actions (Before RFC Update)

1. **Review Breaking Changes**:
   - [ ] `authenticate()` - Add deprecation warning
   - [ ] `validate_token()` - Consider compatibility wrapper

2. **Update Test Suite**:
   - [ ] Modify 8 test cases in `test_auth.py`
   - [ ] Add backward compatibility tests

3. **Update Examples**:
   - [ ] README.md code samples
   - [ ] Quickstart guide

### RFC Documentation Updates

1. **Section 3.2** (MUST_UPDATE):
   - Update function signature
   - Add migration guide subsection
   - Note breaking change with version

2. **Section 4.1** (SHOULD_REVIEW):
   - Review behavior changes
   - Update state diagrams if needed

3. **Appendix A** (ADD):
   - Create "Migration from v1.x" section
   - Document all breaking changes

---

## Change Classification

### By Severity

| Severity | Count | Sections Affected |
|----------|-------|-------------------|
| MUST_UPDATE | 2 | §3.2, §3.5 |
| SHOULD_REVIEW | 5 | §4.1, §4.2, §4.3, §5.1, §6.2 |
| MAY_IGNORE | 12 | Internal implementation details |

### By Type

| Change Type | Count | Examples |
|-------------|-------|----------|
| Breaking Change | 2 | Parameter removed, return type changed |
| API Addition | 3 | New methods added |
| Behavior Change | 5 | Logic modified, no signature change |
| Internal Refactor | 12 | Private methods, implementation details |

---

## Next Steps

1. **Run `/rfc-update`** to regenerate affected sections
2. **Manual review required** for breaking changes (cannot auto-generate migration notes)
3. **Run `make lint`** to validate updated RFC
4. **Commit updated RFC** with changes
5. **Tag new version** if breaking changes warrant it

---

## Analysis Metadata

- **Analysis Duration**: 2.3 seconds
- **Serena MCP Calls**: 47
- **Symbols Analyzed**: 23
- **References Tracked**: 156
- **Confidence Score**: 0.95 (high confidence)

---

**Generated by**: RFC Impact Analyzer v0.1.0
**Powered by**: Serena MCP + lib/impact_analyzer.py
```

## Output Format

Present the report as formatted markdown with:
- Clear section hierarchy
- Emoji indicators for severity (🔴🟡🟢)
- Code snippets with syntax highlighting
- Actionable checklists
- Metadata for audit trail

## Error Handling

If analysis fails:
1. Fall back to lightweight impact_analyzer.py analysis
2. Report error with diagnostic information
3. Suggest troubleshooting steps:
   - Check Serena MCP connection
   - Verify rfc-map.json exists
   - Ensure git repository has commits

## Performance

- Target: <10 seconds for typical changes (1-5 files)
- Serena MCP calls are expensive - use caching where possible
- Limit symbol analysis to public APIs only (skip private methods)
- Progress reporting: "Analyzing file 2/5..."

## Integration

This command is called by:
- PreToolUse hook suggestions: "Run /rfc-analyze-impact for detailed analysis"
- PostToolUse hook: Mentioned in audit trail
- User manually: When preparing RFC updates after code changes

## Related Commands

- `/rfc-generate`: Initial RFC creation
- `/rfc-update`: Regenerate RFC sections
- `/rfc-validate`: Validate RFC compliance
