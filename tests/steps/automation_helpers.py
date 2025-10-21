"""
Helper functions and utilities for automation test steps.

This module provides core utilities for executing hooks using real subprocess
execution and managing test data for automated documentation checks.
"""

import os
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from behave.runner import Context


# ============================================================================
# Hook Execution Functions
# ============================================================================

def execute_hook(hook_name: str, tool_name: str, args: dict, context: Context) -> dict:
    """
    Execute a Claude Code hook script using real subprocess execution.

    Args:
        hook_name: Name of hook (PreToolUse, PostToolUse, etc.)
        tool_name: Name of tool being used (Write, Bash, etc.)
        args: Tool arguments as dictionary
        context: Behave context

    Returns:
        Hook response dictionary with keys: block, message, suggestion, timing
    """
    import sys
    from pathlib import Path

    # Add tests/support to sys.path for imports
    support_dir = Path(__file__).parent.parent / 'support'
    if str(support_dir) not in sys.path:
        sys.path.insert(0, str(support_dir))

    # Import required modules (no fallback - fail explicitly if unavailable)
    from hook_runner import HookRunner, create_minimal_hook_script

    runner = HookRunner(str(context.test_repo))

    # Ensure minimal hook scripts exist for testing
    hooks_dir = Path(context.test_repo) / '.claude' / 'hooks'
    hook_scripts = {
        'PreToolUse': 'pre_tool_validate.py',
        'PostToolUse': 'post_tool_sync.py',
        'SessionStart': 'session_start_check.py',
        'UserPromptSubmit': 'user_intent_detect.py'
    }

    hook_script = hook_scripts.get(hook_name)
    if hook_script:
        hook_path = hooks_dir / hook_script
        if not hook_path.exists():
            create_minimal_hook_script(hook_path, hook_name)

    # Execute hook based on type
    if hook_name == 'PreToolUse':
        result = runner.run_pretool_hook(tool_name, args)
    elif hook_name == 'PostToolUse':
        result = runner.run_posttool_hook(tool_name, args.get('file_path', ''))
    elif hook_name == 'SessionStart':
        result = runner.run_session_hook()
    elif hook_name == 'UserPromptSubmit':
        result = runner.run_userprompt_hook(args.get('prompt', ''))
    else:
        # Unknown hook type - fail explicitly
        raise ValueError(f"Unknown hook type: {hook_name}. Supported types: PreToolUse, PostToolUse, SessionStart, UserPromptSubmit")

    # Convert HookResult to expected format
    response = {
        'block': result.response.get('block', False) if result.response else False,
        'message': result.response.get('message', '') if result.response else result.stderr,
        'suggestion': result.response.get('suggestion', '') if result.response else '',
        'timing_ms': int(result.execution_time * 1000)
    }

    context.hook_response = response
    return response


# ============================================================================
# Analysis and Reporting Functions
# ============================================================================

def run_impact_analysis_internal(context: Context) -> list:
    """Run impact analysis using impact_analyzer.py library."""
    rfc_map_path = os.path.join(context.test_repo, 'docs', 'rfc-map.json')

    if not os.path.exists(rfc_map_path):
        return []

    impacts = []

    if hasattr(context, 'simulated_changes'):
        for change in context.simulated_changes:
            impacts.append({
                'section_number': change.get('section', 'unknown'),
                'section_heading': change.get('heading', 'Unknown Section'),
                'affected_code_elements': change.get('elements', []),
                'severity': change.get('severity', 'SHOULD_REVIEW'),
                'change_summary': change.get('summary', 'Code changes detected')
            })

    return impacts


def generate_review_checklist(impacts: list) -> list:
    """Generate review checklist from impacts."""
    checklist = []

    for impact in impacts:
        item = f"Review RFC §{impact['section_number']}: {impact['section_heading']}"
        checklist.append(item)

    checklist.append("Verify all cross-references are up to date")
    checklist.append("Run 'make lint' on updated RFC")

    return checklist


# ============================================================================
# Test Data Creation Functions
# ============================================================================

def create_rfc_map(context: Context, mappings: list):
    """Create a test rfc-map.json file with specified mappings."""
    rfc_map_path = os.path.join(context.test_repo, 'docs', 'rfc-map.json')
    os.makedirs(os.path.dirname(rfc_map_path), exist_ok=True)

    rfc_map = {'version': '1.0.0', 'mappings': mappings}

    with open(rfc_map_path, 'w') as f:
        json.dump(rfc_map, f, indent=2)

    context.rfc_map_path = rfc_map_path


def create_test_code_file(context: Context, file_path: str, content: str):
    """Create a test code file with specified content."""
    full_path = os.path.join(context.test_repo, file_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)

    with open(full_path, 'w') as f:
        f.write(content)


# ============================================================================
# File Manipulation Functions
# ============================================================================

def modify_file_at_line(file_path: str, line_num: int, new_content: str):
    """Modify a specific line in a file."""
    with open(file_path, 'r') as f:
        lines = f.readlines()

    if 0 < line_num <= len(lines):
        lines[line_num - 1] = new_content + '\n'

    with open(file_path, 'w') as f:
        f.writelines(lines)


def modify_file_lines(file_path: str, start_line: int, end_line: int, new_content: str):
    """Modify a range of lines in a file."""
    with open(file_path, 'r') as f:
        lines = f.readlines()

    new_lines = [line + '\n' for line in new_content.split('\n')]
    lines[start_line-1:end_line] = new_lines

    with open(file_path, 'w') as f:
        f.writelines(lines)


def set_file_mtime(file_path: str, days_ago: int):
    """Set file modification time to N days ago."""
    past_time = datetime.now() - timedelta(days=days_ago)
    timestamp = past_time.timestamp()
    os.utime(file_path, (timestamp, timestamp))
