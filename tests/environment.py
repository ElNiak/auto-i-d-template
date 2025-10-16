"""
Behave environment configuration for RFC generator plugin tests.

This module provides setup and teardown hooks for BDD test scenarios,
including temporary git repository creation, fixture management, and cleanup.

Extended from original i-d-template tests to support RFC generator plugin testing.
"""

import os
import shutil
import tempfile
import subprocess
from pathlib import Path
from behave import fixture, use_fixture  # type: ignore
from behave.runner import Context


def before_all(context):
    """
    Called once before all tests run.

    Setup global test configuration and validate prerequisites.
    """
    # Store original working directory
    context.original_cwd = os.getcwd()

    # Ensure required tools are available
    required_tools = ['git', 'python3']
    for tool in required_tools:
        if shutil.which(tool) is None:
            raise RuntimeError(f"Required tool '{tool}' not found in PATH")

    # Initialize test statistics
    context.test_stats = {
        'scenarios_run': 0,
        'scenarios_passed': 0,
        'scenarios_failed': 0,
        'total_time': 0.0,
        'scenario_times': []  # List of (scenario_name, duration) tuples
    }

    print("\n" + "="*70)
    print("RFC Generator Plugin - BDD Test Suite")
    print("="*70)


def before_scenario(context, scenario):
    """
    Called before each test scenario runs.

    Creates isolated test environment with optional git repository.
    """
    import time

    context.test_stats['scenarios_run'] += 1
    context.scenario_start_time = time.time()

    # Create temporary directory for this scenario
    context.temp_dir = tempfile.mkdtemp(prefix='rfc_test_')
    context.test_repo = Path(context.temp_dir)

    # Initialize git repository only if @git tag is present or by default
    # Skip git init for scenarios tagged with @no-git
    if 'no-git' not in scenario.tags:
        _init_git_repo(context.test_repo)

    # Copy plugin files to test repo if they exist
    plugin_source = Path(context.original_cwd) / '.claude'
    if plugin_source.exists():
        plugin_dest = context.test_repo / '.claude'
        shutil.copytree(plugin_source, plugin_dest, dirs_exist_ok=True)

    # Create test fixture files if scenario requires them
    if 'fixtures' in scenario.tags:
        fixture_name = _extract_fixture_name(scenario.tags)
        _create_fixture(context, fixture_name)

    # Change to test directory
    os.chdir(context.test_repo)

    # Store scenario-specific data
    context.scenario_name = scenario.name
    context.output_files = []
    context.error_log = []

    print(f"\n▶ Running: {scenario.name}")


def after_scenario(context, scenario):
    """
    Called after each test scenario completes.

    Cleanup temporary files and restore working directory.
    """
    import time

    # Calculate scenario execution time
    if hasattr(context, 'scenario_start_time'):
        duration = time.time() - context.scenario_start_time
        context.test_stats['total_time'] += duration
        context.test_stats['scenario_times'].append((scenario.name, duration))

    # Change back to original directory
    os.chdir(context.original_cwd)

    # Update statistics
    if scenario.status == 'passed':
        context.test_stats['scenarios_passed'] += 1
        print(f"✅ Passed: {scenario.name}")
    else:
        context.test_stats['scenarios_failed'] += 1
        print(f"❌ Failed: {scenario.name}")
        # Print error log if available
        if hasattr(context, 'error_log') and context.error_log:
            print("  Errors:")
            for error in context.error_log:
                print(f"    - {error}")

    # Cleanup temporary directory (unless debugging)
    if not os.environ.get('KEEP_TEST_DIRS'):
        # Clean up temp_dir and legacy working_dir/origin_dir if they exist
        for dir_attr in ['temp_dir', 'working_dir', 'origin_dir']:
            if hasattr(context, dir_attr):
                dir_path = getattr(context, dir_attr)
                if os.path.exists(dir_path):
                    shutil.rmtree(dir_path, ignore_errors=True)
                delattr(context, dir_attr)
    else:
        if hasattr(context, 'temp_dir'):
            print(f"  Test directory preserved: {context.temp_dir}")

    # Explicit context cleanup to prevent pollution
    # Remove scenario-specific attributes
    for attr in ['scenario_start_time', 'output_files', 'error_log', 'scenario_name',
                  'generated_rfc', 'command_exit_code', 'command_output', 'command_result',
                  'hook_response', 'rfc_map_path', 'sample_project']:
        if hasattr(context, attr):
            delattr(context, attr)


def after_all(context):
    """
    Called once after all tests complete.

    Print test summary and statistics including performance metrics.
    """
    if hasattr(context, 'test_stats'):
        print("\n" + "="*70)
        print("Test Summary")
        print("="*70)
        print(f"Total scenarios: {context.test_stats['scenarios_run']}")
        print(f"Passed: {context.test_stats['scenarios_passed']} ✅")
        print(f"Failed: {context.test_stats['scenarios_failed']} ❌")

        # Performance metrics
        if context.test_stats['total_time'] > 0:
            print(f"\nExecution Time:")
            print(f"  Total: {context.test_stats['total_time']:.2f}s")
            avg_time = context.test_stats['total_time'] / context.test_stats['scenarios_run']
            print(f"  Average per scenario: {avg_time:.2f}s")

            # Show slowest scenarios (top 5)
            if context.test_stats['scenario_times']:
                sorted_times = sorted(context.test_stats['scenario_times'],
                                     key=lambda x: x[1], reverse=True)
                print(f"\n  Slowest scenarios:")
                for name, duration in sorted_times[:5]:
                    print(f"    {duration:6.2f}s - {name}")

        if context.test_stats['scenarios_failed'] == 0:
            print("\n🎉 All tests passed!")
        else:
            print(f"\n⚠️  {context.test_stats['scenarios_failed']} test(s) failed")

        print("="*70 + "\n")


# Helper functions

def _init_git_repo(repo_path):
    """Initialize a git repository in the test directory."""
    subprocess.run(['git', 'init'], cwd=repo_path, capture_output=True, check=True)
    subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=repo_path, capture_output=True, check=True)
    subprocess.run(['git', 'config', 'user.email', 'test@example.com'], cwd=repo_path, capture_output=True, check=True)

    # Create initial commit
    readme = repo_path / 'README.md'
    readme.write_text('# Test Repository\n')
    subprocess.run(['git', 'add', 'README.md'], cwd=repo_path, capture_output=True, check=True)
    subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=repo_path, capture_output=True, check=True)


def _extract_fixture_name(tags):
    """Extract fixture name from scenario tags."""
    for tag in tags:
        if tag.startswith('fixture.'):
            return tag.replace('fixture.', '')
    return 'default'


def _create_fixture(context, fixture_name):
    """Create test fixture files in the test repository."""
    fixture_source = Path(context.original_cwd) / 'tests' / 'fixtures' / fixture_name

    if fixture_source.exists():
        # Copy fixture files to test repo
        for item in fixture_source.iterdir():
            if item.is_file():
                dest = context.test_repo / item.name
                shutil.copy2(item, dest)
            elif item.is_dir():
                dest = context.test_repo / item.name
                shutil.copytree(item, dest)
    else:
        # Create default fixture
        _create_default_fixture(context)


def _create_default_fixture(context):
    """Create a simple default fixture for testing."""
    # Create src directory with sample Python code
    src_dir = context.test_repo / 'src'
    src_dir.mkdir(exist_ok=True)

    # Sample API file
    (src_dir / 'api.py').write_text('''"""Sample API module."""

def authenticate(username: str, password: str) -> bool:
    """Authenticate a user."""
    return bool(username and password)

class User:
    """User class."""
    def __init__(self, username, email):
        self.username = username
        self.email = email
''')

    # Add to git
    subprocess.run(['git', 'add', 'src/'], cwd=context.test_repo, capture_output=True, check=True)
    subprocess.run(['git', 'commit', '-m', 'Add sample code'], cwd=context.test_repo, capture_output=True, check=True)
