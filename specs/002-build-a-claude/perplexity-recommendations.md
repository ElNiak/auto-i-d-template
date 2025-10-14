# Perplexity Recommendations Integration Analysis

**Date**: 2025-10-13
**Feature**: RFC-Style Documentation Generator
**Source**: Expert consultation via Perplexity AI on agent design, workflows, and best practices
**Status**: Pending User Approval

## Executive Summary

This document consolidates expert recommendations from Perplexity AI on improving the RFC documentation generator's parser, analyzer, and formatter agents, plus the /rfc-generate orchestration command. Recommendations are mapped to existing spec artifacts (data-model.md, tasks.md, agent files) with phased implementation priorities aligned to User Story 1 (Generate Initial RFC Documentation - MVP).

**Key Findings**:
- Parser needs two-phase extraction and LSP-based visibility detection
- Analyzer needs project-level context and multi-pronged standard detection
- Formatter needs abstraction over transcription and additional RFC sections
- Command needs checkpointing, schema validation, and pre/post-processing phases

**Implementation Impact**: ~15 new subtasks, 3 entity enhancements, 4 new library components

---

## 1. Parser Agent Recommendations

### Context
**Agent File**: `.claude/agents/parser.md`
**Data Model Entity**: `Code Element` (data-model.md lines 32-53)
**Current Tasks**: T017 (complete), T020-T023 (pending integration)

### Recommendations with Priority

#### P1 - Critical for MVP (User Story 1)

**R-P1.1: Two-Phase Extraction Approach**
- **What**: First build lightweight index with `get_symbols_overview`, then selectively extract details for public APIs only
- **Why**: Dramatically reduces token consumption while maintaining completeness
- **Where to Apply**:
  - **Agent file** (`.claude/agents/parser.md`): Update workflow section to specify two-phase approach
  - **Tasks**: Modify T020 to include phase separation in coordinator
  ```markdown
  ## Workflow (REVISED)

  ### Phase 1: Lightweight Indexing
  1. Discover Files: Use list_dir to identify code files in target paths
  2. Build Symbol Index: Use get_symbols_overview for ALL files (no body extraction)
  3. Filter Public APIs: Identify public symbols based on visibility metadata

  ### Phase 2: Detailed Extraction
  4. Extract Public APIs: Use find_symbol with include_body=True for public symbols ONLY
  5. Extract Types: Find type definitions, interfaces, enums with full details
  6. Output Normalization: Transform to RFC JSON schema
  ```

**R-P1.2: LSP Visibility Metadata (Language-Agnostic)**
- **What**: Use Serena's LSP-based visibility information instead of naming patterns (underscore prefix)
- **Why**: Language-agnostic - works with Python `_`, Java `private`, Go capitalization, TypeScript `private` keyword
- **Where to Apply**:
  - **Agent file** (`.claude/agents/parser.md`): Update "Key Rules" section
  ```markdown
  ## Key Rules (REVISED)

  1. **Skip private symbols**: Use LSP visibility metadata, NOT naming conventions
     - Query symbol metadata for access level (public/private/protected)
     - Python: `_` prefix becomes visibility="private" via LSP
     - Java: `private` keyword detected by LSP
     - TypeScript: `private`/`public` keywords detected by LSP
     - Go: Capitalization (uppercase=public) detected by LSP
  ```
  - **Tasks**: Add validation in T020 that parser uses visibility metadata

**R-P1.3: Enhanced Output Schema**
- **What**: Add fields to Code Element entity for dependency graphs, symbol provenance, validation rules
- **Why**: Critical for RFC generation (Implementation Notes, API contracts, deprecation)
- **Where to Apply**:
  - **Data Model** (`data-model.md`): Update Code Element entity (lines 32-53)
  ```markdown
  | Field | Type | Required | Description | Validation |
  |-------|------|----------|-------------|------------|
  | `dependencies` | string[] | No | Imported symbols/modules | Valid symbol IDs |
  | `provenance` | enum | Yes | Definition source | Values: defined_here, re_exported, inherited |
  | `parameter_constraints` | Constraint[] | No | API validation rules | Type/range constraints |
  | `deprecation_info` | Deprecation | No | Deprecation status | Version, reason, alternative |
  | `usage_examples` | string[] | No | Example code snippets | From docstrings/tests |
  ```
  - **Agent file**: Update output JSON schema in parser.md
  - **Tasks**: Modify T022 to populate new fields during parsing

#### P2 - Enhanced Reliability

**R-P1.4: Staleness Detection**
- **What**: Pair line numbers with file checksums or git commit hashes to detect stale cross-references
- **Why**: Line numbers shift during refactoring - need staleness detection
- **Where to Apply**:
  - **Data Model** (`data-model.md`): Update Cross-Reference entity (lines 55-72)
  ```markdown
  | Field | Type | Required | Description | Validation |
  |-------|------|----------|-------------|------------|
  | `file_checksum` | string | Yes | SHA256 of source file | 64 hex chars |
  | `git_commit` | string | No | Git commit hash | Valid git hash |
  | `staleness_status` | enum | Yes | Reference validity | Values: fresh, stale, unknown |
  ```
  - **Library**: Add staleness checking to `lib/rfc_mapper.py`
  - **Tasks**: Add to Phase 4 (User Story 2 - Update) as part of T032 (compare with current code state)

**R-P1.5: Serena's Persistent Memory**
- **What**: Leverage Serena's `.serena/memories/` for caching parsed results across runs
- **Why**: Incremental documentation updates become significantly faster
- **Where to Apply**:
  - **Agent file** (`.claude/agents/parser.md`): Add to workflow
  ```markdown
  ## Performance Optimization

  - Serena builds cross-reference databases in `.serena/memories/`
  - Reference previous analysis runs for incremental updates
  - Cache results by file hash to avoid re-parsing unchanged files
  ```
  - **Tasks**: Add to Phase 6 (User Story 4 - Scale) as part of T056 (caching mechanism)

---

## 2. Analyzer Agent Recommendations

### Context
**Agent File**: `.claude/agents/analyzer.md`
**Data Model Entities**: `External Standard` (lines 95-112), `Change Set` (lines 114-133)
**Current Tasks**: T018 (complete), T020-T027 (pending integration)

### Recommendations with Priority

#### P1 - Critical for MVP

**R-A1.1: Project-Level Context Analysis**
- **What**: Always analyze within compilation/project context, not single files, to resolve references correctly
- **Why**: Symbol relationships (inheritance, dependencies) require project-wide understanding
- **Where to Apply**:
  - **Agent file** (`.claude/agents/analyzer.md`): Update workflow section
  ```markdown
  ## Workflow (REVISED)

  ### 1. Establish Project Context
  - Let Serena build its initial index (cross-reference databases)
  - Query project-wide symbol hierarchy before analyzing relationships
  - Use relative_path to scope queries but maintain project context

  ### 2. Analyze Relationships (Project-Wide)
  - Find dependencies: Use find_referencing_symbols across entire project
  - Resolve inheritance: Query parent classes in all modules
  - Map composition: Identify object containment across files
  ```
  - **Tasks**: Modify T020 to ensure analyzer gets project context from coordinator

**R-A1.2: Multi-Pronged External Standard Detection**
- **What**: Three-layer detection pipeline: (1) Config/dependencies → (2) Comments → (3) Protocol signatures
- **Why**: Reduces false positives, provides confidence scoring, matches spec requirement FR-009
- **Where to Apply**:
  - **Agent file** (`.claude/agents/analyzer.md`): Update "Detect External Standards" workflow
  ```markdown
  ## 3. Detect External Standards (REVISED - Hierarchical Pipeline)

  ### Layer 1: Configuration/Dependency Analysis (Confidence: 1.0)
  - Parse package.json, requirements.txt, go.mod, Cargo.toml
  - Identify standard library references (e.g., `oauth2`, `crypto/tls`)
  - Direct evidence of standard usage

  ### Layer 2: Explicit Comment References (Confidence: 0.8)
  - Search for "RFC XXXX", "implements RFC", "see RFC" patterns
  - Use search_for_pattern with regex: `RFC\s+\d{4}`
  - Extract title and context from surrounding comments

  ### Layer 3: Protocol Signature Detection (Confidence: 0.6)
  - Identify standard protocol implementations: OAuth flow, HTTP/2 handshake, TLS negotiation
  - Search for endpoint naming conventions: `/oauth/authorize`, `/oauth/token`
  - Detect authentication headers: `Authorization: Bearer`, `WWW-Authenticate`

  ### Cross-Verification
  - When multiple layers detect same standard, max confidence applies
  - Only report detections with confidence >= 0.6 (configurable threshold)
  ```
  - **Data Model**: Already defined in External Standard entity (lines 95-112) - no changes needed
  - **Tasks**: Modify T023 to implement three-layer pipeline

#### P2 - Enhanced Reliability

**R-A1.3: Semantic Pattern Catalog**
- **What**: Rule-based catalog mapping behavioral patterns (state machines, workflows) across languages
- **Why**: Makes pattern detection robust across Python, Java, TypeScript, Go, Rust, etc.
- **Where to Apply**:
  - **New Library**: Create `lib/pattern_catalog.py` with language-agnostic pattern definitions
  ```python
  # lib/pattern_catalog.py
  PATTERNS = {
      "state_machine": {
          "python": {
              "state_enum": "class.*Enum.*State",
              "transition_method": "def.*\(self, .*state.*\):",
          },
          "typescript": {
              "state_enum": "enum.*State.*\{",
              "transition_method": ".*setState\(.*\):",
          },
          "go": {
              "state_enum": "const.*\(.*iota",
              "transition_method": "func.*Transition.*",
          },
      },
      # ... more patterns
  }
  ```
  - **Agent file**: Reference pattern catalog in analyzer.md
  - **Tasks**: Add new task in Phase 5 (User Story 5 - Standards) after T067

**R-A1.4: Enhanced Output Fields**
- **What**: Add design pattern identification, symbol-to-protocol mapping, state diagrams, dependency graphs
- **Why**: Strengthens RFC behavior and references sections
- **Where to Apply**:
  - **Agent file** (`.claude/agents/analyzer.md`): Update output JSON schema
  ```json
  {
    "relationships": [...],
    "behaviors": [...],
    "external_standards": [...],
    "design_patterns": [
      {
        "pattern_name": "Factory",
        "file": "src/factory.py",
        "symbols": ["create_instance", "register_type"],
        "confidence": 0.9
      }
    ],
    "symbol_to_protocol_map": [
      {
        "symbol": "authenticate",
        "protocol": "RFC 6749",
        "protocol_section": "4.1 Authorization Code Grant",
        "implements": "token_request"
      }
    ],
    "state_diagrams": [
      {
        "name": "Order Processing",
        "mermaid": "stateDiagram-v2\n  [*] --> PENDING\n  ..."
      }
    ],
    "dependency_graph": {
      "nodes": [...],
      "edges": [...]
    }
  }
  ```
  - **Tasks**: Add to T023 (section generation logic)

---

## 3. Formatter Agent Recommendations

### Context
**Agent File**: `.claude/agents/formatter.md`
**Data Model Entity**: `Documentation Section` (lines 74-93)
**Current Tasks**: T019 (complete), T022-T024 (pending integration)

### Recommendations with Priority

#### P1 - Critical for MVP

**R-F1.1: Abstraction Over Transcription**
- **What**: Synthesize code semantics into clear, standards-oriented prose - don't over-transcribe implementation details
- **Why**: RFC is specification, not code documentation - focus on contracts, not implementation
- **Where to Apply**:
  - **Agent file** (`.claude/agents/formatter.md`): Update mission and guidelines
  ```markdown
  ## Your Mission (REVISED)

  Transform parsed code structure and semantic analysis into IETF-compliant RFC documentation by:
  - **ABSTRACTING** implementation into specification language (contracts, not code)
  - **SYNTHESIZING** semantic meaning (what and why, not how)
  - **DOCUMENTING** interfaces, behaviors, and guarantees (not line-by-line code)

  ## Key Rules (REVISED)

  1. **Abstraction First**: Describe WHAT the code does and WHY, not HOW
     - Good: "The service authenticates users via OAuth 2.0 authorization code flow"
     - Bad: "The authenticate() function calls get_token() which returns a JWT"
  2. **Specification Language**: Use RFC 2119 keywords for requirements
     - "The service MUST validate tokens before granting access"
     - NOT "The code checks if token is valid"
  3. **Design Rationale**: Include WHY decisions were made
     - "OAuth 2.0 was selected for its industry-standard security model"
  ```
  - **Tasks**: Update T023 to emphasize abstraction in section generation

**R-F1.2: Mandatory Review Markers**
- **What**: Always mark Security Considerations, protocol design, interface stability with `[NEEDS MANUAL REVIEW]`
- **Why**: These sections require human expertise - AI cannot infer security implications
- **Where to Apply**:
  - **Agent file** (`.claude/agents/formatter.md`): Update section generation guidelines
  ```markdown
  ## Section Generation Guidelines (REVISED)

  ### Security Considerations (ALWAYS NEEDS REVIEW)
  ```markdown
  # Security Considerations

  [NEEDS MANUAL REVIEW - Security analysis requires human expertise]

  Based on code analysis, the following areas require security review:
  - Authentication flow in `src/auth.py`
  - Token storage in `src/tokens.py`
  - API endpoint authorization in `src/api.py`

  **Reviewer Guidance**:
  - Verify OAuth 2.0 implementation against RFC 6749
  - Check for CSRF protection in state parameter
  - Validate token expiration and refresh logic
  ```

  ### Protocol Design Decisions (NEEDS REVIEW)
  Mark any inferred design decisions for human validation:
  - "Why was REST chosen over GraphQL? [NEEDS REVIEW]"
  - "Token expiration set to 1 hour [NEEDS REVIEW - verify against requirements]"
  ```
  - **Tasks**: Modify T024 to insert review markers automatically

**R-F1.3: Enhanced Cross-Reference Strategy**
- **What**: Use kramdown anchor attributes `{: #anchor}` for sections, refer with `{{anchor}}`, embed `<!-- CODE_REF -->`
- **Why**: Enables precise internal linking and code traceability
- **Where to Apply**:
  - **Agent file** (`.claude/agents/formatter.md`): Update cross-reference markers section
  ```markdown
  ## Cross-Reference Strategy (REVISED)

  ### Internal Section Anchors
  Use kramdown anchor attributes for all major elements:
  ```markdown
  ## Authentication Flow {: #auth-flow}

  The service implements OAuth 2.0 as described in {{RFC6749}}.
  See {{#token-validation}} for token handling.

  ### Token Validation {: #token-validation}
  ```

  ### Code-to-RFC Markers
  Embed HTML comments linking code to RFC sections:
  ```markdown
  <!-- CODE_REF: src/auth.py:AuthService.authenticate:45 -->
  ### AuthService.authenticate

  Authenticates user credentials via OAuth 2.0...
  ```

  ### External References
  Use IETF citation format:
  ```markdown
  This specification follows {{RFC6749}} for OAuth 2.0.

  ## Normative References

  {#RFC6749} IETF RFC 6749, "The OAuth 2.0 Authorization Framework", October 2012.
  ```
  ```
  - **Tasks**: Already defined in T022 (cross-reference generation) - no changes needed

#### P2 - Enhanced Quality

**R-F1.4: Additional RFC Sections**
- **What**: Add Use Cases and Examples, Change Log, Implementation Status, Design Rationale sections
- **Why**: Provides context and traceability that standard RFC sections miss
- **Where to Apply**:
  - **Data Model** (`data-model.md`): Update Documentation Section entity (line 84)
  ```markdown
  | `type` | enum | Yes | Section type | Values: abstract, intro, terminology, interfaces, behavior, security, iana, references, use_cases, change_log, implementation_status, design_rationale |
  ```
  - **Agent file** (`.claude/agents/formatter.md`): Add section templates
  ```markdown
  ## Additional RFC Sections (RECOMMENDED)

  ### Use Cases and Examples
  Demonstrate common application flows with code and prose:
  ```markdown
  # Use Cases

  ## User Authentication Flow

  1. Client redirects user to `/oauth/authorize` endpoint
  2. User grants permission
  3. Service redirects with authorization code
  4. Client exchanges code for access token

  Example implementation:
  ~~~python
  # From src/auth.py:45
  token = service.authenticate(code, client_id, redirect_uri)
  ~~~
  ```

  ### Change Log / Revision History
  Track major updates for living documents:
  ```markdown
  # Change Log

  ## Version 02 (2025-10-13)
  - Added rate limiting to API endpoints (§4.2)
  - Clarified token expiration behavior (§3.3)
  - Fixed typo in authentication flow diagram (§2.1)
  ```

  ### Implementation Status
  Document known implementations and test statuses:
  ```markdown
  # Implementation Status

  This specification has been implemented in:
  - Python reference implementation (100% compliant, all tests passing)
  - JavaScript SDK (95% compliant, missing rate limiting)

  ## Test Coverage
  - Unit tests: 547/547 passing
  - Integration tests: 23/23 passing
  - Compliance tests: 18/20 passing (2 known issues)
  ```

  ### Design Rationale
  Explain high-level architectural choices:
  ```markdown
  # Design Rationale

  ## Why OAuth 2.0 Over SAML
  OAuth 2.0 was selected because:
  - Industry standard for API authorization
  - Better mobile/SPA support than SAML
  - Simpler token-based model
  - Wider ecosystem support
  ```
  ```
  - **Tasks**: Add to T023 (section generation logic) - generate these sections when content available

**R-F1.5: Consistent RFC 2119 Usage**
- **What**: Ensure MUST/SHOULD/MAY are used consistently and accurately
- **Why**: RFC 2119 keywords define normative requirements - misuse breaks compliance
- **Where to Apply**:
  - **Agent file** (`.claude/agents/formatter.md`): Update RFC 2119 keywords section
  ```markdown
  ## RFC 2119 Keywords (USAGE GUIDELINES)

  Use when describing requirements (always ALL CAPS):

  - **MUST**: Absolute requirement
    - Use for: Security requirements, protocol compliance, data integrity
    - Example: "The service MUST validate all JWT signatures"

  - **SHOULD**: Strong recommendation (can deviate with valid reason)
    - Use for: Best practices, performance optimization, recommended behavior
    - Example: "Clients SHOULD implement exponential backoff for retries"

  - **MAY**: Optional feature (implementation choice)
    - Use for: Optional features, alternative approaches
    - Example: "Services MAY support refresh token rotation"

  **Anti-Patterns** (DO NOT USE):
  - "The code must check..." → "The service MUST validate..."
  - "Should probably use..." → "Clients SHOULD implement..."
  - "Maybe support..." → "Implementations MAY support..."
  ```
  - **Tasks**: Add validation to T024 (frontmatter generation) or Phase 8 (Validation)

---

## 4. /rfc-generate Command Recommendations

### Context
**Command File**: `.claude/commands/rfc-generate.md`
**Related Agents**: `coordinator.md` (orchestrator)
**Current Tasks**: T016 (complete), T020 (pending integration)

### Recommendations with Priority

#### P1 - Critical for MVP

**R-C1.1: Checkpointing**
- **What**: Save intermediate results after each agent completes (parser.json, analyzer.json, formatter.json)
- **Why**: Enables partial restarts and debugging on failure
- **Where to Apply**:
  - **Command file** (`.claude/commands/rfc-generate.md`): Update workflow
  ```markdown
  ### 3. Spawn Parser Agent (WITH CHECKPOINTING)

  Use Task tool to spawn `.claude/agents/parser.md`:
  - Extract public APIs, types, and structure using Serena MCP tools
  - Return JSON with extracted code elements
  - **CHECKPOINT**: Write parser output to `.claude/.checkpoints/parser-{timestamp}.json`
  - Log completion: "Parser checkpoint saved: .claude/.checkpoints/parser-123456.json"

  ### 4. Spawn Analyzer Agent (WITH CHECKPOINTING)

  Use Task tool to spawn `.claude/agents/analyzer.md`:
  - Analyze for semantic relationships, behavioral patterns, external standards
  - Return JSON with analysis results
  - **CHECKPOINT**: Write analyzer output to `.claude/.checkpoints/analyzer-{timestamp}.json`
  - Log completion: "Analyzer checkpoint saved"

  ### 5. Spawn Formatter Agent (WITH CHECKPOINTING)

  Use Task tool to spawn `.claude/agents/formatter.md`:
  - Generate RFC from analysis in kramdown-rfc format
  - Output RFC content + mappings for rfc-map.json
  - **CHECKPOINT**: Write formatter output to `.claude/.checkpoints/formatter-{timestamp}.json`
  - Log completion: "Formatter checkpoint saved"

  ### Recovery from Failure
  If any agent fails:
  1. Check for checkpoint files in `.claude/.checkpoints/`
  2. Load last successful checkpoint
  3. Resume from failed agent (skip completed agents)
  4. Display: "Resuming from checkpoint: analyzer-123456.json"
  ```
  - **Tasks**: Modify T020 to implement checkpointing in coordinator

**R-C1.2: Schema Validation Between Agents**
- **What**: Validate JSON outputs against schemas before passing to next agent
- **Why**: Catch mismatches early, prevent cascading failures
- **Where to Apply**:
  - **New Library**: Create `lib/schema_validator.py` with JSON Schema validation
  ```python
  # lib/schema_validator.py
  import json
  from jsonschema import validate, ValidationError

  PARSER_SCHEMA = {
      "type": "object",
      "required": ["summary", "files", "symbols"],
      "properties": {
          "summary": {"type": "object"},
          "files": {"type": "array"},
          "symbols": {"type": "array"},
      }
  }

  def validate_parser_output(data: dict) -> tuple[bool, str]:
      try:
          validate(instance=data, schema=PARSER_SCHEMA)
          return True, "Valid"
      except ValidationError as e:
          return False, f"Invalid parser output: {e.message}"
  ```
  - **Command file**: Add validation steps in workflow
  ```markdown
  ### 3. Spawn Parser Agent

  [Agent spawning as above...]

  **VALIDATION**: Use schema_validator.py to validate parser output
  - If invalid: Log error, show validation failure, STOP
  - If valid: Proceed to analyzer agent
  ```
  - **Tasks**: Add new task T020b "Implement schema validation in coordinator" (Phase 3)

**R-C1.3: Pre-Processing Scout Phase**
- **What**: Add "scout" phase to identify files/modules, filter non-code, detect syntax errors before parsing
- **Why**: Fail fast on invalid inputs, provide better error messages
- **Where to Apply**:
  - **Command file** (`.claude/commands/rfc-generate.md`): Add step before parser
  ```markdown
  ### 2. Validate Prerequisites (REVISED - ADD SCOUT PHASE)

  #### Step 2a: Basic Validation
  Check Serena MCP availability using mcp__serena__list_dir on "."
  - ❌ If unavailable: Display "Serena MCP required" and STOP
  - ✅ If available: Continue to scout phase

  #### Step 2b: Scout Phase (Pre-Processing)
  Use mcp__serena__list_dir to discover potential code files:
  - List all files in target paths recursively
  - Filter out non-code files (skip .md, .txt, .json, .yaml, .gitignore)
  - Identify code files by extension (.py, .js, .ts, .go, .rs, .java, etc.)
  - Use mcp__serena__get_symbols_overview on 1-2 sample files to test parsability
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
  mkdir -p docs/generated/

  - ❌ If no code found: Display "No analyzable code in paths" and STOP
  - ✅ If code found: Continue to parser agent
  ```
  - **Tasks**: Add new task T020c "Implement scout pre-processing phase" (Phase 3)

**R-C1.4: Post-Processing Lint Phase**
- **What**: Run kramdown-rfc/xml2rfc validators after formatting to catch syntax errors
- **Why**: Ensures generated RFC is valid before writing final output
- **Where to Apply**:
  - **Command file** (`.claude/commands/rfc-generate.md`): Add step after formatter
  ```markdown
  ### 5. Spawn Formatter Agent

  [Agent spawning as above...]

  ### 6. Post-Processing Lint Phase (NEW)

  Validate generated RFC using Make targets:

  #### Step 6a: Kramdown Syntax Validation
  - Write RFC content to temporary file: `.claude/.temp-rfc.md`
  - Run: `make lint RFC_FILE=.claude/.temp-rfc.md` (dry-run validation)
  - Parse Make output for syntax errors
  - If errors: Display validation failures, mark affected sections `[SYNTAX ERROR]`

  #### Step 6b: XML2RFC Schema Validation
  - Run: `make txt RFC_FILE=.claude/.temp-rfc.md` (generate XML, validate)
  - If errors: Display schema violations
  - Extract line numbers and error messages

  #### Step 6c: Quality Gates
  - Check: All required sections present (abstract, intro, terminology, interfaces)
  - Check: Cross-references resolve (no broken `{{anchor}}` links)
  - Check: RFC 2119 keywords used correctly (MUST/SHOULD/MAY all caps)
  - Check: No empty sections (all sections have content)

  **Validation Report**:
  ```
  ✅ Kramdown Syntax: PASS
  ✅ XML2RFC Schema: PASS
  ⚠️  Quality Gates:
      - Missing section: Security Considerations
      - Broken reference: {{#token-validation}} (anchor not found)
      - RFC keyword error: Line 145 uses "must" (should be "MUST")
  ```

  - If critical errors: STOP, display errors, save draft to `.claude/.draft-failed.md`
  - If warnings only: Continue, but flag warnings in final report
  - If all pass: Continue to write outputs
  ```
  - **Tasks**: Add new task T020d "Implement post-processing lint phase" (Phase 3)

#### P2 - Enhanced Reliability

**R-C1.5: Progress Indicators**
- **What**: Provide real-time progress updates for long-running jobs
- **Why**: User experience improvement, shows system isn't frozen
- **Where to Apply**:
  - **Command file**: Add progress logging throughout workflow
  ```markdown
  ### Progress Reporting (Throughout Workflow)

  Display progress at each step:
  - [1/7] Parsing arguments...
  - [2/7] Validating prerequisites...
  - [3/7] Scout phase: Analyzing codebase structure...
  - [4/7] Spawning parser agent (estimated 2-3 minutes)...
  - [5/7] Spawning analyzer agent...
  - [6/7] Spawning formatter agent...
  - [7/7] Writing outputs and validating...

  For long-running agents, show sub-progress:
  - Parser: [████████░░] 80% (145/189 files processed)
  - Analyzer: [██████░░░░] 60% (analyzing relationships...)
  ```
  - **Tasks**: Add to Phase 6 (User Story 4 - Scale) as part of T058 (progress reporting)

**R-C1.6: Diff Generation for Review**
- **What**: After completion, generate diff between previous and current RFC versions
- **Why**: Enables manual review before committing changes
- **Where to Apply**:
  - **New Library**: Create `lib/diff_generator.py` with RFC diff logic
  ```python
  # lib/diff_generator.py
  import difflib

  def generate_rfc_diff(old_path: str, new_path: str) -> str:
      """Generate unified diff between old and new RFC documents."""
      with open(old_path) as f1, open(new_path) as f2:
          old_lines = f1.readlines()
          new_lines = f2.readlines()

      diff = difflib.unified_diff(
          old_lines, new_lines,
          fromfile='RFC (previous)',
          tofile='RFC (current)',
          lineterm=''
      )
      return '\n'.join(diff)
  ```
  - **Command file**: Add to success report
  ```markdown
  ### 7. Report Success (REVISED)

  ✅ RFC Generated

  Files:
    📄 docs/generated/draft-myapi-02.md
    🔗 docs/rfc-map.json
    📊 .claude/.checkpoints/ (parser, analyzer, formatter)

  Changes:
    📝 Diff vs previous version:
    ```diff
    --- RFC (previous)
    +++ RFC (current)
    @@ -145,7 +145,8 @@
     ### Authentication Flow
    -The service uses basic authentication.
    +The service MUST use OAuth 2.0 authorization code flow
    +as defined in {{RFC6749}}.
    ```

  Next Steps:
    1. Review diff above
    2. Add @preserve blocks for manual sections
    3. Validate: `make txt html`
    4. Commit: `git add docs/ && git commit -m "Update RFC"`
  ```
  - **Tasks**: Add to Phase 4 (User Story 2 - Update) as part of T036 (change summary generation)

**R-C1.7: Idempotent Agents**
- **What**: Make agents idempotent (can be re-run safely without side effects)
- **Why**: Enables retry logic, checkpointing recovery, partial runs
- **Where to Apply**:
  - **Research Doc** (`research.md`): Add to technical decisions (line 163)
  ```markdown
  ### 3. Agent Architecture Deep Dive (REVISED)

  **Agent Boundaries**:

  | Agent | Bounded Context | Idempotent | Caching |
  |-------|----------------|------------|---------|
  | **Parser** | Code structure extraction | Yes - deterministic from input | By file hash |
  | **Analyzer** | Semantic relationships | Yes - deterministic from parser output | By code element |
  | **Formatter** | RFC section generation | Yes (with preserve blocks) | By section |
  ```
  - **Agent Files**: Document idempotency in all agent files
  - **Tasks**: Add validation in Phase 8 (Validation) that agents are idempotent

---

## 5. Data Model Enhancements

### Entities Requiring Updates

#### Code Element Entity (data-model.md lines 32-53)

**Current Fields**: 9 fields (id, type, name, file_path, line_start, line_end, signature, docstring, visibility, language)

**New Fields Needed** (from R-P1.3):
```markdown
| `dependencies` | string[] | No | Imported symbols/modules | Valid symbol IDs |
| `provenance` | enum | Yes | Definition source | Values: defined_here, re_exported, inherited |
| `parameter_constraints` | Constraint[] | No | API validation rules | Type/range constraints |
| `deprecation_info` | Deprecation | No | Deprecation status | Version, reason, alternative |
| `usage_examples` | string[] | No | Example code snippets | From docstrings/tests |
```

**Sub-Entities Needed**:
```markdown
#### Constraint (Sub-Entity)
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `parameter_name` | string | Yes | Parameter being constrained |
| `constraint_type` | enum | Yes | Type of constraint (type_check, range, regex, custom) |
| `constraint_value` | string | Yes | Constraint specification |
| `error_message` | string | No | Validation error message |

#### Deprecation (Sub-Entity)
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `is_deprecated` | boolean | Yes | Deprecation status |
| `since_version` | string | No | Version when deprecated |
| `reason` | string | No | Deprecation reason |
| `alternative` | string | No | Recommended replacement |
```

#### Cross-Reference Entity (data-model.md lines 55-72)

**New Fields Needed** (from R-P1.4):
```markdown
| `file_checksum` | string | Yes | SHA256 of source file | 64 hex chars |
| `git_commit` | string | No | Git commit hash at creation | Valid git hash |
| `staleness_status` | enum | Yes | Reference validity | Values: fresh, stale, unknown |
```

#### Documentation Section Entity (data-model.md lines 74-93)

**Field Update Needed** (from R-F1.4):
```markdown
| `type` | enum | Yes | Section type | Values: abstract, intro, terminology, interfaces, behavior, security, iana, references, use_cases, change_log, implementation_status, design_rationale |
```

---

## 6. New Library Components Needed

### L1: Pattern Catalog (lib/pattern_catalog.py)
- **Purpose**: Language-agnostic behavioral pattern definitions
- **Used By**: Analyzer agent (R-A1.3)
- **Priority**: P2
- **Tasks**: Add new task after T067 (Phase 7 - User Story 5)

### L2: Schema Validator (lib/schema_validator.py)
- **Purpose**: JSON schema validation between agents
- **Used By**: Coordinator (R-C1.2)
- **Priority**: P1
- **Tasks**: Add new task T020b (Phase 3 - User Story 1)

### L3: Diff Generator (lib/diff_generator.py)
- **Purpose**: Generate diffs between RFC versions
- **Used By**: /rfc-generate command, /rfc-update command (R-C1.6)
- **Priority**: P2
- **Tasks**: Add to T036 (Phase 4 - User Story 2)

---

## 7. Task Revisions and Additions

### Phase 3 (User Story 1) - T020-T027 Revisions

**T020: Integrate agents in coordinator**
**REVISIONS NEEDED**:
- Add two-phase extraction coordination (R-P1.1)
- Add checkpointing after each agent (R-C1.1)
- Add schema validation between agents (R-C1.2)
- Add progress reporting (R-C1.5)

**NEW SUBTASKS**:
- **T020a**: Implement two-phase parser orchestration (lightweight index → detailed extraction)
- **T020b**: Create schema_validator.py and add validation checkpoints
- **T020c**: Implement scout pre-processing phase for codebase discovery
- **T020d**: Implement post-processing lint phase with Make target validation
- **T020e**: Add checkpointing system (.claude/.checkpoints/ directory)

**T022: Implement cross-reference generation**
**REVISIONS NEEDED**:
- Already covers R-F1.3 (enhanced cross-reference strategy) - no changes needed
- Add staleness detection fields to rfc-map.json (R-P1.4)

**T023: Add section generation logic**
**REVISIONS NEEDED**:
- Emphasize abstraction over transcription (R-F1.1)
- Add mandatory review markers for security/design sections (R-F1.2)
- Add optional sections: use_cases, change_log, implementation_status, design_rationale (R-F1.4)

**NEW SUBTASKS**:
- **T023a**: Implement abstraction guidelines in section generation
- **T023b**: Auto-insert `[NEEDS MANUAL REVIEW]` markers
- **T023c**: Generate optional sections when content available

**T024: Implement kramdown-rfc frontmatter generation**
**REVISIONS NEEDED**:
- Add RFC 2119 keyword validation (R-F1.5)

---

## 8. Implementation Phasing

### Phase 1: Critical for MVP (User Story 1 Completion)

**Must Implement Before US1 Completion**:
1. **R-P1.1**: Two-phase extraction (parser.md + T020a)
2. **R-P1.2**: LSP visibility metadata (parser.md update)
3. **R-A1.1**: Project-level context (analyzer.md update)
4. **R-A1.2**: Multi-pronged standard detection (analyzer.md + T023 revision)
5. **R-F1.1**: Abstraction over transcription (formatter.md + T023a)
6. **R-F1.2**: Mandatory review markers (formatter.md + T023b)
7. **R-C1.1**: Checkpointing (T020e)
8. **R-C1.2**: Schema validation (T020b)
9. **R-C1.3**: Scout pre-processing (T020c)
10. **R-C1.4**: Lint post-processing (T020d)

**Estimated Effort**: +10 subtasks, ~15-20 hours additional work

### Phase 2: Enhanced Reliability (Post-MVP)

**Can Be Implemented After US1 Works**:
1. **R-P1.3**: Enhanced output schema (data-model.md update + parser changes)
2. **R-P1.4**: Staleness detection (data-model.md + rfc_mapper.py update)
3. **R-A1.3**: Semantic pattern catalog (lib/pattern_catalog.py)
4. **R-A1.4**: Enhanced analyzer output (analyzer.md JSON schema)
5. **R-F1.4**: Additional RFC sections (data-model.md + T023c)
6. **R-F1.5**: RFC 2119 validation (formatter.md or validator agent)
7. **R-C1.5**: Progress indicators (T020 + T058)
8. **R-C1.6**: Diff generation (lib/diff_generator.py + T036)
9. **R-C1.7**: Idempotent agents (agent docs + validation)

**Estimated Effort**: +8 subtasks, ~10-15 hours additional work

### Phase 3: Performance & Scale (User Story 4)

**Can Be Implemented When Scaling**:
1. **R-P1.5**: Serena persistent memory (parser.md + T056)

**Estimated Effort**: Already planned in T056

---

## 9. Constitution Compliance Check

### Principle I (Makefile-First Build System)
- ✅ R-C1.4 (Post-processing lint) uses Make targets (`make lint`, `make txt`)
- ✅ No direct kramdown-rfc/xml2rfc calls

### Principle III (Test-Driven Development)
- ✅ All recommendations integrate into existing test framework (T013-T015)
- ⚠️ New subtasks need corresponding test scenarios added

### Principle VI (Performance & Resource Efficiency)
- ✅ R-P1.1 (Two-phase extraction) reduces token consumption
- ✅ R-P1.5 (Serena caching) improves incremental updates
- ✅ R-C1.1 (Checkpointing) enables recovery without re-running

### Principle XIII (Code-to-Spec Traceability)
- ✅ R-F1.3 (Enhanced cross-references) strengthens traceability
- ✅ R-P1.4 (Staleness detection) ensures mappings stay fresh

### Principle XIV (Context Hygiene)
- ✅ R-P1.2 (LSP visibility) leverages Serena, not custom parsing
- ✅ R-A1.1 (Project-level context) uses Serena's semantic understanding

---

## 10. Risk Assessment

### Low Risk (Safe to Apply)
- R-P1.1, R-P1.2: Agent instruction updates (no code changes)
- R-A1.1, R-A1.2: Agent instruction updates (no code changes)
- R-F1.1, R-F1.2: Agent instruction updates (no code changes)
- R-C1.3, R-C1.4: New phases in workflow (additive changes)

### Medium Risk (Requires Testing)
- R-C1.1 (Checkpointing): New file I/O, error handling complexity
- R-C1.2 (Schema validation): New library, schema maintenance burden
- R-P1.3 (Enhanced output): Data model changes, backward compatibility

### High Risk (Deferred to Phase 2)
- R-A1.3 (Pattern catalog): Complex cross-language pattern matching
- R-C1.7 (Idempotent agents): Requires agent refactoring

---

## 11. User Decision Points

### Question 1: Implementation Scope
**Should we implement all Phase 1 recommendations now, or select a subset?**

Options:
- **Option A**: All Phase 1 (10 recommendations) - most comprehensive, ~20 hours
- **Option B**: Core subset (R-P1.1, R-A1.2, R-F1.1, R-C1.1, R-C1.3) - essential only, ~10 hours
- **Option C**: Agent instructions only (R-P1.1, R-P1.2, R-A1.1, R-A1.2, R-F1.1, R-F1.2) - no new code, ~5 hours

**Recommendation**: Option A (all Phase 1) - provides solid MVP foundation

### Question 2: Data Model Updates
**Should we update data-model.md now or defer to Phase 2?**

Options:
- **Update Now**: Ensures spec is complete, adds ~1 hour
- **Defer**: Focus on implementation first, update spec during Phase 2

**Recommendation**: Update Now - keeps spec accurate

### Question 3: Task File Updates
**Should we revise tasks.md (T020-T027) with subtasks now?**

Options:
- **Revise Now**: Clear implementation roadmap, adds ~30 minutes
- **Defer**: Start implementing, update tasks as we go

**Recommendation**: Revise Now - prevents scope creep

### Question 4: Phase 2 Timing
**When should we implement Phase 2 recommendations?**

Options:
- **After US1 Complete**: Test MVP first, then enhance
- **During US2 (Update)**: Integrate while building update capability
- **Separate Phase 2.5**: Dedicated enhancement phase after US1

**Recommendation**: After US1 Complete - validate MVP before enhancing

---

## 12. Next Steps

**If User Approves Phase 1 Recommendations**:

1. **Update Spec Documents** (~1 hour):
   - Update data-model.md: Code Element, Cross-Reference, Documentation Section entities
   - Update research.md: Add Perplexity consultation to technical decisions
   - Update tasks.md: Add subtasks T020a-T020e, T023a-T023c

2. **Update Agent Instructions** (~2 hours):
   - Revise parser.md: Two-phase extraction, LSP visibility
   - Revise analyzer.md: Project-level context, multi-pronged detection
   - Revise formatter.md: Abstraction guidelines, review markers, cross-references

3. **Update Command Instructions** (~1 hour):
   - Revise rfc-generate.md: Scout phase, checkpointing, lint phase

4. **Implement New Libraries** (~4 hours):
   - Create schema_validator.py: JSON Schema validation
   - Update rfc_mapper.py: Staleness detection fields
   - Add checkpointing system: .claude/.checkpoints/ directory

5. **Update Tests** (~2 hours):
   - Add test scenarios for checkpointing
   - Add test scenarios for schema validation
   - Add test scenarios for scout/lint phases

6. **Integrate in Coordinator** (~8-10 hours):
   - Implement T020a-T020e (revised coordinator integration)
   - Implement T023a-T023c (enhanced section generation)
   - Test end-to-end workflow

**Total Estimated Effort for Phase 1**: ~18-20 hours

---

## Appendix A: Recommendation Quick Reference

| ID | Component | Priority | Title | Estimated Hours |
|----|-----------|----------|-------|-----------------|
| R-P1.1 | Parser | P1 | Two-phase extraction | 2h |
| R-P1.2 | Parser | P1 | LSP visibility metadata | 0.5h |
| R-P1.3 | Parser | P2 | Enhanced output schema | 3h |
| R-P1.4 | Parser | P2 | Staleness detection | 2h |
| R-P1.5 | Parser | P3 | Serena persistent memory | 1h |
| R-A1.1 | Analyzer | P1 | Project-level context | 0.5h |
| R-A1.2 | Analyzer | P1 | Multi-pronged standard detection | 2h |
| R-A1.3 | Analyzer | P2 | Semantic pattern catalog | 4h |
| R-A1.4 | Analyzer | P2 | Enhanced output fields | 2h |
| R-F1.1 | Formatter | P1 | Abstraction over transcription | 1h |
| R-F1.2 | Formatter | P1 | Mandatory review markers | 1h |
| R-F1.3 | Formatter | P1 | Enhanced cross-references | 0h (covered) |
| R-F1.4 | Formatter | P2 | Additional RFC sections | 3h |
| R-F1.5 | Formatter | P2 | RFC 2119 validation | 2h |
| R-C1.1 | Command | P1 | Checkpointing | 3h |
| R-C1.2 | Command | P1 | Schema validation | 2h |
| R-C1.3 | Command | P1 | Scout pre-processing | 2h |
| R-C1.4 | Command | P1 | Lint post-processing | 2h |
| R-C1.5 | Command | P2 | Progress indicators | 1h |
| R-C1.6 | Command | P2 | Diff generation | 2h |
| R-C1.7 | Command | P2 | Idempotent agents | 2h |

**Phase 1 Total**: ~13.5 hours (recommendations only)
**Phase 1 with Integration**: ~20 hours (implementation)
**Phase 2 Total**: ~19 hours (all P2 recommendations)
**Phase 3 Total**: ~1 hour (P3 recommendations)

---

## Appendix B: JSON Schema Examples

### Parser Output Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["summary", "files", "symbols"],
  "properties": {
    "summary": {
      "type": "object",
      "required": ["files_analyzed", "public_apis", "types"],
      "properties": {
        "files_analyzed": {"type": "integer"},
        "public_apis": {"type": "integer"},
        "types": {"type": "integer"}
      }
    },
    "files": {"type": "array", "items": {"type": "string"}},
    "symbols": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "type", "file", "line_start", "visibility"],
        "properties": {
          "name": {"type": "string"},
          "type": {"enum": ["class", "function", "module", "interface", "constant"]},
          "file": {"type": "string"},
          "line_start": {"type": "integer", "minimum": 1},
          "line_end": {"type": "integer", "minimum": 1},
          "visibility": {"enum": ["public", "private", "protected"]},
          "dependencies": {"type": "array", "items": {"type": "string"}},
          "provenance": {"enum": ["defined_here", "re_exported", "inherited"]}
        }
      }
    }
  }
}
```

---

**END OF DOCUMENT**
