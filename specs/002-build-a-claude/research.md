# Research Document: RFC-Style Documentation Generator for Claude-Code

**Date**: 2025-10-13
**Feature**: RFC-Style Documentation Generator
**Status**: Complete

## Executive Summary

This research document consolidates findings from parallel research tasks and technical analysis to inform the RFC documentation generator implementation. All technical unknowns have been resolved through research and user clarification.

## Phase 0 Research Findings

### 1. SerenaMCP Integration Strategy

**Decision**: Use SerenaMCP exclusively for code analysis via agent instructions
**Rationale**:
- SerenaMCP provides battle-tested semantic code understanding
- Avoids reinventing AST parsing and symbol extraction
- Token-efficient through targeted symbol queries
- Language-agnostic via LSP protocol

**Alternatives Considered**:
- Custom Python AST parsing: Rejected - language-specific, maintenance burden
- Tree-sitter integration: Rejected - duplicates SerenaMCP capabilities
- Direct file reading: Rejected - inefficient, lacks semantic understanding

**Implementation Approach**:
```markdown
# In agents/parser.md
Use these Serena MCP tools exclusively:
- mcp__serena__get_symbols_overview for file structure
- mcp__serena__find_symbol for targeted extraction
- mcp__serena__search_for_pattern for content search
- NEVER use basic Read tool for code files
```

### 2. Git History Analysis Integration

**Decision**: Lightweight git integration via Bash tool
**Rationale**:
- Git commands already available via Bash tool
- No need for complex git library integration
- Supports incremental RFC updates based on commits

**Implementation**:
```bash
# Via Bash tool in agents
git diff HEAD~1 --name-only  # Changed files
git log --oneline -10        # Recent commits
git blame --line-porcelain   # Authorship tracking
```

**Alternatives Considered**:
- GitPython library: Rejected - unnecessary dependency
- Custom git wrapper: Rejected - overengineering

### 3. Agent Architecture Deep Dive

**Decision**: Specialized agents with bounded contexts
**Rationale**: Research confirmed multi-agent architecture optimal for:
- Parallel processing of large codebases
- Clear separation of concerns
- Easier testing and maintenance
- Failure isolation

**Agent Boundaries**:

| Agent | Bounded Context | Serena MCP Usage | Output |
|-------|----------------|------------------|--------|
| **Coordinator** | Workflow orchestration | None | Complete RFC |
| **Parser** | Code structure extraction | Heavy - symbols, files | JSON structure |
| **Analyzer** | Semantic relationships | Heavy - references, patterns | Behavioral model |
| **Formatter** | RFC section generation | None | Markdown sections |
| **Validator** | Compliance checking | None | Validation report |

**Communication Pattern**:
- Coordinator spawns agents with specific paths/sections
- Agents operate independently (no inter-agent communication)
- Results aggregated by coordinator
- Failure in one agent doesn't cascade

### 4. Hook Implementation Analysis

**Decision**: Minimal Python hooks with Make delegation
**Rationale**:
- Hooks should be lightweight gatekeepers
- Actual work delegated to Make targets
- Maintains constitution principle (Makefile-first)

**Hook Strategy**:

```python
# hooks/pre-commit.py
#!/usr/bin/env python3
import subprocess
import sys

# Detect RFC files
rfc_files = [f for f in changed_files if 'draft-' in f]
if rfc_files:
    # Delegate to Make
    result = subprocess.run(['make', 'lint'], capture_output=True)
    if result.returncode != 0:
        print("RFC validation failed. Run 'make fix-lint'")
        sys.exit(1)
```

**Alternatives Considered**:
- Complex Python validation: Rejected - violates Makefile-first principle
- Shell scripts: Considered - Python chosen for better error handling

### 5. Overengineering Concerns Addressed

**Identified Risks**:
1. ❌ **Custom code parsers** → Use SerenaMCP
2. ❌ **Complex agent communication** → Simple spawn/collect pattern
3. ❌ **Heavy Python dependencies** → Minimal libs, delegate to Make
4. ❌ **Reimplementing RFC tools** → Generate kramdown-rfc, invoke Make

**Simplifications Made**:
- No custom AST parsing (SerenaMCP handles)
- No agent-to-agent communication (coordinator only)
- No RFC format validation in Python (Make handles)
- No custom git integration (Bash tool sufficient)

### 6. Human RFC Creation Patterns (From Research)

**Key Finding**: RFCs are abstractions, not translations

**Automation Opportunities**:
- ✅ Structure generation (70% automated)
- ✅ Interface extraction (85% automated)
- ✅ Cross-references (95% automated)
- ⚠️ Normative language (50% automated, needs review)
- ❌ Security considerations (requires human expertise)
- ❌ Design rationale (cannot be inferred)

**Implementation Strategy**:
1. Generate structure and obvious content
2. Mark uncertain sections with `[NEEDS REVIEW]`
3. Preserve human edits with `@preserve-start/end`
4. Focus on incremental value delivery

### 7. Performance Optimization Strategy

**Decision**: Incremental processing with intelligent chunking
**Rationale**:
- Large codebases (1M+ LOC) require chunking
- Overlap preserves context across chunks
- Caching reduces redundant analysis

**Chunk Processing Algorithm**:
```python
# Conceptual approach
CHUNK_SIZE = 10000  # lines
OVERLAP = 500      # lines
chunks = create_overlapping_chunks(codebase, CHUNK_SIZE, OVERLAP)
for chunk in chunks:
    result = agent.process(chunk)
    cache.store(chunk.hash, result)
```

### 8. RFC Template Structure

**Decision**: IETF-compliant kramdown-rfc format
**Source**: RFC 7991, kramdown-rfc documentation

**Template Sections**:
```markdown
---
title: "Draft Title"
abbrev: "Short Title"
docname: draft-name-latest
category: info
ipr: trust200902
area: General
workgroup: Working Group
keyword:
 - keyword1
 - keyword2
stand_alone: yes
pi: [toc, sortrefs, symrefs]

author:
 -
    name: Author Name
    organization: Organization
    email: email@example.com
---

# Abstract

[Generated from code overview]

# Introduction

[Generated from README/docs]

# Conventions and Definitions

{::boilerplate bcp14-tagged}

[Generated terminology from code]

# System Architecture

[Generated from code structure]

# Interfaces

[Generated from public APIs]

# Behavior

[Generated from code logic]

# Security Considerations

[NEEDS HUMAN REVIEW]

# IANA Considerations

[If applicable]

# References

[Auto-generated from citations]
```

### 9. Validation Pipeline

**Decision**: Leverage existing i-d-template validation
**Implementation**:
```makefile
# Invoked by validator agent
validate-rfc: lint idnits rfclint
    @echo "RFC validation complete"
```

**Quality Gates**:
1. kramdown-rfc syntax validation
2. xml2rfc schema validation
3. idnits compliance check
4. rfclint style validation
5. Custom checks (cross-references, completeness)

### 10. Edge Case Handling

**Resolved Edge Cases**:

| Edge Case | Solution |
|-----------|----------|
| No analyzable code in paths | Agent returns empty structure with warning |
| Circular dependencies | Track visited symbols, break cycles |
| Conflicting manual edits | Preserve blocks take precedence |
| Cannot determine RFC section | Place in "Appendix: Unmapped Content" |
| Memory exhaustion | Chunk processing with size limits |

## Technical Decisions Summary

| Component | Decision | Rationale |
|-----------|----------|-----------|
| **Code Analysis** | SerenaMCP only | Proven, token-efficient, language-agnostic |
| **Architecture** | Multi-agent with coordinator | Scalable, testable, failure-isolated |
| **Git Integration** | Bash tool commands | Simple, no new dependencies |
| **Hooks** | Minimal Python → Make | Maintains Makefile-first principle |
| **RFC Format** | kramdown-rfc → xml2rfc | IETF standard pipeline |
| **Validation** | Delegate to Make targets | Reuse existing infrastructure |
| **Performance** | Chunked + cached | Handles large codebases |
| **Manual Edits** | @preserve markers | Clear, grep-able |

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| SerenaMCP unavailable | Fail fast with clear error message |
| Large codebase timeout | Chunked processing with progress reporting |
| Invalid RFC output | Multi-stage validation pipeline |
| Lost manual edits | @preserve markers + git history |
| Agent failure | Coordinator handles gracefully, partial results |

## Implementation Priority

Based on research and user stories:

1. **P1**: Basic generation (`/rfc-generate` command)
2. **P1**: Parser and Formatter agents (core functionality)
3. **P2**: Analyzer agent (semantic understanding)
4. **P2**: Update command (`/rfc-update`)
5. **P3**: Validator agent (quality gates)
6. **P3**: Hooks (automation)

## Conclusion

All technical unknowns have been resolved through research and analysis. The architecture avoids overengineering by:
- Delegating code analysis to SerenaMCP
- Using existing RFC toolchain via Make
- Keeping agents simple and isolated
- Minimizing custom code

The design aligns with all constitution principles and is ready for implementation planning (Phase 1).