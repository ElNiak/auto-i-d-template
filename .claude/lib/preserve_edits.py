"""
Library for handling @preserve-start/end markers in RFC documents.

This module provides functions to extract, validate, and merge manual edits
marked with @preserve blocks in generated RFC documentation.
"""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class PreserveBlock:
    """Represents a manually-edited section marked for preservation."""
    start_line: int
    end_line: int
    content: str
    marker_id: Optional[str] = None  # Optional identifier in marker


@dataclass
class ConflictReport:
    """Represents a conflict between preserve blocks or generated content."""
    conflict_type: str  # 'overlapping_blocks', 'content_overlap'
    severity: str  # 'ERROR', 'WARNING'
    blocks_involved: List[PreserveBlock]
    description: str
    suggested_resolution: str


def extract_preserve_blocks(content: str) -> List[PreserveBlock]:
    """
    Parse document for @preserve-start/@preserve-end markers.

    Args:
        content: RFC document content as string

    Returns:
        List of PreserveBlock objects with extracted content

    Examples:
        >>> content = '''
        ... Some text
        ... @preserve-start
        ... This is manual content
        ... @preserve-end
        ... More text
        ... '''
        >>> blocks = extract_preserve_blocks(content)
        >>> len(blocks)
        1
    """
    blocks = []
    lines = content.split('\n')

    in_preserve = False
    current_block_start = -1
    current_content = []
    current_marker_id = None

    for line_num, line in enumerate(lines, start=1):
        # Check for @preserve-start with optional ID
        start_match = re.match(r'^\s*@preserve-start(?:\s+id:(\S+))?\s*$', line.strip())
        if start_match:
            if in_preserve:
                logger.warning(f"Nested @preserve-start at line {line_num}, treating as error")
            in_preserve = True
            current_block_start = line_num
            current_marker_id = start_match.group(1)
            current_content = []
            continue

        # Check for @preserve-end
        if re.match(r'^\s*@preserve-end\s*$', line.strip()):
            if not in_preserve:
                logger.warning(f"@preserve-end without matching start at line {line_num}")
                continue

            # Create block
            block = PreserveBlock(
                start_line=current_block_start,
                end_line=line_num,
                content='\n'.join(current_content),
                marker_id=current_marker_id
            )
            blocks.append(block)

            # Reset state
            in_preserve = False
            current_block_start = -1
            current_content = []
            current_marker_id = None
            continue

        # Collect content inside preserve block
        if in_preserve:
            current_content.append(line)

    # Check for unclosed block
    if in_preserve:
        logger.error(f"Unclosed @preserve-start at line {current_block_start}")

    return blocks


def validate_preserve_blocks(blocks: List[PreserveBlock]) -> List[ConflictReport]:
    """
    Check for overlaps and conflicts in preserve blocks.

    Args:
        blocks: List of PreserveBlock objects to validate

    Returns:
        List of ConflictReport objects (empty if no conflicts)

    Conflict types:
        - Overlapping blocks: Two @preserve blocks overlap in line ranges
        - Nested blocks: One @preserve block inside another
    """
    conflicts = []

    # Sort blocks by start line for easier comparison
    sorted_blocks = sorted(blocks, key=lambda b: b.start_line)

    # Check for overlapping blocks
    for i, block1 in enumerate(sorted_blocks):
        for block2 in sorted_blocks[i+1:]:
            # Check if block2 starts before block1 ends
            if block2.start_line <= block1.end_line:
                conflicts.append(ConflictReport(
                    conflict_type='overlapping_blocks',
                    severity='ERROR',
                    blocks_involved=[block1, block2],
                    description=(
                        f"Preserve blocks overlap: "
                        f"Block at lines {block1.start_line}-{block1.end_line} "
                        f"overlaps with block at lines {block2.start_line}-{block2.end_line}"
                    ),
                    suggested_resolution=(
                        "Remove or adjust one of the preserve blocks to eliminate overlap. "
                        "Each preserve block must have distinct line ranges."
                    )
                ))
            else:
                # No more overlaps possible with this block1
                break

    return conflicts


def detect_content_conflicts(
    preserve_blocks: List[PreserveBlock],
    generated_sections: Dict[str, Tuple[int, int, str]]
) -> List[ConflictReport]:
    """
    Detect conflicts between preserved content and generated sections.

    Args:
        preserve_blocks: List of manually-edited preserve blocks
        generated_sections: Dict mapping section_id to (start_line, end_line, content)

    Returns:
        List of ConflictReport objects for content overlaps (WARNING level)

    Note:
        This generates WARNINGs, not ERRORs. Preservation-priority rule means
        @preserve blocks always win, but we warn about the overlap.
    """
    conflicts = []

    for block in preserve_blocks:
        for section_id, (start, end, content) in generated_sections.items():
            # Check if preserve block overlaps with generated section
            if not (block.end_line < start or block.start_line > end):
                conflicts.append(ConflictReport(
                    conflict_type='content_overlap',
                    severity='WARNING',
                    blocks_involved=[block],
                    description=(
                        f"Preserve block at lines {block.start_line}-{block.end_line} "
                        f"overlaps with generated section '{section_id}' "
                        f"at lines {start}-{end}. Preserved content will take precedence."
                    ),
                    suggested_resolution=(
                        "Review the overlap. The @preserve block content will be kept. "
                        "If you want to use the generated content instead, remove the "
                        "@preserve markers."
                    )
                ))

    return conflicts


def merge_with_preserved(
    generated_content: str,
    preserve_blocks: List[PreserveBlock]
) -> str:
    """
    Merge new generated content with preserved blocks.

    Args:
        generated_content: Newly generated RFC content
        preserve_blocks: List of preserved manual edits to insert

    Returns:
        Merged content with preserve blocks inserted at correct positions

    Logic:
        1. @preserve blocks always take precedence
        2. Insert preserved content at original line positions
        3. Adjust surrounding content to avoid overlap
        4. Add blank lines as padding if needed
    """
    if not preserve_blocks:
        return generated_content

    lines = generated_content.split('\n')

    # Sort blocks by start line (reverse order for insertion)
    sorted_blocks = sorted(preserve_blocks, key=lambda b: b.start_line, reverse=True)

    for block in sorted_blocks:
        # Calculate insertion point (0-indexed)
        insert_pos = max(0, block.start_line - 1)

        # Prepare preserve block with markers
        block_lines = [
            f"@preserve-start" + (f" id:{block.marker_id}" if block.marker_id else ""),
            *block.content.split('\n'),
            "@preserve-end"
        ]

        # Calculate how many lines to replace
        # This preserves the general structure while inserting preserved content
        replace_count = block.end_line - block.start_line + 1

        # Replace or insert
        if insert_pos < len(lines):
            # Replace existing lines with preserved content
            end_pos = min(insert_pos + replace_count, len(lines))
            lines[insert_pos:end_pos] = block_lines
        else:
            # Append if past end of document
            lines.extend([''] * (insert_pos - len(lines)))  # Pad if needed
            lines.extend(block_lines)

    return '\n'.join(lines)


def apply_preservation_priority(
    content: str,
    preserve_blocks: List[PreserveBlock]
) -> str:
    """
    Ensure @preserve blocks take absolute precedence in final content.

    This is a safety check that runs after merge to ensure no preserved
    content was accidentally overwritten.

    Args:
        content: Merged content
        preserve_blocks: Original preserve blocks

    Returns:
        Content with preserve blocks guaranteed intact
    """
    # Re-extract blocks from merged content
    merged_blocks = extract_preserve_blocks(content)

    # Verify all original blocks are present
    for original in preserve_blocks:
        found = False
        for merged in merged_blocks:
            if (merged.start_line == original.start_line and
                merged.content.strip() == original.content.strip()):
                found = True
                break

        if not found:
            logger.error(
                f"Preserve block at line {original.start_line} was lost during merge. "
                "This should never happen - please report this bug."
            )

    return content


def generate_conflict_log(
    conflicts: List[ConflictReport],
    output_path: str = ".claude/.preserve-conflicts.log"
) -> None:
    """
    Write conflict report to log file for user review.

    Args:
        conflicts: List of detected conflicts
        output_path: Path to write conflict log

    Format:
        Each conflict includes:
        - Severity (ERROR/WARNING)
        - Type and description
        - Affected line ranges
        - Suggested resolution
    """
    if not conflicts:
        logger.info("No preserve block conflicts detected")
        return

    with open(output_path, 'w') as f:
        f.write("# Preserve Block Conflict Report\n\n")
        f.write(f"Total conflicts found: {len(conflicts)}\n\n")

        for i, conflict in enumerate(conflicts, start=1):
            f.write(f"## Conflict {i}: {conflict.conflict_type}\n\n")
            f.write(f"**Severity**: {conflict.severity}\n\n")
            f.write(f"**Description**: {conflict.description}\n\n")

            if conflict.blocks_involved:
                f.write("**Affected Blocks**:\n")
                for block in conflict.blocks_involved:
                    f.write(f"- Lines {block.start_line}-{block.end_line}")
                    if block.marker_id:
                        f.write(f" (id: {block.marker_id})")
                    f.write("\n")
                f.write("\n")

            f.write(f"**Resolution**: {conflict.suggested_resolution}\n\n")
            f.write("---\n\n")

    logger.info(f"Conflict report written to {output_path}")


# Utility function for testing
def _example_usage():
    """Example usage of the preserve_edits module."""
    sample_doc = """
# RFC Draft

## Section 1: Introduction

Some generated content here.

@preserve-start
This is my custom introduction that I wrote manually.
It should not be overwritten by the generator.
@preserve-end

## Section 2: Terminology

More generated content.
"""

    # Extract preserve blocks
    blocks = extract_preserve_blocks(sample_doc)
    print(f"Found {len(blocks)} preserve blocks")

    # Validate for conflicts
    conflicts = validate_preserve_blocks(blocks)
    if conflicts:
        print(f"Conflicts detected: {len(conflicts)}")
        generate_conflict_log(conflicts)
    else:
        print("No conflicts found")

    # Merge with new generated content
    new_content = """
# RFC Draft

## Section 1: Introduction

This is newly generated introduction text.

## Section 2: Terminology

Newly generated terminology.
"""

    merged = merge_with_preserved(new_content, blocks)
    print("\nMerged content:")
    print(merged)


if __name__ == "__main__":
    # Setup logging for standalone execution
    logging.basicConfig(level=logging.INFO)
    _example_usage()
