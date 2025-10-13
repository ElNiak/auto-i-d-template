# Tasks: RFC-Style Documentation Generator for Claude-Code

**Input**: Design documents from `/specs/002-build-a-claude/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: Tests are included per BDD framework specified in plan.md (Behave integration tests)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions
- **Claude-Code plugin**: `.claude/` for plugin files
- **Tests**: `tests/` at repository root (outside .claude/)
- **Documentation**: `docs/` at repository root

---

## Phase 0: RFC Examples Collection (Reference Material)

**Purpose**: Collect and organize example RFCs (both IETF and company-defined) across different application profiles to serve as reference material for documentation generation

**Why**: Having curated RFC examples helps the formatter agent understand proper RFC structure, terminology, and formatting conventions for different types of technical documentation.

### Application Profiles

- [X] T000a Create RFC examples directory structure: `.claude/rfc-examples/<profile>/`
- [X] T000b [P] Research and collect REST API RFCs in `.claude/rfc-examples/rest-apis/`
  - **IETF**: RFC 9110 (HTTP Semantics), RFC 9112 (HTTP/1.1), RFC 6570 (URI Templates), RFC 7807 (Problem Details)
  - **Company**: Google API Design Guide, AWS API Gateway patterns, Stripe API documentation patterns
- [X] T000c [P] Research and collect Network Protocol RFCs in `.claude/rfc-examples/network-protocols/`
  - **IETF**: RFC 793 (TCP), RFC 8446 (TLS 1.3), RFC 9000 (QUIC), RFC 791 (IP)
  - **Company**: Google QUIC implementation docs, Cloudflare protocol documentation
- [X] T000d [P] Research and collect Security Protocol RFCs in `.claude/rfc-examples/security-protocols/`
  - **IETF**: RFC 5246 (TLS 1.2), RFC 6749 (OAuth 2.0), RFC 7519 (JWT), RFC 8017 (PKCS #1)
  - **Company**: Auth0 security patterns, Okta protocol documentation, Microsoft identity platform specs
- [X] T000e [P] Research and collect Data Format RFCs in `.claude/rfc-examples/data-formats/`
  - **IETF**: RFC 8259 (JSON), RFC 7049 (CBOR), RFC 4506 (XDR), RFC 7464 (JSON Text Sequences)
  - **Company**: Protocol Buffers (Google), Apache Avro, MessagePack specifications
- [X] T000f [P] Research and collect Authentication RFCs in `.claude/rfc-examples/authentication/`
  - **IETF**: RFC 7617 (HTTP Basic), RFC 6750 (OAuth Bearer), RFC 8471 (Token Binding), RFC 4559 (SPNEGO)
  - **Company**: GitHub OAuth implementation, AWS Signature Version 4, Azure AD authentication patterns
- [X] T000g [P] Research and collect Distributed Systems RFCs in `.claude/rfc-examples/distributed-systems/`
  - **IETF**: RFC 7540 (HTTP/2), RFC 7049 (CBOR-RPC), RFC 6455 (WebSocket)
  - **Company**: gRPC protocol (Google), Apache Kafka wire protocol, NATS messaging protocol
- [X] T000h [P] Research and collect Database RFCs in `.claude/rfc-examples/databases/`
  - **IETF**: RFC 2616 (HTTP for RESTful DB access patterns)
  - **Company**: PostgreSQL wire protocol, MySQL protocol documentation, Redis protocol (RESP)
- [X] T000i [P] Research and collect Cloud-Native RFCs in `.claude/rfc-examples/cloud-native/`
  - **Company**: Kubernetes API conventions, Docker Registry HTTP API, OpenTelemetry protocol specs
- [X] T000j Create RFC examples index in `.claude/rfc-examples/index.json` with mappings:
  ```json
  {
    "profiles": {
      "<profile-name>": {
        "ietf": ["RFC####", ...],
        "company": [
          {"org": "Google", "title": "...", "url": "..."},
          ...
        ]
      }
    }
  }
  ```

**Checkpoint**: Reference material collected - formatter agent can reference these examples for structure and style

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create plugin directory structure: `.claude/commands/`, `.claude/agents/`, `.claude/hooks/`, `.claude/lib/`, `.claude/templates/`
- [X] T002 [P] Create plugin manifest in `.claude/plugin.json` with metadata (name, version, description)
- [X] T003 [P] Create marketplace distribution config in `.claude/marketplace.json`
- [X] T004 [P] Create test directory structure: `tests/features/`, `tests/steps/`, `tests/fixtures/`
- [X] T005 [P] Initialize Python environment with `requirements.txt` for hooks (Python 3.11+)
- [X] T006 [P] Create RFC skeleton template in `.claude/templates/rfc-skeleton.md` following kramdown-rfc format
- [X] T007 [P] Create section templates: `.claude/templates/sections/terminology.md`, `.claude/templates/sections/interfaces.md`, `.claude/templates/sections/behavior.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T008 Implement rfc_mapper.py library in `.claude/lib/rfc_mapper.py` for managing rfc-map.json traceability (code ↔ RFC section mappings)
- [X] T009 [P] Implement preserve_edits.py library in `.claude/lib/preserve_edits.py` for handling @preserve-start/end markers
- [X] T010 [P] Implement impact_analyzer.py library in `.claude/lib/impact_analyzer.py` for analyzing code changes and RFC impact
- [X] T011 Create coordinator workflow instructions in `.claude/instructions/coordinator.md` with workflow orchestration logic
- [X] T012 Setup Behave environment configuration in `tests/environment.py` with setup/teardown for test repos

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Initial RFC Documentation (Priority: P1) 🎯 MVP

**Goal**: Enable developers to generate RFC Documents from source code using Claude-Code slash commands

**Independent Test**: Can be fully tested by selecting a project directory and generating an RFC Document that includes at least terminology, interfaces, and behavior sections

### Tests for User Story 1 ⚠️

**NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T013 [P] [US1] Create Behave feature file in `tests/features/generate.feature` with scenarios: (1) generate from clean repo, (2) select specific paths, (3) verify cross-references
- [ ] T014 [P] [US1] Implement test steps in `tests/steps/generate_steps.py` for RFC generation scenarios
- [ ] T015 [P] [US1] Create test fixture codebase in `tests/fixtures/sample-project/` with known structure

### Implementation for User Story 1

- [ ] T016 [US1] Create `/rfc-generate` slash command in `.claude/commands/rfc-generate.md` with arguments: paths, output file, sections filter
- [ ] T017 [P] [US1] Implement parser agent in `.claude/agents/parser.md` using Serena MCP tools (get_symbols_overview, find_symbol, search_for_pattern)
- [ ] T018 [P] [US1] Implement analyzer agent in `.claude/agents/analyzer.md` for semantic analysis via Serena MCP (find_referencing_symbols)
- [ ] T019 [P] [US1] Implement formatter agent in `.claude/agents/formatter.md` for generating RFC sections in kramdown-rfc format
- [ ] T020 [US1] Integrate agents in coordinator: spawn parser → analyzer → formatter, aggregate results
- [ ] T021 [US1] Add path selection logic in coordinator to filter selected directories/files
- [ ] T022 [US1] Implement cross-reference generation in formatter using rfc_mapper.py
- [ ] T023 [US1] Add section generation logic: terminology from type definitions, interfaces from public APIs, behavior from implementation
- [ ] T024 [US1] Implement kramdown-rfc frontmatter generation (docname, title, authors, category)
- [ ] T025 [US1] Create rfc-map.json output with bidirectional code ↔ section mappings
- [ ] T026 [US1] Add error handling for: empty paths, no analyzable code, Serena MCP unavailable
- [ ] T027 [US1] Add logging throughout generation workflow for debugging

**Checkpoint**: At this point, User Story 1 should be fully functional - can generate initial RFC from codebase

---

## Phase 4: User Story 2 - Update Existing RFC Documentation (Priority: P2)

**Goal**: Enable maintainers to update existing RFC Documents after code changes without duplicating unchanged content

**Independent Test**: Can be tested by modifying code in a documented project and running the update command to verify only changed sections are updated

### Tests for User Story 2 ⚠️

- [ ] T028 [P] [US2] Create Behave feature file in `tests/features/update.feature` with scenarios: (1) update after code changes, (2) preserve manual edits, (3) generate change summary
- [ ] T029 [P] [US2] Implement test steps in `tests/steps/update_steps.py` for RFC update scenarios

### Implementation for User Story 2

- [ ] T030 [US2] Create `/rfc-update` slash command in `.claude/commands/rfc-update.md` with argument: path to existing RFC document
- [ ] T031 [US2] Implement change detection in impact_analyzer.py using git diff commands via Bash tool
- [ ] T032 [US2] Add logic to load existing rfc-map.json and compare with current code state
- [ ] T033 [US2] Implement preserve block parsing in preserve_edits.py to extract @preserve-start/end sections
- [ ] T034 [US2] Extend formatter agent to merge new content with preserved blocks
- [ ] T035 [US2] Implement incremental update in coordinator: detect changes → re-analyze affected sections → update only changed sections
- [ ] T036 [US2] Add change summary generation showing: modified sections, preserved blocks, updated cross-references
- [ ] T037 [US2] Implement deduplication logic to prevent regenerating unchanged sections
- [ ] T038 [US2] Update rfc-map.json with new mappings while preserving unchanged ones
- [ ] T039 [US2] Add validation that manual edits are preserved correctly
- [ ] T040 [US2] Add error handling for: missing rfc-map.json, conflicting edits, invalid preserve markers
- [ ] T041b [US2] Implement conflict detection and resolution in preserve_edits.py:
  * Detect overlapping @preserve blocks → ERROR (abort update)
  * Detect preserved content overlapping with generated sections → WARNING
  * Apply preservation-priority rule: @preserve blocks always take precedence
  * Adjust adjacent sections to avoid overlap (padding with blank lines)
  * Log all conflicts to conflicts.log with section references
  * Generate conflict report for user review before git commit
  * Add test scenario: overlapping preserve blocks, preserved content conflicting with new generation

**Checkpoint**: At this point, User Stories 1 AND 2 should both work - can generate and update RFC docs

---

## Phase 5: User Story 3 - Automated Documentation Checks (Priority: P3)

**Goal**: Enable team leads to configure automated documentation quality checks during code reviews

**Independent Test**: Can be tested by configuring automation hooks and verifying they trigger during code review workflows

### Tests for User Story 3 ⚠️

- [ ] T041 [P] [US3] Create Behave feature file in `tests/features/automation.feature` with scenarios: (1) pre-commit validation, (2) API change detection, (3) reviewer guidance
- [ ] T042 [P] [US3] Implement test steps in `tests/steps/automation_steps.py` for hook scenarios

### Implementation for User Story 3

- [ ] T043 [P] [US3] Implement PreToolUse hook in `.claude/hooks/pre_tool_validate.py` with tool matcher `Write|Edit`:
  - Extract file path from tool arguments (parse JSON input)
  - Check if file is tracked in rfc-map.json (any mappings reference this file)
  - Import and call `lib.impact_analyzer` to detect affected RFC sections (git diff + line tracking)
  - Display warning with affected sections if high-confidence matches found
  - Return JSON: `{"block": false, "message": "⚠️ Affects RFC §3.2...", "suggestion": "Run /rfc-analyze-impact"}`
  - Use Python logging for debugging
- [ ] T044 [P] [US3] Implement PreToolUse hook in `.claude/hooks/pre_bash_enforce.py` with tool matcher `Bash`:
  - Parse Bash command from tool arguments
  - Detect direct kramdown-rfc, xml2rfc, or mmark invocations using regex
  - Block execution if not invoked via Make targets
  - Return JSON: `{"block": true, "message": "Use 'make txt' instead of 'xml2rfc'", "suggestion": "..."}`
  - Allow-list: `make`, `git`, standard unix tools (configurable)
- [ ] T045 [P] [US3] Implement PostToolUse hook in `.claude/hooks/post_tool_sync.py` with tool matcher `Write|Edit|Bash`:
  - Parse tool result to detect modified files
  - Import and call `lib.rfc_mapper.update_timestamps()` for affected code elements
  - Flag stale cross-references (code changed but RFC not updated)
  - Append changes to `.claude/.hook-history.json` for audit trail
  - Return JSON: `{"block": false, "message": "Updated rfc-map.json for 3 files"}`
- [ ] T046 [US3] Implement UserPromptSubmit hook in `.claude/hooks/user_intent_detect.py`:
  - Pattern match user prompt for RFC-related keywords: `/rfc-`, "RFC", "documentation", "spec"
  - Load relevant memory files from `.claude/memory/` (codebase-overview.md, rfc-architecture.md)
  - Return JSON with injected context (Claude Code will prepend to conversation)
  - Log intent detection to `.claude/.hook-history.json` for telemetry
- [ ] T047 [US3] Implement SessionStart hook in `.claude/hooks/session_start_check.py`:
  - Check last modification time of rfc-map.json using `os.path.getmtime()`
  - If > 30 days old (configurable threshold), display staleness warning
  - Suggest running `/rfc-update` to refresh documentation
  - Use `subprocess.run(["git", "status", "--porcelain"])` to check for uncommitted changes in docs/generated/
  - Return JSON: `{"block": false, "message": "RFC docs last updated 45 days ago..."}`
- [ ] T048 [P] [US3] Add hook configuration in `.claude/plugin.json` with Claude Code native format:
  ```json
  {
    "hooks": {
      "preToolUse": [
        {
          "script": ".claude/hooks/pre_tool_validate.py",
          "toolPattern": "Write|Edit",
          "enabled": true,
          "blocking": false,
          "description": "Validate RFC cross-references before file modifications"
        },
        {
          "script": ".claude/hooks/pre_bash_enforce.py",
          "toolPattern": "Bash",
          "enabled": true,
          "blocking": true,
          "description": "Enforce Make target usage for RFC build commands"
        }
      ],
      "postToolUse": [
        {
          "script": ".claude/hooks/post_tool_sync.py",
          "toolPattern": "Write|Edit|Bash",
          "enabled": true,
          "blocking": false,
          "description": "Synchronize rfc-map.json after code changes"
        }
      ],
      "userPromptSubmit": [
        {
          "script": ".claude/hooks/user_intent_detect.py",
          "enabled": true,
          "blocking": false,
          "description": "Detect RFC-related intent and load context"
        }
      ],
      "sessionStart": [
        {
          "script": ".claude/hooks/session_start_check.py",
          "enabled": true,
          "blocking": false,
          "description": "Check for stale RFC documentation"
        }
      ]
    },
    "mandatory_sections": ["abstract", "introduction", "terminology", "interfaces", "behavior"],
    "validation_strictness": "standard",
    "staleness_threshold_days": 30
  }
  ```
  All hooks enabled by default per FR-011. Users can disable individual hooks or adjust blocking behavior.
- [ ] T049 [US3] Implement lightweight impact analysis in `lib/impact_analyzer.py` (language-agnostic):
  - Use `git diff --unified=0` to detect changed line ranges in modified files
  - Cross-reference changed lines with rfc-map.json line number mappings
  - Flag any changes in RFC-tracked code regions (code.line within changed range)
  - Return list of affected RFC sections with confidence scores
  - Estimate severity based on section type (interfaces=BREAKING, behavior=COMPATIBLE, etc.)
  - Language-agnostic: works with Python, JS, Go, Rust, C++, any language
  - Must complete in <100ms for hook responsiveness
- [ ] T049b [US3] Create `/rfc-analyze-impact` slash command in `.claude/commands/rfc-analyze-impact.md`:
  - Spawn analyzer agent that uses Serena MCP tools for deep semantic analysis
  - Use `find_symbol` to extract detailed signatures with full context
  - Use `find_referencing_symbols` to understand call graphs and dependencies
  - Compare with rfc-map.json to identify affected RFC sections
  - Generate comprehensive impact report with: changed symbols, affected sections, breaking changes, migration guidance
  - Output markdown report to stdout for user review
- [ ] T050 [US3] Implement reviewer guidance generation in `lib/reviewer_guidance.py`:
  - Input: list of changed code elements from impact_analyzer
  - Query rfc-map.json for affected RFC sections
  - Generate markdown report: "## Documentation Impact", list of sections, review checklist
  - Identify missing mandatory sections if any
  - Output to stdout for hook consumption
- [ ] T051 [US3] Add hook utilities in `lib/hook_utils.py`:
  - `load_rfc_map()`: Parse rfc-map.json safely with error handling
  - `format_warning(message, suggestion)`: Return JSON with warning format
  - `format_error(message, suggestion)`: Return JSON with error format
  - `log_hook_event(event_type, details)`: Append to .claude/.hook-history.json
  - `check_enabled(hook_name)`: Read plugin.json to check if hook enabled
  - `get_config(key, default)`: Safe config retrieval with defaults
- [ ] T052 [US3] Integrate Make targets in hooks using Python subprocess:
  - PreToolUse hook calls `subprocess.run(["make", "-n", "lint"])` for dry-run validation
  - PostToolUse hook optionally calls `subprocess.run(["make", "idnits"])` if RFC files modified
  - Parse Make output to detect potential failures without side effects
  - Use timeout parameter to prevent hanging (e.g., timeout=5)
- [ ] T053 [US3] Add graceful degradation and error handling in Python hooks:
  - All hooks must use try-except blocks with proper logging
  - If rfc-map.json missing, hooks should warn but not block (return `{"block": false}`)
  - If git commands fail, fall back to basic file checking
  - Log all hook failures to `.claude/.hook-errors.log` with traceback
  - Set up Python logging with rotating file handler for debugging

**Checkpoint**: All Claude Code native hooks should now trigger at appropriate times and provide automated guidance. Impact analysis is language-agnostic (git diff + line tracking). For deep semantic analysis, users run `/rfc-analyze-impact` which spawns agents with Serena MCP access.

---

## Phase 6: User Story 4 - Scale to Large Codebases (Priority: P2)

**Goal**: Enable architects to generate RFC documentation for large enterprise codebases (>100K lines) while maintaining performance

**Independent Test**: Can be tested by running generation on progressively larger codebases and measuring completion time and memory usage

### Tests for User Story 4 ⚠️

- [ ] T052 [P] [US4] Create Behave feature file in `tests/features/performance.feature` with scenarios: (1) 100K+ LOC codebase, (2) cross-module references, (3) chunk processing
- [ ] T053 [P] [US4] Create large test fixture in `tests/fixtures/large-project/` with >10K LOC
- [ ] T054 [P] [US4] Implement test steps in `tests/steps/performance_steps.py` with timing assertions

### Implementation for User Story 4

- [ ] T055 [US4] Implement chunk processing algorithm in coordinator: split codebase into 10K line chunks with 500 line overlap
- [ ] T056 [US4] Add caching mechanism in parser agent to store results by file hash (avoid re-parsing unchanged files)
- [ ] T057 [US4] Implement incremental processing: process chunks sequentially, aggregate results, maintain context
- [ ] T058 [US4] Add progress reporting in coordinator: show chunk X/Y completed, estimated time remaining
- [ ] T059 [US4] Optimize Serena MCP usage: scope queries to specific paths, use relative_path parameter consistently
- [ ] T060 [US4] Implement cross-module reference tracking in analyzer agent to maintain accuracy across chunks
- [ ] T061 [US4] Add memory monitoring and limits: abort if exceeding thresholds
- [ ] T062 [US4] Implement result aggregation: merge chunk results into coherent RFC sections
- [ ] T063 [US4] Add performance logging: track time per chunk, total time, memory usage

**Checkpoint**: Large codebases should now complete within performance targets (100K lines < 20min)

---

## Phase 7: User Story 5 - Reference External Standards (Priority: P3)

**Goal**: Enable compliance officers to have RFC documentation explicitly reference and link to relevant external standards

**Independent Test**: Can be tested by verifying that generated documentation includes properly formatted references to detected standards

### Tests for User Story 5 ⚠️

- [ ] T064 [P] [US5] Create Behave feature file in `tests/features/standards.feature` with scenarios: (1) detect IETF RFCs, (2) generate bibliography, (3) hierarchical detection pipeline
- [ ] T065 [P] [US5] Create test fixture with code implementing standard protocols in `tests/fixtures/standards-project/`
- [ ] T066 [P] [US5] Implement test steps in `tests/steps/standards_steps.py` for standard detection

### Implementation for User Story 5

- [ ] T067 [US5] Implement standard detection in analyzer agent using hierarchical pipeline: (1) config/dependencies, (2) comments, (3) protocol signatures
- [ ] T068 [US5] Add config/dependency analysis: parse package.json, requirements.txt, go.mod for standard library references
- [ ] T069 [US5] Add comment pattern matching: search for "RFC XXXX", "implements RFC", "see RFC" patterns using search_for_pattern
- [ ] T070 [US5] Add protocol signature detection: identify standard protocol implementations (HTTP/2, TLS, OAuth patterns)
- [ ] T071 [US5] Implement standard reference formatting in formatter agent: inline citations and bibliography section
- [ ] T072 [US5] Create standard reference templates with proper IETF citation format
- [ ] T073 [US5] Add confidence scoring for detected standards (config=1.0, comment=0.8, signature=0.6)
- [ ] T074 [US5] Implement reference deduplication: merge multiple detections of same standard
- [ ] T075 [US5] Add references section generation with normative/informative categorization

**Checkpoint**: Generated RFCs should now include properly formatted external standard references

---

## Phase 8: Validation & Quality Gates (Cross-Cutting)

**Goal**: Ensure generated RFC documents meet IETF compliance standards

**Purpose**: Quality assurance that affects all user stories

- [ ] T076 [P] [US-ALL] Implement validator agent in `.claude/agents/validator.md` for IETF compliance checking
- [ ] T077 [P] [US-ALL] Create `/rfc-validate` slash command in `.claude/commands/rfc-validate.md` to run validation pipeline
- [ ] T078 [US-ALL] Add kramdown-rfc syntax validation in validator using Make targets (make lint)
- [ ] T079 [US-ALL] Add xml2rfc schema validation via Make targets (make txt)
- [ ] T080 [US-ALL] Add idnits compliance check via Make targets (make idnits)
- [ ] T081 [US-ALL] Add custom validation: cross-reference accuracy, section completeness, preserve block integrity
- [ ] T082 [US-ALL] Implement validation report generation with errors, warnings, and suggestions
- [ ] T083 [US-ALL] Add quick-fix suggestions for common validation errors
- [ ] T084 [US-ALL] Integrate validator into coordinator workflow: validate before writing output

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T085 [P] Add comprehensive documentation in `docs/plugin-guide.md` covering installation, usage, troubleshooting
- [ ] T086 [P] Update quickstart.md with real examples from test fixtures
- [ ] T087 [P] Create agent debugging guide in `docs/agent-debugging.md`
- [ ] T088 Code cleanup: add docstrings to all Python modules, ensure PEP 8 compliance
- [ ] T089 Refactor coordinator agent for improved readability and maintainability
- [ ] T090 [P] Add unit tests for Python libraries in `tests/unit/test_rfc_mapper.py`, `tests/unit/test_preserve_edits.py`, `tests/unit/test_impact_analyzer.py`
- [ ] T091 Performance optimization: profile and optimize hot paths in chunk processing
- [ ] T092 Security review: ensure no code execution, validate input paths, check for path traversal
- [ ] T093 Add error recovery: graceful handling of agent failures, partial result recovery
- [ ] T094 Run full quickstart.md validation with real repository
- [ ] T095 Create demo video showing end-to-end workflow
- [ ] T096 Prepare marketplace submission: validate plugin.json, marketplace.json, add screenshots

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - US1 can proceed after Phase 2
  - US2 depends on US1 (requires existing RFC docs to update)
  - US3 can proceed in parallel with US4, US5
  - US4 can proceed in parallel with US3, US5
  - US5 can proceed in parallel with US3, US4
- **Validation (Phase 8)**: Can integrate with any user story after Phase 2
- **Polish (Phase 9)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - Core generation capability
- **User Story 2 (P2)**: Depends on US1 (needs generation working first) - Update capability
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Independent automation
- **User Story 4 (P2)**: Can start after US1 (enhances generation) - Performance optimization
- **User Story 5 (P3)**: Can start after US1 (enhances generation) - Standard references

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Parser agent before analyzer agent (data flow dependency)
- Analyzer before formatter (semantic understanding before formatting)
- Formatter before validator (generate before validate)
- Core implementation before integration with coordinator
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (T002, T003, T004, T005, T006, T007)
- All Foundational tasks marked [P] can run in parallel (T009, T010)
- Once Foundational completes:
  - US3, US4, US5 can all start in parallel (after US1 complete)
  - Within each story, tasks marked [P] can run in parallel
- All test files marked [P] can be created in parallel
- All agent instruction files marked [P] can be created in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all test files together:
Task: "Create Behave feature file in tests/features/generate.feature"
Task: "Implement test steps in tests/steps/generate_steps.py"
Task: "Create test fixture codebase in tests/fixtures/sample-project/"

# Launch all agent files together (after tests):
Task: "Implement parser agent in .claude/agents/parser.md"
Task: "Implement analyzer agent in .claude/agents/analyzer.md"
Task: "Implement formatter agent in .claude/agents/formatter.md"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently with real codebase
5. Demo RFC generation capability

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → **Demo: Generate RFC from code** (MVP!)
3. Add User Story 2 → Test independently → **Demo: Update RFC after changes**
4. Add User Story 4 → Test independently → **Demo: Handle large codebase**
5. Add User Story 3 → Test independently → **Demo: Automated PR checks**
6. Add User Story 5 → Test independently → **Demo: Standard compliance**
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers (after Foundational complete):

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (P1 - core generation)
   - After US1 complete:
     - Developer B: User Story 2 (P2 - updates, depends on US1)
     - Developer C: User Story 3 (P3 - automation)
     - Developer D: User Story 4 (P2 - performance)
     - Developer E: User Story 5 (P3 - standards)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- [US-ALL] indicates cross-cutting concerns affecting all stories
- Each user story should be independently completable and testable
- Verify tests fail before implementing (TDD approach)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- All code analysis MUST use Serena MCP tools (no custom parsing)
- All RFC build operations MUST use Make targets (no direct tool calls)
- Performance targets: 10K lines/2min, 100K lines/20min, 1M lines/60min

---

## Task Count Summary

- **Total Tasks**: 100
- **Phase 1 (Setup)**: 7 tasks
- **Phase 2 (Foundational)**: 5 tasks (BLOCKING)
- **Phase 3 (US1 - Generate)**: 15 tasks (MVP)
- **Phase 4 (US2 - Update)**: 14 tasks
- **Phase 5 (US3 - Automation)**: 14 tasks
- **Phase 6 (US4 - Scale)**: 9 tasks
- **Phase 7 (US5 - Standards)**: 9 tasks
- **Phase 8 (Validation)**: 9 tasks
- **Phase 9 (Polish)**: 12 tasks

**Parallel Opportunities Identified**: 30 tasks marked [P]

**Independent Test Criteria**:
- US1: Generate RFC with terminology, interfaces, behavior sections from test fixture
- US2: Modify test fixture code, update RFC, verify only changed sections updated
- US3: Configure Claude Code native Python hooks, trigger on Write/Edit/Bash, verify automated guidance with git diff + line tracking
- US4: Process 10K+ LOC fixture, complete within time budget, verify accuracy
- US5: Process fixture with standard references, verify bibliography generated

**Suggested MVP Scope**: Phase 1 + Phase 2 + Phase 3 (User Story 1) = 27 tasks

**Notes**:
- Task T041b added to address conflict resolution for @preserve blocks (HIGH severity issue G1 remediation)
- Task T049b added for deep semantic impact analysis via `/rfc-analyze-impact` slash command
- US3 revised to use Claude Code native hooks (PreToolUse, PostToolUse, UserPromptSubmit, SessionStart) with Python scripts
- Impact analysis is language-agnostic using git diff + line tracking (no AST parsing required)
