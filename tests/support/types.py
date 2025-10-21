"""
Type definitions for BDD test infrastructure.

This module provides TypedDict definitions and type aliases for common data structures
used throughout the test suite, improving type safety and IDE support.
"""

from typing import TypedDict, List, Optional, Dict, Any, Literal
from dataclasses import dataclass, field


# ============================================================================
# Command Execution Types
# ============================================================================

@dataclass
class CommandResult:
    """
    Result from executing a slash command.

    Attributes:
        exit_code: Command exit status (0=success, 1=error, 2=prerequisites not met)
        output: List of output messages
        files_created: List of absolute paths to files created
        files_modified: List of absolute paths to files modified
        errors: List of error messages
        warnings: List of warning messages
    """
    exit_code: int
    output: List[str] = field(default_factory=list)
    files_created: List[str] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


# ============================================================================
# Hook Execution Types
# ============================================================================

@dataclass
class HookResult:
    """
    Result from executing a Claude Code hook.

    Attributes:
        exit_code: Hook exit status (0=success, non-zero=error/timeout)
        stdout: Raw stdout from hook script
        stderr: Raw stderr from hook script
        response: Parsed JSON response from hook (if valid JSON)
        execution_time: Time taken to execute hook in seconds
        errors: List of error messages
    """
    exit_code: int
    stdout: str
    stderr: str
    response: Optional[Dict[str, Any]] = None
    execution_time: float = 0.0
    errors: List[str] = field(default_factory=list)


class HookResponse(TypedDict, total=False):
    """
    Standard response structure from Claude Code hooks.

    Keys:
        block: Whether to block tool execution (PreToolUse only)
        message: Human-readable message to display
        suggestion: Suggested action/command for user
        timing_ms: Hook execution time in milliseconds
        metadata: Optional additional metadata
    """
    block: bool
    message: str
    suggestion: str
    timing_ms: int
    metadata: Dict[str, Any]


# ============================================================================
# RFC Document Types
# ============================================================================

class RFCFrontmatter(TypedDict, total=False):
    """
    Kramdown-rfc frontmatter structure.

    Keys:
        docname: RFC document name (e.g., "draft-myproject-00")
        title: RFC title
        abbrev: Abbreviated title
        category: RFC category (std, bcp, info, exp, historic)
        ipr: IPR disclosure (e.g., "trust200902")
        workgroup: IETF working group
        keyword: List of keywords
        author: List of author dictionaries
        date: Publication date
    """
    docname: str
    title: str
    abbrev: str
    category: Literal['std', 'bcp', 'info', 'exp', 'historic']
    ipr: str
    workgroup: str
    keyword: List[str]
    author: List[Dict[str, str]]
    date: str


class RFCSection(TypedDict):
    """
    RFC document section structure.

    Keys:
        number: Section number (e.g., "3.1")
        heading: Section heading
        content: Section markdown content
        subsections: List of subsection dictionaries
    """
    number: str
    heading: str
    content: str
    subsections: List['RFCSection']


class RFCDocument(TypedDict):
    """
    Complete RFC document structure.

    Keys:
        frontmatter: YAML frontmatter metadata
        sections: List of top-level RFC sections
        raw_content: Full markdown content
    """
    frontmatter: RFCFrontmatter
    sections: List[RFCSection]
    raw_content: str


# ============================================================================
# RFC Map (Traceability) Types
# ============================================================================

class CodeElement(TypedDict):
    """
    Code element reference in rfc-map.json.

    Keys:
        file: Relative path to source file
        symbol: Symbol name (class, function, etc.)
        line: Line number where symbol is defined
        end_line: Optional ending line number
        checksum: Optional content checksum for staleness detection
    """
    file: str
    symbol: str
    line: int
    end_line: Optional[int]
    checksum: Optional[str]


class RFCReference(TypedDict):
    """
    RFC section reference in rfc-map.json.

    Keys:
        section: Section number (e.g., "3.1")
        heading: Section heading text
        anchor: Optional kramdown anchor ID
    """
    section: str
    heading: str
    anchor: Optional[str]


RelationshipType = Literal['describes', 'implements', 'references', 'example']


class RFCMapping(TypedDict):
    """
    Single code-to-RFC mapping entry.

    Keys:
        code: Code element information
        rfc: RFC section information
        relationship: Type of relationship between code and RFC
        confidence: Confidence score (0.0-1.0) of mapping accuracy
        last_synced: ISO 8601 timestamp of last synchronization
        notes: Optional human-readable notes
    """
    code: CodeElement
    rfc: RFCReference
    relationship: RelationshipType
    confidence: float
    last_synced: str
    notes: Optional[str]


class RFCMap(TypedDict):
    """
    Complete rfc-map.json structure.

    Keys:
        version: Schema version (e.g., "1.0.0")
        rfc_file: Path to RFC markdown file
        generated_at: ISO 8601 timestamp of generation
        mappings: List of code-to-RFC mappings
    """
    version: str
    rfc_file: str
    generated_at: str
    mappings: List[RFCMapping]


# ============================================================================
# Preserve Block Types (for /rfc-update)
# ============================================================================

class PreserveBlock(TypedDict):
    """
    @preserve block detected in RFC document.

    Keys:
        id: Optional block identifier
        start_line: Line number of @preserve-start marker
        end_line: Line number of @preserve-end marker
        content: Raw content between markers
        section: RFC section containing the block
    """
    id: Optional[str]
    start_line: int
    end_line: int
    content: str
    section: str


SeverityLevel = Literal['ERROR', 'WARNING', 'INFO']


class PreserveConflict(TypedDict):
    """
    Conflict detected with preserve blocks.

    Keys:
        severity: Conflict severity level
        description: Human-readable description
        block_id: ID of affected preserve block
        recommendation: Suggested resolution
    """
    severity: SeverityLevel
    description: str
    block_id: Optional[str]
    recommendation: str


# ============================================================================
# Impact Analysis Types
# ============================================================================

class ImpactReport(TypedDict):
    """
    Impact analysis report for code changes.

    Keys:
        section_number: Affected RFC section number
        section_heading: Section heading
        affected_code_elements: List of changed code elements
        severity: Change severity (MUST_REVIEW, SHOULD_REVIEW, MAY_REVIEW)
        change_summary: Description of changes
        recommended_actions: List of recommended actions
    """
    section_number: str
    section_heading: str
    affected_code_elements: List[str]
    severity: Literal['MUST_REVIEW', 'SHOULD_REVIEW', 'MAY_REVIEW']
    change_summary: str
    recommended_actions: List[str]


# ============================================================================
# Agent Execution Types (for multi-agent workflows)
# ============================================================================

AgentType = Literal['parser', 'analyzer', 'formatter', 'validator']


class AgentInput(TypedDict, total=False):
    """
    Input data for specialized agent execution.

    Keys:
        agent_type: Type of agent to spawn
        paths: List of paths to analyze
        rfc_file: Existing RFC file (for updates)
        sections: List of section filters
        options: Additional agent-specific options
    """
    agent_type: AgentType
    paths: List[str]
    rfc_file: Optional[str]
    sections: Optional[List[str]]
    options: Dict[str, Any]


class AgentOutput(TypedDict):
    """
    Output data from specialized agent execution.

    Keys:
        agent_type: Type of agent that executed
        status: Execution status (success, error, partial)
        data: Agent-specific output data
        warnings: List of warning messages
        errors: List of error messages
        execution_time_ms: Time taken in milliseconds
    """
    agent_type: AgentType
    status: Literal['success', 'error', 'partial']
    data: Dict[str, Any]
    warnings: List[str]
    errors: List[str]
    execution_time_ms: int


# ============================================================================
# Test Fixture Types
# ============================================================================

class TestCodeFile(TypedDict):
    """
    Test code file fixture structure.

    Keys:
        path: Relative path to file
        language: Programming language
        content: File content
        symbols: List of symbol names in the file
    """
    path: str
    language: str
    content: str
    symbols: List[str]


class TestProject(TypedDict):
    """
    Test project fixture structure.

    Keys:
        name: Project name
        root_dir: Absolute path to project root
        code_files: List of code file fixtures
        has_rfc: Whether RFC documentation exists
        has_rfc_map: Whether rfc-map.json exists
    """
    name: str
    root_dir: str
    code_files: List[TestCodeFile]
    has_rfc: bool
    has_rfc_map: bool


# ============================================================================
# Type Aliases
# ============================================================================

# Path types
FilePath = str  # Absolute or relative file path
DirectoryPath = str  # Absolute or relative directory path

# Timestamp types
ISOTimestamp = str  # ISO 8601 format: "2025-10-15T12:34:56Z"

# Version types
SemanticVersion = str  # Semantic versioning: "1.0.0"

# Git types
GitCommitHash = str  # Full or short git commit hash

# Command types
SlashCommand = str  # Slash command string: "/rfc-generate src/"
