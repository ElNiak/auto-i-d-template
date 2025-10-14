#!/usr/bin/env python3
"""
PreToolUse Hook: Bash Command Enforcement

Blocks direct RFC tool invocations (kramdown-rfc, xml2rfc, mmark) and enforces
Make target usage per project constitution.

Performance Target: <100ms response time
Constitution: "All RFC transformations MUST go through Make targets"
"""

import sys
import json
import os
import re
import logging
from pathlib import Path

# Setup logging
LOG_DIR = Path(__file__).parent.parent / '.hook-logs'
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'pre_bash_enforce.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('pre_bash_enforce')

# Compile regex patterns at module load (performance optimization)
KRAMDOWN_REGEX = re.compile(
    r'(?:^|[;&|]|\s)'                          # Start or separator
    r'(?:bundle\s+exec\s+)?'                    # Optional: bundle exec
    r'(?:\S*/)?'                                # Optional: path prefix
    r'(kramdown-rfc2629|kramdown-rfc)'          # Tool name
    r'(?:\s|$|;|&&|\||>)',                     # End or separator
    re.IGNORECASE
)

XML2RFC_REGEX = re.compile(
    r'(?:^|[;&|]|\s)'                          # Start or separator
    r'(?:python3?\s+-m\s+)?'                    # Optional: python -m
    r'(?:\S*/)?'                                # Optional: path prefix
    r'(xml2rfc)'                                # Tool name
    r'(?:\s|$|;|&&|\||>)',                     # End or separator
    re.IGNORECASE
)

MMARK_REGEX = re.compile(
    r'(?:^|[;&|]|\s)'                          # Start or separator
    r'(?:\S*/)?'                                # Optional: path prefix
    r'(mmark)'                                  # Tool name
    r'(?:\s|$|;|&&|\||>)',                     # End or separator
    re.IGNORECASE
)

# Error message templates
ERROR_TEMPLATES = {
    'kramdown-rfc': {
        'message': (
            "🚫 Direct kramdown-rfc execution blocked per project constitution. "
            "All RFC transformations must go through Make targets."
        ),
        'suggestion': "Use 'make txt' to generate text output, or 'make html' for HTML output.",
        'docs': "See CLAUDE.md: 'Core Philosophy - Build automation through GNU Make'"
    },
    'xml2rfc': {
        'message': (
            "🚫 Direct xml2rfc execution blocked per project constitution. "
            "All RFC transformations must go through Make targets."
        ),
        'suggestion_text': "Use 'make txt' to generate text output.",
        'suggestion_html': "Use 'make html' to generate HTML output.",
        'docs': "See CLAUDE.md: 'Architecture - Build Pipeline'"
    },
    'mmark': {
        'message': (
            "🚫 Direct mmark execution blocked per project constitution. "
            "All RFC transformations must go through Make targets."
        ),
        'suggestion': "Use 'make txt' to generate text output from mmark-style markdown.",
        'docs': "See CLAUDE.md: 'Common Commands - Building Drafts'"
    }
}

# Allow-list of safe commands
ALLOWED_PREFIXES = {
    'make',      # Primary build method
    'git',       # Version control
    'ls', 'cat', 'grep', 'find', 'wc', 'sed', 'awk',  # Unix tools
    'head', 'tail', 'sort', 'uniq', 'cut', 'tr',
    'echo', 'printf', 'test', 'true', 'false',
    'cd', 'pwd', 'mkdir', 'rm', 'mv', 'cp', 'touch',
    'chmod', 'chown', 'ln', 'readlink',
}


def parse_hook_input() -> dict:
    """
    Parse hook invocation input from multiple possible sources.

    Returns:
        Tool arguments dictionary
    """
    tool_args = {}

    # Method 1: Environment variables
    command = os.environ.get('CLAUDE_TOOL_COMMAND')
    if command:
        tool_args = {'command': command}
        logger.debug(f"Parsed from env: command={command[:100]}")
        return tool_args

    # Method 2: stdin JSON
    try:
        if not sys.stdin.isatty():
            input_data = json.load(sys.stdin)
            tool_args = input_data.get('args', input_data.get('arguments', {}))
            logger.debug(f"Parsed from stdin: args={tool_args}")
            return tool_args
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Failed to parse stdin JSON: {e}")

    # Method 3: Command line arguments
    if len(sys.argv) > 1:
        try:
            tool_args = json.loads(sys.argv[1])
        except json.JSONDecodeError:
            # Treat as raw command
            tool_args = {'command': ' '.join(sys.argv[1:])}
        logger.debug(f"Parsed from argv: args={tool_args}")
        return tool_args

    logger.error("Could not parse hook input")
    return {}


def preprocess_command(command: str) -> str:
    """
    Remove comments and handle edge cases before pattern matching.

    Args:
        command: Raw bash command string

    Returns:
        Preprocessed command string
    """
    lines = command.split('\n')
    filtered = []

    for line in lines:
        # Skip comment-only lines
        stripped = line.strip()
        if stripped.startswith('#'):
            continue

        # Skip git clone URLs (false positive avoidance)
        if 'git clone' in line:
            continue

        filtered.append(line)

    return '\n'.join(filtered)


def is_allowed_command(command: str) -> bool:
    """
    Check if command is in the allow-list and safe to execute.

    Args:
        command: Bash command to check

    Returns:
        True if command should be allowed without blocking
    """
    command = command.strip().lower()

    if not command:
        return True

    # Extract first token (command name)
    tokens = command.split()
    if not tokens:
        return True

    first_token = tokens[0]

    # Remove path prefix if present
    if '/' in first_token:
        first_token = first_token.split('/')[-1]

    # Check against allow-list
    if first_token in ALLOWED_PREFIXES:
        logger.debug(f"Command '{first_token}' in allow-list")
        return True

    # Special case: bundle exec (check next token)
    if first_token == 'bundle' and len(tokens) > 2 and tokens[1] == 'exec':
        next_token = tokens[2]
        if '/' in next_token:
            next_token = next_token.split('/')[-1]
        if next_token == 'make':
            logger.debug("bundle exec make allowed")
            return True

    logger.debug(f"Command '{first_token}' not in allow-list")
    return False


def detect_tool_invocation(command: str) -> tuple[bool, str, str]:
    """
    Detect RFC tool invocations using regex patterns.

    Args:
        command: Preprocessed bash command

    Returns:
        (is_blocked, tool_name, suggested_make_target)
    """
    # Check kramdown-rfc
    kramdown_match = KRAMDOWN_REGEX.search(command)
    if kramdown_match:
        logger.info(f"Detected kramdown-rfc invocation: {kramdown_match.group(0)}")
        return (True, 'kramdown-rfc', 'make txt')

    # Check xml2rfc (context-aware suggestion)
    xml2rfc_match = XML2RFC_REGEX.search(command)
    if xml2rfc_match:
        logger.info(f"Detected xml2rfc invocation: {xml2rfc_match.group(0)}")
        # Determine suggested target based on flags
        if '--html' in command or '--css' in command:
            return (True, 'xml2rfc', 'make html')
        else:
            return (True, 'xml2rfc', 'make txt')

    # Check mmark
    mmark_match = MMARK_REGEX.search(command)
    if mmark_match:
        logger.info(f"Detected mmark invocation: {mmark_match.group(0)}")
        return (True, 'mmark', 'make txt')

    return (False, '', '')


def is_informational_command(command: str) -> bool:
    """
    Check if command is just asking for help/version info.

    Args:
        command: Bash command

    Returns:
        True if command is informational (--help, --version)
    """
    return any(flag in command for flag in ['--help', '-h', '--version', '-v', 'help'])


def generate_error_message(tool_name: str, command: str, make_target: str) -> dict:
    """
    Generate context-aware error message for blocked tool.

    Args:
        tool_name: Name of blocked tool
        command: Full command that was blocked
        make_target: Suggested Make target to use instead

    Returns:
        Hook response dict with block=True
    """
    template = ERROR_TEMPLATES.get(tool_name, {})

    # Handle informational commands differently
    if is_informational_command(command):
        return {
            'block': True,
            'message': (
                f"⚠️  {tool_name} should be invoked via Make targets. "
                f"For version info, check deps.mk configuration or .venv/bin/{tool_name}."
            ),
            'suggestion': f"Use '{make_target}' for RFC generation instead.",
            'metadata': {
                'tool': tool_name,
                'type': 'informational',
                'blocked_command': command[:100]
            }
        }

    # Determine suggestion based on tool and context
    if tool_name == 'xml2rfc':
        if make_target == 'make html':
            suggestion = template.get('suggestion_html', f"Use '{make_target}'")
        else:
            suggestion = template.get('suggestion_text', f"Use '{make_target}'")
    else:
        suggestion = template.get('suggestion', f"Use '{make_target}' instead.")

    return {
        'block': True,
        'message': template.get('message', f'Direct {tool_name} execution blocked.'),
        'suggestion': suggestion,
        'metadata': {
            'tool': tool_name,
            'docs': template.get('docs', ''),
            'blocked_command': command[:100],
            'suggested_target': make_target
        }
    }


def parse_multiline_command(command: str) -> list[str]:
    """
    Split multi-line bash commands into individual statements.

    Handles line continuations, semicolons, &&, ||, |

    Args:
        command: Multi-line bash command string

    Returns:
        List of individual command statements
    """
    # Remove line continuation backslashes
    command = command.replace('\\\n', ' ')

    # Split on command separators (naive approach - sufficient for common cases)
    statements = re.split(r'[;&]+', command)

    # Filter empty statements
    return [stmt.strip() for stmt in statements if stmt.strip()]


def check_command_enforcement(command: str) -> dict:
    """
    Main enforcement logic - check command and return response.

    Args:
        command: Bash command to check

    Returns:
        Hook response dictionary
    """
    # Preprocess command
    processed = preprocess_command(command)

    if not processed:
        logger.debug("Empty command after preprocessing")
        return {'block': False, 'message': '', 'suggestion': ''}

    # Handle multi-line commands
    statements = parse_multiline_command(processed)

    for stmt in statements:
        # Check allow-list first (fast path)
        if is_allowed_command(stmt):
            continue

        # Detect blocked tool invocations
        is_blocked, tool_name, make_target = detect_tool_invocation(stmt)

        if is_blocked:
            return generate_error_message(tool_name, stmt, make_target)

    # All statements allowed
    return {'block': False, 'message': '', 'suggestion': ''}


def main():
    """Hook entry point - enforces Make target usage for RFC tools."""

    logger.info("=== PreToolUse Hook (Bash Enforcement) Started ===")

    # Initialize response
    response = {
        "block": False,
        "message": "",
        "suggestion": ""
    }

    try:
        # Parse hook input
        tool_args = parse_hook_input()

        if not tool_args:
            logger.error("Failed to parse hook input")
            response["message"] = "Hook error: Could not parse tool invocation"
            print(json.dumps(response))
            return

        # Extract command
        command = tool_args.get('command', '')

        if not command:
            logger.warning("No command found in tool arguments")
            print(json.dumps(response))
            return

        logger.info(f"Checking command: {command[:200]}")

        # Enforce Make target usage
        response = check_command_enforcement(command)

        if response['block']:
            logger.warning(f"BLOCKED: {response['message']}")
        else:
            logger.info("Command allowed")

    except Exception as e:
        logger.exception(f"Unexpected error in hook: {e}")
        # Don't block on errors (graceful degradation)
        response["block"] = False
        response["message"] = f"Hook error: {str(e)}"
        response["suggestion"] = "Check .claude/.hook-logs/pre_bash_enforce.log"

    finally:
        # Return response to Claude Code
        print(json.dumps(response))
        logger.info(f"=== Hook Complete: block={response['block']} ===")


if __name__ == "__main__":
    main()
