# BDD Test Improvement - Detailed Task Breakdown

> **IMPORTANT**: This document has been **SUPERSEDED** by [TEST-IMPLEMENTATION-STATUS.md](./TEST-IMPLEMENTATION-STATUS.md) as of 2025-10-15.
>
> The new status document reflects actual implementation progress and current state. Phase 1 is now 99% complete (only 3 stub implementations remaining as of original roadmap creation). Most implementation work occurred between 2025-01-15 (roadmap creation) and 2025-10-15 (status assessment).
>
> **For current status and next steps, see TEST-IMPLEMENTATION-STATUS.md**

---

> **Status**: Approved Plan (OUTDATED - see note above)
> **Total Estimated Effort**: 15-22 days
> **Created**: 2025-01-15
> **Priority**: CRITICAL - Current tests provide false confidence

---

## Table of Contents

- [Phase 1: Fix Critical Issues (Days 1-5)](#phase-1-fix-critical-issues-days-1-5)
- [Phase 2: Add Missing Test Coverage (Days 6-12)](#phase-2-add-missing-test-coverage-days-6-12)
- [Phase 3: Improve Code Quality (Days 13-15)](#phase-3-improve-code-quality-days-13-15)
- [Phase 4: Enhance Test Quality (Days 16-18)](#phase-4-enhance-test-quality-days-16-18)
- [Phase 5: Add Advanced Testing (Days 19-22)](#phase-5-add-advanced-testing-days-19-22)
- [Task Dependencies](#task-dependencies)
- [Success Metrics](#success-metrics)

---

## Phase 1: Fix Critical Issues (Days 1-5)

**Goal**: Replace stubs and simulations with real implementations
**Priority**: CRITICAL
**Estimated Effort**: 3-5 days

### 1.1: Implement Real Step Definitions for update_steps.py

**File**: `tests/steps/update_steps.py`
**Lines to fix**: 783-1065 (282 lines of stubs)
**Estimated**: 2 days

#### Tasks:

- [ ] **T1.1.1**: Implement verification steps (lines 786-797)
  - `step_rfc_not_modified()` - Check file mtime hasn't changed
  - `step_rfc_map_not_modified()` - Verify rfc-map.json integrity
  - **Acceptance**: Steps fail when files are modified, pass when unchanged
  - **Effort**: 2 hours

- [ ] **T1.1.2**: Implement timestamp verification steps (lines 862-873)
  - `step_timestamp_updated_to_current()` - Parse rfc-map.json, check timestamp is recent
  - `step_timestamp_unchanged()` - Verify specific timestamp preserved
  - **Acceptance**: Can detect timestamp changes to within 1 second accuracy
  - **Effort**: 2 hours

- [ ] **T1.1.3**: Implement section regeneration verification (lines 883-893)
  - `step_multiple_sections_regenerated()` - Parse RFC, verify sections updated
  - `step_other_sections_unchanged()` - Compare against baseline
  - **Acceptance**: Can diff RFC sections and detect changes
  - **Effort**: 3 hours

- [ ] **T1.1.4**: Implement preservation verification steps (lines 895-911)
  - `step_merge_applies_preservation_priority()` - Verify preserve blocks intact
  - `step_preserve_content_takes_precedence()` - Check conflict resolution
  - `step_generated_content_discarded()` - Verify line ranges preserved
  - **Acceptance**: Can parse `@preserve-start`/`@preserve-end` markers
  - **Effort**: 4 hours

- [ ] **T1.1.5**: Implement checkpoint verification steps (lines 913-937)
  - `step_parser_checkpoint_preserved()` - Check `.claude/.checkpoints/parser-*.json` exists
  - `step_analyzer_checkpoint_preserved()` - Check analyzer checkpoint
  - `step_can_retry_update()` - Verify checkpoint can be loaded
  - **Acceptance**: Can resume from checkpoints after failures
  - **Effort**: 4 hours

- [ ] **T1.1.6**: Implement kramdown validation steps (lines 939-949)
  - `step_updated_rfc_valid_kramdown()` - Run kramdown-rfc syntax check
  - `step_see_reminder()` - Parse command output for reminder text
  - **Acceptance**: Can invoke kramdown-rfc and parse errors
  - **Effort**: 2 hours

- [ ] **T1.1.7**: Implement impact analysis steps (lines 951-973)
  - `step_change_classified_as_severity()` - Parse impact report JSON
  - `step_impact_summary_shows()` - Verify summary format
  - `step_section_marked_for_review()` - Check review markers
  - `step_change_summary_explains()` - Validate explanation text
  - **Acceptance**: Can parse and validate impact_analyzer.py output
  - **Effort**: 3 hours

- [ ] **T1.1.8**: Implement cross-reference verification (lines 975-997)
  - `step_cross_reference_valid()` - Check anchor links
  - `step_no_broken_cross_references()` - Scan RFC for broken refs
  - **Acceptance**: Can validate kramdown-rfc cross-references
  - **Effort**: 3 hours

- [ ] **T1.1.9**: Implement CODE_REF marker verification (lines 999-1015)
  - `step_code_ref_updated()` - Parse `<!-- CODE_REF: ... -->` markers
  - `step_mapping_reflects_new_line()` - Verify rfc-map.json line numbers
  - `step_cross_reference_correct()` - Validate marker accuracy
  - **Acceptance**: Can track code line number changes
  - **Effort**: 3 hours

- [ ] **T1.1.10**: Implement frontmatter preservation (lines 1017-1023)
  - `step_updated_rfc_retains_field()` - Parse YAML frontmatter
  - **Acceptance**: Can extract and compare frontmatter fields
  - **Effort**: 2 hours

- [ ] **T1.1.11**: Implement formatter verification (lines 1044-1066)
  - `step_formatter_generates_sections()` - Verify section filter works
  - `step_formatter_no_frontmatter()` - Check frontmatter excluded
  - `step_formatter_no_unchanged_sections()` - Verify selective output
  - `step_coordinator_merges_partial()` - Validate merge logic
  - **Acceptance**: Can test partial RFC regeneration
  - **Effort**: 4 hours

**Subtotal for 1.1**: ~32 hours (4 days)

---

### 1.2: Implement Real Step Definitions for generate_steps.py

**File**: `tests/steps/generate_steps.py`
**Lines to fix**: 355-558 (203 lines of stubs)
**Estimated**: 1.5 days

#### Tasks:

- [ ] **T1.2.1**: Implement file existence verification (lines 350-356)
  - `step_file_should_be_created()` - Check file exists at path
  - **Acceptance**: Fails if file missing, passes if exists
  - **Effort**: 1 hour

- [ ] **T1.2.2**: Implement rfc-map.json validation (lines 358-363)
  - `step_rfc_map_contains_mappings()` - Parse JSON, validate schema
  - **Acceptance**: Can validate mapping structure per spec
  - **Effort**: 2 hours

- [ ] **T1.2.3**: Implement path filtering verification (lines 372-383)
  - `step_rfc_references_only_paths()` - Check rfc-map.json file references
  - `step_rfc_no_other_references()` - Verify exclusions
  - **Acceptance**: Can validate path filtering worked correctly
  - **Effort**: 2 hours

- [ ] **T1.2.4**: Implement symbol mapping verification (lines 397-413)
  - `step_rfc_map_contains_symbol()` - Search mappings for symbol
  - `step_mapping_includes_file_path()` - Verify file path correct
  - `step_mapping_includes_line_numbers()` - Check line numbers present
  - **Acceptance**: Can query rfc-map.json by symbol name
  - **Effort**: 3 hours

- [ ] **T1.2.5**: Implement warning/error message verification (lines 415-445)
  - `step_see_warning()` - Parse command output for warnings
  - `step_no_rfc_created()` - Verify no output files
  - `step_command_exit_code()` - Check exit status
  - `step_see_error()` - Parse error messages
  - `step_see_suggestion()` - Verify suggestion text
  - **Acceptance**: Can capture and parse command output
  - **Effort**: 2 hours

- [ ] **T1.2.6**: Implement frontmatter validation (lines 447-463)
  - `step_valid_frontmatter()` - Parse YAML, validate schema
  - `step_frontmatter_includes_field()` - Check field exists
  - `step_docname_matches_pattern()` - Regex validation
  - **Acceptance**: Can validate kramdown-rfc frontmatter
  - **Effort**: 3 hours

- [ ] **T1.2.7**: Implement terminology section verification (lines 465-481)
  - `step_terminology_defines_term()` - Parse terminology section
  - `step_definition_lists_fields()` - Check field list format
  - `step_cross_reference_links_source()` - Validate CODE_REF markers
  - **Acceptance**: Can extract and validate terminology definitions
  - **Effort**: 3 hours

- [ ] **T1.2.8**: Implement interfaces section verification (lines 483-505)
  - `step_interfaces_documents_function()` - Find function in RFC
  - `step_documentation_includes_parameters()` - Check params documented
  - `step_documentation_includes_return_type()` - Check return type
  - `step_documentation_references_rfc2119()` - Detect MUST/SHOULD keywords
  - **Acceptance**: Can validate API documentation completeness
  - **Effort**: 4 hours

- [ ] **T1.2.9**: Implement behavior section verification (lines 507-523)
  - `step_behavior_describes_states()` - Parse state machine description
  - `step_behavior_references_implementation()` - Check CODE_REF markers
  - `step_cross_reference_specific_lines()` - Verify line numbers
  - **Acceptance**: Can validate behavior documentation
  - **Effort**: 3 hours

- [ ] **T1.2.10**: Implement references section verification (lines 525-541)
  - `step_references_includes_rfc()` - Find RFC citation
  - `step_reference_ietf_format()` - Validate citation format
  - `step_inline_citations_link_bibliography()` - Check cross-refs
  - **Acceptance**: Can validate IETF reference formatting
  - **Effort**: 3 hours

- [ ] **T1.2.11**: Implement lint validation (lines 543-558)
  - `step_linter_passes()` - Run `make lint`, parse output
  - `step_kramdown_syntax_valid()` - Check kramdown errors
  - `step_xml2rfc_processes()` - Run `make txt`, verify success
  - **Acceptance**: Can run Make targets and validate output
  - **Effort**: 2 hours

**Subtotal for 1.2**: ~28 hours (3.5 days)

---

### 1.3: Replace Simulated Command Execution with Real Execution

**File**: `tests/steps/update_steps.py:476-573`, `generate_steps.py:300-327`
**Estimated**: 0.5 days

#### Tasks:

- [ ] **T1.3.1**: Implement real /rfc-update command execution
  - **Current**: Lines 476-573 simulate command with hardcoded responses
  - **New**: Actually invoke slash command via subprocess or Claude Code API
  - **Acceptance**: Command runs in test environment, produces real outputs
  - **Effort**: 2 hours
  - **Dependencies**: Requires `.claude/commands/rfc-update.md` to be executable

- [ ] **T1.3.2**: Implement real /rfc-generate command execution
  - **Current**: Lines 306-320 in generate_steps.py simulate execution
  - **New**: Actually invoke slash command
  - **Acceptance**: Command generates actual RFC files
  - **Effort**: 2 hours

- [ ] **T1.3.3**: Create command execution helper
  - **Location**: New file `tests/support/command_runner.py`
  - **Function**: `run_slash_command(context, command, args) -> CommandResult`
  - **Acceptance**: Can invoke any slash command and capture output
  - **Effort**: 2 hours

- [ ] **T1.3.4**: Update all command invocation steps to use real execution
  - **Files**: `update_steps.py`, `generate_steps.py`
  - **Acceptance**: No more simulated responses
  - **Effort**: 2 hours

**Subtotal for 1.3**: ~8 hours (1 day)

---

### 1.4: Implement Real Hook Testing

**File**: `tests/steps/automation_steps.py`
**Estimated**: 1 day

#### Tasks:

- [ ] **T1.4.1**: Create real hook execution helper
  - **Location**: New file `tests/support/hook_runner.py`
  - **Function**: `run_hook(hook_script, hook_type, input_data) -> HookResult`
  - **Features**:
    - Execute Python script as subprocess
    - Pass input via environment variables AND stdin JSON
    - Capture stdout, stderr, exit code
    - Parse JSON response
    - Measure execution time
  - **Acceptance**: Can run any hook script and get real results
  - **Effort**: 4 hours

- [ ] **T1.4.2**: Replace simulate_pretool_hook() with real execution
  - **Current**: Lines 59-97 mock PreToolUse behavior
  - **New**: Execute `.claude/hooks/pre_tool_validate.py` (if exists)
  - **Acceptance**: Tests run actual hook scripts
  - **Effort**: 2 hours

- [ ] **T1.4.3**: Replace simulate_posttool_hook() with real execution
  - **Current**: Lines 99-165 mock PostToolUse behavior
  - **New**: Execute `.claude/hooks/post_tool_sync.py`
  - **Acceptance**: Hook actually modifies rfc-map.json
  - **Effort**: 2 hours

- [ ] **T1.4.4**: Replace simulate_session_hook() with real execution
  - **Current**: Lines 167-201 mock SessionStart behavior
  - **New**: Execute `.claude/hooks/session_start_check.py`
  - **Acceptance**: Hook reads real file mtimes
  - **Effort**: 2 hours

- [ ] **T1.4.5**: Replace simulate_userprompt_hook() with real execution
  - **Current**: Lines 203-245 mock UserPromptSubmit behavior
  - **New**: Execute `.claude/hooks/user_intent_detect.py`
  - **Acceptance**: Hook detects RFC keywords in prompts
  - **Effort**: 2 hours

- [ ] **T1.4.6**: Update execute_hook() to use real subprocess execution
  - **Current**: Line 26-56 calls simulate_* functions
  - **New**: Call real hook scripts via hook_runner.py
  - **Acceptance**: All hook tests use real execution
  - **Effort**: 2 hours

- [ ] **T1.4.7**: Create actual hook scripts if missing
  - **Files**: Create `.claude/hooks/*.py` if they don't exist
  - **Scripts**: pre_tool_validate.py, post_tool_sync.py, session_start_check.py, user_intent_detect.py
  - **Acceptance**: Hook scripts follow research best practices
  - **Effort**: 4 hours

**Subtotal for 1.4**: ~18 hours (2.25 days)

---

### Phase 1 Total: ~86 hours (10.75 days actual, 3-5 days with parallelization)

**Critical Path**: 1.1 → 1.2 → 1.3 → 1.4 (sequential)
**Parallelization opportunity**: 1.1 and 1.2 can be done concurrently by different developers

---

## Phase 2: Add Missing Test Coverage (Days 6-12)

**Goal**: Test all Claude Code components (commands, hooks, agents)
**Priority**: HIGH
**Estimated Effort**: 5-7 days

### 2.1: Add Slash Command Testing

**New Files**: `tests/features/commands/slash_commands.feature`, `tests/steps/command_steps.py`
**Estimated**: 2 days

#### Tasks:

- [ ] **T2.1.1**: Create slash_commands.feature
  - **Content**: 15-20 scenarios covering:
    - Command file parsing
    - Frontmatter validation
    - Parameter expansion
    - Error handling
  - **Acceptance**: Feature file follows Gherkin best practices
  - **Effort**: 3 hours

- [ ] **T2.1.2**: Implement command file parsing tests
  - **Scenarios**:
    - Valid command with all frontmatter fields
    - Invalid YAML frontmatter
    - Missing required fields
    - Command with allowed-tools restrictions
  - **Acceptance**: Can parse `.md` files and extract frontmatter
  - **Effort**: 4 hours

- [ ] **T2.1.3**: Implement $ARGUMENTS expansion tests
  - **Scenarios**:
    - No arguments provided (empty string)
    - Single argument
    - Multiple arguments
    - Arguments with spaces
    - Arguments with special characters
  - **Acceptance**: Validates $ARGUMENTS → actual args substitution
  - **Effort**: 3 hours

- [ ] **T2.1.4**: Implement positional parameter tests
  - **Scenarios**:
    - $1, $2, $3 expansion
    - More placeholders than arguments
    - Missing positional parameters
  - **Acceptance**: Validates $N placeholder substitution
  - **Effort**: 2 hours

- [ ] **T2.1.5**: Implement allowed-tools validation tests
  - **Scenarios**:
    - Tool in allowed list (should work)
    - Tool not in allowed list (should block)
    - Wildcard patterns (e.g., `Bash(git:*)`)
  - **Acceptance**: Tool permission enforcement works
  - **Effort**: 3 hours

- [ ] **T2.1.6**: Implement command error handling tests
  - **Scenarios**:
    - Command file not found
    - Malformed command syntax
    - Command timeout
    - Command crashes mid-execution
  - **Acceptance**: Errors are caught and reported correctly
  - **Effort**: 3 hours

**Subtotal for 2.1**: ~18 hours (2.25 days)

---

### 2.2: Add Agent Testing

**New Files**: `tests/features/agents/agent_execution.feature`, `tests/steps/agent_steps.py`
**Estimated**: 2 days

#### Tasks:

- [ ] **T2.2.1**: Create agent_execution.feature
  - **Content**: 12-15 scenarios covering:
    - Agent definition validation
    - Tool permission enforcement
    - Context isolation
    - Structured output
  - **Acceptance**: Feature file covers all agent aspects
  - **Effort**: 3 hours

- [ ] **T2.2.2**: Implement agent definition validation tests
  - **Scenarios**:
    - Valid agent with all frontmatter
    - Missing required fields (name, description, tools)
    - Invalid tool patterns
    - Missing system prompt
  - **Acceptance**: Can parse `.claude/agents/*.md` files
  - **Effort**: 3 hours

- [ ] **T2.2.3**: Implement tool permission tests
  - **Scenarios**:
    - Agent uses allowed tool (succeeds)
    - Agent attempts forbidden tool (blocked)
    - Wildcard permissions (e.g., `mcp__serena__*`)
    - Empty tools list (no tools allowed)
  - **Acceptance**: Tool access control works
  - **Effort**: 4 hours

- [ ] **T2.2.4**: Implement context isolation tests
  - **Scenarios**:
    - Agent doesn't see main context
    - Agent only receives input data
    - Agent output doesn't leak to main context
  - **Acceptance**: Agents have independent context windows
  - **Effort**: 4 hours

- [ ] **T2.2.5**: Implement structured output validation tests
  - **Scenarios**:
    - Agent returns valid JSON
    - Agent returns invalid JSON (error)
    - Agent returns required schema fields
    - Agent missing required fields (error)
  - **Acceptance**: Can validate JSON schema compliance
  - **Effort**: 3 hours

- [ ] **T2.2.6**: Implement agent invocation tests
  - **Scenarios**:
    - Spawn agent via Task tool
    - Agent receives correct input
    - Agent returns output to caller
    - Agent execution timeout
  - **Acceptance**: Can test full agent invocation lifecycle
  - **Effort**: 4 hours

**Subtotal for 2.2**: ~21 hours (2.6 days)

---

### 2.3: Add Integration Testing

**New Files**: `tests/features/integration/workflows.feature`, `tests/steps/integration_steps.py`
**Estimated**: 3 days

#### Tasks:

- [ ] **T2.3.1**: Create workflows.feature
  - **Content**: 10-12 end-to-end scenarios
  - **Coverage**:
    - Command → Agent → Hook pipelines
    - Multi-agent workflows
    - Checkpoint/recovery
    - Error propagation
  - **Acceptance**: Scenarios test realistic user workflows
  - **Effort**: 4 hours

- [ ] **T2.3.2**: Implement command → agent flow tests
  - **Scenario**: `/rfc-generate` spawns parser → analyzer → formatter agents
  - **Verification**:
    - Command invokes correct agents in order
    - Data flows between agents
    - Final output matches expectations
  - **Acceptance**: Can test multi-agent pipelines
  - **Effort**: 6 hours

- [ ] **T2.3.3**: Implement agent → hook flow tests
  - **Scenario**: Agent writes file → PostToolUse hook updates rfc-map.json
  - **Verification**:
    - Hook triggered by agent action
    - Hook receives correct input
    - Hook modifies state correctly
  - **Acceptance**: Can test hook integration with agents
  - **Effort**: 4 hours

- [ ] **T2.3.4**: Implement checkpoint/recovery tests
  - **Scenario**: Agent fails mid-workflow → checkpoint saved → retry succeeds
  - **Verification**:
    - Checkpoint file created
    - Checkpoint contains correct data
    - Retry loads checkpoint
    - Workflow completes from checkpoint
  - **Acceptance**: Checkpoint system works end-to-end
  - **Effort**: 6 hours

- [ ] **T2.3.5**: Implement concurrent agent tests
  - **Scenario**: Spawn 3 agents in parallel → all complete successfully
  - **Verification**:
    - Agents run concurrently (not sequential)
    - No race conditions
    - All agents complete
    - Results aggregated correctly
  - **Acceptance**: Can test parallel execution
  - **Effort**: 6 hours

- [ ] **T2.3.6**: Implement error propagation tests
  - **Scenario**: Agent fails → error bubbles to command → hook notified
  - **Verification**:
    - Error captured at each level
    - Error context preserved
    - Recovery actions triggered
  - **Acceptance**: Error handling works across components
  - **Effort**: 4 hours

**Subtotal for 2.3**: ~30 hours (3.75 days)

---

### 2.4: Add MCP Integration Tests (with Mocks)

**New Files**: `tests/support/mcp_mocks.py`
**Estimated**: 1 day

#### Tasks:

- [ ] **T2.4.1**: Create MCP mock infrastructure
  - **File**: `tests/support/mcp_mocks.py`
  - **Classes**:
    - `MockSerenaMCP` - Mocks serena tool calls
    - `MockContext7MCP` - Mocks documentation lookups
    - `MockIDEMCP` - Mocks IDE diagnostics
  - **Acceptance**: Can replace real MCP calls with predictable responses
  - **Effort**: 4 hours

- [ ] **T2.4.2**: Implement Serena MCP mock scenarios
  - **Scenarios**:
    - get_symbols_overview returns mock symbols
    - find_symbol returns mock symbol data
    - MCP unavailable (connection error)
  - **Acceptance**: Tests can run without real Serena MCP server
  - **Effort**: 3 hours

- [ ] **T2.4.3**: Add MCP error injection tests
  - **Scenarios**:
    - MCP timeout
    - MCP returns malformed data
    - MCP authentication failure
  - **Acceptance**: Error handling for MCP issues works
  - **Effort**: 3 hours

**Subtotal for 2.4**: ~10 hours (1.25 days)

---

### Phase 2 Total: ~79 hours (9.9 days actual, 5-7 days with parallelization)

**Critical Path**: 2.1 → 2.2 → 2.3 (can overlap)
**Parallelization opportunity**: 2.1, 2.2, 2.4 can be done concurrently

---

## Phase 3: Improve Code Quality (Days 13-15)

**Goal**: Reorganize code for maintainability
**Priority**: MEDIUM
**Estimated Effort**: 2-3 days

### 3.1: Reorganize Test Structure

**Estimated**: 1 day

#### Tasks:

- [ ] **T3.1.1**: Create new directory structure
  - **New dirs**:
    ```
    tests/
    ├── features/
    │   ├── rfc_generation/
    │   ├── rfc_update/
    │   ├── automation/
    │   ├── commands/
    │   ├── agents/
    │   └── integration/
    ├── steps/
    ├── support/
    └── fixtures/
    ```
  - **Acceptance**: Directory structure created
  - **Effort**: 15 minutes

- [ ] **T3.1.2**: Move feature files to domain directories
  - **Moves**:
    - `generate.feature` → `rfc_generation/`
    - `update.feature` → `rfc_update/`
    - `automation.feature` → `automation/hooks.feature`
  - **Acceptance**: Feature files relocated
  - **Effort**: 30 minutes

- [ ] **T3.1.3**: Split large step files
  - **Actions**:
    - Split `update_steps.py` (1066 lines) into:
      - `update_steps.py` (Given/When steps) - ~400 lines
      - `update_assertions.py` (Then steps) - ~400 lines
      - `update_helpers.py` (utilities) - ~200 lines
    - Split `generate_steps.py` similarly
  - **Acceptance**: No file >500 lines
  - **Effort**: 3 hours

- [ ] **T3.1.4**: Rename step files to be more descriptive
  - **Renames**:
    - `repo_setup.py` → `git_repository_steps.py`
    - `build_commands.py` → `make_build_steps.py`
    - `results.py` → `assertion_helpers.py`
  - **Acceptance**: Names reflect file purpose
  - **Effort**: 30 minutes

- [ ] **T3.1.5**: Update imports across all files
  - **Action**: Fix all import statements after reorganization
  - **Acceptance**: All tests still pass
  - **Effort**: 2 hours

**Subtotal for 3.1**: ~6 hours

---

### 3.2: Extract Common Utilities

**Estimated**: 1 day

#### Tasks:

- [ ] **T3.2.1**: Create tests/support/helpers.py
  - **Functions to extract**:
    - `cd()` context manager (currently in 3 files)
    - `run_with_capture()` (build_commands.py)
    - `create_test_code_file()` (automation_steps.py)
    - `set_file_mtime()` (automation_steps.py)
  - **Acceptance**: Common utilities centralized
  - **Effort**: 2 hours

- [ ] **T3.2.2**: Create tests/support/fixtures.py
  - **Functions to extract**:
    - `create_rfc_map()` (automation_steps.py)
    - `_create_fixture()` (environment.py)
    - `_create_default_fixture()` (environment.py)
  - **Acceptance**: Fixture creation centralized
  - **Effort**: 2 hours

- [ ] **T3.2.3**: Create tests/support/test_data.py
  - **Content**: Test data generators using factory pattern
  - **Factories**:
    - `RFCDocumentFactory` - Generate test RFC files
    - `RFCMapFactory` - Generate rfc-map.json data
    - `CodeFileFactory` - Generate test source files
  - **Acceptance**: Can generate test data programmatically
  - **Effort**: 3 hours

- [ ] **T3.2.4**: Create tests/support/assertions.py
  - **Functions**:
    - `assert_file_contains(path, content, message=None)`
    - `assert_rfc_section_exists(rfc_content, section_name)`
    - `assert_valid_kramdown(rfc_path)`
    - `assert_valid_rfc_map(map_path)`
  - **Acceptance**: Custom assertions available
  - **Effort**: 2 hours

- [ ] **T3.2.5**: Update all step files to use support modules
  - **Action**: Replace duplicated code with imports
  - **Acceptance**: All tests still pass, less duplication
  - **Effort**: 2 hours

**Subtotal for 3.2**: ~11 hours

---

### 3.3: Fix environment.py

**File**: `tests/environment.py`
**Estimated**: 0.5 days

#### Tasks:

- [ ] **T3.3.1**: Remove wildcard import
  - **Change**: `from behave import *` → `from behave import given, when, then, fixture, use_fixture`
  - **Acceptance**: Explicit imports only
  - **Effort**: 15 minutes

- [ ] **T3.3.2**: Make git initialization conditional
  - **Change**: Only init git if `@git` tag present on scenario
  - **Acceptance**: Non-git tests faster
  - **Effort**: 1 hour

- [ ] **T3.3.3**: Add explicit context cleanup
  - **Change**: Add `del context.temp_dir` etc. in after_scenario
  - **Acceptance**: No context pollution between scenarios
  - **Effort**: 30 minutes

- [ ] **T3.3.4**: Unify test_repo and working_dir naming
  - **Change**: Use only `context.test_repo` consistently
  - **Acceptance**: No confusion between attributes
  - **Effort**: 1 hour

- [ ] **T3.3.5**: Add performance metrics tracking
  - **Change**: Track scenario execution time, add to stats
  - **Acceptance**: Can identify slow scenarios
  - **Effort**: 1 hour

- [ ] **T3.3.6**: Remove duplicate cleanup logic
  - **Change**: Consolidate lines 90-93 with main cleanup
  - **Acceptance**: Single cleanup code path
  - **Effort**: 30 minutes

**Subtotal for 3.3**: ~4.5 hours

---

### 3.4: Add Type Annotations

**Estimated**: 0.5 days

#### Tasks:

- [ ] **T3.4.1**: Add return type annotations to all step functions
  - **Example**: `def step_impl(context: Context) -> None:`
  - **Acceptance**: All functions have return types
  - **Effort**: 2 hours

- [ ] **T3.4.2**: Add type hints to helper functions
  - **Files**: All in `tests/support/`
  - **Acceptance**: Mypy passes with no errors
  - **Effort**: 2 hours

- [ ] **T3.4.3**: Create type stubs for complex data structures
  - **File**: `tests/support/types.py`
  - **Classes**: `RFCDocument`, `RFCMapping`, `HookResponse`, `CommandResult`
  - **Acceptance**: TypedDict or dataclass for each structure
  - **Effort**: 2 hours

**Subtotal for 3.4**: ~6 hours

---

### Phase 3 Total: ~27.5 hours (3.4 days actual, 2-3 days with focus)

**Critical Path**: 3.1 → 3.2 → 3.3 (sequential)
**Parallelization opportunity**: 3.4 can be done alongside 3.2

---

## Phase 4: Enhance Test Quality (Days 16-18)

**Goal**: Make tests more maintainable and reliable
**Priority**: MEDIUM
**Estimated Effort**: 2-3 days

### 4.1: Use Scenario Outlines

**Estimated**: 1 day

#### Tasks:

- [ ] **T4.1.1**: Convert repeated scenarios to outlines in update.feature
  - **Target**: Lines with similar structure but different data
  - **Example**:
    ```gherkin
    Scenario Outline: Update RFC after code changes
      Given an existing RFC document
      And I modify "<file>" <change_type>
      When I run "/rfc-update <rfc_file>"
      Then sections "<sections>" should be regenerated
      And I should see "<message>"

    Examples: Different Change Types
      | file              | change_type        | rfc_file         | sections | message              |
      | src/calculator.py | method signature   | draft-calc-00.md | 3.1      | Sections regenerated |
      | src/utils.py      | function signature | draft-calc-00.md | 4.1      | Sections regenerated |
    ```
  - **Target reduction**: 28 scenarios → ~15 scenarios + outlines
  - **Acceptance**: Less duplication, same coverage
  - **Effort**: 4 hours

- [ ] **T4.1.2**: Convert error handling scenarios to outlines
  - **Target**: Scenarios testing different error conditions
  - **Examples table**: error_type, input, expected_message, exit_code
  - **Acceptance**: Error tests use data-driven approach
  - **Effort**: 2 hours

- [ ] **T4.1.3**: Convert hook testing scenarios to outlines
  - **Target**: automation.feature hook scenarios
  - **Examples**: Different hook types, inputs, expected responses
  - **Acceptance**: Hook tests more concise
  - **Effort**: 2 hours

**Subtotal for 4.1**: ~8 hours

---

### 4.2: Improve Scenario Independence

**Estimated**: 1 day

#### Tasks:

- [ ] **T4.2.1**: Audit all scenarios for dependencies
  - **Action**: Review each scenario, identify shared state
  - **Tool**: Run behave with `--format json`, analyze dependencies
  - **Acceptance**: List of dependent scenarios identified
  - **Effort**: 2 hours

- [ ] **T4.2.2**: Fix scenarios with implicit dependencies
  - **Action**: Add explicit Given steps for prerequisites
  - **Example**: "And an existing RFC document" instead of assuming from Background
  - **Acceptance**: Each scenario self-contained
  - **Effort**: 4 hours

- [ ] **T4.2.3**: Add scenario execution order randomization test
  - **Action**: Run `behave --format json --no-capture --order random`
  - **Acceptance**: All scenarios pass in any order
  - **Effort**: 1 hour

- [ ] **T4.2.4**: Fix context cleanup issues
  - **Action**: Ensure all context attributes cleaned in after_scenario
  - **Acceptance**: No context pollution between scenarios
  - **Effort**: 2 hours

**Subtotal for 4.2**: ~9 hours

---

### 4.3: Add Test Data Generators

**Estimated**: 1 day

#### Tasks:

- [ ] **T4.3.1**: Implement RFCDocumentFactory
  - **File**: `tests/support/test_data.py`
  - **Methods**:
    - `create_minimal()` - Bare minimum RFC
    - `create_with_sections(sections=[])` - RFC with specific sections
    - `create_with_frontmatter(fields={})` - Custom frontmatter
  - **Acceptance**: Can generate valid RFC markdown
  - **Effort**: 3 hours

- [ ] **T4.3.2**: Implement RFCMapFactory
  - **Methods**:
    - `create_empty()` - Empty rfc-map.json
    - `create_with_mappings(count=N)` - N random mappings
    - `create_for_files(files=[])` - Mappings for specific files
  - **Acceptance**: Can generate valid rfc-map.json
  - **Effort**: 2 hours

- [ ] **T4.3.3**: Implement CodeFileFactory
  - **Methods**:
    - `create_python_class(name, methods=[])` - Python class
    - `create_python_function(name, params=[])` - Python function
    - `create_typescript_interface(name, fields=[])` - TS interface
  - **Acceptance**: Can generate valid source code files
  - **Effort**: 3 hours

- [ ] **T4.3.4**: Replace hardcoded test data with factory calls
  - **Action**: Update all step definitions to use factories
  - **Acceptance**: No more hardcoded test data in steps
  - **Effort**: 2 hours

**Subtotal for 4.3**: ~10 hours

---

### Phase 4 Total: ~27 hours (3.4 days actual, 2-3 days with focus)

---

## Phase 5: Add Advanced Testing (Days 19-22)

**Goal**: Performance, error injection, CI/CD
**Priority**: LOW
**Estimated Effort**: 3-4 days

### 5.1: Performance Testing

**Estimated**: 1 day

#### Tasks:

- [ ] **T5.1.1**: Add timing assertions to hook tests
  - **Assertion**: Hook execution <100ms for PreToolUse
  - **Implementation**: Wrap hook calls with timing decorator
  - **Acceptance**: Slow hooks fail tests
  - **Effort**: 2 hours

- [ ] **T5.1.2**: Add large file handling tests
  - **Scenarios**:
    - Generate RFC from 10,000 line codebase
    - Update RFC with 1MB rfc-map.json
  - **Acceptance**: Can handle large inputs without timeout
  - **Effort**: 3 hours

- [ ] **T5.1.3**: Add concurrent scenario execution tests
  - **Tool**: `behave-parallel` or custom runner
  - **Acceptance**: Can run scenarios in parallel without conflicts
  - **Effort**: 3 hours

**Subtotal for 5.1**: ~8 hours

---

### 5.2: Error Injection Testing

**Estimated**: 1.5 days

#### Tasks:

- [ ] **T5.2.1**: Add hook failure tests
  - **Scenarios**:
    - Hook times out (>60 seconds)
    - Hook crashes (exit code 1)
    - Hook returns invalid JSON
    - Hook permission denied
  - **Acceptance**: All error conditions handled gracefully
  - **Effort**: 4 hours

- [ ] **T5.2.2**: Add MCP unavailability tests
  - **Scenarios**:
    - Serena MCP not running
    - Serena MCP times out
    - Serena MCP returns 500 error
  - **Acceptance**: Clear error messages, graceful degradation
  - **Effort**: 3 hours

- [ ] **T5.2.3**: Add filesystem error tests
  - **Scenarios**:
    - Permission denied writing RFC
    - Disk full
    - File locked by another process
  - **Acceptance**: Filesystem errors caught and reported
  - **Effort**: 3 hours

- [ ] **T5.2.4**: Add malformed file tests
  - **Scenarios**:
    - Invalid YAML frontmatter in command file
    - Invalid JSON in rfc-map.json
    - Corrupted checkpoint file
  - **Acceptance**: Parse errors caught, recovery attempted
  - **Effort**: 3 hours

**Subtotal for 5.2**: ~13 hours

---

### 5.3: CI/CD Integration

**Estimated**: 1.5 days

#### Tasks:

- [ ] **T5.3.1**: Add JUnit XML output
  - **Command**: `behave --junit --junit-directory test-reports/`
  - **Acceptance**: XML reports generated for CI
  - **Effort**: 1 hour

- [ ] **T5.3.2**: Add coverage reporting
  - **Tool**: coverage.py with behave
  - **Config**: `.coveragerc` with source paths
  - **Acceptance**: Coverage reports generated
  - **Effort**: 2 hours

- [ ] **T5.3.3**: Create GitHub Actions workflow
  - **File**: `.github/workflows/bdd-tests.yml`
  - **Steps**:
    - Setup Python
    - Install dependencies
    - Run behave
    - Upload test results
    - Upload coverage
  - **Acceptance**: Tests run on every PR
  - **Effort**: 3 hours

- [ ] **T5.3.4**: Add test result archiving
  - **Action**: Archive JUnit XML, HTML reports, screenshots
  - **Acceptance**: Test artifacts available in CI
  - **Effort**: 2 hours

- [ ] **T5.3.5**: Add parallel test execution in CI
  - **Tool**: `behave-parallel` or pytest-xdist
  - **Config**: Split scenarios across runners
  - **Acceptance**: Tests run faster in CI
  - **Effort**: 3 hours

**Subtotal for 5.3**: ~11 hours

---

### Phase 5 Total: ~32 hours (4 days actual, 3-4 days with focus)

---

## Task Dependencies

### Critical Path

```
Phase 1 (Days 1-5)
  ↓
Phase 2 (Days 6-12)
  ↓
Phase 3 (Days 13-15)
  ↓
Phase 4 (Days 16-18)
  ↓
Phase 5 (Days 19-22)
```

### Parallelization Opportunities

**Phase 1**: Tasks 1.1 and 1.2 can be done concurrently (2 developers)

**Phase 2**: Tasks 2.1, 2.2, 2.4 can be done concurrently (3 developers)

**Phase 3**: Tasks 3.2 and 3.4 can be done concurrently

**Phase 4**: All tasks can be done concurrently (3 developers)

**Phase 5**: Tasks 5.1, 5.2, 5.3 can be done concurrently (3 developers)

### Blocking Dependencies

- **T1.3.x requires T1.1.x and T1.2.x** (need step definitions before testing real execution)
- **T2.3.x requires T2.1.x and T2.2.x** (need component tests before integration tests)
- **T3.1.x blocks T3.2.x** (reorganize before extracting utilities)
- **Phase 4 requires Phase 3** (need clean code before enhancing quality)

---

## Success Metrics

### Quantitative Metrics

| Metric | Current | Target | Phase |
|--------|---------|--------|-------|
| Stub step definitions | 40% | 0% | Phase 1 |
| Real execution | 0% | 100% | Phase 1 |
| Command test coverage | 0% | 100% | Phase 2 |
| Hook test coverage | 30% | 100% | Phase 1,2 |
| Agent test coverage | 0% | 100% | Phase 2 |
| Max file size | 1066 lines | <500 lines | Phase 3 |
| Code duplication | High | Low | Phase 3 |
| Type annotations | 10% | 100% | Phase 3 |
| Scenario independence | 60% | 100% | Phase 4 |
| Test execution time | N/A | <5 min | Phase 5 |
| Code coverage | N/A | >80% | Phase 5 |

### Qualitative Metrics

- [ ] Tests run without any MCP server running (using mocks)
- [ ] Tests can run in any order (random execution passes)
- [ ] New developers can understand test structure
- [ ] CI catches real bugs before merge
- [ ] Refactoring is safe (tests provide confidence)

---

## Risk Mitigation

### High Risk Areas

1. **Real command execution may require Claude Code API changes**
   - Mitigation: Start with subprocess execution of slash commands
   - Fallback: Document limitations, prioritize other phases

2. **MCP mocking may not match real behavior**
   - Mitigation: Create comprehensive mock based on real MCP responses
   - Fallback: Add integration tests with real MCP in separate suite

3. **Reorganization may break existing tests**
   - Mitigation: Make changes incrementally, run tests after each step
   - Fallback: Feature branch, revert if issues arise

### Medium Risk Areas

1. **Performance testing may reveal systemic slowness**
   - Mitigation: Profile before optimizing, focus on critical path
   - Fallback: Set realistic timeout thresholds

2. **Scenario independence fixes may require major rewrites**
   - Mitigation: Start with low-hanging fruit, document dependencies
   - Fallback: Accept some dependencies if time-constrained

---

## Next Steps

1. **Review and approve** this detailed breakdown
2. **Assign tasks** to developers (if multiple people)
3. **Start with Phase 1.1** (implement stub step definitions)
4. **Daily standup** to track progress and blockers
5. **Weekly review** to adjust estimates and priorities

---

## Appendix: Task Estimation Guidelines

- **1 hour**: Simple function, clear acceptance criteria
- **2 hours**: Moderate complexity, some unknowns
- **3 hours**: Complex logic, multiple edge cases
- **4 hours**: Integration work, multiple components
- **6+ hours**: Research required, new patterns

**Buffer factor**: Add 20% to all estimates for unknowns and debugging.
