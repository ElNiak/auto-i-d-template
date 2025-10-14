#!/usr/bin/env python3
"""
PreToolUse Hook: RFC Cross-Reference Validator

Intercepts Write/Edit tool calls to detect modifications to RFC-tracked files.
Returns non-blocking warnings with affected RFC sections.

Performance Target: <100ms response time
Strategy: Simple file path lookup in rfc-map.json (no git diff analysis)
"""

import sys
import json
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional

# Setup logging
LOG_DIR = Path(__file__).parent.parent / '.hook-logs'
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'pre_tool_validate.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('pre_tool_validate')


def parse_hook_input() -> tuple[str, Dict]:
    """
    Parse hook invocation input from multiple possible sources.

    Claude Code may pass input via:
    1. Environment variables (CLAUDE_TOOL_NAME, CLAUDE_TOOL_FILE_PATH)
    2. stdin JSON
    3. Command line arguments

    Returns:
        (tool_name, tool_args) tuple
    """
    tool_name = None
    tool_args = {}

    # Method 1: Environment variables (preferred for performance)
    tool_name = os.environ.get('CLAUDE_TOOL_NAME')
    if tool_name:
        tool_args = {
            'file_path': os.environ.get('CLAUDE_TOOL_FILE_PATH', ''),
            'content': os.environ.get('CLAUDE_TOOL_CONTENT', ''),
            'command': os.environ.get('CLAUDE_TOOL_COMMAND', '')
        }
        logger.debug(f"Parsed from env: tool={tool_name}, args={tool_args}")
        return tool_name, tool_args

    # Method 2: stdin JSON
    try:
        if not sys.stdin.isatty():
            input_data = json.load(sys.stdin)
            tool_name = input_data.get('tool', input_data.get('tool_name'))
            tool_args = input_data.get('args', input_data.get('arguments', {}))
            logger.debug(f"Parsed from stdin: tool={tool_name}, args={tool_args}")
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
                # Fallback: treat as file path
                tool_args = {'file_path': sys.argv[2]}
        logger.debug(f"Parsed from argv: tool={tool_name}, args={tool_args}")
        return tool_name, tool_args

    # Fallback: unknown invocation
    logger.error("Could not determine hook invocation method")
    return None, {}


def get_repository_root() -> Optional[Path]:
    """Find repository root by looking for .git directory."""
    current = Path.cwd()
    while current != current.parent:
        if (current / '.git').exists():
            return current
        current = current.parent
    return None


def load_rfc_map(rfc_map_path: Path) -> Optional[Dict]:
    """
    Load and parse rfc-map.json with error handling.

    Args:
        rfc_map_path: Path to rfc-map.json

    Returns:
        Parsed JSON dict or None on error
    """
    if not rfc_map_path.exists():
        logger.warning(f"rfc-map.json not found at {rfc_map_path}")
        return None

    try:
        with open(rfc_map_path, 'r') as f:
            rfc_map = json.load(f)

        # Validate structure
        if 'mappings' not in rfc_map:
            logger.error("rfc-map.json missing 'mappings' key")
            return None

        logger.debug(f"Loaded rfc-map.json with {len(rfc_map['mappings'])} mappings")
        return rfc_map

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in rfc-map.json: {e}")
        return None
    except Exception as e:
        logger.error(f"Error reading rfc-map.json: {e}")
        return None


def extract_file_path(tool_name: str, tool_args: Dict, repo_root: Path) -> Optional[str]:
    """
    Extract file path from tool arguments and normalize to relative path.

    Args:
        tool_name: Name of the tool (Write, Edit, etc.)
        tool_args: Tool arguments dict
        repo_root: Repository root path

    Returns:
        Relative file path or None
    """
    file_path = None

    # Extract path based on tool type
    if tool_name in ['Write', 'Edit']:
        file_path = tool_args.get('file_path', '')
    elif tool_name == 'Bash':
        # For Bash, we don't validate file paths (handled by pre_bash_enforce.py)
        return None

    if not file_path:
        logger.debug(f"No file_path found in {tool_name} arguments")
        return None

    # Convert to Path and make relative to repo root
    file_path = Path(file_path)

    # Handle absolute paths
    if file_path.is_absolute():
        try:
            file_path = file_path.relative_to(repo_root)
        except ValueError:
            # Path is outside repository
            logger.warning(f"File path {file_path} is outside repository")
            return None

    return str(file_path)


def find_affected_sections(file_path: str, rfc_map: Dict) -> List[Dict[str, str]]:
    """
    Fast lookup: Check if file is tracked in rfc-map.json.

    Args:
        file_path: Relative file path
        rfc_map: Parsed rfc-map.json dict

    Returns:
        List of affected sections with metadata
    """
    affected = []

    for mapping in rfc_map.get('mappings', []):
        code_info = mapping.get('code', {})
        rfc_info = mapping.get('rfc', {})

        # Match file path
        if code_info.get('file') == file_path:
            affected.append({
                'section': rfc_info.get('section', 'unknown'),
                'heading': rfc_info.get('heading', 'Unknown Section'),
                'symbol': code_info.get('symbol', ''),
                'line': code_info.get('line', 0)
            })

    logger.debug(f"Found {len(affected)} affected sections for {file_path}")
    return affected


def format_warning_message(affected_sections: List[Dict[str, str]], file_path: str) -> str:
    """
    Format user-facing warning message.

    Args:
        affected_sections: List of affected section dicts
        file_path: File being modified

    Returns:
        Formatted warning message
    """
    if not affected_sections:
        return ""

    # Limit to first 3 sections to avoid UI clutter
    display_sections = affected_sections[:3]

    # Format section list
    section_list = []
    for sect in display_sections:
        section_num = sect['section']
        heading = sect['heading']
        section_list.append(f"§{section_num}: {heading}")

    message = f"⚠️  Modifying RFC-tracked file: {file_path}\n"
    message += f"Affects RFC sections: {', '.join(section_list)}"

    if len(affected_sections) > 3:
        message += f" (+{len(affected_sections) - 3} more)"

    return message


def main():
    """Hook entry point - validates RFC cross-references before tool execution."""

    logger.info("=== PreToolUse Hook Started ===")

    # Initialize response
    response = {
        "block": False,
        "message": "",
        "suggestion": ""
    }

    try:
        # Parse hook input
        tool_name, tool_args = parse_hook_input()

        if not tool_name:
            logger.error("Failed to parse hook input")
            response["message"] = "Hook error: Could not parse tool invocation"
            print(json.dumps(response))
            return

        logger.info(f"Tool: {tool_name}, Args: {tool_args}")

        # Find repository root
        repo_root = get_repository_root()
        if not repo_root:
            logger.warning("Not in a git repository")
            response["message"] = "Not in a git repository"
            print(json.dumps(response))
            return

        # Load rfc-map.json
        rfc_map_path = repo_root / 'docs' / 'rfc-map.json'
        rfc_map = load_rfc_map(rfc_map_path)

        if rfc_map is None:
            # Graceful degradation: suggest generating RFC docs
            logger.info("No RFC documentation found")
            response["message"] = "No RFC documentation found"
            response["suggestion"] = "Run /rfc-generate to create initial RFC documentation"
            print(json.dumps(response))
            return

        # Extract file path from tool arguments
        file_path = extract_file_path(tool_name, tool_args, repo_root)

        if not file_path:
            logger.debug("No file path to validate")
            print(json.dumps(response))
            return

        # Check if file is tracked in rfc-map.json
        affected_sections = find_affected_sections(file_path, rfc_map)

        if affected_sections:
            # Generate warning
            response["message"] = format_warning_message(affected_sections, file_path)
            response["suggestion"] = "Run /rfc-analyze-impact for detailed semantic analysis"
            logger.info(f"Warning generated: {len(affected_sections)} sections affected")
        else:
            logger.info(f"File {file_path} not tracked in RFC documentation")

        # Always non-blocking (per FR-011)
        response["block"] = False

    except Exception as e:
        logger.exception(f"Unexpected error in hook: {e}")
        response["block"] = False
        response["message"] = f"Hook error: {str(e)}"
        response["suggestion"] = "Check .claude/.hook-logs/pre_tool_validate.log"

    finally:
        # Return response to Claude Code
        print(json.dumps(response))
        logger.info(f"=== Hook Complete: block={response['block']} ===")


if __name__ == "__main__":
    main()
