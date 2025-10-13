# Implementation Plan: RFC-Style Documentation Generator for Claude-Code

**Branch**: `002-build-a-claude` | **Date**: 2025-10-13 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-build-a-claude/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Build a Claude-Code plugin that generates and maintains RFC-style documentation from source code using specialized agents with Serena MCP for semantic analysis. The system uses slash commands to spawn coordinated agents (parser, analyzer, formatter, validator) that leverage existing MCP tools for code intelligence, producing IETF-compliant documentation with cross-references, incremental updates, and preservation of manual edits.

## Technical Context

**Language/Version**: Python 3.11+ for hooks, Bash for Make integration, Markdown for agent instructions
**Primary Dependencies**: Serena MCP (semantic analysis), kramdown-rfc (RFC generation), xml2rfc (validation), GNU Make (build orchestration)
**Storage**: JSON for rfc-map.json traceability, Markdown files for RFC drafts, Memory files for codebase context
**Testing**: Behave (BDD tests), Integration tests with i-d-template repository, Validation with idnits/rfclint
**Target Platform**: Claude-Code CLI environment (macOS/Linux), GitHub Actions CI/CD
**Project Type**: Claude-Code plugin (single project structure)
**Performance Goals**: Initial: 10K lines/2min, 100K/20min, 1M/60min; Incremental: <10min any size; On-save impact: <2sec
**Constraints**: Read-only code analysis, No execution of user code, Preserve manual edits, Token-efficient via Serena MCP
**Scale/Scope**: Handle 1M+ LOC codebases, Multiple specialized agents, Cross-referenced RFC sections

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Compliance Assessment

**✅ PASS - Principle I (Makefile-First Build System)**
- Plugin invokes existing Make targets (`make txt`, `make html`, `make lint`)
- No reimplementation of build logic
- Generates kramdown-rfc markdown that feeds into existing pipeline

**✅ PASS - Principle II (RFC Standards Compliance)**
- Generates RFC 7991 compliant XML via kramdown-rfc
- Integrates idnits and rfclint validation
- Follows IETF formatting conventions

**✅ PASS - Principle III (Test-Driven Development)**
- Integration tests using i-d-template as test subject
- BDD tests with Behave framework
- Validation against real IETF repositories

**✅ PASS - Principle VI (Performance & Resource Efficiency)**
- Meets performance targets via Serena MCP optimization
- Incremental processing with overlap
- Caching and scoped analysis

**✅ PASS - Principle XIII (Code-to-Spec Traceability)**
- Implements rfc-map.json for bidirectional mapping
- Maintains code symbol ↔ RFC section relationships
- Enables impact analysis

**✅ PASS - Principle XIV (Context Hygiene)**
- Uses Serena MCP for semantic analysis (not custom scripts)
- Scoped, incremental processing
- Read-only operations

**✅ PASS - Principle XVI (Security & Privacy)**
- No code execution (static analysis only)
- Sandboxed operations
- Secret detection patterns

**✅ PASS - Serena MCP Tool Usage Guidelines**
- Agents instructed to use Serena tools exclusively
- No custom parsing scripts
- Follows prescribed usage patterns

### Gate Status: **APPROVED TO PROCEED**

## Project Structure

### Documentation (this feature)

```
specs/002-build-a-claude/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output - COMPLETE
├── data-model.md        # Phase 1 output - COMPLETE
├── quickstart.md        # Phase 1 output - COMPLETE
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```
.claude/
├── plugin.json              # Plugin manifest with metadata
├── marketplace.json         # Claude marketplace distribution config
├── commands/
│   ├── rfc-generate.md      # Primary slash command for RFC generation
│   ├── rfc-update.md        # Update existing RFC Documents
│   ├── rfc-validate.md      # Validate RFC compliance
│   └── rfc-analyze-impact.md # Deep semantic impact analysis via Serena MCP
├── agents/
│   ├── coordinator.md       # Orchestrates workflow across agents
│   ├── parser.md           # Extracts code structure via Serena MCP
│   ├── analyzer.md         # Semantic analysis via Serena MCP
│   ├── formatter.md        # Generates RFC sections in kramdown-rfc
│   └── validator.md        # IETF compliance checking
├── hooks/
│   ├── pre_tool_validate.py      # PreToolUse: Validate RFC cross-refs before Write|Edit
│   ├── pre_bash_enforce.py       # PreToolUse: Enforce Make target usage for Bash
│   ├── post_tool_sync.py         # PostToolUse: Sync rfc-map.json after Write|Edit|Bash
│   ├── user_intent_detect.py     # UserPromptSubmit: Load RFC context on intent
│   └── session_start_check.py    # SessionStart: Check for stale documentation
├── lib/
│   ├── rfc_mapper.py             # Manages rfc-map.json traceability
│   ├── preserve_edits.py         # Handles @preserve-start/end markers
│   ├── impact_analyzer.py        # Analyzes code changes (git diff + line tracking)
│   ├── reviewer_guidance.py      # Generates documentation impact reports
│   └── hook_utils.py             # Shared utilities for hook scripts
└── templates/
    ├── rfc-skeleton.md     # IETF RFC template structure
    └── sections/          # Individual section templates
        ├── terminology.md
        ├── interfaces.md
        └── behavior.md

tests/
├── features/              # BDD test scenarios (outside .claude/)
│   ├── generate.feature
│   ├── update.feature
│   └── validate.feature
├── steps/                # Test step implementations
└── fixtures/            # Test codebases for validation

docs/
├── generated/           # Generated RFC documents go here
│   └── draft-*.md      # RFC drafts in kramdown-rfc format
└── rfc-map.json        # Traceability mapping (code ↔ RFC sections)
```

**Structure Decision**: Claude-Code plugin structure in `.claude/` directory following official conventions. All code analysis delegated to Serena MCP (no custom parsing), with agents providing orchestration and RFC formatting. Integration with i-d-template via Make targets. Tests remain outside `.claude/` as they're for development, not runtime.

## Complexity Tracking

*No violations - all constitution principles satisfied*

## Design Notes

### Why No API Contracts

This is a Claude-Code plugin that uses:
- **Agent spawning** via Task tool (not HTTP APIs)
- **Markdown instruction files** (not REST services)
- **Internal result passing** (not API calls)

Therefore, formal OpenAPI contracts would be overengineering. Instead:
- Agent instructions define inputs/outputs in markdown
- Data model documents entities for clarity
- Quickstart guide shows practical usage

## Phase Summary

### Phase 0: Research (COMPLETE)
- Resolved all technical unknowns
- Analyzed SerenaMCP integration
- Identified automation opportunities
- Addressed overengineering concerns

### Phase 1: Design (COMPLETE)
- Created data model with all entities
- Generated quickstart guide for users
- Updated agent context for Claude
- Validated against constitution

### Next Steps
- Run `/speckit.tasks` to generate ordered task list
- Begin implementation following tasks.md
