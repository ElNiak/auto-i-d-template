#!/usr/bin/env python3
"""
PostToolUse Hook: rfc-map.json Synchronization

Synchronizes rfc-map.json after Write/Edit/Bash tool execution.
Updates timestamps, file checksums, and staleness status.
Maintains audit trail in .claude/.hook-history.json.

Performance Target: <500ms response time
"""

import sys
import json
import os
import subprocess
import hashlib
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
LOG_DIR = Path(__file__).parent.parent / '.hook-logs'
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'post_tool_sync.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('post_tool_sync')


def parse_hook_input() -> tuple[str | None, dict]:
    """
    Parse hook invocation input from multiple possible sources.

    Returns:
        (tool_name, tool_args) tuple
    """
    tool_name = None
    tool_args = {}

    # Method 1: Environment variables
    tool_name = os.environ.get('CLAUDE_TOOL_NAME')
    if tool_name:
        tool_args = {
            'file_path': os.environ.get('CLAUDE_TOOL_FILE_PATH', ''),
            'content': os.environ.get('CLAUDE_TOOL_CONTENT', ''),
            'command': os.environ.get('CLAUDE_TOOL_COMMAND', '')
        }
        logger.debug(f"Parsed from env: tool={tool_name}")
        return tool_name, tool_args

    # Method 2: stdin JSON
    try:
        if not sys.stdin.isatty():
            input_data = json.load(sys.stdin)
            tool_name = input_data.get('tool', input_data.get('tool_name'))
            tool_args = input_data.get('args', input_data.get('arguments', {}))
            logger.debug(f"Parsed from stdin: tool={tool_name}")
            return tool_name, tool_args
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Failed to parse stdin JSON: {e}")

    # Method 3: Command line arguments
    if len(sys.argv) > 1:
        tool_name = sys.argv[1]
        if len(sys.argv) > 2:
            try:
                tool_args = json.loads(sys.argv[2])
            except json.JSONDecodeError:
                # Fallback: treat as command
                tool_args = {'command': ' '.join(sys.argv[2:])}
        logger.debug(f"Parsed from argv: tool={tool_name}")
        return tool_name, tool_args

    logger.error("Could not parse hook input")
    return None, {}


def get_repository_root() -> Path | None:
    """Find repository root by looking for .git directory."""
    current = Path.cwd()
    while current != current.parent:
        if (current / '.git').exists():
            return current
        current = current.parent
    return None


def normalize_to_relative(file_path: str, repo_root: Path) -> str:
    """
    Convert file path to relative path from repo root.

    Args:
        file_path: Absolute or relative file path
        repo_root: Repository root directory

    Returns:
        Relative path from repo root
    """
    file_path_obj = Path(file_path)

    # Handle absolute paths
    if file_path_obj.is_absolute():
        try:
            return str(file_path_obj.relative_to(repo_root))
        except ValueError:
            # Path is outside repository
            logger.warning(f"File path {file_path} is outside repository")
            return str(file_path_obj)

    # Already relative
    return str(file_path_obj)


def detect_bash_modifications(repo_root: Path) -> list[str]:
    """
    Use git status to detect files modified by Bash command.

    Args:
        repo_root: Repository root directory

    Returns:
        List of modified file paths (relative to repo root)
    """
    try:
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            logger.warning(f"Git status failed: {result.stderr}")
            return []

        modified_files = []
        for line in result.stdout.split('\n'):
            if line.strip():
                # Parse git status format: "XY filename"
                status = line[:2].strip()
                filename = line[3:].strip()

                # Track modifications, additions, renames
                if status in ['M', 'A', 'R', 'AM', 'MM', 'RM']:
                    modified_files.append(filename)

        logger.debug(f"Detected {len(modified_files)} modified files via git status")
        return modified_files

    except subprocess.TimeoutExpired:
        logger.error("Git status command timed out")
        return []
    except Exception as e:
        logger.error(f"Error running git status: {e}")
        return []


def detect_modified_files(tool_name: str, tool_args: dict, repo_root: Path) -> list[str]:
    """
    Detect which files were modified by the tool execution.

    Args:
        tool_name: Name of the tool (Write, Edit, Bash)
        tool_args: Tool arguments dictionary
        repo_root: Repository root path

    Returns:
        List of relative file paths that were modified
    """
    modified_files = []

    if tool_name == 'Write':
        # Direct: file_path from arguments
        file_path = tool_args.get('file_path', '')
        if file_path:
            rel_path = normalize_to_relative(file_path, repo_root)
            modified_files.append(rel_path)
            logger.info(f"Write tool modified: {rel_path}")

    elif tool_name == 'Edit':
        # Direct: file_path from arguments
        file_path = tool_args.get('file_path', '')
        if file_path:
            rel_path = normalize_to_relative(file_path, repo_root)
            modified_files.append(rel_path)
            logger.info(f"Edit tool modified: {rel_path}")

    elif tool_name == 'Bash':
        # Indirect: detect via git status (after command execution)
        modified_files = detect_bash_modifications(repo_root)
        logger.info(f"Bash tool modified {len(modified_files)} files")

    return modified_files


def calculate_file_checksum(file_path: Path) -> str:
    """
    Calculate SHA256 checksum of file contents.

    Args:
        file_path: Absolute path to file

    Returns:
        64-character hex string (SHA256 hash)
    """
    sha256 = hashlib.sha256()

    try:
        with open(file_path, 'rb') as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)

        return sha256.hexdigest()

    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return "0" * 64  # Placeholder for missing file
    except Exception as e:
        logger.error(f"Error calculating checksum for {file_path}: {e}")
        return "0" * 64


def get_current_commit_hash(repo_root: Path) -> str | None:
    """
    Get current git HEAD commit hash (full 40-char SHA-1).

    Args:
        repo_root: Repository root directory

    Returns:
        40-character hex string or None if not in git repo
    """
    try:
        result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=2
        )

        if result.returncode == 0:
            commit_hash = result.stdout.strip()
            # Validate format: 40 hex characters
            if len(commit_hash) == 40 and all(c in '0123456789abcdef' for c in commit_hash):
                return commit_hash

        return None

    except Exception as e:
        logger.warning(f"Could not get git commit hash: {e}")
        return None


def should_skip_synchronization(modified_files: list[str], rfc_map_path: Path) -> bool:
    """
    Fast path: Determine if we can skip synchronization entirely.

    Args:
        modified_files: List of modified file paths
        rfc_map_path: Path to rfc-map.json

    Returns:
        True if synchronization should be skipped
    """
    # No files modified
    if not modified_files:
        logger.debug("No files modified - skipping sync")
        return True

    # rfc-map.json doesn't exist
    if not rfc_map_path.exists():
        logger.debug("rfc-map.json missing - skipping sync")
        return True

    # Load rfc-map.json to check if any modified files are tracked
    try:
        with open(rfc_map_path, 'r') as f:
            rfc_map = json.load(f)

        tracked_files = {m['code']['file'] for m in rfc_map.get('mappings', [])}

        # Check intersection
        if not any(f in tracked_files for f in modified_files):
            logger.debug("No tracked files modified - skipping sync")
            return True

        return False

    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Error reading rfc-map.json: {e}")
        return True  # Skip on error


def update_rfc_map_for_files(
    modified_files: list[str],
    rfc_map_path: Path,
    repo_root: Path
) -> tuple[int, list[str]]:
    """
    Update rfc-map.json entries for modified files.

    Args:
        modified_files: List of relative file paths
        rfc_map_path: Path to rfc-map.json
        repo_root: Repository root directory

    Returns:
        (updated_count, affected_sections) tuple
    """
    # Load rfc-map.json
    with open(rfc_map_path, 'r') as f:
        rfc_map = json.load(f)

    updated_count = 0
    affected_sections = []
    current_timestamp = datetime.now().isoformat()

    # Get current git commit hash (optional)
    git_commit = get_current_commit_hash(repo_root)

    # Update each mapping that references modified files
    for mapping in rfc_map.get('mappings', []):
        code_info = mapping.get('code', {})
        file_path = code_info.get('file', '')

        if file_path in modified_files:
            # Calculate new checksum
            abs_file_path = repo_root / file_path
            new_checksum = calculate_file_checksum(abs_file_path)

            # Update fields
            mapping['last_synced'] = current_timestamp
            mapping['file_checksum'] = new_checksum
            mapping['staleness_status'] = 'fresh'  # Just synchronized

            if git_commit:
                mapping['git_commit'] = git_commit

            # Track affected section
            section = mapping.get('rfc', {}).get('section', 'unknown')
            if section not in affected_sections:
                affected_sections.append(section)

            updated_count += 1
            logger.info(f"Updated mapping for {file_path} (section {section})")

    # Write back to file atomically
    temp_path = rfc_map_path.with_suffix('.tmp')

    with open(temp_path, 'w') as f:
        json.dump(rfc_map, f, indent=2)

    # Atomic rename
    temp_path.replace(rfc_map_path)

    logger.info(f"Updated {updated_count} mappings in rfc-map.json")
    return updated_count, affected_sections


def append_to_hook_history(
    history_path: Path,
    entry: dict
) -> bool:
    """
    Append entry to .hook-history.json atomically.

    Args:
        history_path: Path to .hook-history.json
        entry: Dictionary entry to append

    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure parent directory exists
        history_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing history
        if history_path.exists():
            with open(history_path, 'r') as f:
                try:
                    history = json.load(f)
                except json.JSONDecodeError:
                    # Corrupted file - start fresh
                    logger.warning("Corrupted hook history, recreating")
                    history = {"entries": []}
        else:
            history = {"entries": []}

        # Append new entry
        history["entries"].append(entry)

        # Size management: keep last 1000 entries
        if len(history["entries"]) > 1000:
            history["entries"] = history["entries"][-1000:]
            logger.debug("Trimmed hook history to 1000 entries")

        # Write atomically using temp file + rename
        temp_path = history_path.with_suffix('.tmp')

        with open(temp_path, 'w') as f:
            json.dump(history, f, indent=2)

        # Atomic rename
        temp_path.replace(history_path)

        return True

    except Exception as e:
        logger.error(f"Failed to append to hook history: {e}")
        return False


def main():
    """Hook entry point - synchronizes rfc-map.json after tool execution."""

    logger.info("=== PostToolUse Hook (Synchronization) Started ===")

    start_time = datetime.now()

    # Initialize response
    response = {
        "block": False,  # Always non-blocking
        "message": "",
        "metadata": {}
    }

    try:
        # Parse hook input
        tool_name, tool_args = parse_hook_input()

        if not tool_name:
            logger.error("Failed to parse hook input")
            response["message"] = "Hook error: Could not parse tool invocation"
            print(json.dumps(response))
            return

        logger.info(f"Tool: {tool_name}")

        # Find repository root
        repo_root = get_repository_root()
        if not repo_root:
            logger.warning("Not in a git repository")
            print(json.dumps(response))
            return

        # Detect modified files
        modified_files = detect_modified_files(tool_name, tool_args, repo_root)

        if not modified_files:
            logger.debug("No files modified")
            print(json.dumps(response))
            return

        logger.info(f"Detected {len(modified_files)} modified files")

        # Load rfc-map.json
        rfc_map_path = repo_root / 'docs' / 'rfc-map.json'

        # Fast path: skip if no tracked files modified
        if should_skip_synchronization(modified_files, rfc_map_path):
            print(json.dumps(response))
            return

        # Update rfc-map.json
        updated_count, affected_sections = update_rfc_map_for_files(
            modified_files,
            rfc_map_path,
            repo_root
        )

        # Calculate duration
        duration = (datetime.now() - start_time).total_seconds() * 1000

        # Log to audit trail
        history_path = repo_root / '.claude' / '.hook-history.json'
        append_to_hook_history(
            history_path,
            {
                "timestamp": datetime.now().isoformat(),
                "hook": "post_tool_sync",
                "tool": tool_name,
                "files_modified": modified_files,
                "mappings_updated": updated_count,
                "sections_affected": affected_sections,
                "action": "synchronized",
                "metadata": {
                    "duration_ms": int(duration)
                }
            }
        )

        # Generate response
        if updated_count > 0:
            response["message"] = f"✅ Updated {updated_count} mappings in rfc-map.json ({len(modified_files)} files)"
            response["metadata"] = {
                "files_modified": modified_files[:5],  # Limit to first 5
                "mappings_updated": updated_count,
                "sections_affected": affected_sections[:5],
                "duration_ms": int(duration)
            }
            logger.info(f"Synchronization complete: {updated_count} mappings updated")
        else:
            logger.debug("No mappings needed updating")

    except Exception as e:
        logger.exception(f"Unexpected error in hook: {e}")
        # Don't block on errors (graceful degradation)
        response["message"] = f"⚠️  Sync error: {str(e)}"
        response["suggestion"] = "Check .claude/.hook-logs/post_tool_sync.log"

    finally:
        # Return response to Claude Code
        print(json.dumps(response))
        logger.info(f"=== Hook Complete: {response['message'][:100] if response['message'] else 'No updates'} ===")


if __name__ == "__main__":
    main()
