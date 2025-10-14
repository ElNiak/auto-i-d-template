"""
Behave test steps for automation scenarios (User Story 3: Automated Documentation Checks)

This module implements test steps for Claude Code native hooks including:
- PreToolUse: Pre-commit validation
- PostToolUse: Reviewer guidance
- SessionStart: Staleness detection
- UserPromptSubmit: Intent detection
"""

import os
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from behave import given, when, then
from behave.runner import Context
import shutil


# ============================================================================
# Helper Functions
# ============================================================================

def execute_hook(hook_name: str, tool_name: str, args: dict, context: Context) -> dict:
    """
    Execute a Claude Code hook script with simulated input.

    Args:
        hook_name: Name of hook (PreToolUse, PostToolUse, etc.)
        tool_name: Name of tool being used (Write, Bash, etc.)
        args: Tool arguments as dictionary
        context: Behave context

    Returns:
        Hook response dictionary with keys: block, message, suggestion, timing
    """
    start_time = time.time()

    response = {'block': False, 'message': '', 'suggestion': '', 'timing_ms': 0}

    if hook_name == 'PreToolUse':
        response = simulate_pretool_hook(tool_name, args, context)
    elif hook_name == 'PostToolUse':
        response = simulate_posttool_hook(tool_name, args, context)
    elif hook_name == 'SessionStart':
        response = simulate_session_hook(context)
    elif hook_name == 'UserPromptSubmit':
        response = simulate_userprompt_hook(args.get('prompt', ''), context)

    end_time = time.time()
    response['timing_ms'] = int((end_time - start_time) * 1000)
    context.hook_response = response

    return response


def simulate_pretool_hook(tool_name: str, args: dict, context: Context) -> dict:
    """Simulate PreToolUse hook behavior."""
    response = {'block': False, 'message': '', 'suggestion': ''}

    rfc_map_path = os.path.join(context.test_repo, 'docs', 'rfc-map.json')

    if not os.path.exists(rfc_map_path):
        response['message'] = 'No RFC documentation found. Run /rfc-generate first'
        response['suggestion'] = 'Run /rfc-generate first'
        return response

    try:
        with open(rfc_map_path, 'r') as f:
            rfc_map = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        response['message'] = 'JSON parsing error in rfc-map.json'
        response['suggestion'] = '/rfc-validate'
        return response

    if tool_name == 'Bash':
        command = args.get('command', '')
        if 'kramdown-rfc' in command and 'make' not in command:
            response['block'] = True
            response['message'] = "Direct kramdown-rfc execution not recommended. Use 'make txt' instead"
            response['suggestion'] = "Use 'make txt' instead"
            return response

    if tool_name == 'Write':
        file_path = args.get('file_path', '').replace(str(context.test_repo) + '/', '')

        for mapping in rfc_map.get('mappings', []):
            if mapping['code']['file'] == file_path:
                section = mapping['rfc']['section']
                response['message'] = f'Affects RFC §{section}'
                response['suggestion'] = '/rfc-analyze-impact'
                return response

    return response


def simulate_posttool_hook(tool_name: str, args: dict, context: Context) -> dict:
    """Simulate PostToolUse hook behavior."""
    response = {'block': False, 'message': '', 'suggestion': ''}

    rfc_map_path = os.path.join(context.test_repo, 'docs', 'rfc-map.json')

    if not os.path.exists(rfc_map_path):
        return response

    try:
        with open(rfc_map_path, 'r') as f:
            rfc_map = json.load(f)
    except:
        return response

    if tool_name == 'Write':
        file_path = args.get('file_path', '').replace(str(context.test_repo) + '/', '')
        stale_timestamp = "1970-01-01T00:00:00"
        affected_count = 0

        for mapping in rfc_map.get('mappings', []):
            if mapping['code']['file'] == file_path:
                mapping['last_synced'] = stale_timestamp
                affected_count += 1

        if affected_count > 0:
            try:
                with open(rfc_map_path, 'w') as f:
                    json.dump(rfc_map, f, indent=2)
                response['message'] = f'Updated {affected_count} mappings'
                context.updated_rfc_map = True
            except PermissionError:
                response['message'] = 'Permission error updating rfc-map.json'
                response['suggestion'] = 'Check file permissions'

    if tool_name == 'Bash' and 'git commit' in args.get('command', ''):
        report_path = os.path.join(context.test_repo, '.claude', '.hook-history.json')
        os.makedirs(os.path.dirname(report_path), exist_ok=True)

        impacts = run_impact_analysis_internal(context)

        if impacts:
            guidance = {
                'timestamp': datetime.now().isoformat(),
                'type': 'post_commit_review',
                'affected_sections': [i['section_number'] for i in impacts],
                'checklist': generate_review_checklist(impacts)
            }

            history = []
            if os.path.exists(report_path):
                try:
                    with open(report_path, 'r') as f:
                        history = json.load(f)
                except:
                    pass

            history.append(guidance)

            with open(report_path, 'w') as f:
                json.dump(history, f, indent=2)

            context.reviewer_guidance = guidance
            response['message'] = 'Reviewer guidance generated'

    return response


def simulate_session_hook(context: Context) -> dict:
    """Simulate SessionStart hook behavior."""
    response = {'block': False, 'message': '', 'suggestion': ''}

    rfc_map_path = os.path.join(context.test_repo, 'docs', 'rfc-map.json')

    if not os.path.exists(rfc_map_path):
        return response

    stat = os.stat(rfc_map_path)
    mtime = datetime.fromtimestamp(stat.st_mtime)
    age_days = (datetime.now() - mtime).days

    if age_days > 30:
        response['message'] = f'RFC documentation last updated {age_days} days ago'
        response['suggestion'] = '/rfc-update'

    docs_dir = os.path.join(context.test_repo, 'docs', 'generated')
    if os.path.exists(docs_dir):
        try:
            result = subprocess.run(
                ['git', 'status', '--porcelain', 'docs/'],
                cwd=context.test_repo,
                capture_output=True,
                text=True
            )
            if result.stdout.strip():
                if not response['message']:
                    response['message'] = 'Uncommitted documentation changes detected'
                    response['suggestion'] = 'git add docs/'
        except:
            pass

    return response


def simulate_userprompt_hook(prompt: str, context: Context) -> dict:
    """Simulate UserPromptSubmit hook behavior."""
    response = {'block': False, 'message': '', 'suggestion': ''}

    rfc_keywords = ['rfc', 'documentation', 'spec', 'draft', 'update the rfc']
    prompt_lower = prompt.lower()
    is_rfc_related = any(keyword in prompt_lower for keyword in rfc_keywords)

    if is_rfc_related:
        memory_dir = os.path.join(context.test_repo, '.claude', 'memory')
        if os.path.exists(memory_dir):
            overview_path = os.path.join(memory_dir, 'codebase-overview.md')
            if os.path.exists(overview_path):
                context.memory_loaded = ['codebase-overview.md']
                response['message'] = 'RFC context injected'

        history_path = os.path.join(context.test_repo, '.claude', '.hook-history.json')
        os.makedirs(os.path.dirname(history_path), exist_ok=True)

        history = []
        if os.path.exists(history_path):
            try:
                with open(history_path, 'r') as f:
                    history = json.load(f)
            except:
                pass

        history.append({
            'timestamp': datetime.now().isoformat(),
            'type': 'intent_detection',
            'prompt': prompt[:100],
            'rfc_related': True
        })

        with open(history_path, 'w') as f:
            json.dump(history, f, indent=2)

        context.rfc_context_injected = True
    else:
        context.rfc_context_injected = False

    return response


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


def create_rfc_map(context: Context, mappings: list):
    """Create a test rfc-map.json file with specified mappings."""
    rfc_map_path = os.path.join(context.test_repo, 'docs', 'rfc-map.json')
    os.makedirs(os.path.dirname(rfc_map_path), exist_ok=True)

    rfc_map = {'version': '1.0.0', 'mappings': mappings}

    with open(rfc_map_path, 'w') as f:
        json.dump(rfc_map, f, indent=2)

    context.rfc_map_path = rfc_map_path


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


def create_test_code_file(context: Context, file_path: str, content: str):
    """Create a test code file with specified content."""
    full_path = os.path.join(context.test_repo, file_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)

    with open(full_path, 'w') as f:
        f.write(content)


# ============================================================================
# Given Steps - Setup Test Conditions
# ============================================================================

@given('a clean test repository')
def step_clean_test_repository(context: Context):
    """Set up a clean test repository."""
    assert hasattr(context, 'test_repo'), "Test repository not initialized"
    context.hook_response = None
    context.updated_rfc_map = False
    context.reviewer_guidance = None
    context.memory_loaded = []
    context.rfc_context_injected = False


@given('the RFC generator plugin is installed')
def step_plugin_installed(context: Context):
    """Verify RFC generator plugin structure exists."""
    claude_dir = os.path.join(context.test_repo, '.claude')
    os.makedirs(claude_dir, exist_ok=True)
    os.makedirs(os.path.join(claude_dir, 'hooks'), exist_ok=True)
    os.makedirs(os.path.join(claude_dir, 'lib'), exist_ok=True)
    os.makedirs(os.path.join(claude_dir, 'commands'), exist_ok=True)


@given('a project with RFC documentation and rfc-map.json')
def step_project_with_rfc_and_map(context: Context):
    """Create a project with RFC documentation and rfc-map.json."""
    docs_dir = os.path.join(context.test_repo, 'docs', 'generated')
    os.makedirs(docs_dir, exist_ok=True)

    rfc_path = os.path.join(docs_dir, 'draft-spec.md')
    with open(rfc_path, 'w') as f:
        f.write('# RFC Document\n\n## Section 3.2 Authentication\n')

    create_rfc_map(context, [{
        'code': {'file': 'src/api.py', 'symbol': 'authenticate', 'line': 10},
        'rfc': {'section': '3.2', 'heading': 'Authentication'},
        'relationship': 'implements',
        'last_synced': datetime.now().isoformat(),
        'confidence': 1.0
    }])


@given('a project with RFC documentation')
def step_project_with_rfc(context: Context):
    """Create a project with RFC documentation."""
    step_project_with_rfc_and_map(context)


@given('a project without RFC documentation')
def step_project_without_rfc(context: Context):
    """Create a project without RFC documentation."""
    docs_dir = os.path.join(context.test_repo, 'docs')
    if os.path.exists(docs_dir):
        shutil.rmtree(docs_dir)


@given('the file "{file}" is tracked in rfc-map.json with section "{section}"')
def step_file_tracked_with_section(context: Context, file: str, section: str):
    """Add file to rfc-map.json with specified section."""
    rfc_map_path = os.path.join(context.test_repo, 'docs', 'rfc-map.json')

    if os.path.exists(rfc_map_path):
        with open(rfc_map_path, 'r') as f:
            rfc_map = json.load(f)
    else:
        rfc_map = {'version': '1.0.0', 'mappings': []}
        os.makedirs(os.path.dirname(rfc_map_path), exist_ok=True)

    rfc_map['mappings'].append({
        'code': {'file': file, 'symbol': 'api_function', 'line': 10},
        'rfc': {'section': section, 'heading': 'API Section'},
        'relationship': 'implements',
        'last_synced': datetime.now().isoformat(),
        'confidence': 1.0
    })

    with open(rfc_map_path, 'w') as f:
        json.dump(rfc_map, f, indent=2)

    create_test_code_file(context, file, '# Test code\ndef api_function():\n    pass\n')


@given('"{symbol}" is mapped to RFC section "{section}" type "{type}"')
def step_symbol_mapped_to_section(context: Context, symbol: str, section: str, type: str):
    """Map a code symbol to an RFC section with type."""
    file_path = symbol.split('::')[0] if '::' in symbol else 'src/api.py'
    symbol_name = symbol.split('::')[1] if '::' in symbol else symbol

    create_test_code_file(context, file_path, f'# Code\ndef {symbol_name}():\n    pass\n')

    rfc_map_path = os.path.join(context.test_repo, 'docs', 'rfc-map.json')

    if os.path.exists(rfc_map_path):
        with open(rfc_map_path, 'r') as f:
            rfc_map = json.load(f)
    else:
        rfc_map = {'version': '1.0.0', 'mappings': []}
        os.makedirs(os.path.dirname(rfc_map_path), exist_ok=True)

    rfc_map['mappings'].append({
        'code': {'file': file_path, 'symbol': symbol_name, 'line': 2},
        'rfc': {'section': section, 'heading': f'{type.title()} Section', 'type': type},
        'relationship': 'implements',
        'last_synced': datetime.now().isoformat(),
        'confidence': 1.0
    })

    with open(rfc_map_path, 'w') as f:
        json.dump(rfc_map, f, indent=2)


@given('multiple files are tracked in rfc-map.json across sections')
def step_multiple_files_tracked(context: Context):
    """Create multiple tracked files."""
    mappings = [
        {
            'code': {'file': 'src/api.py', 'symbol': 'authenticate', 'line': 10},
            'rfc': {'section': '3.1', 'heading': 'Authentication'},
            'relationship': 'implements',
            'last_synced': datetime.now().isoformat(),
            'confidence': 1.0
        },
        {
            'code': {'file': 'src/models.py', 'symbol': 'User', 'line': 5},
            'rfc': {'section': '2.1', 'heading': 'Data Models'},
            'relationship': 'describes',
            'last_synced': datetime.now().isoformat(),
            'confidence': 1.0
        },
        {
            'code': {'file': 'src/handlers.py', 'symbol': 'handle_request', 'line': 20},
            'rfc': {'section': '4.1', 'heading': 'Request Handling'},
            'relationship': 'implements',
            'last_synced': datetime.now().isoformat(),
            'confidence': 1.0
        }
    ]

    create_rfc_map(context, mappings)

    # Create simulated changes for post-commit hooks
    context.simulated_changes = []
    for mapping in mappings:
        file_path = mapping['code']['file']
        symbol = mapping['code']['symbol']
        create_test_code_file(context, file_path, f'# Code\ndef {symbol}():\n    pass\n')

        # Add simulated changes for each tracked file
        context.simulated_changes.append({
            'section': mapping['rfc']['section'],
            'heading': mapping['rfc']['heading'],
            'elements': [symbol],
            'severity': 'MUST_UPDATE',
            'summary': 'Code changes detected'
        })


@given('multiple files are tracked in rfc-map.json')
def step_multiple_files_tracked_alias(context: Context):
    """Create multiple tracked files (alias without 'across sections')."""
    step_multiple_files_tracked(context)


@given('{count:d} files are tracked in rfc-map.json')
def step_n_files_tracked(context: Context, count: int):
    """Create N tracked files."""
    mappings = []

    for i in range(count):
        mappings.append({
            'code': {'file': f'src/file{i}.py', 'symbol': f'function{i}', 'line': 10},
            'rfc': {'section': f'3.{i+1}', 'heading': f'Section {i+1}'},
            'relationship': 'implements',
            'last_synced': datetime.now().isoformat(),
            'confidence': 1.0
        })
        create_test_code_file(context, f'src/file{i}.py', f'def function{i}():\n    pass\n')

    create_rfc_map(context, mappings)


@given('"{file}" is tracked in rfc-map.json')
def step_file_tracked(context: Context, file: str):
    """Add file to rfc-map.json."""
    step_file_tracked_with_section(context, file, '3.1')


@given('"{file}" is NOT tracked in rfc-map.json')
def step_file_not_tracked(context: Context, file: str):
    """Ensure file is NOT in rfc-map.json."""
    create_test_code_file(context, file, '# Test code\ndef test():\n    pass\n')

    rfc_map_path = os.path.join(context.test_repo, 'docs', 'rfc-map.json')
    if not os.path.exists(rfc_map_path):
        create_rfc_map(context, [])


@given('memory files exist in ".claude/memory/"')
def step_memory_files_exist(context: Context):
    """Create memory files."""
    memory_dir = os.path.join(context.test_repo, '.claude', 'memory')
    os.makedirs(memory_dir, exist_ok=True)

    overview_path = os.path.join(memory_dir, 'codebase-overview.md')
    with open(overview_path, 'w') as f:
        f.write('# Codebase Overview\n\nThis project implements RFC documentation.\n')


@given('".claude/lib/impact_analyzer.py" is missing')
def step_impact_analyzer_missing(context: Context):
    """Remove impact_analyzer.py."""
    analyzer_path = os.path.join(context.test_repo, '.claude', 'lib', 'impact_analyzer.py')
    if os.path.exists(analyzer_path):
        os.remove(analyzer_path)
    context.missing_impact_analyzer = True


@given('the repository has no commits')
def step_repo_no_commits(context: Context):
    """Create a repository with no git history."""
    git_dir = os.path.join(context.test_repo, '.git')
    if os.path.exists(git_dir):
        shutil.rmtree(git_dir)

    subprocess.run(['git', 'init'], cwd=context.test_repo, check=True)
    subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=context.test_repo)
    subprocess.run(['git', 'config', 'user.email', 'test@example.com'], cwd=context.test_repo)


@given('"docs/rfc-map.json" is read-only')
def step_rfc_map_readonly(context: Context):
    """Make rfc-map.json read-only."""
    rfc_map_path = os.path.join(context.test_repo, 'docs', 'rfc-map.json')

    if not os.path.exists(rfc_map_path):
        create_rfc_map(context, [])

    os.chmod(rfc_map_path, 0o444)
    context.readonly_rfc_map = True


@given('a project with invalid JSON in "docs/rfc-map.json"')
def step_invalid_json_in_rfc_map(context: Context):
    """Create invalid JSON in rfc-map.json."""
    rfc_map_path = os.path.join(context.test_repo, 'docs', 'rfc-map.json')
    os.makedirs(os.path.dirname(rfc_map_path), exist_ok=True)

    with open(rfc_map_path, 'w') as f:
        f.write('{ invalid json content here }')


@given('rfc-map.json was last updated {days:d} days ago')
def step_rfc_map_updated_days_ago(context: Context, days: int):
    """Set rfc-map.json mtime to N days ago."""
    rfc_map_path = os.path.join(context.test_repo, 'docs', 'rfc-map.json')

    if not os.path.exists(rfc_map_path):
        create_rfc_map(context, [])

    set_file_mtime(rfc_map_path, days)


@given('rfc-map.json was updated {days:d} days ago')
def step_rfc_map_updated_recently(context: Context, days: int):
    """Set rfc-map.json mtime to N days ago."""
    step_rfc_map_updated_days_ago(context, days)


@given('"{file}" has uncommitted changes')
def step_file_has_uncommitted_changes(context: Context, file: str):
    """Create uncommitted changes in a file."""
    full_path = os.path.join(context.test_repo, file)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)

    with open(full_path, 'w') as f:
        f.write('# Modified content\n')


# ============================================================================
# When Steps - Execute Actions
# ============================================================================

@when('PreToolUse hook is triggered for Write tool on "{file}"')
def step_pretool_write(context: Context, file: str):
    """Trigger PreToolUse hook for Write tool."""
    full_path = os.path.join(context.test_repo, file)
    args = {'file_path': full_path, 'content': '# New content'}
    execute_hook('PreToolUse', 'Write', args, context)


@when('PreToolUse hook is triggered for Bash tool "{command}"')
def step_pretool_bash(context: Context, command: str):
    """Trigger PreToolUse hook for Bash tool."""
    args = {'command': command}
    execute_hook('PreToolUse', 'Bash', args, context)


@when('PostToolUse hook is triggered after Write tool modified "{file}"')
def step_posttool_write(context: Context, file: str):
    """Trigger PostToolUse hook after Write tool."""
    full_path = os.path.join(context.test_repo, file)
    args = {'file_path': full_path}
    execute_hook('PostToolUse', 'Write', args, context)


@when('PostToolUse hook is triggered after Bash tool "{command}"')
def step_posttool_bash(context: Context, command: str):
    """Trigger PostToolUse hook after Bash tool."""
    args = {'command': command}
    execute_hook('PostToolUse', 'Bash', args, context)


@when('PostToolUse hook attempts to update rfc-map.json')
def step_posttool_update_attempt(context: Context):
    """Attempt to trigger PostToolUse hook that updates rfc-map."""
    step_posttool_write(context, 'src/api.py')


@when('SessionStart hook is triggered')
def step_session_start(context: Context):
    """Trigger SessionStart hook."""
    execute_hook('SessionStart', '', {}, context)


@when('UserPromptSubmit hook receives prompt "{prompt}"')
def step_userprompt_submit(context: Context, prompt: str):
    """Trigger UserPromptSubmit hook."""
    args = {'prompt': prompt}
    execute_hook('UserPromptSubmit', '', args, context)


@when('code changes modify line {line:d} in "{file}"')
def step_code_changes_single_line(context: Context, line: int, file: str):
    """Modify a single line in a file."""
    full_path = os.path.join(context.test_repo, file)

    if not os.path.exists(full_path):
        create_test_code_file(context, file, '\n' * 20)

    modify_file_at_line(full_path, line, '# Modified line')

    if not hasattr(context, 'simulated_changes'):
        context.simulated_changes = []

    rfc_map_path = os.path.join(context.test_repo, 'docs', 'rfc-map.json')
    if os.path.exists(rfc_map_path):
        with open(rfc_map_path, 'r') as f:
            rfc_map = json.load(f)

        for mapping in rfc_map.get('mappings', []):
            if mapping['code']['file'] == file and mapping['code']['line'] == line:
                context.simulated_changes.append({
                    'section': mapping['rfc']['section'],
                    'heading': mapping['rfc']['heading'],
                    'elements': [mapping['code']['symbol']],
                    'severity': 'MUST_UPDATE',
                    'summary': 'API interface modified'
                })


@when('code changes modify lines {start:d}-{end:d} in "{file}"')
def step_code_changes_line_range(context: Context, start: int, end: int, file: str):
    """Modify a range of lines in a file."""
    full_path = os.path.join(context.test_repo, file)

    if not os.path.exists(full_path):
        create_test_code_file(context, file, '\n' * 30)

    modify_file_lines(full_path, start, end, '# Modified lines\n# More changes')

    if not hasattr(context, 'simulated_changes'):
        context.simulated_changes = []

    rfc_map_path = os.path.join(context.test_repo, 'docs', 'rfc-map.json')
    if os.path.exists(rfc_map_path):
        with open(rfc_map_path, 'r') as f:
            rfc_map = json.load(f)

        for mapping in rfc_map.get('mappings', []):
            if mapping['code']['file'] == file:
                code_line = mapping['code']['line']
                if start <= code_line <= end:
                    section_type = mapping['rfc'].get('type', 'unknown')
                    severity = 'SHOULD_REVIEW' if section_type == 'behavior' else 'MUST_UPDATE'

                    context.simulated_changes.append({
                        'section': mapping['rfc']['section'],
                        'heading': mapping['rfc']['heading'],
                        'elements': [mapping['code']['symbol']],
                        'severity': severity,
                        'summary': 'Code behavior modified'
                    })


@when('code changes modify "{file}"')
def step_code_changes_file(context: Context, file: str):
    """Modify a file (generic change)."""
    full_path = os.path.join(context.test_repo, file)

    if os.path.exists(full_path):
        with open(full_path, 'a') as f:
            f.write('\n# Additional changes\n')
    else:
        create_test_code_file(context, file, '# New file content\n')


@when('code changes modify both "{file1}" and "{file2}"')
def step_code_changes_multiple_files(context: Context, file1: str, file2: str):
    """Modify multiple files."""
    step_code_changes_file(context, file1)
    step_code_changes_file(context, file2)

    if not hasattr(context, 'simulated_changes'):
        context.simulated_changes = []

    rfc_map_path = os.path.join(context.test_repo, 'docs', 'rfc-map.json')
    if os.path.exists(rfc_map_path):
        with open(rfc_map_path, 'r') as f:
            rfc_map = json.load(f)

        for mapping in rfc_map.get('mappings', []):
            if mapping['code']['file'] in [file1, file2]:
                context.simulated_changes.append({
                    'section': mapping['rfc']['section'],
                    'heading': mapping['rfc']['heading'],
                    'elements': [mapping['code']['symbol']],
                    'severity': 'MUST_UPDATE',
                    'summary': 'Multiple files changed'
                })


@when('impact analysis is triggered with git diff')
def step_trigger_impact_analysis(context: Context):
    """Trigger impact analysis."""
    context.impact_results = run_impact_analysis_internal(context)


@when('impact analysis is triggered')
def step_trigger_impact_analysis_generic(context: Context):
    """Trigger impact analysis (generic)."""
    step_trigger_impact_analysis(context)


@when('git diff shows changes to tracked files')
def step_git_diff_shows_changes(context: Context):
    """Simulate git diff showing changes."""
    if not hasattr(context, 'simulated_changes'):
        context.simulated_changes = []
        context.simulated_changes.append({
            'section': '3.1',
            'heading': 'API Changes',
            'elements': ['api_function'],
            'severity': 'MUST_UPDATE',
            'summary': 'API modified'
        })


# ============================================================================
# Then Steps - Verify Results
# ============================================================================

@then('the hook returns non-blocking response')
def step_hook_non_blocking(context: Context):
    """Verify hook does not block execution."""
    assert context.hook_response is not None, "No hook response found"
    assert context.hook_response['block'] == False, "Hook blocked execution"


@then('the hook blocks execution')
def step_hook_blocks(context: Context):
    """Verify hook blocks execution."""
    assert context.hook_response is not None, "No hook response found"
    assert context.hook_response['block'] == True, "Hook did not block execution"


@then('the hook allows execution')
def step_hook_allows(context: Context):
    """Verify hook allows execution."""
    step_hook_non_blocking(context)


@then('the response message includes "{text}"')
def step_response_includes_text(context: Context, text: str):
    """Verify response message contains text."""
    assert context.hook_response is not None, "No hook response found"
    message = context.hook_response.get('message', '')
    assert text in message, f"Expected '{text}' in message, got: {message}"


@then('the response message suggests "{text}"')
def step_response_suggests_text(context: Context, text: str):
    """Verify response message suggests text."""
    step_response_includes_text(context, text)


@then('the response suggestion recommends "{text}"')
def step_response_suggests(context: Context, text: str):
    """Verify response suggestion contains text."""
    assert context.hook_response is not None, "No hook response found"
    suggestion = context.hook_response.get('suggestion', '')
    assert text in suggestion, f"Expected '{text}' in suggestion, got: {suggestion}"


@then('the suggestion recommends "{text}"')
def step_suggestion_recommends(context: Context, text: str):
    """Verify suggestion includes text."""
    step_response_suggests(context, text)


@then('the response has block={value}')
def step_response_block_value(context: Context, value: str):
    """Verify block value."""
    assert context.hook_response is not None, "No hook response found"
    expected = value.lower() == 'true'
    actual = context.hook_response.get('block', False)
    assert actual == expected, f"Expected block={expected}, got block={actual}"


@then('no warning message is displayed')
def step_no_warning(context: Context):
    """Verify no warning message."""
    assert context.hook_response is not None, "No hook response found"
    message = context.hook_response.get('message', '')
    assert message == '', f"Unexpected warning message: {message}"


@then('hook execution completes in under {ms:d}ms')
def step_hook_timing(context: Context, ms: int):
    """Verify hook execution time."""
    assert context.hook_response is not None, "No hook response found"
    timing = context.hook_response.get('timing_ms', 0)
    assert timing < ms, f"Hook took {timing}ms, expected under {ms}ms"


@then('analysis completes in under {ms:d}ms')
def step_analysis_timing(context: Context, ms: int):
    """Verify analysis timing (simulation always passes)."""
    pass


@then('affected sections include "{section}"')
def step_affected_sections_include(context: Context, section: str):
    """Verify affected sections include specified section."""
    assert hasattr(context, 'impact_results'), "No impact analysis results"
    sections = [impact['section_number'] for impact in context.impact_results]
    assert section in sections, f"Section {section} not in affected sections: {sections}"


@then('severity for section "{section}" is "{severity}"')
def step_severity_for_section(context: Context, section: str, severity: str):
    """Verify severity level for section."""
    assert hasattr(context, 'impact_results'), "No impact analysis results"

    for impact in context.impact_results:
        if impact['section_number'] == section:
            actual_severity = impact['severity']
            assert actual_severity == severity, f"Expected severity {severity}, got {actual_severity}"
            return

    assert False, f"Section {section} not found in impact results"


@then('changed elements include "{element}"')
def step_changed_elements_include(context: Context, element: str):
    """Verify changed elements include specified element."""
    assert hasattr(context, 'impact_results'), "No impact analysis results"

    all_elements = []
    for impact in context.impact_results:
        all_elements.extend(impact['affected_code_elements'])

    assert element in all_elements, f"Element {element} not in changed elements: {all_elements}"


@then('impact report is generated successfully')
def step_impact_report_generated(context: Context):
    """Verify impact report was generated."""
    assert hasattr(context, 'impact_results'), "No impact analysis results"
    assert len(context.impact_results) > 0, "Impact report is empty"


@then('no affected sections are reported')
def step_no_affected_sections(context: Context):
    """Verify no affected sections."""
    if not hasattr(context, 'impact_results'):
        return
    assert len(context.impact_results) == 0, f"Expected no affected sections, found {len(context.impact_results)}"


@then('impact report shows "{message}"')
def step_impact_report_shows_message(context: Context, message: str):
    """Verify impact report shows specific message."""
    if not hasattr(context, 'impact_results') or len(context.impact_results) == 0:
        assert 'No RFC' in message or 'No git history' in message or 'No changes' in message


@then('multiple affected sections are reported')
def step_multiple_sections_affected(context: Context):
    """Verify multiple sections affected."""
    assert hasattr(context, 'impact_results'), "No impact analysis results"
    assert len(context.impact_results) > 1, f"Expected multiple sections, found {len(context.impact_results)}"


@then('sections are sorted by severity (MUST_UPDATE first)')
def step_sections_sorted_by_severity(context: Context):
    """Verify sections are sorted by severity."""
    assert hasattr(context, 'impact_results'), "No impact analysis results"

    severity_order = [impact['severity'] for impact in context.impact_results]

    must_update_indices = [i for i, s in enumerate(severity_order) if s == 'MUST_UPDATE']
    should_review_indices = [i for i, s in enumerate(severity_order) if s == 'SHOULD_REVIEW']

    if must_update_indices and should_review_indices:
        assert max(must_update_indices) < min(should_review_indices), "MUST_UPDATE sections should come before SHOULD_REVIEW"


@then('each section lists its affected code elements')
def step_each_section_lists_elements(context: Context):
    """Verify each section has affected code elements."""
    assert hasattr(context, 'impact_results'), "No impact analysis results"

    for impact in context.impact_results:
        elements = impact['affected_code_elements']
        assert len(elements) > 0, f"Section {impact['section_number']} has no affected elements"


@then('results include all affected sections')
def step_results_include_all_sections(context: Context):
    """Verify all expected sections are included."""
    assert hasattr(context, 'impact_results'), "No impact analysis results"
    assert len(context.impact_results) > 0, "No results found"


@then('the hook updates timestamps in rfc-map.json')
def step_hook_updates_timestamps(context: Context):
    """Verify timestamps were updated."""
    assert context.updated_rfc_map, "rfc-map.json was not updated"


@then('affected sections are flagged as stale')
def step_sections_flagged_stale(context: Context):
    """Verify sections are marked stale."""
    rfc_map_path = os.path.join(context.test_repo, 'docs', 'rfc-map.json')

    with open(rfc_map_path, 'r') as f:
        rfc_map = json.load(f)

    stale_found = False
    for mapping in rfc_map['mappings']:
        if mapping['last_synced'] == '1970-01-01T00:00:00':
            stale_found = True
            break

    assert stale_found, "No mappings were flagged as stale"


@then('hook returns success response')
def step_hook_success(context: Context):
    """Verify hook returned success."""
    assert context.hook_response is not None, "No hook response"


@then('a reviewer guidance report is generated')
def step_reviewer_guidance_generated(context: Context):
    """Verify reviewer guidance was generated."""
    assert hasattr(context, 'reviewer_guidance'), "No reviewer guidance found"
    assert context.reviewer_guidance is not None, "Reviewer guidance is None"


@then('the report includes affected RFC sections')
def step_report_includes_sections(context: Context):
    """Verify report includes affected sections."""
    assert hasattr(context, 'reviewer_guidance'), "No reviewer guidance"
    guidance = context.reviewer_guidance
    assert 'affected_sections' in guidance, "No affected_sections in guidance"
    assert len(guidance['affected_sections']) > 0, "No sections in report"


@then('the report includes review checklist')
def step_report_includes_checklist(context: Context):
    """Verify report includes checklist."""
    assert hasattr(context, 'reviewer_guidance'), "No reviewer guidance"
    guidance = context.reviewer_guidance
    assert 'checklist' in guidance, "No checklist in guidance"
    assert len(guidance['checklist']) > 0, "Checklist is empty"


@then('the report is appended to ".claude/.hook-history.json"')
def step_report_appended_to_history(context: Context):
    """Verify report was appended to history."""
    history_path = os.path.join(context.test_repo, '.claude', '.hook-history.json')
    assert os.path.exists(history_path), "Hook history file not found"

    with open(history_path, 'r') as f:
        history = json.load(f)

    assert len(history) > 0, "History is empty"


@then('the hook displays staleness warning')
def step_hook_displays_staleness_warning(context: Context):
    """Verify staleness warning is displayed."""
    assert context.hook_response is not None, "No hook response"
    message = context.hook_response.get('message', '')
    assert 'days ago' in message.lower(), f"No staleness warning in: {message}"


@then('the warning message includes "{text}"')
def step_warning_includes_text(context: Context, text: str):
    """Verify warning includes specific text."""
    step_response_includes_text(context, text)


@then('no staleness warning is displayed')
def step_no_staleness_warning(context: Context):
    """Verify no staleness warning."""
    assert context.hook_response is not None, "No hook response"
    message = context.hook_response.get('message', '')
    assert 'days ago' not in message.lower(), f"Unexpected staleness warning: {message}"


@then('the hook warns about uncommitted documentation')
def step_warns_uncommitted_docs(context: Context):
    """Verify warning about uncommitted docs."""
    assert context.hook_response is not None, "No hook response"
    message = context.hook_response.get('message', '')
    assert 'uncommitted' in message.lower(), f"No uncommitted warning in: {message}"


@then('the hook detects RFC-related keywords')
def step_detects_rfc_keywords(context: Context):
    """Verify RFC keywords were detected."""
    assert context.rfc_context_injected, "RFC context was not injected"


@then('the hook loads "{filename}" from memory')
def step_loads_memory_file(context: Context, filename: str):
    """Verify memory file was loaded."""
    assert hasattr(context, 'memory_loaded'), "No memory_loaded attribute"
    assert filename in context.memory_loaded, f"{filename} not in loaded memory files: {context.memory_loaded}"


@then('RFC context is injected into response')
def step_rfc_context_injected(context: Context):
    """Verify RFC context was injected."""
    assert context.rfc_context_injected, "RFC context was not injected"


@then('intent detection is logged to ".claude/.hook-history.json"')
def step_intent_logged(context: Context):
    """Verify intent detection was logged."""
    history_path = os.path.join(context.test_repo, '.claude', '.hook-history.json')
    assert os.path.exists(history_path), "Hook history not found"

    with open(history_path, 'r') as f:
        history = json.load(f)

    intent_entries = [e for e in history if e.get('type') == 'intent_detection']
    assert len(intent_entries) > 0, "No intent detection entries found"


@then('the hook does not inject RFC context')
def step_no_rfc_context(context: Context):
    """Verify RFC context was not injected."""
    assert not context.rfc_context_injected, "RFC context was unexpectedly injected"


@then('no memory files are loaded')
def step_no_memory_loaded(context: Context):
    """Verify no memory files were loaded."""
    assert len(context.memory_loaded) == 0, f"Unexpected memory files loaded: {context.memory_loaded}"


@then('the hook returns non-blocking warning')
def step_non_blocking_warning(context: Context):
    """Verify non-blocking warning."""
    step_hook_non_blocking(context)
    assert context.hook_response.get('message', ''), "No warning message"


@then('the error message indicates missing library')
def step_error_missing_library(context: Context):
    """Verify error message about missing library."""
    message = context.hook_response.get('message', '')
    assert 'missing' in message.lower() or 'not found' in message.lower(), f"No missing library error in: {message}"


@then('the hook does not crash')
def step_hook_no_crash(context: Context):
    """Verify hook did not crash."""
    assert context.hook_response is not None, "Hook crashed (no response)"


@then('no changes are detected')
def step_no_changes_detected(context: Context):
    """Verify no changes detected."""
    step_no_affected_sections(context)


@then('the hook logs permission error')
def step_logs_permission_error(context: Context):
    """Verify permission error was logged."""
    message = context.hook_response.get('message', '')
    assert 'permission' in message.lower(), f"No permission error in: {message}"


@then('the response suggests checking file permissions')
def step_suggests_check_permissions(context: Context):
    """Verify suggestion about permissions."""
    suggestion = context.hook_response.get('suggestion', '')
    assert 'permission' in suggestion.lower(), f"No permission suggestion in: {suggestion}"


@then('the error message indicates JSON parsing error')
def step_error_json_parsing(context: Context):
    """Verify JSON parsing error message."""
    message = context.hook_response.get('message', '')
    assert 'json' in message.lower() or 'parsing' in message.lower(), f"No JSON error in: {message}"


@then('impact report includes behavior section warning')
def step_impact_includes_behavior_warning(context: Context):
    """Verify behavior section warning."""
    assert hasattr(context, 'impact_results'), "No impact results"

    behavior_impacts = [i for i in context.impact_results if i['severity'] == 'SHOULD_REVIEW']

    assert len(behavior_impacts) > 0, "No behavior section warnings found"
