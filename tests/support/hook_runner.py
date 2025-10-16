"""
Hook execution helper for BDD tests.

This module provides real execution of Claude Code hooks (PreToolUse, PostToolUse,
SessionStart, UserPromptSubmit) by running the actual Python hook scripts.
"""

import os
import sys
import json
import subprocess
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class HookResult:
    """Result from executing a hook"""
    exit_code: int
    stdout: str
    stderr: str
    response: Optional[Dict[str, Any]] = None
    execution_time: float = 0.0
    errors: list = field(default_factory=list)


class HookRunner:
    """Executes Claude Code hooks using real subprocess execution"""

    def __init__(self, test_dir: str):
        """
        Initialize hook runner.

        Args:
            test_dir: Root directory of the test repository
        """
        self.test_dir = Path(test_dir)
        self.hooks_dir = self.test_dir / '.claude' / 'hooks'

    def run_hook(
        self,
        hook_script: str,
        hook_type: str,
        input_data: Dict[str, Any],
        timeout: int = 60
    ) -> HookResult:
        """
        Execute a hook script with input data.

        Args:
            hook_script: Name of hook script (e.g., 'pre_tool_validate.py')
            hook_type: Type of hook (PreToolUse, PostToolUse, SessionStart, UserPromptSubmit)
            input_data: Hook input data to pass via stdin
            timeout: Timeout in seconds (default 60)

        Returns:
            HookResult with execution details
        """
        hook_path = self.hooks_dir / hook_script

        if not hook_path.exists():
            return HookResult(
                exit_code=1,
                stdout='',
                stderr=f'Hook script not found: {hook_path}',
                errors=[f'Hook script not found: {hook_script}']
            )

        # Prepare environment variables
        env = os.environ.copy()
        env['HOOK_TYPE'] = hook_type
        env['TEST_MODE'] = 'true'

        # Add test directory to environment for hooks to use
        env['TEST_DIR'] = str(self.test_dir)

        # Prepare stdin data (JSON)
        stdin_data = json.dumps(input_data)

        # Execute hook script
        start_time = time.time()

        try:
            result = subprocess.run(
                [sys.executable, str(hook_path)],
                input=stdin_data,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env,
                cwd=str(self.test_dir)
            )

            execution_time = time.time() - start_time

            # Parse response (hooks should return JSON)
            response = None
            if result.stdout:
                try:
                    response = json.loads(result.stdout)
                except json.JSONDecodeError:
                    # If not valid JSON, treat as plain text
                    response = {'output': result.stdout}

            return HookResult(
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                response=response,
                execution_time=execution_time,
                errors=[result.stderr] if result.stderr else []
            )

        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            return HookResult(
                exit_code=124,  # Standard timeout exit code
                stdout='',
                stderr=f'Hook timed out after {timeout} seconds',
                execution_time=execution_time,
                errors=[f'Hook execution timed out ({timeout}s)']
            )
        except Exception as e:
            execution_time = time.time() - start_time
            return HookResult(
                exit_code=1,
                stdout='',
                stderr=str(e),
                execution_time=execution_time,
                errors=[f'Hook execution failed: {str(e)}']
            )

    def run_pretool_hook(
        self,
        tool_name: str,
        tool_input: Dict[str, Any]
    ) -> HookResult:
        """
        Execute PreToolUse hook.

        Args:
            tool_name: Name of tool being validated
            tool_input: Tool input parameters

        Returns:
            HookResult
        """
        input_data = {
            'hook_type': 'PreToolUse',
            'tool_name': tool_name,
            'tool_input': tool_input
        }

        return self.run_hook(
            'pre_tool_validate.py',
            'PreToolUse',
            input_data
        )

    def run_posttool_hook(
        self,
        tool_name: str,
        tool_output: Any,
        files_modified: Optional[List[str]] = None
    ) -> HookResult:
        """
        Execute PostToolUse hook.

        Args:
            tool_name: Name of tool that was executed
            tool_output: Output from the tool
            files_modified: List of files modified by the tool

        Returns:
            HookResult
        """
        input_data = {
            'hook_type': 'PostToolUse',
            'tool_name': tool_name,
            'tool_output': tool_output,
            'files_modified': files_modified or []
        }

        return self.run_hook(
            'post_tool_sync.py',
            'PostToolUse',
            input_data
        )

    def run_session_hook(self) -> HookResult:
        """
        Execute SessionStart hook.

        Returns:
            HookResult
        """
        input_data = {
            'hook_type': 'SessionStart',
            'timestamp': time.time()
        }

        return self.run_hook(
            'session_start_check.py',
            'SessionStart',
            input_data
        )

    def run_userprompt_hook(self, user_prompt: str) -> HookResult:
        """
        Execute UserPromptSubmit hook.

        Args:
            user_prompt: User's prompt text

        Returns:
            HookResult
        """
        input_data = {
            'hook_type': 'UserPromptSubmit',
            'prompt': user_prompt
        }

        return self.run_hook(
            'user_intent_detect.py',
            'UserPromptSubmit',
            input_data
        )


def run_hook(
    test_dir: str,
    hook_script: str,
    hook_type: str,
    input_data: Dict[str, Any],
    timeout: int = 60
) -> HookResult:
    """
    Convenience function to run a hook.

    Args:
        test_dir: Test repository directory
        hook_script: Name of hook script
        hook_type: Type of hook
        input_data: Hook input data
        timeout: Timeout in seconds

    Returns:
        HookResult
    """
    runner = HookRunner(test_dir)
    return runner.run_hook(hook_script, hook_type, input_data, timeout)


def create_minimal_hook_script(hook_path: Path, hook_type: str):
    """
    Create a behavior-aware hook script for testing.

    Args:
        hook_path: Path where hook script should be created
        hook_type: Type of hook (PreToolUse, PostToolUse, SessionStart, UserPromptSubmit)
    """
    hook_path.parent.mkdir(parents=True, exist_ok=True)

    if hook_type == 'PreToolUse':
        hook_content = _create_pretool_hook_script()
    elif hook_type == 'PostToolUse':
        hook_content = _create_posttool_hook_script()
    elif hook_type == 'SessionStart':
        hook_content = _create_session_hook_script()
    elif hook_type == 'UserPromptSubmit':
        hook_content = _create_userprompt_hook_script()
    else:
        # Fallback: minimal hook for unknown types
        hook_content = _create_generic_hook_script(hook_type)

    hook_path.write_text(hook_content)
    hook_path.chmod(0o755)  # Make executable


def _create_pretool_hook_script() -> str:
    """Generate PreToolUse hook script content"""
    return '''#!/usr/bin/env python3
"""
PreToolUse hook for testing - validates tool execution before running
"""
import sys
import json
import os

def main():
    input_data = json.loads(sys.stdin.read())
    tool_name = input_data.get('tool_name', '')
    tool_input = input_data.get('tool_input', {})

    response = {'block': False, 'message': '', 'suggestion': ''}

    # Get test directory from environment
    test_dir = os.environ.get('TEST_DIR', os.getcwd())
    rfc_map_path = os.path.join(test_dir, 'docs', 'rfc-map.json')

    # Check if rfc-map.json exists
    if not os.path.exists(rfc_map_path):
        response['message'] = 'No RFC documentation found. Run /rfc-generate first'
        response['suggestion'] = 'Run /rfc-generate first'
        print(json.dumps(response))
        sys.exit(0)

    # Load rfc-map.json
    try:
        with open(rfc_map_path, 'r') as f:
            rfc_map = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        response['message'] = 'JSON parsing error in rfc-map.json'
        response['suggestion'] = '/rfc-validate'
        print(json.dumps(response))
        sys.exit(0)

    # Check for direct kramdown-rfc usage
    if tool_name == 'Bash':
        command = tool_input.get('command', '')
        if 'kramdown-rfc' in command and 'make' not in command:
            response['block'] = True
            response['message'] = "Direct kramdown-rfc execution not recommended. Use 'make txt' instead"
            response['suggestion'] = "Use 'make txt' instead"
            print(json.dumps(response))
            sys.exit(0)

    # Check if file being written is tracked
    if tool_name == 'Write':
        file_path = tool_input.get('file_path', '').replace(test_dir + '/', '')

        for mapping in rfc_map.get('mappings', []):
            if mapping['code']['file'] == file_path:
                section = mapping['rfc']['section']
                response['message'] = f'Affects RFC §{section}'
                response['suggestion'] = '/rfc-analyze-impact'
                break

    print(json.dumps(response))
    sys.exit(0)

if __name__ == '__main__':
    main()
'''


def _create_posttool_hook_script() -> str:
    """Generate PostToolUse hook script content"""
    return '''#!/usr/bin/env python3
"""
PostToolUse hook for testing - updates tracking after tool execution
"""
import sys
import json
import os
from datetime import datetime

def main():
    input_data = json.loads(sys.stdin.read())
    tool_name = input_data.get('tool_name', '')
    tool_output = input_data.get('tool_output', '')

    response = {'block': False, 'message': '', 'suggestion': ''}

    test_dir = os.environ.get('TEST_DIR', os.getcwd())
    rfc_map_path = os.path.join(test_dir, 'docs', 'rfc-map.json')

    if not os.path.exists(rfc_map_path):
        print(json.dumps(response))
        sys.exit(0)

    # Load rfc-map.json
    try:
        with open(rfc_map_path, 'r') as f:
            rfc_map = json.load(f)
    except:
        print(json.dumps(response))
        sys.exit(0)

    # Mark affected files as stale after Write operations
    if tool_name == 'Write':
        file_path = str(tool_output).replace(test_dir + '/', '')
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
            except PermissionError:
                response['message'] = 'Permission error updating rfc-map.json'
                response['suggestion'] = 'Check file permissions'

    print(json.dumps(response))
    sys.exit(0)

if __name__ == '__main__':
    main()
'''


def _create_session_hook_script() -> str:
    """Generate SessionStart hook script content"""
    return '''#!/usr/bin/env python3
"""
SessionStart hook for testing - detects stale documentation
"""
import sys
import json
import os
from datetime import datetime

def main():
    input_data = json.loads(sys.stdin.read())

    response = {'block': False, 'message': '', 'suggestion': ''}

    test_dir = os.environ.get('TEST_DIR', os.getcwd())
    rfc_map_path = os.path.join(test_dir, 'docs', 'rfc-map.json')

    if not os.path.exists(rfc_map_path):
        print(json.dumps(response))
        sys.exit(0)

    # Check staleness based on file mtime
    stat = os.stat(rfc_map_path)
    mtime = datetime.fromtimestamp(stat.st_mtime)
    age_days = (datetime.now() - mtime).days

    if age_days > 30:
        response['message'] = f'RFC documentation last updated {age_days} days ago'
        response['suggestion'] = '/rfc-update'

    print(json.dumps(response))
    sys.exit(0)

if __name__ == '__main__':
    main()
'''


def _create_userprompt_hook_script() -> str:
    """Generate UserPromptSubmit hook script content"""
    return '''#!/usr/bin/env python3
"""
UserPromptSubmit hook for testing - detects RFC-related intent
"""
import sys
import json
import os

def main():
    input_data = json.loads(sys.stdin.read())
    prompt = input_data.get('prompt', '')

    response = {'block': False, 'message': '', 'suggestion': ''}

    # Detect RFC-related keywords
    rfc_keywords = ['rfc', 'documentation', 'spec', 'draft', 'update the rfc']
    prompt_lower = prompt.lower()
    is_rfc_related = any(keyword in prompt_lower for keyword in rfc_keywords)

    if is_rfc_related:
        test_dir = os.environ.get('TEST_DIR', os.getcwd())
        memory_dir = os.path.join(test_dir, '.claude', 'memory')

        # Check if memory files exist
        if os.path.exists(memory_dir):
            overview_path = os.path.join(memory_dir, 'codebase-overview.md')
            if os.path.exists(overview_path):
                response['message'] = 'RFC context injected'

    print(json.dumps(response))
    sys.exit(0)

if __name__ == '__main__':
    main()
'''


def _create_generic_hook_script(hook_type: str) -> str:
    """Generate generic hook script for unknown hook types"""
    return f'''#!/usr/bin/env python3
"""
Minimal {hook_type} hook for testing
"""
import sys
import json

def main():
    input_data = json.loads(sys.stdin.read())

    response = {{
        'status': 'success',
        'hook_type': '{hook_type}',
        'input_received': True
    }}

    print(json.dumps(response))
    sys.exit(0)

if __name__ == '__main__':
    main()
'''
