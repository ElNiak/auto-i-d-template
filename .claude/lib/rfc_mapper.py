"""
Library for managing rfc-map.json traceability between code and RFC sections.

This module provides functions to create, read, update, and validate bidirectional
mappings between source code elements and RFC documentation sections.
"""

import json
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class CodeReference:
    """Reference to a code element."""
    file: str
    symbol: str
    line: int


@dataclass
class RFCReference:
    """Reference to an RFC section."""
    section: str  # Format: "3.2.1"
    heading: str


@dataclass
class Mapping:
    """Bidirectional mapping between code and RFC documentation."""
    code: CodeReference
    rfc: RFCReference
    relationship: str  # 'describes', 'implements', 'references', 'example'
    last_synced: str   # ISO 8601 timestamp
    confidence: float = 1.0  # 0.0 to 1.0


class RFCMapper:
    """
    Manages rfc-map.json file for code-to-RFC traceability.

    Provides methods to add, update, query, and validate mappings.
    """

    def __init__(self, map_file_path: str = "docs/rfc-map.json"):
        """
        Initialize RFC mapper.

        Args:
            map_file_path: Path to rfc-map.json file
        """
        self.map_file_path = Path(map_file_path)
        self.mappings: List[Mapping] = []
        self.version = "1.0.0"

        # Create parent directory if needed
        self.map_file_path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> bool:
        """
        Load existing rfc-map.json file.

        Returns:
            True if loaded successfully, False otherwise
        """
        if not self.map_file_path.exists():
            logger.info(f"No existing rfc-map.json found at {self.map_file_path}")
            return False

        try:
            with open(self.map_file_path, 'r') as f:
                data = json.load(f)

            self.version = data.get('version', '1.0.0')

            # Parse mappings
            self.mappings = []
            for item in data.get('mappings', []):
                code_data = item['code']
                rfc_data = item['rfc']

                mapping = Mapping(
                    code=CodeReference(
                        file=code_data['file'],
                        symbol=code_data['symbol'],
                        line=code_data['line']
                    ),
                    rfc=RFCReference(
                        section=rfc_data['section'],
                        heading=rfc_data['heading']
                    ),
                    relationship=item['relationship'],
                    last_synced=item['last_synced'],
                    confidence=item.get('confidence', 1.0)
                )
                self.mappings.append(mapping)

            logger.info(f"Loaded {len(self.mappings)} mappings from {self.map_file_path}")
            return True

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {self.map_file_path}: {e}")
            return False
        except KeyError as e:
            logger.error(f"Missing required field in mapping: {e}")
            return False
        except Exception as e:
            logger.error(f"Error loading rfc-map.json: {e}")
            return False

    def save(self) -> bool:
        """
        Save current mappings to rfc-map.json file.

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Prepare data structure
            data = {
                "version": self.version,
                "mappings": []
            }

            for mapping in self.mappings:
                data["mappings"].append({
                    "code": {
                        "file": mapping.code.file,
                        "symbol": mapping.code.symbol,
                        "line": mapping.code.line
                    },
                    "rfc": {
                        "section": mapping.rfc.section,
                        "heading": mapping.rfc.heading
                    },
                    "relationship": mapping.relationship,
                    "last_synced": mapping.last_synced,
                    "confidence": mapping.confidence
                })

            # Write to file with pretty formatting
            with open(self.map_file_path, 'w') as f:
                json.dump(data, f, indent=2)

            logger.info(f"Saved {len(self.mappings)} mappings to {self.map_file_path}")
            return True

        except Exception as e:
            logger.error(f"Error saving rfc-map.json: {e}")
            return False

    def add_mapping(
        self,
        code_file: str,
        code_symbol: str,
        code_line: int,
        rfc_section: str,
        rfc_heading: str,
        relationship: str = "describes",
        confidence: float = 1.0
    ) -> bool:
        """
        Add a new mapping between code and RFC section.

        Args:
            code_file: Path to source file
            code_symbol: Symbol name (function, class, etc.)
            code_line: Line number in source file
            rfc_section: RFC section number (e.g., "3.2.1")
            rfc_heading: RFC section heading text
            relationship: Type of relationship
            confidence: Confidence score (0.0 to 1.0)

        Returns:
            True if added successfully
        """
        # Check for duplicate
        for existing in self.mappings:
            if (existing.code.file == code_file and
                existing.code.symbol == code_symbol and
                existing.rfc.section == rfc_section):
                logger.warning(
                    f"Mapping already exists: {code_symbol} → §{rfc_section}"
                )
                return False

        mapping = Mapping(
            code=CodeReference(
                file=code_file,
                symbol=code_symbol,
                line=code_line
            ),
            rfc=RFCReference(
                section=rfc_section,
                heading=rfc_heading
            ),
            relationship=relationship,
            last_synced=datetime.now().isoformat(),
            confidence=confidence
        )

        self.mappings.append(mapping)
        logger.info(f"Added mapping: {code_symbol} → §{rfc_section}")
        return True

    def find_mappings_by_file(self, file_path: str) -> List[Mapping]:
        """
        Get all mappings for a specific source file.

        Args:
            file_path: Path to source file

        Returns:
            List of Mapping objects for that file
        """
        return [m for m in self.mappings if m.code.file == file_path]

    def find_mappings_by_section(self, section: str) -> List[Mapping]:
        """
        Get all code elements mapped to a specific RFC section.

        Args:
            section: RFC section number (e.g., "3.2.1")

        Returns:
            List of Mapping objects for that section
        """
        return [m for m in self.mappings if m.rfc.section == section]

    def find_mappings_by_symbol(self, symbol: str) -> List[Mapping]:
        """
        Get all mappings for a specific code symbol.

        Args:
            symbol: Symbol name to search for

        Returns:
            List of Mapping objects for that symbol
        """
        return [m for m in self.mappings if m.code.symbol == symbol]

    def update_timestamp(
        self,
        code_file: str,
        code_symbol: str,
        timestamp: Optional[str] = None
    ) -> int:
        """
        Update last_synced timestamp for mappings.

        Args:
            code_file: Path to source file
            code_symbol: Symbol name
            timestamp: ISO 8601 timestamp (default: now)

        Returns:
            Number of mappings updated
        """
        if timestamp is None:
            timestamp = datetime.now().isoformat()

        count = 0
        for mapping in self.mappings:
            if (mapping.code.file == code_file and
                mapping.code.symbol == code_symbol):
                mapping.last_synced = timestamp
                count += 1

        logger.info(f"Updated {count} timestamps for {code_symbol}")
        return count

    def mark_stale(self, file_paths: List[str]) -> int:
        """
        Mark mappings as stale for specified files.

        This is useful when code changes are detected but RFC hasn't been updated yet.

        Args:
            file_paths: List of file paths that changed

        Returns:
            Number of mappings marked stale
        """
        # Set a very old timestamp to indicate staleness
        stale_timestamp = "1970-01-01T00:00:00"

        count = 0
        for mapping in self.mappings:
            if mapping.code.file in file_paths:
                mapping.last_synced = stale_timestamp
                count += 1

        logger.info(f"Marked {count} mappings as stale")
        return count

    def get_stale_mappings(self, max_age_days: int = 30) -> List[Mapping]:
        """
        Find mappings that haven't been synced recently.

        Args:
            max_age_days: Maximum age in days before considering stale

        Returns:
            List of stale Mapping objects
        """
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(days=max_age_days)
        stale = []

        for mapping in self.mappings:
            try:
                synced = datetime.fromisoformat(mapping.last_synced)
                if synced < cutoff:
                    stale.append(mapping)
            except ValueError:
                # Invalid timestamp format
                logger.warning(f"Invalid timestamp in mapping: {mapping.last_synced}")
                stale.append(mapping)

        return stale

    def remove_mapping(self, code_file: str, code_symbol: str, rfc_section: str) -> bool:
        """
        Remove a specific mapping.

        Args:
            code_file: Path to source file
            code_symbol: Symbol name
            rfc_section: RFC section number

        Returns:
            True if removed, False if not found
        """
        for i, mapping in enumerate(self.mappings):
            if (mapping.code.file == code_file and
                mapping.code.symbol == code_symbol and
                mapping.rfc.section == rfc_section):
                del self.mappings[i]
                logger.info(f"Removed mapping: {code_symbol} → §{rfc_section}")
                return True

        logger.warning(f"Mapping not found: {code_symbol} → §{rfc_section}")
        return False

    def remove_mappings_by_file(self, file_path: str) -> int:
        """
        Remove all mappings for a specific file.

        Useful when a file is deleted from the codebase.

        Args:
            file_path: Path to source file

        Returns:
            Number of mappings removed
        """
        original_count = len(self.mappings)
        self.mappings = [m for m in self.mappings if m.code.file != file_path]
        removed = original_count - len(self.mappings)

        logger.info(f"Removed {removed} mappings for {file_path}")
        return removed

    def remove_mappings_by_section(self, section: str) -> int:
        """
        Remove all mappings for a specific RFC section.

        Useful when a section is removed from the RFC document.

        Args:
            section: RFC section number

        Returns:
            Number of mappings removed
        """
        original_count = len(self.mappings)
        self.mappings = [m for m in self.mappings if m.rfc.section != section]
        removed = original_count - len(self.mappings)

        logger.info(f"Removed {removed} mappings for section {section}")
        return removed

    def validate_integrity(self) -> List[str]:
        """
        Validate mapping integrity and return list of issues.

        Checks:
        - All code files exist
        - Line numbers are positive
        - Section numbers follow pattern
        - No duplicate mappings
        - Relationship types are valid

        Returns:
            List of error messages (empty if all valid)
        """
        errors = []
        seen_mappings = set()

        valid_relationships = {'describes', 'implements', 'references', 'example'}

        for i, mapping in enumerate(self.mappings):
            # Check line number
            if mapping.code.line < 1:
                errors.append(
                    f"Mapping {i}: Invalid line number {mapping.code.line}"
                )

            # Check section format (e.g., "3.2.1")
            import re
            if not re.match(r'^\d+(\.\d+)*$', mapping.rfc.section):
                errors.append(
                    f"Mapping {i}: Invalid section number format '{mapping.rfc.section}'"
                )

            # Check relationship type
            if mapping.relationship not in valid_relationships:
                errors.append(
                    f"Mapping {i}: Invalid relationship '{mapping.relationship}'"
                )

            # Check for duplicates
            key = (mapping.code.file, mapping.code.symbol, mapping.rfc.section)
            if key in seen_mappings:
                errors.append(
                    f"Mapping {i}: Duplicate mapping {mapping.code.symbol} → §{mapping.rfc.section}"
                )
            seen_mappings.add(key)

            # Check confidence range
            if not (0.0 <= mapping.confidence <= 1.0):
                errors.append(
                    f"Mapping {i}: Confidence {mapping.confidence} out of range [0.0, 1.0]"
                )

        if errors:
            logger.warning(f"Found {len(errors)} integrity issues")
        else:
            logger.info("All mappings validated successfully")

        return errors

    def get_statistics(self) -> Dict[str, int]:
        """
        Get statistics about current mappings.

        Returns:
            Dictionary with counts and metrics
        """
        stats = {
            'total_mappings': len(self.mappings),
            'unique_files': len(set(m.code.file for m in self.mappings)),
            'unique_sections': len(set(m.rfc.section for m in self.mappings)),
            'unique_symbols': len(set(m.code.symbol for m in self.mappings)),
        }

        # Count by relationship type
        for rel_type in ['describes', 'implements', 'references', 'example']:
            count = sum(1 for m in self.mappings if m.relationship == rel_type)
            stats[f'{rel_type}_mappings'] = count

        return stats

    def compare_with_current_state(
        self,
        current_symbols: List[Dict],
        repo_root: str = "."
    ) -> Dict[str, List[Mapping]]:
        """
        Compare existing rfc-map.json with current code state.

        This function enables incremental RFC updates by identifying:
        - Removed mappings: Code symbols that no longer exist
        - Modified mappings: Code symbols that moved or changed
        - Unchanged mappings: Code symbols still at same location
        - New symbols: Code not yet in rfc-map.json (requires new mappings)

        Args:
            current_symbols: List of symbol dicts from parser agent output
                            Each dict should have: {file, symbol, line, type}
            repo_root: Repository root path for normalizing file paths

        Returns:
            Dictionary with keys:
            - 'removed': Mappings where code no longer exists
            - 'modified': Mappings where code moved/changed
            - 'unchanged': Mappings still valid
            - 'new_symbols': Symbols not yet mapped (for new sections)

        Example:
            >>> mapper = load_rfc_map()
            >>> current_symbols = parser_agent_output['symbols']
            >>> diff = mapper.compare_with_current_state(current_symbols)
            >>> print(f"Need to update {len(diff['modified'])} sections")
        """
        from pathlib import Path

        # Normalize repo_root
        repo_path = Path(repo_root).resolve()

        # Build lookup table for current symbols
        # Key: (file, symbol) -> {line, type, ...}
        current_lookup = {}
        for sym in current_symbols:
            file_key = str(Path(sym['file']).resolve().relative_to(repo_path))
            symbol_key = sym['symbol']
            current_lookup[(file_key, symbol_key)] = sym

        # Categorize existing mappings
        removed = []
        modified = []
        unchanged = []

        for mapping in self.mappings:
            key = (mapping.code.file, mapping.code.symbol)

            if key not in current_lookup:
                # Symbol no longer exists
                removed.append(mapping)
                logger.debug(
                    f"Symbol removed: {mapping.code.symbol} in {mapping.code.file}"
                )

            else:
                # Symbol still exists - check if it moved
                current = current_lookup[key]
                current_line = current.get('line', mapping.code.line)

                if current_line != mapping.code.line:
                    # Line number changed
                    modified.append(mapping)
                    logger.debug(
                        f"Symbol moved: {mapping.code.symbol} "
                        f"from line {mapping.code.line} to {current_line}"
                    )
                else:
                    # No change detected
                    unchanged.append(mapping)

        # Identify new symbols not in rfc-map.json
        mapped_symbols = set(
            (m.code.file, m.code.symbol) for m in self.mappings
        )
        new_symbols = []

        for sym in current_symbols:
            file_key = str(Path(sym['file']).resolve().relative_to(repo_path))
            symbol_key = sym['symbol']

            if (file_key, symbol_key) not in mapped_symbols:
                new_symbols.append(sym)
                logger.debug(f"New symbol: {symbol_key} in {file_key}")

        logger.info(
            f"Comparison complete: "
            f"{len(removed)} removed, "
            f"{len(modified)} modified, "
            f"{len(unchanged)} unchanged, "
            f"{len(new_symbols)} new symbols"
        )

        return {
            'removed': removed,
            'modified': modified,
            'unchanged': unchanged,
            'new_symbols': new_symbols
        }


# Convenience functions for quick operations

def load_rfc_map(map_file_path: str = "docs/rfc-map.json") -> Optional[RFCMapper]:
    """
    Load rfc-map.json and return mapper instance.

    Args:
        map_file_path: Path to rfc-map.json

    Returns:
        RFCMapper instance or None if loading failed
    """
    mapper = RFCMapper(map_file_path)
    if mapper.load():
        return mapper
    return None


def create_new_rfc_map(map_file_path: str = "docs/rfc-map.json") -> RFCMapper:
    """
    Create a new empty rfc-map.json file.

    Args:
        map_file_path: Path to create rfc-map.json

    Returns:
        New RFCMapper instance
    """
    mapper = RFCMapper(map_file_path)
    mapper.save()
    logger.info(f"Created new rfc-map.json at {map_file_path}")
    return mapper


# Example usage
def _example_usage():
    """Example usage of rfc_mapper module."""
    # Create new mapper
    mapper = RFCMapper("example-rfc-map.json")

    # Add some mappings
    mapper.add_mapping(
        code_file="src/api.py",
        code_symbol="authenticate",
        code_line=42,
        rfc_section="3.2",
        rfc_heading="Authentication Interface",
        relationship="implements"
    )

    mapper.add_mapping(
        code_file="src/api.py",
        code_symbol="User",
        code_line=10,
        rfc_section="2.1",
        rfc_heading="Terminology",
        relationship="describes"
    )

    # Save to file
    mapper.save()

    # Query mappings
    print(f"Mappings for src/api.py: {len(mapper.find_mappings_by_file('src/api.py'))}")
    print(f"Mappings for section 3.2: {len(mapper.find_mappings_by_section('3.2'))}")

    # Validate
    errors = mapper.validate_integrity()
    print(f"Validation errors: {len(errors)}")

    # Statistics
    stats = mapper.get_statistics()
    print(f"Statistics: {stats}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    _example_usage()
