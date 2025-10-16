"""
Behave test steps for automation scenarios (User Story 3: Automated Documentation Checks)

This module implements @given and @when step definitions for Claude Code native hooks including:
- PreToolUse: Pre-commit validation
- PostToolUse: Reviewer guidance
- SessionStart: Staleness detection
- UserPromptSubmit: Intent detection
"""

import os
import json
import subprocess
from datetime import datetime
from behave import given, when
from behave.runner import Context
import shutil

# Import helper functions
from automation_helpers import (
    execute_hook,
    create_rfc_map,
    create_test_code_file,
    modify_file_at_line,
    modify_file_lines,
    set_file_mtime,
    run_impact_analysis_internal
)


# ============================================================================
# Given Steps - Setup Test Conditions
# ============================================================================

@given('a clean test repository')
def step_clean_test_repository(context: Context):
    """Set up a clean test repository."""
    assert hasattr(context, 'test_repo'), "Test repository not initialized"

    # Automation test attributes
    context.hook_response = None
    context.updated_rfc_map = False
    context.reviewer_guidance = None
    context.memory_loaded = []
    context.rfc_context_injected = False

    # Generate/Update test attributes
    context.generated_rfc = None
    context.command_exit_code = None
    context.command_output = None
    context.command_result = None


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


@when('PreToolUse hook is triggered for Write tool')
def step_pretool_write_generic(context: Context):
    """Trigger PreToolUse hook for Write tool (generic file)."""
    # Use a generic test file
    full_path = os.path.join(context.test_repo, 'src', 'test.py')
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


@when('code changes modify {count:d} tracked files')
def step_code_changes_n_tracked_files(context: Context, count: int):
    """Modify N tracked files (assumes they were already set up)."""
    if not hasattr(context, 'simulated_changes'):
        context.simulated_changes = []

    rfc_map_path = os.path.join(context.test_repo, 'docs', 'rfc-map.json')
    if os.path.exists(rfc_map_path):
        with open(rfc_map_path, 'r') as f:
            rfc_map = json.load(f)

        # Get the first N tracked files and modify them
        modified_count = 0
        for mapping in rfc_map.get('mappings', []):
            if modified_count >= count:
                break

            file_path = mapping['code']['file']
            step_code_changes_file(context, file_path)

            # Add simulated change for this file
            context.simulated_changes.append({
                'section': mapping['rfc']['section'],
                'heading': mapping['rfc']['heading'],
                'elements': [mapping['code']['symbol']],
                'severity': 'MUST_UPDATE',
                'summary': f'File {file_path} modified'
            })

            modified_count += 1


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
