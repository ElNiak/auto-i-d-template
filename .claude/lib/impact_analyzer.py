"""
Library for analyzing code changes and RFC documentation impact.

This module provides language-agnostic impact analysis using git diff
and line tracking to determine which RFC sections need updates when code changes.
"""

import subprocess
import json
import logging
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ChangeRange:
    """Represents a range of changed lines in a file."""
    file_path: str
    start_line: int
    end_line: int
    change_type: str  # 'add', 'modify', 'delete'


@dataclass
class ImpactResult:
    """Represents the impact of code changes on RFC documentation."""
    affected_sections: List[str]  # RFC section numbers
    changed_elements: List[str]   # Code element identifiers
    severity: str  # 'MUST_UPDATE', 'SHOULD_REVIEW', 'MAY_IGNORE'
    confidence: float  # 0.0 to 1.0
    description: str


@dataclass
class SectionImpact:
    """Detailed impact on a specific RFC section."""
    section_number: str
    section_heading: str
    affected_code_elements: List[str]
    change_summary: str
    severity: str


def get_changed_files(
    base_ref: str = "HEAD~1",
    target_ref: str = "HEAD",
    repo_root: Optional[str] = None
) -> List[str]:
    """
    Use git diff to find modified files between two references.

    Args:
        base_ref: Base git reference (default: previous commit)
        target_ref: Target git reference (default: current HEAD)
        repo_root: Repository root path (default: current directory)

    Returns:
        List of changed file paths relative to repo root

    Examples:
        >>> files = get_changed_files()
        >>> 'src/main.py' in files
        True
    """
    try:
        cmd = [
            "git", "diff",
            "--name-only",
            base_ref,
            target_ref
        ]

        if repo_root:
            result = subprocess.run(
                cmd,
                cwd=repo_root,
                capture_output=True,
                text=True,
                timeout=10
            )
        else:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

        if result.returncode != 0:
            logger.error(f"Git diff failed: {result.stderr}")
            return []

        files = [line.strip() for line in result.stdout.split('\n') if line.strip()]
        logger.info(f"Found {len(files)} changed files")
        return files

    except subprocess.TimeoutExpired:
        logger.error("Git diff command timed out")
        return []
    except Exception as e:
        logger.error(f"Error getting changed files: {e}")
        return []


def get_changed_lines(
    file_path: str,
    base_ref: str = "HEAD~1",
    target_ref: str = "HEAD",
    repo_root: Optional[str] = None
) -> List[ChangeRange]:
    """
    Extract line ranges from git diff output for a specific file.

    Uses git diff --unified=0 to get precise line changes without context.

    Args:
        file_path: Path to file relative to repo root
        base_ref: Base git reference
        target_ref: Target git reference
        repo_root: Repository root path

    Returns:
        List of ChangeRange objects with changed line information

    Examples:
        >>> ranges = get_changed_lines('src/main.py')
        >>> ranges[0].start_line
        42
    """
    try:
        cmd = [
            "git", "diff",
            "--unified=0",  # No context lines
            base_ref,
            target_ref,
            "--",
            file_path
        ]

        if repo_root:
            result = subprocess.run(
                cmd,
                cwd=repo_root,
                capture_output=True,
                text=True,
                timeout=10
            )
        else:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

        if result.returncode != 0:
            logger.error(f"Git diff failed for {file_path}: {result.stderr}")
            return []

        # Parse diff output
        changes = []
        for line in result.stdout.split('\n'):
            # Look for @@ -old_start,old_count +new_start,new_count @@ format
            if line.startswith('@@'):
                # Extract line numbers
                # Format: @@ -10,5 +10,7 @@
                import re
                match = re.search(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', line)
                if match:
                    old_start = int(match.group(1))
                    old_count = int(match.group(2)) if match.group(2) else 1
                    new_start = int(match.group(3))
                    new_count = int(match.group(4)) if match.group(4) else 1

                    # Determine change type
                    if old_count == 0:
                        change_type = 'add'
                        start_line = new_start
                        end_line = new_start + new_count - 1
                    elif new_count == 0:
                        change_type = 'delete'
                        start_line = old_start
                        end_line = old_start + old_count - 1
                    else:
                        change_type = 'modify'
                        start_line = new_start
                        end_line = new_start + new_count - 1

                    changes.append(ChangeRange(
                        file_path=file_path,
                        start_line=start_line,
                        end_line=end_line,
                        change_type=change_type
                    ))

        logger.info(f"Found {len(changes)} change ranges in {file_path}")
        return changes

    except subprocess.TimeoutExpired:
        logger.error(f"Git diff timed out for {file_path}")
        return []
    except Exception as e:
        logger.error(f"Error parsing diff for {file_path}: {e}")
        return []


def cross_reference_changes(
    changes: List[ChangeRange],
    rfc_map: Dict
) -> Dict[str, List[str]]:
    """
    Match changed line ranges to rfc-map.json to find affected RFC sections.

    Args:
        changes: List of ChangeRange objects
        rfc_map: Parsed rfc-map.json dictionary

    Returns:
        Dictionary mapping RFC section numbers to lists of affected code elements

    Logic:
        For each changed line range:
        1. Find mappings in rfc-map.json with matching file path
        2. Check if changed lines overlap with mapping line numbers
        3. Collect affected RFC sections
    """
    affected_sections = {}

    if 'mappings' not in rfc_map:
        logger.warning("No mappings found in rfc-map.json")
        return affected_sections

    for change in changes:
        for mapping in rfc_map['mappings']:
            code_info = mapping.get('code', {})
            rfc_info = mapping.get('rfc', {})

            # Check if file matches
            if code_info.get('file') != change.file_path:
                continue

            # Check if line ranges overlap
            mapped_line = code_info.get('line', 0)
            if change.start_line <= mapped_line <= change.end_line:
                section = rfc_info.get('section', 'unknown')
                code_symbol = code_info.get('symbol', 'unknown')

                if section not in affected_sections:
                    affected_sections[section] = []

                if code_symbol not in affected_sections[section]:
                    affected_sections[section].append(code_symbol)

    logger.info(f"Found {len(affected_sections)} affected RFC sections")
    return affected_sections


def calculate_impact_severity(
    section_number: str,
    change_types: Set[str],
    section_type: Optional[str] = None
) -> str:
    """
    Determine update priority based on section type and change type.

    Args:
        section_number: RFC section number
        change_types: Set of change types ('add', 'modify', 'delete')
        section_type: Type of section ('interfaces', 'behavior', etc.)

    Returns:
        Severity level: 'MUST_UPDATE', 'SHOULD_REVIEW', 'MAY_IGNORE'

    Rules:
        - Interface changes (delete/modify) → MUST_UPDATE
        - Interface additions → SHOULD_REVIEW
        - Behavior changes → SHOULD_REVIEW
        - Internal implementation → MAY_IGNORE
    """
    # Determine section type from number if not provided
    if not section_type:
        # Common RFC section numbering conventions
        if section_number.startswith('3'):
            section_type = 'interfaces'
        elif section_number.startswith('4'):
            section_type = 'behavior'
        elif section_number.startswith('2'):
            section_type = 'terminology'
        else:
            section_type = 'unknown'

    # Apply severity rules
    if section_type == 'interfaces':
        if 'delete' in change_types or 'modify' in change_types:
            return 'MUST_UPDATE'
        elif 'add' in change_types:
            return 'SHOULD_REVIEW'

    if section_type == 'behavior':
        if change_types:
            return 'SHOULD_REVIEW'

    if section_type == 'terminology':
        if 'delete' in change_types:
            return 'MUST_UPDATE'
        elif 'add' in change_types or 'modify' in change_types:
            return 'SHOULD_REVIEW'

    return 'MAY_IGNORE'


def detect_affected_sections(
    file_paths: Optional[List[str]] = None,
    rfc_map_path: str = "docs/rfc-map.json",
    base_ref: str = "HEAD~1",
    target_ref: str = "HEAD"
) -> List[SectionImpact]:
    """
    Main function: Analyze code changes and determine RFC sections needing updates.

    Args:
        file_paths: Specific files to analyze (default: all changed files)
        rfc_map_path: Path to rfc-map.json
        base_ref: Base git reference for comparison
        target_ref: Target git reference for comparison

    Returns:
        List of SectionImpact objects with detailed impact analysis

    This is the primary entry point for hooks and commands.
    """
    # Load rfc-map.json
    try:
        with open(rfc_map_path, 'r') as f:
            rfc_map = json.load(f)
    except FileNotFoundError:
        logger.error(f"rfc-map.json not found at {rfc_map_path}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in rfc-map.json: {e}")
        return []

    # Get changed files
    if file_paths is None:
        file_paths = get_changed_files(base_ref, target_ref)

    if not file_paths:
        logger.info("No changed files detected")
        return []

    # Analyze each file
    all_changes = []
    for file_path in file_paths:
        changes = get_changed_lines(file_path, base_ref, target_ref)
        all_changes.extend(changes)

    if not all_changes:
        logger.info("No line-level changes detected")
        return []

    # Cross-reference with rfc-map.json
    affected = cross_reference_changes(all_changes, rfc_map)

    # Build detailed impact results
    impacts = []
    for section_num, code_elements in affected.items():
        # Determine change types for this section
        change_types = set()
        for change in all_changes:
            for elem in code_elements:
                # Simple heuristic: if any changed code affects this element
                change_types.add(change.change_type)

        severity = calculate_impact_severity(section_num, change_types)

        # Find section heading from rfc-map
        section_heading = "Unknown Section"
        for mapping in rfc_map.get('mappings', []):
            if mapping.get('rfc', {}).get('section') == section_num:
                section_heading = mapping.get('rfc', {}).get('heading', section_heading)
                break

        impacts.append(SectionImpact(
            section_number=section_num,
            section_heading=section_heading,
            affected_code_elements=code_elements,
            change_summary=f"Changed {len(code_elements)} code elements",
            severity=severity
        ))

    # Sort by severity
    severity_order = {'MUST_UPDATE': 0, 'SHOULD_REVIEW': 1, 'MAY_IGNORE': 2}
    impacts.sort(key=lambda x: severity_order.get(x.severity, 3))

    logger.info(f"Impact analysis complete: {len(impacts)} sections affected")
    return impacts


def format_impact_report(impacts: List[SectionImpact]) -> str:
    """
    Format impact analysis results as markdown for display.

    Args:
        impacts: List of SectionImpact objects

    Returns:
        Markdown-formatted report string
    """
    if not impacts:
        return "✅ No RFC documentation impact detected."

    lines = ["# RFC Documentation Impact Report\n"]

    # Group by severity
    for severity in ['MUST_UPDATE', 'SHOULD_REVIEW', 'MAY_IGNORE']:
        severity_impacts = [i for i in impacts if i.severity == severity]
        if not severity_impacts:
            continue

        # Severity header
        if severity == 'MUST_UPDATE':
            lines.append("## 🔴 Critical Updates Required\n")
        elif severity == 'SHOULD_REVIEW':
            lines.append("## 🟡 Review Recommended\n")
        else:
            lines.append("## 🟢 Minor Changes\n")

        for impact in severity_impacts:
            lines.append(f"### Section {impact.section_number}: {impact.section_heading}\n")
            lines.append(f"**Affected Code Elements**: {', '.join(impact.affected_code_elements)}\n")
            lines.append(f"**Summary**: {impact.change_summary}\n")
            lines.append("")

    lines.append("\n---\n")
    lines.append(f"**Total Sections Affected**: {len(impacts)}\n")

    return '\n'.join(lines)


# Utility function for testing and CLI usage
def _example_usage():
    """Example usage of impact_analyzer module."""
    import sys

    # Detect impacts
    impacts = detect_affected_sections()

    if impacts:
        report = format_impact_report(impacts)
        print(report)
        sys.exit(1 if any(i.severity == 'MUST_UPDATE' for i in impacts) else 0)
    else:
        print("✅ No RFC documentation updates needed")
        sys.exit(0)


if __name__ == "__main__":
    # Setup logging for standalone execution
    logging.basicConfig(level=logging.INFO)
    _example_usage()
