# Feature Specification: RFC-Style Documentation Generator for Claude-Code

**Feature Branch**: `002-build-a-claude`
**Created**: 2025-10-13
**Status**: Draft
**Input**: User description: "Build a Claude-Code agents, hooks and slash-command based solution that lets any repository generate and maintain accurate, non-redundant RFC-style specifications directly from its source code and related documents. Users can select paths to include, produce cross-referenced sections aligned with IETF conventions, and keep specs coherent as code evolves. The system supports on-demand runs and optional automation, provides reviewer guidance, scales to large codebases, and preserves context quality. Primary outcomes: trustworthy RFC-like docs that mirror current behavior, clear interfaces/terminology/behavior sections, and explicit references to external standards when needed."

## Clarifications

### Session 2025-10-13

- Q: When users trigger RFC documentation generation, what should be the primary interface mechanism? → A: Slash command with arguments about area of interest and describing methodology and spawning agents
- Q: How should the system handle preservation of manual edits when updating RFC documentation? → A: Preserve edits in specially marked sections
- Q: Which RFC sections should be mandatory in every generated document? → A: User-configurable mandatory sections from full IETF template
- Q: What threshold should trigger documentation update notifications during code reviews? → A: Changes to public APIs and interfaces
- Q: How should the system maintain context quality when processing large codebases? → A: Incremental chunk processing with overlap
- Q: How should specialized agents be architected and coordinated? → A: Multiple specialized agents (parser, analyzer, formatter, validator) with coordinator/orchestrator
- Q: What format should be used for marking sections to preserve manual edits? → A: Custom directives (@preserve-start/@preserve-end)
- Q: How should we differentiate performance targets between initial generation and incremental updates? → A: Initial: 10K lines/2min, 100K/20min, 1M/60min; Incremental: <10min for any size
- Q: How should the system detect which external standards are implemented in the code? → A: Hierarchical pipeline: Config/dependencies first, then comments, then protocol signatures

## Definitions

**RFC Document**: The generated specification artifact in kramdown-rfc format, representing the authoritative documentation of the codebase's behavior, interfaces, and architecture. See data-model.md for the complete entity schema.

**RFC documentation process**: The workflow of generating, updating, and validating RFC Documents from source code using specialized agents and automation.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate Initial RFC Documentation (Priority: P1)

A developer needs to generate RFC-style documentation for a project that has never had formal specifications, using Claude-Code to analyze the codebase and produce IETF-compliant documentation.

**Why this priority**: This is the core functionality that delivers immediate value by creating documentation where none existed before. Without this, no other features can provide value.

**Independent Test**: Can be fully tested by selecting a project directory and generating an RFC Document that includes at least terminology, interfaces, and behavior sections.

**Acceptance Scenarios**:

1. **Given** a repository with source code but no RFC Document, **When** the user invokes the RFC generation command with selected paths, **Then** the system produces a complete RFC Document with all mandatory sections
2. **Given** a user selecting specific directories to analyze, **When** they trigger documentation generation, **Then** only the selected paths are analyzed and documented
3. **Given** a generated RFC Document, **When** the user reviews it, **Then** all code references are accurately cross-referenced with line numbers and file paths

---

### User Story 2 - Update Existing RFC Documentation (Priority: P2)

A maintainer needs to update an existing RFC Document after code changes, ensuring the specification remains accurate and reflects the current implementation without duplicating unchanged content.

**Why this priority**: Maintaining documentation accuracy over time is critical for long-term value, but requires the initial generation capability to exist first.

**Independent Test**: Can be tested by modifying code in a documented project and running the update command to verify only changed sections are updated.

**Acceptance Scenarios**:

1. **Given** an existing RFC Document and modified source code, **When** the user runs the update command, **Then** only sections affected by code changes are updated
2. **Given** a project with recent code changes, **When** documentation update runs, **Then** the system preserves manual edits in specially marked sections using custom directives (@preserve-start/@preserve-end)
3. **Given** documentation needing updates, **When** the update completes, **Then** a change summary shows what sections were modified

---

### User Story 3 - Automated Documentation Checks (Priority: P3)

A team lead wants automated documentation quality checks to run during development workflows, providing real-time guidance about documentation completeness and accuracy through Claude Code native hooks.

**Why this priority**: Automation enhances workflow efficiency but is not essential for basic documentation generation and maintenance functionality.

**Independent Test**: Can be tested by configuring Claude Code native hooks and verifying they trigger during Write, Edit, and Bash tool usage.

**Acceptance Scenarios**:

1. **Given** a developer is about to modify RFC-tracked code files, **When** PreToolUse hook triggers before Write/Edit, **Then** the system validates that the modification won't break cross-references and warns if documentation updates are needed
2. **Given** a developer has modified code using Write/Edit/Bash tools, **When** PostToolUse hook triggers, **Then** rfc-map.json is automatically updated to reflect the changes and stale cross-references are flagged
3. **Given** an incomplete RFC Document exists, **When** automated validation runs via hooks, **Then** it identifies missing mandatory sections and suggests content
4. **Given** changes to public APIs detected by PreToolUse hook, **When** the developer proceeds with the change, **Then** affected RFC sections are listed and reviewer guidance is generated
5. **Given** a UserPromptSubmit hook detects RFC-related intent (keywords: "RFC", "documentation", "/rfc-"), **When** the user submits a prompt, **Then** relevant RFC context is automatically loaded from memory files

**Hook Architecture**:
- **PreToolUse** hooks with tool matchers `Write|Edit` detect file modifications before they occur, validate against rfc-map.json, and provide warnings
- **PreToolUse** hook with tool matcher `Bash` enforces Make target usage (blocks direct kramdown-rfc/xml2rfc calls)
- **PostToolUse** hooks with tool matcher `Write|Edit|Bash` automatically synchronize rfc-map.json and detect stale cross-references
- **UserPromptSubmit** hook detects RFC-related intent and loads relevant context
- **SessionStart** hook checks for stale documentation (last update > 30 days) and prompts user

---

### User Story 4 - Scale to Large Codebases (Priority: P2)

An architect needs to generate RFC documentation for a large enterprise codebase (>100K lines) while maintaining performance and context quality.

**Why this priority**: Enterprise adoption requires handling large codebases effectively, making this critical for broader applicability.

**Independent Test**: Can be tested by running generation on progressively larger codebases and measuring completion time and memory usage.

**Acceptance Scenarios**:

1. **Given** a codebase with over 100,000 lines of code, **When** RFC generation runs, **Then** it completes within 10 minutes
2. **Given** a large project with multiple modules, **When** generating documentation, **Then** the system maintains cross-references between modules accurately
3. **Given** resource constraints, **When** processing large codebases, **Then** the system uses incremental chunk processing with overlap to preserve context quality

---

### User Story 5 - Reference External Standards (Priority: P3)

A standards compliance officer needs the RFC documentation to explicitly reference and link to relevant external standards (IETF RFCs, W3C specs, etc.) that the code implements.

**Why this priority**: External standard references enhance documentation quality but are not required for basic functionality.

**Independent Test**: Can be tested by verifying that generated documentation includes properly formatted references to detected standards.

**Acceptance Scenarios**:

1. **Given** code implementing standard protocols, **When** RFC documentation generates, **Then** it includes references to relevant IETF RFCs
2. **Given** detected external standards, **When** documentation renders, **Then** references include both inline citations and a bibliography section

---

### Edge Cases

- What happens when the selected paths contain no analyzable code?
- How does the system handle circular dependencies between modules?
- What occurs when existing RFC documentation has conflicting manual edits? **Resolution**: When @preserve blocks conflict with generated content during updates, preserved content takes precedence. Conflicts are logged as warnings requiring user review. Adjacent sections are adjusted to avoid overlap. User MUST review diff before committing.
- How does the system respond when it cannot determine the appropriate RFC section for certain code?
- What happens when the codebase is too large to process in available memory?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST generate RFC-style documentation from source code following IETF documentation conventions, with user-configurable mandatory sections based on the full IETF template
- **FR-002**: System MUST allow users to select specific paths and directories for inclusion in documentation
- **FR-003**: System MUST produce cross-referenced sections linking code elements to their documentation
- **FR-004**: System MUST detect and prevent redundant content when updating existing documentation
- **FR-005**: Users MUST be able to trigger documentation generation through slash commands that accept arguments for area of interest, describe methodology, and spawn specialized agents
- **FR-006**: System MUST maintain coherence between documentation sections as code evolves. Coherence is ensured through:
  * Cross-reference accuracy: All section references and code links resolve correctly (100% valid links)
  * Terminology consistency: Terms used uniformly per definitions section
  * Logical consistency: No contradictory statements exist between sections
  * Completeness: All code elements mentioned in one section are documented elsewhere
- **FR-007**: System MUST preserve context quality when processing large codebases through incremental chunk processing with overlap
- **FR-008**: System MUST generate distinct sections for interfaces, terminology, and behavior
- **FR-009**: System MUST identify and reference external standards when detected in code using a hierarchical pipeline (configuration/dependency analysis, then comment pattern matching, then protocol signature detection)
- **FR-010**: System MUST provide reviewer guidance for documentation completeness
- **FR-011**: System MUST support optional automation through Claude Code native hooks (PreToolUse, PostToolUse, UserPromptSubmit, SessionStart). All hooks MUST be enabled by default to maximize automation value and encourage best practices. Hooks use tool matcher patterns (regex) to target specific operations (Write|Edit for file modifications, Bash for command execution). Users can disable individual hooks or adjust blocking behavior via plugin configuration
- **FR-012**: System MUST scale to handle large enterprise codebases through intelligent problem decomposition, maintaining coherence across modules, and accurate mapping of all code elements
- **FR-013**: System MUST complete documentation generation within reasonable time limits
- **FR-014**: System MUST validate generated documentation against IETF RFC formatting standards

### Key Entities

- **RFC Document**: The generated specification document containing all sections, cross-references, and metadata about the analyzed codebase
- **Code Element**: A discrete unit of source code (function, class, module) that gets documented with its interfaces, behavior, and relationships
- **Cross-Reference**: A bidirectional link between documentation sections and source code locations, maintaining line numbers and file paths
- **Documentation Section**: A structured part of the RFC document (Abstract, Introduction, Terminology, Interfaces, Behavior, Security Considerations, etc.)
- **External Standard**: A referenced specification (IETF RFC, W3C standard, etc.) that the codebase implements or conforms to
- **Change Set**: A collection of code modifications that trigger documentation updates, tracked to prevent redundant regeneration
- **Parser Agent**: Specialized agent that analyzes source code structure and extracts syntactic information
- **Analyzer Agent**: Specialized agent that extracts semantic meaning, relationships, and behavioral patterns from parsed code
- **Formatter Agent**: Specialized agent that generates RFC-compliant documentation sections from analyzed data
- **Validator Agent**: Specialized agent that ensures IETF standards compliance and documentation completeness
- **Coordinator/Orchestrator**: Central agent that manages workflow, balances load, and ensures context consistency across all specialized agents

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Initial generation completes in: 10,000 lines under 2 minutes, 100,000 lines under 20 minutes, 1,000,000 lines under 60 minutes
- **SC-002**: Incremental documentation updates complete within 10 minutes for any codebase size when changes affect less than 5% of files
- **SC-003**: 95% of code elements are correctly mapped to appropriate RFC sections without manual intervention
- **SC-004**: System maintains sub-30 second response time for single-file incremental updates regardless of codebase size
- **SC-005**: Documentation accuracy score of 90% or higher when validated against actual code behavior
- **SC-006**: Cross-references maintain 100% accuracy between documentation and source code locations
- **SC-007**: Reduce documentation maintenance time by 70% compared to manual documentation updates
- **SC-008**: 85% of reviewers report improved confidence in code reviews when using generated documentation guidance
- **SC-009**: Zero duplicate content sections in updated documentation when code hasn't changed
- **SC-010**: Successfully detect and reference 90% of implemented external standards in generated documentation

## Assumptions

- Users have basic familiarity with RFC document structure and IETF conventions
- The codebase being documented follows reasonable coding standards and has identifiable structure
- Source code files use standard programming languages that can be parsed and analyzed
- Manual edits to generated documentation follow a consistent format that allows preservation during updates
- System has sufficient computational resources for analyzing large codebases
- Claude-Code agent infrastructure is available and properly configured
- File system permissions allow reading source code and writing documentation files