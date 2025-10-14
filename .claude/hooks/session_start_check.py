#!/usr/bin/env python3
"""
SessionStart Hook: RFC Documentation Staleness Check

Checks for stale RFC documentation and uncommitted changes on session start.
Provides non-blocking warnings and suggestions for maintenance.

Performance Target: <200ms response time
"""

import sys
import json
import os
import subprocess
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Setup logging
LOG_DIR = Path(__file__).parent.parent / '.hook-logs'
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'session_start_check.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('session_start_check')

# Default staleness threshold (days)
DEFAULT_STALENESS_THRESHOLD = 30


def get_repository_root() -> Path | None:
    """Find repository root by looking for .git directory."""
    current = Path.cwd()
    while current != current.parent:
        if (current / '.git').exists():
            return current
        current = current.parent
    return None


def load_plugin_config() -> dict:
    """
    Load hook configuration from plugin.json.

    Returns:
        Configuration dictionary with staleness_threshold_days
    """
    try:
        repo_root = get_repository_root()
        if not repo_root:
            return {'staleness_threshold_days': DEFAULT_STALENESS_THRESHOLD}

        plugin_json = repo_root / '.claude' / 'plugin.json'

        if not plugin_json.exists():
            return {'staleness_threshold_days': DEFAULT_STALENESS_THRESHOLD}

        with open(plugin_json, 'r') as f:
            data = json.load(f)

        threshold = data.get('staleness_threshold_days', DEFAULT_STALENESS_THRESHOLD)
        logger.debug(f"Loaded staleness threshold: {threshold} days")

        return {'staleness_threshold_days': threshold}

    except Exception as e:
        logger.warning(f"Failed to load plugin config: {e}")
        return {'staleness_threshold_days': DEFAULT_STALENESS_THRESHOLD}


def check_rfc_map_staleness(repo_root: Path, threshold_days: int) -> tuple[bool, str, int]:
    """
    Check if rfc-map.json is stale based on modification time.

    Args:
        repo_root: Repository root directory
        threshold_days: Staleness threshold in days

    Returns:
        (is_stale, message, days_old) tuple
    """
    rfc_map_path = repo_root / 'docs' / 'rfc-map.json'

    # Check if file exists
    if not rfc_map_path.exists():
        logger.info("rfc-map.json not found - no RFC documentation")
        return (False, "", 0)

    try:
        # Get last modification time
        mtime = os.path.getmtime(rfc_map_path)
        mod_datetime = datetime.fromtimestamp(mtime)

        # Calculate age
        age = datetime.now() - mod_datetime
        days_old = age.days

        logger.debug(f"rfc-map.json is {days_old} days old")

        # Check against threshold
        if days_old > threshold_days:
            message = (
                f"⚠️  RFC documentation is {days_old} days old "
                f"(threshold: {threshold_days} days)"
            )
            logger.info(f"Documentation stale: {days_old} days > {threshold_days} days")
            return (True, message, days_old)

        logger.debug(f"Documentation fresh: {days_old} days <= {threshold_days} days")
        return (False, "", days_old)

    except Exception as e:
        logger.error(f"Error checking rfc-map.json staleness: {e}")
        return (False, "", 0)


def check_uncommitted_docs(repo_root: Path) -> tuple[bool, str, list[str]]:
    """
    Check for uncommitted changes in docs/generated/ directory.

    Args:
        repo_root: Repository root directory

    Returns:
        (has_uncommitted, message, files) tuple
    """
    docs_dir = repo_root / 'docs' / 'generated'

    if not docs_dir.exists():
        logger.debug("docs/generated/ directory not found")
        return (False, "", [])

    try:
        # Run git status on docs directory
        result = subprocess.run(
            ['git', 'status', '--porcelain', 'docs/generated/'],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            logger.warning(f"Git status failed: {result.stderr}")
            return (False, "", [])

        # Parse output
        uncommitted_files = []
        for line in result.stdout.split('\n'):
            if line.strip():
                # Format: "XY filename"
                status = line[:2].strip()
                filename = line[3:].strip()

                # Track any non-committed changes
                if status:
                    uncommitted_files.append(filename)

        if uncommitted_files:
            message = (
                f"⚠️  {len(uncommitted_files)} uncommitted documentation files "
                f"in docs/generated/"
            )
            logger.info(f"Uncommitted docs found: {len(uncommitted_files)} files")
            return (True, message, uncommitted_files)

        logger.debug("No uncommitted documentation changes")
        return (False, "", [])

    except subprocess.TimeoutExpired:
        logger.error("Git status timed out")
        return (False, "", [])
    except Exception as e:
        logger.error(f"Error checking uncommitted docs: {e}")
        return (False, "", [])


def check_stale_mappings(repo_root: Path) -> tuple[int, list[str]]:
    """
    Check for stale mappings in rfc-map.json (checksum-based).

    Args:
        repo_root: Repository root directory

    Returns:
        (stale_count, stale_sections) tuple
    """
    rfc_map_path = repo_root / 'docs' / 'rfc-map.json'

    if not rfc_map_path.exists():
        return (0, [])

    try:
        with open(rfc_map_path, 'r') as f:
            rfc_map = json.load(f)

        stale_count = 0
        stale_sections = []

        for mapping in rfc_map.get('mappings', []):
            staleness = mapping.get('staleness_status', 'unknown')

            if staleness == 'stale':
                section = mapping.get('rfc', {}).get('section', 'unknown')
                if section not in stale_sections:
                    stale_sections.append(section)
                stale_count += 1

        if stale_count > 0:
            logger.info(f"Found {stale_count} stale mappings affecting {len(stale_sections)} sections")

        return (stale_count, stale_sections)

    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Error reading rfc-map.json: {e}")
        return (0, [])


def format_suggestions(
    is_stale: bool,
    has_uncommitted: bool,
    stale_count: int
) -> str:
    """
    Generate suggestions based on detected issues.

    Args:
        is_stale: Whether rfc-map.json is stale
        has_uncommitted: Whether there are uncommitted docs
        stale_count: Number of stale mappings

    Returns:
        Formatted suggestions string
    """
    suggestions = []

    if is_stale:
        suggestions.append("Run /rfc-update to refresh RFC documentation")

    if has_uncommitted:
        suggestions.append("Commit documentation changes: git add docs/ && git commit")

    if stale_count > 0:
        suggestions.append(f"{stale_count} stale mappings detected - consider running /rfc-update")

    if not suggestions:
        return ""

    return " • ".join(suggestions)


def main():
    """Hook entry point - checks documentation staleness on session start."""

    logger.info("=== SessionStart Hook (Staleness Check) Started ===")

    # Initialize response
    response = {
        "block": False,  # Never blocking
        "message": "",
        "suggestion": "",
        "metadata": {}
    }

    try:
        # Find repository root
        repo_root = get_repository_root()

        if not repo_root:
            logger.debug("Not in a git repository - skipping checks")
            print(json.dumps(response))
            return

        # Load configuration
        config = load_plugin_config()
        threshold_days = config['staleness_threshold_days']

        # Check rfc-map.json staleness
        is_stale, stale_message, days_old = check_rfc_map_staleness(
            repo_root,
            threshold_days
        )

        # Check for uncommitted documentation
        has_uncommitted, uncommitted_message, uncommitted_files = check_uncommitted_docs(
            repo_root
        )

        # Check for stale mappings (checksum-based)
        stale_count, stale_sections = check_stale_mappings(repo_root)

        # Build response if any issues found
        messages = []
        if stale_message:
            messages.append(stale_message)
        if uncommitted_message:
            messages.append(uncommitted_message)
        if stale_count > 0:
            messages.append(f"🔍 {stale_count} stale code-RFC mappings detected")

        if messages:
            response["message"] = "\n".join(messages)
            response["suggestion"] = format_suggestions(
                is_stale,
                has_uncommitted,
                stale_count
            )
            response["metadata"] = {
                "days_since_update": days_old,
                "uncommitted_files": len(uncommitted_files),
                "stale_mappings": stale_count,
                "stale_sections": stale_sections[:5]  # First 5
            }

            logger.info(f"Staleness detected: {len(messages)} issues")
        else:
            logger.info("Documentation is up-to-date")

    except Exception as e:
        logger.exception(f"Unexpected error in hook: {e}")
        # Don't block on errors
        response["message"] = f"⚠️  Staleness check error: {str(e)}"
        response["suggestion"] = "Check .claude/.hook-logs/session_start_check.log"

    finally:
        # Return response to Claude Code
        print(json.dumps(response))
        logger.info("=== Hook Complete ===")


if __name__ == "__main__":
    main()
