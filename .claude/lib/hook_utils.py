"""
Utility functions for Claude Code native hooks.

This module provides common utilities for hook scripts including:
- Safe configuration loading
- Standardized response formatting
- Hook event logging
- RRC map access
"""

import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


def load_rfc_map(rfc_map_path: str = "docs/rfc-map.json") -> Optional[Dict]:
    """
    Parse rfc-map.json safely with error handling.

    Args:
        rfc_map_path: Path to rfc-map.json

    Returns:
        Parsed rfc-map dictionary or None if error occurs
    """
    try:
        path = Path(rfc_map_path)
        if not path.exists():
            logger.warning(f"rfc-map.json not found at {rfc_map_path}")
            return None

        with open(path, 'r') as f:
            rfc_map = json.load(f)

        logger.debug(f"Successfully loaded rfc-map from {rfc_map_path}")
        return rfc_map

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in rfc-map.json: {e}")
        return None
    except Exception as e:
        logger.error(f"Error loading rfc-map.json: {e}")
        return None


def load_plugin_config(config_path: str = ".claude/plugin.json") -> Dict:
    """
    Load plugin configuration with safe defaults.

    Args:
        config_path: Path to plugin.json

    Returns:
        Configuration dictionary (empty dict if error)
    """
    try:
        path = Path(config_path)
        if not path.exists():
            logger.warning(f"Plugin config not found at {config_path}")
            return {}

        with open(path, 'r') as f:
            config = json.load(f)

        logger.debug(f"Successfully loaded plugin config from {config_path}")
        return config

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in plugin.json: {e}")
        return {}
    except Exception as e:
        logger.error(f"Error loading plugin.json: {e}")
        return {}


def format_warning(message: str, suggestion: str = "") -> Dict[str, Any]:
    """
    Return JSON with warning format for non-blocking hooks.

    Args:
        message: Warning message to display
        suggestion: Optional suggestion for user action

    Returns:
        Hook response dictionary
    """
    response = {
        "block": False,
        "message": message
    }

    if suggestion:
        response["suggestion"] = suggestion

    return response


def format_error(message: str, suggestion: str = "") -> Dict[str, Any]:
    """
    Return JSON with error format for blocking hooks.

    Args:
        message: Error message to display
        suggestion: Optional suggestion for user action

    Returns:
        Hook response dictionary with block=true
    """
    response = {
        "block": True,
        "message": message
    }

    if suggestion:
        response["suggestion"] = suggestion

    return response


def format_success(message: str = "", metadata: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Return JSON with success format (non-blocking, optional message).

    Args:
        message: Optional success message
        metadata: Optional metadata dictionary

    Returns:
        Hook response dictionary
    """
    response = {
        "block": False
    }

    if message:
        response["message"] = message

    if metadata:
        response["metadata"] = metadata

    return response


def log_hook_event(
    event_type: str,
    details: Dict[str, Any],
    log_path: str = ".claude/.hook-history.json"
) -> bool:
    """
    Append event to hook history log for audit trail.

    Args:
        event_type: Type of event (e.g., 'pretool_validate', 'posttool_sync')
        details: Event details dictionary
        log_path: Path to hook history log file

    Returns:
        True if logged successfully, False otherwise
    """
    try:
        log_file = Path(log_path)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        # Load existing history
        history = []
        if log_file.exists():
            try:
                with open(log_file, 'r') as f:
                    history = json.load(f)
            except json.JSONDecodeError:
                logger.warning("Corrupted hook history, creating new log")
                history = []

        # Add new event
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "details": details
        }
        history.append(event)

        # Keep only last 1000 events to prevent unbounded growth
        if len(history) > 1000:
            history = history[-1000:]

        # Write back
        with open(log_file, 'w') as f:
            json.dump(history, f, indent=2)

        logger.debug(f"Logged {event_type} event to {log_path}")
        return True

    except Exception as e:
        logger.error(f"Error logging hook event: {e}")
        return False


def check_enabled(hook_name: str, config_path: str = ".claude/plugin.json") -> bool:
    """
    Check if a specific hook is enabled in plugin configuration.

    Args:
        hook_name: Name of hook to check (e.g., 'preToolUse')
        config_path: Path to plugin.json

    Returns:
        True if hook is enabled, False otherwise
    """
    config = load_plugin_config(config_path)

    if not config:
        # Default to enabled if no config
        logger.debug(f"No config found, defaulting hook {hook_name} to enabled")
        return True

    hooks_config = config.get('hooks', {})
    hook_list = hooks_config.get(hook_name, [])

    # If hook_list exists and has entries, check if any are enabled
    if isinstance(hook_list, list):
        for hook in hook_list:
            if isinstance(hook, dict) and hook.get('enabled', True):
                return True
        # If list exists but all disabled
        return False

    # Default to enabled
    return True


def get_config(
    key: str,
    default: Any = None,
    config_path: str = ".claude/plugin.json"
) -> Any:
    """
    Safe config retrieval with defaults.

    Args:
        key: Configuration key (supports dot notation, e.g., 'hooks.preToolUse')
        default: Default value if key not found
        config_path: Path to plugin.json

    Returns:
        Configuration value or default
    """
    config = load_plugin_config(config_path)

    if not config:
        return default

    # Support dot notation for nested keys
    keys = key.split('.')
    value = config

    for k in keys:
        if isinstance(value, dict):
            value = value.get(k)
        else:
            return default

        if value is None:
            return default

    return value


def is_file_tracked(file_path: str, rfc_map: Optional[Dict] = None) -> bool:
    """
    Check if a file is tracked in rfc-map.json.

    Args:
        file_path: File path to check
        rfc_map: Parsed rfc-map.json (will load if not provided)

    Returns:
        True if file has any mappings, False otherwise
    """
    if rfc_map is None:
        rfc_map = load_rfc_map()

    if not rfc_map:
        return False

    for mapping in rfc_map.get('mappings', []):
        code_file = mapping.get('code', {}).get('file', '')
        if code_file == file_path:
            return True

    return False


def get_tracked_files(rfc_map: Optional[Dict] = None) -> List[str]:
    """
    Get list of all files tracked in rfc-map.json.

    Args:
        rfc_map: Parsed rfc-map.json (will load if not provided)

    Returns:
        List of tracked file paths
    """
    if rfc_map is None:
        rfc_map = load_rfc_map()

    if not rfc_map:
        return []

    tracked_files = set()
    for mapping in rfc_map.get('mappings', []):
        code_file = mapping.get('code', {}).get('file', '')
        if code_file:
            tracked_files.add(code_file)

    return sorted(list(tracked_files))


def get_sections_for_file(file_path: str, rfc_map: Optional[Dict] = None) -> List[str]:
    """
    Get RFC sections that reference a specific file.

    Args:
        file_path: File path to query
        rfc_map: Parsed rfc-map.json (will load if not provided)

    Returns:
        List of RFC section numbers
    """
    if rfc_map is None:
        rfc_map = load_rfc_map()

    if not rfc_map:
        return []

    sections = set()
    for mapping in rfc_map.get('mappings', []):
        code_file = mapping.get('code', {}).get('file', '')
        if code_file == file_path:
            section = mapping.get('rfc', {}).get('section', '')
            if section:
                sections.add(section)

    return sorted(list(sections))


def format_section_list(sections: List[str], max_display: int = 3) -> str:
    """
    Format a list of section numbers for display.

    Args:
        sections: List of RFC section numbers
        max_display: Maximum sections to display before truncating

    Returns:
        Formatted string like "§3.2, §4.1, §5.3 (+2 more)"
    """
    if not sections:
        return "none"

    # Sort sections numerically if possible
    try:
        sorted_sections = sorted(sections, key=lambda s: [int(n) for n in s.split('.')])
    except (ValueError, AttributeError):
        sorted_sections = sorted(sections)

    displayed = sorted_sections[:max_display]
    formatted = ', '.join(f"§{s}" for s in displayed)

    if len(sorted_sections) > max_display:
        remaining = len(sorted_sections) - max_display
        formatted += f" (+{remaining} more)"

    return formatted


def run_make_validation(
    target: str,
    repo_root: Optional[str] = None,
    timeout: int = 10,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Run Make validation target and parse results.

    Args:
        target: Make target to run (e.g., 'lint', 'idnits', 'txt')
        repo_root: Repository root path (default: current directory)
        timeout: Timeout in seconds (default: 10)
        dry_run: If True, run with -n flag (no execution)

    Returns:
        Dictionary with 'success', 'output', 'errors' keys
    """
    import subprocess

    cmd = ['make']
    if dry_run:
        cmd.append('-n')
    cmd.append(target)

    result = {
        'success': False,
        'output': '',
        'errors': '',
        'returncode': -1
    }

    try:
        process = subprocess.run(
            cmd,
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        result['success'] = (process.returncode == 0)
        result['output'] = process.stdout
        result['errors'] = process.stderr
        result['returncode'] = process.returncode

        if process.returncode == 0:
            logger.debug(f"Make {target} succeeded")
        else:
            logger.warning(f"Make {target} failed with code {process.returncode}")

    except subprocess.TimeoutExpired:
        logger.error(f"Make {target} timed out after {timeout}s")
        result['errors'] = f"Command timed out after {timeout} seconds"
    except FileNotFoundError:
        logger.error("Make command not found")
        result['errors'] = "Make command not found in PATH"
    except Exception as e:
        logger.error(f"Error running make {target}: {e}")
        result['errors'] = str(e)

    return result


def is_rfc_file(file_path: str) -> bool:
    """
    Check if a file is an RFC document file.

    Args:
        file_path: File path to check

    Returns:
        True if file is an RFC document
    """
    rfc_patterns = [
        'draft-',  # IETF draft naming convention
        '.md',     # Markdown source
        '.xml',    # XML RFC format
        '.txt',    # Generated text
        '.html'    # Generated HTML
    ]

    file_path_lower = file_path.lower()
    return any(pattern in file_path_lower for pattern in rfc_patterns)


# Utility function for testing
def _example_usage():
    """Example usage of hook_utils module."""
    import sys

    print("=== Hook Utilities Example ===\n")

    # Load rfc-map
    rfc_map = load_rfc_map()
    if rfc_map:
        print(f"✅ Loaded rfc-map with {len(rfc_map.get('mappings', []))} mappings")
    else:
        print("❌ Failed to load rfc-map")

    # Load config
    config = load_plugin_config()
    if config:
        print(f"✅ Loaded plugin config")
        print(f"   Mandatory sections: {config.get('mandatory_sections', [])}")
    else:
        print("❌ No plugin config found")

    # Check tracked files
    tracked = get_tracked_files(rfc_map)
    print(f"\n📁 Tracked files: {len(tracked)}")
    for file_path in tracked[:5]:
        sections = get_sections_for_file(file_path, rfc_map)
        print(f"   {file_path} → {format_section_list(sections)}")

    # Format responses
    print("\n📋 Response formats:")
    print("Warning:", json.dumps(format_warning("Test warning", "Run /rfc-update"), indent=2))
    print("Error:", json.dumps(format_error("Test error", "Fix the issue"), indent=2))
    print("Success:", json.dumps(format_success("All good!"), indent=2))

    # Log event
    logged = log_hook_event("example_event", {"test": "data"})
    print(f"\n📝 Event logging: {'✅ Success' if logged else '❌ Failed'}")


if __name__ == "__main__":
    # Setup logging for standalone execution
    logging.basicConfig(level=logging.DEBUG)
    _example_usage()
