# Make Target Analysis - RFC Validation Quick Reference

## Overview

This document provides a concise reference for the Make targets used in RFC validation workflows, specifically focusing on `lint` and `txt` targets that integrate with the RFC generation plugin.

---

## `make lint` Target

### Purpose
Validates draft source files for formatting issues and repository configuration problems without building outputs.

### Tools Used
- **Native Bash/grep**: Pattern matching for whitespace and content validation
- **Git**: Repository state validation

### Success Criteria
- Exit code: 0
- No output (silent success)
- All checks pass:
  - Files end with newline
  - No trailing whitespace
  - Correct docname format (draft-*-latest)
  - Default branch configured

### Common Errors

#### 1. Trailing Whitespace
```
draft-example-latest.md contains trailing whitespace
*** Run 'make fix-lint' to automatically fix some errors
```
**Fix**: `make fix-lint` (automatically removes trailing spaces)

#### 2. Missing Newline at EOF
```
draft-example-latest.md has no newline on the last line
*** Run 'make fix-lint' to automatically fix some errors
```
**Fix**: `make fix-lint` (automatically adds newline)

#### 3. Incorrect Docname
```
draft-example-latest.md does not contain its own name (draft-example-latest)
*** Correct the name of drafts in docname or similar fields
```
**Fix**: Update frontmatter in `.md` file to include correct `docname: draft-example-latest`

#### 4. Default Branch Warning (CI only)
```
warning: A default branch for 'origin' is not recorded in this clone.
```
**Fix**: `make fix-lint-default-branch` (auto-configures branch)

### Invocation Pattern
```makefile
# From main.mk:202-210
lint::
ifneq (true,$(CI))
lint:: lint-default-branch
endif
ifneq (true,$(PRE_SETUP))
lint:: lint-docname lint-whitespace
endif
```

### Sub-targets
- `lint-whitespace`: Checks trailing whitespace and newline endings
- `lint-docname`: Validates docname contains draft filename
- `lint-default-branch`: Verifies git remote configuration

### Output in CI (GitHub Actions)
When `TRACE_FILE` is set, lint results are captured and formatted into `GITHUB_STEP_SUMMARY` for visual feedback.

---

## `make txt` Target

### Purpose
Generates RFC-compliant plain text output from draft source files (Markdown or XML).

### Build Pipeline
```
draft-*.md → kramdown-rfc → xml2rfc (v2v3) → add-note.py → [.xml] → xml2rfc (txt) → draft-*.txt
```

#### Stage-by-Stage Breakdown

**Stage 1: kramdown-rfc** (Markdown → XML conversion)
- **Tool**: `kramdown-rfc --v3`
- **Input**: `draft-example-latest.md`
- **Output**: XML (stdout)
- **Purpose**: Parses kramdown-rfc markdown syntax into RFCXML v3 format

**Stage 2: add-note.py** (Venue metadata injection)
- **Tool**: `python add-note.py`
- **Input**: XML from stage 1
- **Output**: XML with venue metadata (stdout)
- **Purpose**: Adds draft submission venue information

**Stage 3: xml2rfc v2v3** (Version upgrade)
- **Tool**: `xml2rfc --v2v3`
- **Input**: XML from stage 2
- **Output**: RFCXML v3 compliant XML (stdout)
- **Purpose**: Converts v2 elements to v3 schema if needed

**Stage 4: xml2rfc txt** (Text rendering)
- **Tool**: `xml2rfc --text --no-pagination`
- **Input**: `draft-example-latest.xml` (intermediate file)
- **Output**: `draft-example-latest.txt`
- **Purpose**: Renders final RFC-compliant plain text

### Tools Used

#### 1. kramdown-rfc (Primary Markdown Parser)
- **Version**: Installed via Ruby bundler (`Gemfile`)
- **Location**: `$(BUNDLE_BIN)/kramdown-rfc`
- **Configuration**:
  - `KRAMDOWN_NO_TARGETS=true`: Disables auto-generated link targets
  - `KRAMDOWN_PERSISTENT=true`: Enables persistent reference cache
  - `KRAMDOWN_REFCACHE_QUIET=true`: Suppresses download messages
  - `KRAMDOWN_REFCACHEDIR`: Cache directory for external references
  - `KRAMDOWN_REFCACHETTL`: Cache TTL (300s in CI, 604800s locally)

#### 2. xml2rfc (RFC Processing Tool)
- **Version**: Installed via Python pip (`requirements.txt`)
- **Location**: `$(VENV)/xml2rfc`
- **Common Options**:
  - `-q`: Quiet mode
  - `--rfc-base-url https://www.rfc-editor.org/rfc/`: RFC link base
  - `--id-base-url https://datatracker.ietf.org/doc/html/`: Internet-Draft link base
  - `--allow-local-file-access`: Permits local file includes
  - `--cache=$(XML2RFC_REFCACHEDIR)`: Reference cache directory
  - `--text`: Generate text output
  - `--no-pagination`: Disable page breaks

#### 3. trace.sh (Build Monitoring)
- **Purpose**: Wraps tool invocations with status tracking
- **Verbose Mode**: Shows "OK" or "FAIL" with colored output
- **Trace File Mode**: Logs status to `$TRACE_FILE` for CI summaries
- **Exit Codes**: Propagates tool exit codes to Make

### Success Criteria
- Exit code: 0
- Output file generated: `draft-*.txt`
- File size: > 0 bytes
- No XML schema errors
- No IDREF resolution errors
- Intermediate `.xml` file auto-deleted (marked `.INTERMEDIATE`)

### Common Errors

#### 1. Invalid Markdown Syntax
```
Unable to detect '%%%' or '---' in markdown file
make: *** [draft-example-latest.xml] Error 1
```
**Cause**: File missing YAML frontmatter (`---`) or mmark header (`%%%`)
**Fix**: Add valid frontmatter to `.md` file

#### 2. kramdown-rfc Parsing Errors
```
*** sections left [nil]!
test-validation: kramdown-rfc ... OK
```
**Cause**: Structural issues in markdown (e.g., anchor without section)
**Fix**: Review kramdown-rfc syntax (anchors must be inside sections)

#### 3. IDREF Resolution Errors
```
draft-example-latest.xml:42: Error: IDREF 'sec-overview' not found
draft-example-latest: xml2rfc-txt ... FAIL
```
**Cause**: Cross-reference to undefined anchor (`{{sec-overview}}` without `{: #sec-overview}`)
**Fix**: Ensure all referenced anchors are defined with `{: #anchor-name}` syntax

#### 4. XML Schema Validation Errors
```
draft-example-latest.xml:15: Error: Element 'section': Missing required attribute 'anchor'
draft-example-latest: xml2rfc-txt ... FAIL
```
**Cause**: Generated XML violates RFC 7991 schema
**Fix**: Review kramdown-rfc output; may indicate malformed markdown structure

#### 5. Dependency Missing
```
/bin/sh: kramdown-rfc: command not found
draft-example-latest: kramdown-rfc ... FAIL
```
**Cause**: Ruby dependencies not installed
**Fix**: `make deps` or `bundle install`

### Invocation Pattern
```makefile
# From main.mk:54,139-140
txt:: $(drafts_txt)

%.txt: %.xml $(DEPS_FILES)
	$(at)$(trace) $@ -s xml2rfc-txt $(xml2rfc) $(XML2RFC_TEXT) $< -o $@
```

### Dependency Chain
```
draft-*.txt ← draft-*.xml ← draft-*.md ← $(DEPS_FILES)
```

Where `$(DEPS_FILES)` includes:
- `.requirements.txt` (Python dependencies)
- `Gemfile.lock` (Ruby dependencies)
- `package-lock.json` (Node.js dependencies, if present)

### Intermediate File Handling
```makefile
# From main.mk:59
.INTERMEDIATE: $(filter-out $(drafts_source),$(addsuffix .xml,$(drafts)))
```

XML files are automatically deleted after successful `.txt` generation to avoid clutter. Use `VERBOSE=true` to see the full pipeline.

---

## Integration Points for RFC Plugin

### 1. How RFC Plugin Output Feeds into Make

**Plugin Workflow** (`/rfc-generate`):
1. Scout Phase: Discover code files
2. Parser Agent: Extract symbols using Serena MCP
3. Analyzer Agent: Map relationships
4. Formatter Agent: Generate kramdown-rfc markdown
5. **Validation Phase** (calls Make):
   - Step 6a: `make lint` (syntax validation)
   - Step 6b: `make txt` (schema validation)
   - Step 6c: Quality gate checks (internal)
6. Output: `docs/generated/draft-*.md` + `docs/rfc-map.json`

**Critical Requirements for Plugin**:
- Draft markdown MUST include YAML frontmatter with `docname: draft-*-latest`
- Anchors MUST use kramdown syntax: `{: #anchor-name}`
- Cross-references MUST use double braces: `{{anchor-name}}`
- Sections MUST have proper heading hierarchy (`#`, `##`, `###`)
- Files MUST end with newline, no trailing whitespace

### 2. File Dependencies and Build Order

**Dependency Graph**:
```
User invokes: /rfc-generate .claude/lib/

       ↓
Plugin generates: docs/generated/draft-plugin-libraries-latest.md
       ↓
Plugin invokes: cd docs/generated && make lint
       ↓ (if pass)
Plugin invokes: cd docs/generated && make txt
       ↓ (if pass)
Plugin writes: docs/rfc-map.json
       ↓
User inspects: docs/generated/draft-plugin-libraries-latest.txt
```

**Make Invocation from Plugin** (recommended pattern):
```python
import subprocess

def validate_rfc_output(draft_path: str) -> tuple[bool, str]:
    """
    Validates RFC draft using Make targets.

    Args:
        draft_path: Absolute path to draft-*.md file

    Returns:
        (success: bool, error_message: str)
    """
    draft_dir = os.path.dirname(draft_path)

    # Step 1: Lint check
    result = subprocess.run(
        ["make", "lint"],
        cwd=draft_dir,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        return False, f"Lint failed:\n{result.stderr}"

    # Step 2: Text generation (also validates XML)
    result = subprocess.run(
        ["make", "txt"],
        cwd=draft_dir,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        return False, f"Text generation failed:\n{result.stderr}"

    return True, ""
```

### 3. Expected Outputs and Validation Status

**Success Pattern**:
```bash
$ cd docs/generated && make lint && make txt
# (no output on lint)
draft-plugin-libraries-latest: kramdown-rfc ... OK
draft-plugin-libraries-latest: venue ... OK
draft-plugin-libraries-latest: v2v3 ... OK
draft-plugin-libraries-latest: xml2rfc-txt ... OK
```

**Validation Status Codes**:
- Exit 0 + no stderr → Full pass, RFC is valid
- Exit 0 + warnings → Pass with notes (review recommended)
- Exit 1 + errors → Fail, must fix before submission

**Generated Artifacts** (after successful `make txt`):
```
docs/generated/
├── draft-plugin-libraries-latest.md   (source)
├── draft-plugin-libraries-latest.txt  (RFC text output)
└── draft-plugin-libraries-latest.xml  (deleted if .INTERMEDIATE)
```

---

## Environment Variables

### Critical for Plugin Integration

| Variable | Purpose | Default |
|----------|---------|---------|
| `CI` | Enables CI-specific behavior | `false` |
| `VERBOSE` | Shows full pipeline output | `false` |
| `TRACE_FILE` | Path for trace logging | (unset) |
| `LIBDIR` | Path to i-d-template lib | `lib` |
| `KRAMDOWN_REFCACHEDIR` | Reference cache directory | `~/.cache/xml2rfc` |
| `XML2RFC_REFCACHEDIR` | XML2RFC cache directory | `~/.cache/xml2rfc` |

### Plugin-Specific Recommendations

**For automated validation** (plugin context):
```bash
export VERBOSE=false        # Suppress verbose output
export CI=false             # Local validation mode
export TRACE_FILE=/tmp/trace-$$.log  # Capture detailed logs
```

**For debugging** (user context):
```bash
export VERBOSE=true         # Show full pipeline
make txt                    # See all tool invocations
```

---

## Troubleshooting Quick Reference

### Symptom: `make lint` fails with whitespace errors
**Solution**: Run `make fix-lint` (auto-fixes whitespace issues)

### Symptom: `make txt` fails with "IDREF not found"
**Solution**: Check cross-references match anchors:
- Reference: `{{sec-intro}}`
- Anchor: `{: #sec-intro}` (must be inside a section)

### Symptom: `make txt` fails with "kramdown-rfc: command not found"
**Solution**: Install dependencies: `make deps` or `bundle install`

### Symptom: Intermediate XML file missing
**Expected**: XML files are auto-deleted after successful build
**Debug**: Use `VERBOSE=true make txt` to see pipeline stages

### Symptom: Cache issues (stale references)
**Solution**: Clear cache:
```bash
rm -rf ~/.cache/xml2rfc
make DISABLE_CACHE=true txt
```

---

## References

- **kramdown-rfc Syntax**: https://github.com/cabo/kramdown-rfc
- **xml2rfc Tool**: https://xml2rfc.tools.ietf.org/
- **RFC 7991 (XML Format)**: https://www.rfc-editor.org/rfc/rfc7991.html
- **RFC 7998 (Text Format)**: https://www.rfc-editor.org/rfc/rfc7998.html

---

## Summary

### Key Takeaways for Plugin Development

1. **Validation is two-phase**: `lint` (formatting) → `txt` (schema)
2. **Pipeline is multi-stage**: kramdown-rfc → xml2rfc (v2v3) → xml2rfc (txt)
3. **Errors propagate via exit codes**: Check `returncode` in subprocess calls
4. **Intermediate files are ephemeral**: XML is auto-deleted after successful build
5. **Verbose mode is your friend**: Use `VERBOSE=true` for debugging

### Critical Success Factors

- YAML frontmatter with correct `docname`
- Proper anchor syntax (`{: #name}`)
- Matching cross-references (`{{name}}`)
- Valid section hierarchy
- No trailing whitespace
- Newline at EOF

---

**Document Version**: 1.0
**Last Updated**: 2025-10-14
**Status**: Operational (validated with draft-plugin-test-latest.md)
