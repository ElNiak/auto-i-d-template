# RFC I-D Template Plugin Constitution

<!--
===================================================================================
CONSTITUTION SYNC IMPACT REPORT
===================================================================================
Version Change: 1.1.0 → 1.2.0
Change Type: MINOR (New principles for code-to-spec workflow)
Ratification Date: 2025-10-11
Last Amended: 2025-10-12

Modified Principles:
  - Principle X (Single Source of Truth) → Enhanced with code-to-spec traceability (rfc-map.json)
  - Principle XI (Reproducible Build Pipelines) → Enhanced with code analysis pipeline constraints
  - Principle VI (Performance & Resource Efficiency) → Enhanced with code analysis performance budgets

Added Sections:
  - Principle XIII: Code-to-Spec Traceability (NEW)
  - Principle XIV: Context Hygiene for Code Analysis (NEW)
  - Principle XV: Review Gates & Impact Analysis (NEW)
  - Principle XVI: Security & Privacy for Code Analysis (NEW)
  - Code Analysis Pipeline section under Definitions (NEW)

Removed Sections: None

Templates Requiring Updates:
  ✅ .specify/templates/plan-template.md - Constitution Check covers both workflows
  ✅ .specify/templates/spec-template.md - Requirements support both RFC authoring and code-to-spec
  ✅ .specify/templates/tasks-template.md - Task phases support code analysis tasks

Follow-up TODOs:
  - Implement rfc-map.json schema and generation logic (Principle XIII)
  - Create LSP-based code harvesting scripts respecting SPECIFY_FEATURE scoping (Principle XIV)
  - Add performance monitoring for code analysis operations (Principle XIV, VI)
  - Implement impact analysis triggered by code changes (Principle XV)
  - Create security audit checklist for code analysis features (Principle XVI)
  - Extend existing containerized pipeline with code analysis stages (Principle XI)
  - Document rfc-map.json format in definitions.md
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

Output documents MUST conform to IETF formatting, structural, and normative language requirements.

**Rules**:
- All text output MUST pass idnits validation without errors
- XML intermediate format MUST be RFC 7991 (xml2rfc v3) compliant
- Generated HTML MUST follow RFC formatting conventions
- Version numbering MUST follow draft-*-## convention
- Metadata extraction MUST support all mandatory RFC frontmatter fields
- Normative language MUST follow RFC 2119 and RFC 8174 conventions (see Principle VIII)
- All citations to external specifications MUST be properly formatted (see Principle IX)

**Rationale**: Non-compliant documents cannot be submitted to the IETF datatracker. Standards compliance is the non-negotiable deliverable of this toolchain. RFC 2119 keyword discipline ensures unambiguous requirements expression.

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
- Technical terms and concepts MUST be defined in a single authoritative location (see Principle X)

**Rationale**: Contributors range from Makefile experts to draft authors unfamiliar with build systems. Clear, defensive code reduces support burden and enables community contributions. Centralized definitions prevent documentation drift and ambiguity.

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
- **Code analysis operations** (new):
  * On-save impact detection MUST complete in under 2 seconds for changed files
  * Incremental RFC generation from code MUST complete in under 30 seconds for target projects
  * LSP-based code harvesting MUST use scoped paths to minimize analysis scope

**Rationale**: Authors iterate frequently during draft development. Slow builds disrupt creative flow. CI/CD costs scale with execution time. Code analysis operations must be performant to enable real-time feedback during development.

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

### VIII. Normative Language Discipline (RFC-QUALITY)

All specifications, requirements, and technical documentation MUST use RFC 2119/8174 normative keywords with precision and consistency.

**Rules**:
- MUST use uppercase for RFC 2119 keywords: MUST, MUST NOT, REQUIRED, SHALL, SHALL NOT, SHOULD, SHOULD NOT, RECOMMENDED, NOT RECOMMENDED, MAY, OPTIONAL
- Each document containing normative keywords MUST include the RFC 8174 boilerplate in its introduction
- MUST distinguish between normative requirements (MUST/REQUIRED) and recommendations (SHOULD/RECOMMENDED)
- MUST NOT use RFC 2119 keywords in non-normative text (use lowercase: "should", "may", "can")
- Configuration files and code comments MAY use normative keywords when describing system behavior
- Lint targets MUST validate proper RFC 2119 keyword usage in markdown and XML sources
- **Code-to-spec generation** MUST preserve or synthesize normative keywords from code contracts (assertions, type constraints, validation logic)

**RFC 8174 Boilerplate**:
```
The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and
"OPTIONAL" in this document are to be interpreted as described in
BCP 14 [RFC2119] [RFC8174] when, and only when, they appear in all
capitals, as shown here.
```

**Rationale**: RFC 2119 provides unambiguous requirements specification critical for interoperability standards. Proper normative language discipline ensures implementers understand obligation levels. This template produces IETF documents; its own documentation should model best practices.

**Examples**:
- **Correct**: "The Makefile MUST define a `txt` target." (normative requirement)
- **Incorrect**: "The Makefile must define a `txt` target." (ambiguous - sounds normative but isn't)
- **Correct**: "We recommend using GNU Make 4.0+." (non-normative advice)
- **Incorrect**: "You SHOULD use GNU Make 4.0+." (normative language inappropriate for advice)

### IX. External Standards Citations (RFC-QUALITY)

References to external specifications, tools, and standards MUST be properly cited with authoritative sources.

**Rules**:
- All references to RFCs MUST use official RFC number format: RFC #### (e.g., RFC 2119, RFC 7991)
- References to IETF specifications MUST link to https://www.rfc-editor.org/rfc/rfc####.html or https://datatracker.ietf.org/doc/html/rfc####
- References to tools MUST include version constraints when behavior-dependent (e.g., "GNU Make 4.0+", "Python 3.6+")
- References to external projects MUST include stable URLs (prefer permalink over HEAD)
- References to standards bodies MUST use official names (IETF, W3C, ECMA, ISO)
- Generated documents MUST include a References section with all cited specifications
- Configuration files SHOULD include inline comments citing relevant specifications for non-obvious requirements

**Rationale**: Proper citations enable readers to verify claims, understand context, and trace requirements to authoritative sources. RFC authoring requires rigorous citation discipline; this template should model that practice.

**Examples**:
- **Correct**: "XML format MUST comply with RFC 7991 (https://www.rfc-editor.org/rfc/rfc7991.html)"
- **Incorrect**: "XML format must comply with xml2rfc v3 spec" (informal, no citation)
- **Correct**: "<!-- Timeout value per HTTP/1.1 RFC 7230 Section 6.3 -->"
- **Incorrect**: "<!-- Timeout value recommended by HTTP spec -->" (vague, no citation)

### X. Single Source of Truth (RFC-QUALITY)

Each technical term, concept, file path convention, and configuration parameter MUST be defined in exactly one authoritative location.

**Rules**:
- All technical definitions MUST be centralized in one of:
  * `definitions.md` for conceptual terms (e.g., "draft name", "editor's copy")
  * `config.mk` for build parameters (e.g., `LIBDIR`, `VENVDIR`)
  * `README.md` or `doc/` for user-facing concepts
- All other documents MUST reference the authoritative definition, NOT redefine it
- When definitions change, only the single authoritative source MUST be updated
- Makefiles MUST use variables defined in `config.mk`, NOT hardcode paths or values
- Documentation MUST use consistent terminology matching the authoritative definitions
- Each definition MUST include:
  * Canonical term (emphasized or in a heading)
  * Clear, concise definition
  * Examples if non-obvious
  * Related terms (cross-references)
- **Code-to-spec traceability** (new):
  * Code is the single source of truth for implementation behavior
  * Curated documentation provides context, rationale, and examples
  * `rfc-map.json` maintains bidirectional mapping between code symbols and RFC sections
  * When code changes, affected RFC sections are identified via `rfc-map.json`
  * Duplication between code comments and RFC text MUST be avoided; use cross-references

**Authoritative Locations** (as of v1.2.0):
- **Build variables**: `config.mk` (or equivalent top-level config file)
- **Conceptual terms**: `definitions.md` (to be created per Follow-up TODOs)
- **User workflows**: `README.md` and `doc/FEATURES.md`
- **File structure**: `CLAUDE.md` (project-specific guide)
- **Code-to-RFC mapping**: `rfc-map.json` (authoritative traceability map)
- **Implementation behavior**: Source code (code is truth, RFC describes it)

**Rationale**: Documentation drift occurs when the same concept is defined in multiple places. Centralized definitions ensure consistency, simplify maintenance, and reduce ambiguity. This mirrors RFC practice of defining terms once in a Terminology section. For code-derived specs, the code itself is the authoritative source; generated RFCs describe the code, not vice versa.

**Examples**:
- **Correct**: README says "See definitions.md for draft naming conventions" (reference)
- **Incorrect**: README redefines "draft name" differently than doc/GLOSSARY.md (drift)
- **Correct**: Makefile uses `$(LIBDIR)` variable from config.mk
- **Incorrect**: Makefile hardcodes `lib/` path (violates single source of truth)
- **Correct**: RFC section references `src/parser.py:validate()` method via rfc-map.json
- **Incorrect**: RFC duplicates validation logic in prose (drift risk)

### XI. Reproducible Build Pipelines (RFC-QUALITY)

All build, lint, and validation operations MUST be reproducible across environments and SHOULD be containerized.

**Rules**:
- CI/CD workflows MUST produce identical outputs given identical inputs (deterministic builds)
- Docker images MUST be provided for all critical build and validation steps
- Docker images MUST pin dependency versions (e.g., `xml2rfc==3.12.0`, `kramdown-rfc2629==1.6.0`)
- Docker images MUST be versioned and tagged with semantic versions
- Local builds and CI builds MUST use identical toolchains (same Docker image or venv/bundler locks)
- Build environments MUST NOT depend on ambient system state (e.g., globally installed tools)
- Dockerfile and CI workflow definitions MUST be version-controlled in the repository
- Each Docker image MUST include a README or inline comments documenting its purpose and contents
- Build logs MUST include environment information (tool versions, OS) for reproducibility debugging
- **Code analysis pipeline** (new):
  * Containerized pipeline MUST support: `code → kramdown-rfc2629 → RFCXML → xml2rfc → txt/html`
  * LSP analysis MUST be reproducible (pinned LSP server versions)
  * Validators (`rfclint`, `idnits`) MUST run in containers with pinned versions
  * All validators MUST pass on `main` branch (blocking requirement)

**Rationale**: Reproducibility is fundamental to scientific and engineering rigor. RFC authoring requires builds that produce identical results regardless of author's local environment. Containerization isolates dependencies and ensures long-term buildability of historical drafts. Code-to-spec generation requires stable analysis tooling to ensure consistent output.

**Implementation**:
- Existing: Python venv, Ruby bundler, npm caching
- New requirements: Docker images for full build environment including code analysis
- Container naming: `ghcr.io/martinthomson/i-d-template:v<VERSION>` (example)
- CI integration: GitHub Actions uses `container: ghcr.io/...` directive

**Examples**:
- **Correct**: `docker run i-d-template:1.2.0 make txt` (containerized, versioned)
- **Incorrect**: `make txt` relying on user's local xml2rfc version (non-reproducible)
- **Correct**: Dockerfile pins `RUN pip install xml2rfc==3.12.0 rfclint==0.13.0`
- **Incorrect**: Dockerfile uses `RUN pip install xml2rfc rfclint` (version drift)

### XII. Publication Quality Gates (RFC-QUALITY)

No document MAY be published or submitted unless it passes all mandatory validation checks.

**Rules**:
- All submissions MUST pass `make idnits` without errors
- All submissions MUST pass `make lint` without errors
- CI workflows MUST fail on validation errors (blocking checks)
- Git hooks (pre-commit) SHOULD run quick validation checks locally
- The following are MANDATORY gates for publication:
  * idnits validation (IETF submission requirements)
  * RFC 2119 keyword validation (normative language discipline)
  * XML schema validation (RFC 7991 compliance)
  * Citation format validation (all references well-formed)
  * Whitespace and formatting lint (clean source)
  * rfclint validation (RFC style conformance)
- Warning-level issues SHOULD be reviewed but MAY be overridden with justification
- Each quality gate MUST document its purpose and how to resolve failures
- The `make publish` or `make upload` target MUST run all quality gates before submitting
- CI/CD MUST report quality gate results in pull request checks

**Quality Gate Implementation**:
```makefile
# Example structure (not yet implemented)
.PHONY: check-quality-gates
check-quality-gates: lint idnits check-rfc2119 check-citations rfclint
	@echo "All quality gates passed"

.PHONY: upload
upload: check-quality-gates
	# Actual upload logic
```

**Rationale**: Quality gates prevent publication of non-compliant or low-quality documents. Blocking checks enforce discipline and catch errors early. This mirrors RFC publication process which has mandatory editorial checks.

**Examples**:
- **Correct**: CI fails on `idnits` errors, blocks merge
- **Incorrect**: CI warnings ignored, broken draft reaches datatracker
- **Correct**: `make upload` runs all checks first, aborts on failure
- **Incorrect**: `make upload` submits without validation

### XIII. Code-to-Spec Traceability (CODE-DERIVED SPECS)

When generating RFC specifications from code, bidirectional traceability MUST be maintained between code symbols and RFC sections.

**Rules**:
- `rfc-map.json` MUST be the authoritative traceability map
- `rfc-map.json` MUST map:
  * Code symbols (file path + symbol name) → RFC section numbers
  * RFC section numbers → code symbols (list of source locations)
- `rfc-map.json` schema MUST include:
  * Code location: `{"file": "src/parser.py", "symbol": "validate", "line": 42}`
  * RFC reference: `{"section": "3.2.1", "heading": "Validation Rules"}`
  * Relationship type: `describes`, `implements`, `references`, `example`
- All code-to-RFC generation tools MUST update `rfc-map.json` incrementally
- Impact analysis MUST use `rfc-map.json` to identify affected RFC sections when code changes
- RFC text MUST include cross-references to source code (e.g., "See `parser.py:validate()` for implementation")
- Avoid duplication: code comments and RFC text MUST NOT duplicate behavioral descriptions
- Manual curated documentation (context, rationale, examples) MUST be clearly marked as such

**Rationale**: Code-derived specifications require rigorous traceability to remain accurate as code evolves. `rfc-map.json` serves as the single source of truth for code↔RFC relationships, enabling automated impact analysis and preventing documentation drift. This approach respects that code defines behavior while RFCs document and explain it.

**rfc-map.json Schema Example**:
```json
{
  "version": "1.0.0",
  "mappings": [
    {
      "code": {"file": "src/parser.py", "symbol": "Parser.validate", "line": 42},
      "rfc": {"section": "3.2.1", "heading": "Input Validation"},
      "relationship": "implements",
      "last_synced": "2025-10-12T10:30:00Z"
    }
  ]
}
```

**Examples**:
- **Correct**: Code change triggers impact analysis via rfc-map.json, flags Section 3.2.1 for review
- **Incorrect**: Code changes without updating rfc-map.json (traceability lost)
- **Correct**: RFC section 3.2.1 says "Input validation is performed by `Parser.validate()` (src/parser.py:42)"
- **Incorrect**: RFC duplicates validation logic prose (duplication risk)

### XIV. Context Hygiene for Code Analysis (CODE-DERIVED SPECS)

Code analysis operations MUST be scoped, efficient, and non-invasive to ensure performance and security.

**Rules**:
- LSP-based harvesting MUST be the primary code analysis mechanism
- All code analysis MUST respect scoping constraints:
  * `SPECIFY_FEATURE` environment variable defines feature-specific scope
  * Glob patterns (e.g., `src/parser/**/*.py`) restrict analysis paths
  * Incremental updates process only changed files since last analysis
- Code analysis MUST NOT execute user code (static analysis only)
- Code analysis MUST use Serena MCP tools for semantic code understanding:
  * `get_symbols_overview` for file-level structure
  * `find_symbol` with `relative_path` for scoped searches
  * `search_for_pattern` with `paths_include_glob` for targeted queries
- Analysis results MUST be cached and invalidated only on relevant code changes
- On-save impact detection MUST complete in under 2 seconds (see Principle VI)
- Analysis MUST NOT modify source code (read-only operations)

**Rationale**: Analyzing entire codebases for RFC generation is prohibitively expensive and unnecessary. Scoped, incremental analysis enables real-time feedback. LSP provides language-aware semantic understanding. Static analysis (no code execution) ensures safety and reproducibility. Serena MCP tools optimize token usage and analysis performance.

**Examples**:
- **Correct**: `SPECIFY_FEATURE=parser make rfc-analyze` (scoped to parser module)
- **Incorrect**: Analyzing entire repository on every file save (performance degradation)
- **Correct**: LSP analysis via `get_symbols_overview("src/parser.py")`
- **Incorrect**: Running `exec()` on Python source to extract behavior (security risk)

### XV. Review Gates & Impact Analysis (CODE-DERIVED SPECS)

All code changes MUST trigger impact analysis to identify affected RFC sections. Review gates enforce different requirements based on branch protection level.

**Rules**:
- **Non-blocking checks** (feature branches):
  * Impact analysis runs automatically on PR creation
  * Affected RFC sections identified via `rfc-map.json`
  * Review checklist generated listing sections needing update
  * Warnings displayed but PR can merge without resolution
- **Blocking checks** (protected branches: `main`, `release/*`):
  * All quality gates MUST pass (see Principle XII)
  * Impact analysis MUST complete successfully
  * Affected RFC sections MUST be reviewed (manual checklist sign-off)
  * `rfclint` and `idnits` MUST pass without errors
  * No unresolved TODO/FIXME markers in affected sections
- Impact analysis output MUST include:
  * List of changed code symbols
  * Mapped RFC sections (via `rfc-map.json`)
  * Severity assessment (MUST update, SHOULD review, MAY ignore)
  * Generated review checklist
- All changes trigger impact analysis (no exceptions)
- Review checklist MUST be tracked in PR metadata or separate tracking file

**Rationale**: Code changes can invalidate RFC descriptions. Automated impact analysis ensures affected sections are identified early. Non-blocking checks on feature branches enable rapid development. Blocking checks on protected branches ensure spec quality. This mirrors RFC editorial process where substantive changes require review.

**Examples**:
- **Correct**: PR to feature branch shows "3 RFC sections affected" warning (non-blocking)
- **Incorrect**: Merging code change to `main` without impact analysis (blind merge)
- **Correct**: PR to `main` blocked until Section 3.2.1 review checklist signed off
- **Incorrect**: Protected branch allows merge with unresolved impact analysis warnings

### XVI. Security & Privacy for Code Analysis (CODE-DERIVED SPECS)

Code analysis operations MUST respect security and privacy constraints to protect sensitive information and prevent supply chain attacks.

**Rules**:
- Code analysis MUST be read-only (no code modification, no file writes outside designated output dirs)
- Code analysis MUST NOT execute user code (static analysis only, no `eval()`, `exec()`, subprocess execution)
- Code analysis MUST NOT make external network calls during lint/build operations
- Secrets MUST NEVER be included in generated RFC specifications:
  * API keys, passwords, tokens, credentials
  * Private keys, certificates, cryptographic secrets
  * Database connection strings with credentials
  * Internal hostnames, IP addresses, network topology
- Secret detection MUST run as pre-publication quality gate
- Secret patterns MUST be defined in `.rfc-secret-patterns` (gitignore-style syntax)
- Code analysis tools MUST run in sandboxed containers (see Principle XI)
- LSP servers MUST NOT have network access during analysis
- Generated RFCs MUST be reviewed for accidental sensitive information disclosure

**Secret Pattern Examples**:
```
# .rfc-secret-patterns
**/secrets/**
**/*.key
**/*.pem
*_token
*_secret
DATABASE_URL=*
```

**Rationale**: Code analysis operates on potentially sensitive source code. Read-only, offline, sandboxed analysis minimizes security risks. Secret detection prevents accidental credential leakage. This principle protects both the project and users of generated RFCs.

**Examples**:
- **Correct**: Code analysis runs in Docker container with no network access
- **Incorrect**: Code analysis executes arbitrary Python code (security vulnerability)
- **Correct**: Pre-publication check flags `api_key = "sk-..."` in RFC example code
- **Incorrect**: Generated RFC includes production database credentials (data leak)

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

## Definitions

### Core Terminology

**Draft Name**: The base identifier for an Internet-Draft without version number (e.g., `draft-ietf-httpbis-cache`). File naming convention: `draft-name.md` or `draft-name.xml`.

**Draft Version**: The two-digit version suffix appended to draft names for IETF submission (e.g., `draft-ietf-httpbis-cache-02`). Used in git tags and datatracker URLs.

**Editor's Copy**: The most recent HTML rendering of a draft, hosted on GitHub Pages, representing the current working state (not yet submitted to IETF).

**Makefile Target**: A named build rule in GNU Make (e.g., `txt`, `html`, `lint`) that defines dependencies and commands to produce outputs.

**xml2rfc**: The canonical IETF tool for converting RFC 7991 XML format to text, HTML, and PDF outputs. See https://xml2rfc.tools.ietf.org/

**kramdown-rfc**: Ruby gem for converting markdown source to RFC 7991 XML. Supports IETF-specific extensions. See https://github.com/cabo/kramdown-rfc2629

**idnits**: IETF validation tool that checks text drafts for formatting compliance and common errors. Required before datatracker submission.

**rfclint**: Python-based RFC style checker that validates RFC XML and text against RFC formatting rules. See https://pypi.org/project/rfclint/

**Reproducible Build**: A build process that produces bit-identical outputs given identical inputs, regardless of build environment or timestamp. Critical for archival and verification.

**Normative Language**: RFC 2119 keywords (MUST, SHOULD, MAY) used to specify requirement levels unambiguously in technical specifications.

**Quality Gate**: An automated check that MUST pass before publication or merge. Examples: lint, idnits, schema validation.

**rfc-map.json**: Authoritative JSON file mapping code symbols to RFC sections, enabling bidirectional traceability for code-derived specifications. Schema includes code location, RFC reference, relationship type, and sync timestamp.

**Code-Derived Specification**: RFC-style document generated from source code using automated analysis and curated documentation. Code is the single source of truth for behavior; the RFC describes and explains it.

**Impact Analysis**: Automated process that identifies RFC sections affected by code changes, using `rfc-map.json` for traceability. Generates review checklists and severity assessments.

**Context Hygiene**: Discipline of scoping code analysis operations to minimize performance overhead and token usage. Includes path scoping, incremental updates, and LSP-based semantic analysis.

### Code Analysis Pipeline

For code-to-spec workflows, the pipeline is:

```
Source Code (*.py, *.js, etc.)
    ↓
LSP-based Analysis (scoped paths, Serena MCP)
    ↓
rfc-map.json Update (traceability)
    ↓
Curated Documentation Merge
    ↓
kramdown-rfc2629 → RFCXML
    ↓
xml2rfc → txt/html
    ↓
Validation (rfclint, idnits)
    ↓
Impact Analysis (code change → affected sections)
    ↓
Review Gates (blocking on main branch)
```

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

**Current Version**: 1.2.0
**Ratified**: 2025-10-11
**Last Amended**: 2025-10-12

### Versioning Policy

- **MAJOR (x.0.0)**: Backward incompatible principle changes, removed requirements
- **MINOR (0.x.0)**: New principles added, material guidance expansions
- **PATCH (0.0.x)**: Clarifications, typo fixes, non-semantic edits

### Enforcement

Constitution principles are enforced through:
1. Code review checklists referencing specific principles
2. Automated linting and testing gates (Principles III, IV, VI, XII)
3. CI/CD validation against test suites (Principle II, III, XI, XII)
4. Plugin validation tooling (`claude plugin validate`)
5. Community review for template updates
6. Impact analysis and review gates (Principle XV)
7. Secret detection and security audits (Principle XVI)

**Conflict Resolution**: When principles conflict, priority order is:
1. Security & Privacy (XVI)
2. RFC Standards Compliance (II)
3. Backward Compatibility (V)
4. Makefile-First Build System (I)
5. Publication Quality Gates (XII)
6. All other principles weighted equally, resolved case-by-case

---

**Version**: 1.2.0 | **Ratified**: 2025-10-11 | **Last Amended**: 2025-10-12
