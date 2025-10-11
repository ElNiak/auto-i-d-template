# RFC I-D Template Plugin Constitution

<!--
===================================================================================
CONSTITUTION SYNC IMPACT REPORT
===================================================================================
Version Change: INITIAL → 1.0.0
Change Type: MAJOR (Initial constitution establishment)
Ratification Date: 2025-10-11

Modified Principles: N/A (Initial creation)
Added Sections:
  - Core Principles (7 principles)
  - Claude Code Plugin Standards
  - Serena MCP Tool Usage Guidelines
  - Governance

Removed Sections: N/A (Initial creation)

Templates Requiring Updates:
  ✅ .specify/templates/plan-template.md - Reviewed, constitution check placeholder present
  ✅ .specify/templates/spec-template.md - Reviewed, requirements structure aligns
  ✅ .specify/templates/tasks-template.md - Reviewed, task organization supports principles

Follow-up TODOs:
  - Monitor adherence to Makefile-first principle during initial implementations
  - Validate that first features follow test-driven development workflow
  - Ensure documentation generation meets RFC formatting standards
===================================================================================
-->

## Core Principles

### I. Makefile-First Build System (NON-NEGOTIABLE)

All build operations, transformations, and automation MUST be orchestrated through GNU Make.

**Rules**:
- Every user-facing operation (build, lint, test, deploy) MUST have a corresponding Make target
- Make targets MUST be composable and dependency-aware
- Python scripts, shell scripts, and other tools are invoked BY Makefiles, never standalone
- All file transformations MUST declare explicit dependencies in Make
- Tool configuration (xml2rfc, kramdown-rfc, mmark) MUST be centralized in config.mk
- Build artifacts MUST be reproducible and traceable through Make's dependency graph

**Rationale**: This project exists to provide a robust, maintainable build template for IETF Internet Drafts. Make's dependency tracking, parallel execution, and composability are foundational to reliability. Any deviation undermines the core value proposition of the template.

### II. RFC Standards Compliance (NON-NEGOTIABLE)

Output documents MUST conform to IETF formatting and structural requirements.

**Rules**:
- All text output MUST pass idnits validation without errors
- XML intermediate format MUST be RFC 7991 (xml2rfc v3) compliant
- Generated HTML MUST follow RFC formatting conventions
- Version numbering MUST follow draft-*-## convention
- Metadata extraction MUST support all mandatory RFC frontmatter fields

**Rationale**: Non-compliant documents cannot be submitted to the IETF datatracker. Standards compliance is the non-negotiable deliverable of this toolchain.

### III. Test-Driven Development (REQUIRED for new features)

New features and significant modifications MUST follow TDD workflow.

**Rules**:
- Write tests FIRST that describe expected behavior
- Verify tests FAIL before implementation begins
- Implement minimum code to make tests pass (Red-Green-Refactor)
- Integration tests MUST cover: markdown-to-XML conversion, version numbering, gh-pages generation, datatracker upload
- Behavioral tests (behave framework) MUST validate user-facing workflows
- Tests MUST be runnable in CI/CD without manual intervention

**Rationale**: This template is used by hundreds of IETF working groups. Breaking changes have wide blast radius. TDD provides regression safety and behavior contracts.

### IV. Code Quality & Maintainability

Code MUST be maintainable by future contributors with diverse skill levels.

**Rules**:
- Shell scripts MUST use `set -e` (fail on error) and validate all inputs
- Python scripts MUST include docstrings for all public functions
- Makefiles MUST include comments explaining non-obvious logic
- Magic numbers MUST be replaced with named variables
- Complex regex patterns MUST have explanatory comments
- All tools MUST provide `--help` or `-h` flag documentation
- Error messages MUST be actionable (explain what went wrong AND how to fix it)

**Rationale**: Contributors range from Makefile experts to draft authors unfamiliar with build systems. Clear, defensive code reduces support burden and enables community contributions.

### V. Backward Compatibility & Graceful Degradation

Changes MUST NOT break existing draft repositories using the template.

**Rules**:
- Breaking changes require MAJOR version bump and migration guide
- Deprecated features MUST emit warnings for 2 minor versions before removal
- New features MUST work with existing drafts without modification
- Optional dependencies (Ruby, Node.js) MUST be skippable with fallback behavior
- Environment variable configuration MUST have sensible defaults
- Git tag parsing MUST handle historical tag formats

**Rationale**: Draft repositories span years of history. Forcing breaking migrations disrupts active IETF work. Stability is a core requirement.

### VI. Performance & Resource Efficiency

Build operations MUST complete quickly to support iterative authoring workflows.

**Rules**:
- Parallel execution MUST be enabled for independent targets
- Dependency tracking MUST avoid unnecessary rebuilds
- Large file processing MUST be incremental where possible
- CI/CD workflows MUST complete in under 5 minutes for typical drafts
- Tool installations MUST use caching (venv, bundler, npm cache)
- Verbose output MUST be opt-in (via VERBOSE or CI environment variables)

**Rationale**: Authors iterate frequently during draft development. Slow builds disrupt creative flow. CI/CD costs scale with execution time.

### VII. Documentation & User Experience Consistency

Documentation MUST be comprehensive, accurate, and accessible to non-technical users.

**Rules**:
- Every Make target MUST have a one-line description in help text
- README.md MUST provide quick start steps executable by beginners
- Error messages MUST suggest next actions (e.g., "Run `make update-deps` to install missing tools")
- Breaking changes MUST be documented in CHANGELOG with before/after examples
- Setup process MUST be automated (`make -f lib/setup.mk`)
- Generated files (Makefile, README, workflows) MUST include comments explaining purpose

**Rationale**: Primary users are RFC authors focused on content, not build systems. Excellent UX reduces friction and support requests.

## Claude Code Plugin Standards

### Plugin Structure Requirements

**Rules**:
- MUST include `plugin.json` with name (kebab-case), description, version, author
- MUST provide `.claude-plugin/marketplace.json` for distribution
- MUST support installation from GitHub, local paths, and Git repositories
- MUST use `${CLAUDE_PLUGIN_ROOT}` environment variable for path resolution
- MUST include commands for: build, lint, preview, submit, update
- MUST provide hooks for: pre-commit (lint + build check), post-merge (update check)

### Agent Configuration

**Rules**:
- MUST define agents for complex workflows: `/speckit.plan`, `/speckit.implement`, `/speckit.analyze`
- Agents MUST have clear, single-responsibility descriptions
- Agents MUST operate idempotently (safe to re-run)
- Agent outputs MUST be human-readable markdown
- Agents MUST use Serena MCP tools for codebase analysis (see next section)

### Validation & Testing

**Rules**:
- MUST pass `claude plugin validate` without errors
- MUST include integration tests for all slash commands
- MUST test installation from clean environment
- MUST verify generated files match expected structure
- MUST validate against real-world IETF draft repositories

**Rationale**: Plugin quality directly impacts user trust in Claude Code marketplace. Robust validation prevents distribution of broken plugins.

## Serena MCP Tool Usage Guidelines

### When to Use Serena Tools (MANDATORY for plugin agents)

Serena MCP provides semantic code analysis superior to naive file reading. Plugin agents MUST use these tools.

**Required Usage Patterns**:

1. **Initial codebase exploration**:
   - Use `get_symbols_overview` for file structure understanding (NOT `read_file`)
   - Use `list_dir` with `recursive=true` to map project layout
   - Use `find_file` with patterns to locate specific file types

2. **Symbol-based code reading**:
   - Use `find_symbol` with `name_path` for targeted symbol retrieval
   - Use `depth` parameter to include children (e.g., methods of a class)
   - Use `include_body=false` initially, then `true` only for relevant symbols
   - AVOID reading entire files unless truly necessary

3. **Code relationship analysis**:
   - Use `find_referencing_symbols` to understand usage and impact
   - Use `include_kinds` to filter by LSP symbol types (5=class, 12=function, etc.)
   - Use `relative_path` to scope searches to relevant directories

4. **Pattern-based search** (when symbol name unknown):
   - Use `search_for_pattern` with regex for content search
   - Use `paths_include_glob` to restrict search scope (e.g., "*.mk", "*.py")
   - Use `restrict_search_to_code_files=true` for code-only searches
   - Use context lines (`context_lines_before`, `context_lines_after`) sparingly

5. **Code modifications**:
   - Use `replace_symbol_body` for surgical updates to functions/classes
   - Use `insert_after_symbol` and `insert_before_symbol` for additions
   - AVOID line-based edits unless symbol-based approach impossible

### Prohibited Patterns (WILL cause inefficiency)

- Reading entire source files without first using `get_symbols_overview`
- Using basic `read_file` for code exploration (allowed only for non-code: markdown, config)
- Searching without restricting path or glob patterns
- Reading symbol bodies with `include_body=true` before confirming relevance
- Using line-based edits when symbol-based tools available

### Memory Management

**Rules**:
- Use `write_memory` to persist codebase insights (architecture, patterns, conventions)
- Use `list_memories` at conversation start to check existing knowledge
- Use `read_memory` for relevant memories (infer from filename)
- NEVER read same memory multiple times in one conversation
- Use `delete_memory` only on explicit user request

**Rationale**: Serena's semantic tools enable token-efficient codebase understanding. Naive file reading wastes context and slows analysis. Plugin agents operating in resource-constrained environments MUST optimize.

## Governance

### Amendment Process

1. Proposed changes MUST be documented in pull request with justification
2. Breaking principle changes require MAJOR version bump
3. New principles or material expansions require MINOR version bump
4. Clarifications and wording fixes require PATCH version bump
5. Amendment approval requires:
   - Technical review (correctness, feasibility)
   - Impact analysis (existing drafts, CI/CD, documentation)
   - Migration plan for breaking changes

### Compliance Review

**Rules**:
- All pull requests MUST verify constitution adherence
- New features MUST document which principles they satisfy
- Principle violations MUST be explicitly justified with rationale
- Constitution supersedes all other documentation in case of conflict

### Version Tracking

**Current Version**: 1.0.0
**Ratified**: 2025-10-11
**Last Amended**: 2025-10-11

### Versioning Policy

- **MAJOR (x.0.0)**: Backward incompatible principle changes, removed requirements
- **MINOR (0.x.0)**: New principles added, material guidance expansions
- **PATCH (0.0.x)**: Clarifications, typo fixes, non-semantic edits

### Enforcement

Constitution principles are enforced through:
1. Code review checklists referencing specific principles
2. Automated linting and testing gates (Principles III, IV, VI)
3. CI/CD validation against test suites (Principle II, III)
4. Plugin validation tooling (`claude plugin validate`)
5. Community review for template updates

**Conflict Resolution**: When principles conflict, priority order is:
1. RFC Standards Compliance (II)
2. Backward Compatibility (V)
3. Makefile-First Build System (I)
4. All other principles weighted equally, resolved case-by-case

---

**Version**: 1.0.0 | **Ratified**: 2025-10-11 | **Last Amended**: 2025-10-11
