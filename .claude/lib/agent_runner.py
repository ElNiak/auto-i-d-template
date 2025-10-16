"""
Agent runner with timeout and progress tracking.

Provides timeout enforcement and progress monitoring for RFC generator agents.
Integrates with checkpoint system for intelligent timeout reset.

CHK009 Resolution: Agent operation timeouts with hybrid static + dynamic scaling.
"""

import os
import sys
import time
import json
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Callable

logger = logging.getLogger(__name__)


# ============================================================================
# Exceptions
# ============================================================================

class AgentTimeoutError(Exception):
    """Raised when agent exceeds timeout."""
    pass


# ============================================================================
# Timeout Parsing
# ============================================================================

def parse_timeout(value: str) -> int:
    """
    Parse timeout string to seconds.

    Args:
        value: Timeout string (e.g., "5m", "300s", "1h")

    Returns:
        Timeout in seconds (0 = no timeout)

    Raises:
        ValueError: If format invalid or out of range

    Examples:
        >>> parse_timeout("300")
        300
        >>> parse_timeout("5m")
        300
        >>> parse_timeout("1h")
        3600
        >>> parse_timeout("infinity")
        0
    """
    import re

    # Handle special values
    if value.lower() in ('infinity', 'none', 'unlimited'):
        return 0  # 0 = no timeout in subprocess.run()

    # Parse numeric value
    match = re.match(r'^(\d+)(s|sec|m|min|h|hr|hour)?$', value.lower())
    if not match:
        raise ValueError(f"Invalid timeout format: {value}")

    num, unit = match.groups()
    num = int(num)

    # Convert to seconds
    if unit in (None, 's', 'sec'):
        seconds = num
    elif unit in ('m', 'min'):
        seconds = num * 60
    elif unit in ('h', 'hr', 'hour'):
        seconds = num * 3600
    else:
        raise ValueError(f"Unknown unit: {unit}")

    # Validate range
    if seconds > 0 and seconds < 30:
        raise ValueError(f"Timeout too short: {seconds}s (minimum: 30s)")
    if seconds > 86400:  # 24 hours
        raise ValueError(f"Timeout too long: {seconds}s (maximum: 24h)")

    # Warnings
    if 0 < seconds < 60:
        logger.warning(f"Very short timeout ({seconds}s) may cause failures")
    if seconds > 7200:
        logger.warning(f"Long timeout ({seconds}s) may hide hung processes")

    return seconds


def calculate_timeout(agent_type: str, **kwargs) -> int:
    """
    Calculate dynamic timeout based on agent type and codebase characteristics.

    Args:
        agent_type: Agent type ('parser', 'analyzer', 'formatter', 'validator')
        **kwargs: Additional parameters:
            - loc: Lines of code (for parser)
            - symbols: Number of symbols (for analyzer)
            - sections: Number of sections (for formatter)
            - rfc_size_kb: RFC size in KB (for validator)

    Returns:
        Timeout in seconds
    """
    # Base timeouts
    base_timeouts = {
        'parser': 600,      # 10 minutes
        'analyzer': 360,    # 6 minutes
        'formatter': 180,   # 3 minutes
        'validator': 120    # 2 minutes
    }

    base = base_timeouts.get(agent_type, 600)

    # Apply scaling
    if agent_type == 'parser':
        loc = kwargs.get('loc', 0)
        scale = (loc / 10000) * 60  # 1 min per 10K LOC
        return int(base + scale)

    elif agent_type == 'analyzer':
        symbols = kwargs.get('symbols', 0)
        scale_factor = min(symbols / 100, 60)  # Cap at 60x multiplier
        return int(base + (scale_factor * 30))  # Max 36 minutes

    elif agent_type == 'formatter':
        sections = kwargs.get('sections', 0)
        return int(base + (sections * 15))  # 15s per section

    elif agent_type == 'validator':
        rfc_size_kb = kwargs.get('rfc_size_kb', 0)
        return int(base + (rfc_size_kb / 100) * 10)  # 10s per 100KB

    return base


# ============================================================================
# Agent Runner
# ============================================================================

class AgentRunner:
    """
    Wrapper for running agents with timeout and progress tracking.

    Monitors agent execution, tracks progress via checkpoints, and enforces
    timeouts with intelligent auto-extension based on progress indicators.
    """

    def __init__(
        self,
        agent_name: str,
        timeout: int,
        checkpoint_dir: str = ".claude/.checkpoints",
        auto_extend: bool = True,
        extend_factor: float = 0.5
    ):
        """
        Initialize agent runner.

        Args:
            agent_name: Name of agent (parser/analyzer/formatter/validator)
            timeout: Timeout in seconds (0 = no timeout)
            checkpoint_dir: Directory for checkpoint files
            auto_extend: Whether to auto-extend timeout when progress detected
            extend_factor: Factor to extend timeout by (0.5 = +50%)
        """
        self.agent_name = agent_name
        self.timeout = timeout
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.auto_extend = auto_extend
        self.extend_factor = extend_factor
        self.extended = False  # Track if timeout was already extended

    def run(
        self,
        agent_path: str,
        input_data: Dict[str, Any],
        on_progress: Optional[Callable[[int, int], None]] = None
    ) -> Dict[str, Any]:
        """
        Run agent with timeout and progress tracking.

        Args:
            agent_path: Path to agent markdown file
            input_data: Input data for agent
            on_progress: Optional callback(elapsed, timeout) for progress updates

        Returns:
            Agent output dictionary

        Raises:
            AgentTimeoutError: If agent exceeds timeout
            RuntimeError: If agent fails
        """
        if self.timeout == 0:
            # No timeout - run without monitoring
            return self._run_without_timeout(agent_path, input_data)

        start_time = time.time()
        checkpoint_pattern = f"{self.agent_name}-*.json"
        initial_checkpoints = set(self.checkpoint_dir.glob(checkpoint_pattern))

        # Write input to temp file
        input_file = self.checkpoint_dir / f"{self.agent_name}-input.json"
        with open(input_file, 'w') as f:
            json.dump(input_data, f, indent=2)

        # Build command for agent execution
        # NOTE: This is conceptual - actual Claude Code agent invocation may differ
        cmd = [
            sys.executable,  # Use current Python interpreter
            '-m', 'claude_code_agent',  # Conceptual agent runner
            agent_path,
            '--input', str(input_file)
        ]

        try:
            # Run agent as subprocess with timeout monitoring
            logger.info(f"Starting {self.agent_name} (timeout: {self.timeout}s)")

            # Progress tracking loop
            remaining_timeout = self.timeout
            poll_interval = 5  # Check every 5 seconds

            # Start process (non-blocking, for progress tracking)
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            last_warning_pct = 0

            while remaining_timeout > 0:
                # Check if process completed
                if process.poll() is not None:
                    stdout, stderr = process.communicate()
                    elapsed = time.time() - start_time

                    if process.returncode == 0:
                        logger.info(f"{self.agent_name} completed in {elapsed:.1f}s")
                        return self._parse_output(stdout)
                    else:
                        raise RuntimeError(f"{self.agent_name} failed: {stderr}")

                # Check for new checkpoints (progress indicator)
                current_checkpoints = set(self.checkpoint_dir.glob(checkpoint_pattern))
                new_checkpoints = current_checkpoints - initial_checkpoints

                if new_checkpoints and self.auto_extend and not self.extended:
                    latest_checkpoint = max(new_checkpoints, key=lambda p: p.stat().st_mtime)
                    checkpoint_age = time.time() - latest_checkpoint.stat().st_mtime

                    if checkpoint_age < poll_interval * 2:
                        # Recent checkpoint = progress detected
                        extension = int(self.timeout * self.extend_factor)
                        logger.info(
                            f"{self.agent_name} checkpoint detected, "
                            f"extending timeout by {extension}s"
                        )
                        remaining_timeout += extension
                        self.timeout += extension
                        self.extended = True

                # Report progress
                elapsed = time.time() - start_time
                progress_pct = (elapsed / self.timeout) * 100

                # Warning thresholds
                if progress_pct >= 90 and last_warning_pct < 90:
                    logger.warning(
                        f"{self.agent_name} at 90% timeout "
                        f"({elapsed:.0f}s / {self.timeout}s)"
                    )
                    print(f"\n⚠️  {self.agent_name} near timeout limit ({elapsed:.0f}s / {self.timeout}s)")
                    print("   - Agent still active")
                    if self.auto_extend and not self.extended:
                        print("   - Will auto-extend if checkpoint exists")
                    last_warning_pct = 90

                elif progress_pct >= 75 and last_warning_pct < 75:
                    logger.warning(
                        f"{self.agent_name} at 75% timeout "
                        f"({elapsed:.0f}s / {self.timeout}s)"
                    )
                    print(f"\n⚠️  {self.agent_name} approaching timeout ({elapsed:.0f}s / {self.timeout}s)")
                    if new_checkpoints:
                        print("   - Agent is progressing (checkpoint detected)")
                    print("   - Consider reducing scope or extending timeout")
                    last_warning_pct = 75

                # Call progress callback
                if on_progress:
                    on_progress(int(elapsed), self.timeout)

                # Sleep and decrement timeout
                time.sleep(poll_interval)
                remaining_timeout -= poll_interval

            # Timeout exceeded
            process.terminate()
            time.sleep(1)
            if process.poll() is None:
                process.kill()

            elapsed = time.time() - start_time
            has_checkpoint = bool(new_checkpoints)

            raise AgentTimeoutError(
                f"{self.agent_name} timed out after {elapsed:.0f}s "
                f"(limit: {self.timeout}s). "
                f"Checkpoint detected: {has_checkpoint}"
            )

        except subprocess.TimeoutExpired:
            elapsed = time.time() - start_time
            raise AgentTimeoutError(
                f"{self.agent_name} timed out after {elapsed:.0f}s "
                f"(limit: {self.timeout}s)"
            )

    def _run_without_timeout(self, agent_path: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run agent without timeout monitoring (blocking)."""
        logger.info(f"Starting {self.agent_name} (no timeout)")

        input_file = self.checkpoint_dir / f"{self.agent_name}-input.json"
        with open(input_file, 'w') as f:
            json.dump(input_data, f, indent=2)

        cmd = [
            sys.executable,
            '-m', 'claude_code_agent',
            agent_path,
            '--input', str(input_file)
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )

        return self._parse_output(result.stdout)

    def _parse_output(self, stdout: str) -> Dict[str, Any]:
        """Parse agent output from stdout."""
        try:
            return json.loads(stdout)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse {self.agent_name} output: {e}")
            return {"error": "Invalid JSON output", "raw": stdout}


# ============================================================================
# Configuration Loading
# ============================================================================

def load_timeout_config(plugin_config_path: str = ".claude/plugin.json") -> Dict[str, Any]:
    """
    Load timeout configuration from plugin.json.

    Args:
        plugin_config_path: Path to plugin configuration file

    Returns:
        Timeout configuration dict
    """
    defaults = {
        'parser': 600,
        'analyzer': 360,
        'formatter': 180,
        'validator': 120,
        'workflow': 1800,
        'serena_call': 30,
        'make_target': 60,
        'auto_extend': True,
        'extend_factor': 0.5,
        'enable_scaling': True
    }

    if not os.path.exists(plugin_config_path):
        logger.info(f"Plugin config not found, using defaults")
        return defaults

    try:
        with open(plugin_config_path) as f:
            config = json.load(f)

        timeouts = config.get('timeouts', {})

        # Merge with defaults
        for key in defaults:
            if key in timeouts:
                defaults[key] = timeouts[key]

        # Apply environment variable overrides
        env_overrides = {
            'RFC_PARSER_TIMEOUT': 'parser',
            'RFC_ANALYZER_TIMEOUT': 'analyzer',
            'RFC_FORMATTER_TIMEOUT': 'formatter',
            'RFC_VALIDATOR_TIMEOUT': 'validator',
            'RFC_WORKFLOW_TIMEOUT': 'workflow',
            'RFC_TIMEOUT': None  # Global override
        }

        for env_var, config_key in env_overrides.items():
            value = os.getenv(env_var)
            if value:
                if config_key:
                    defaults[config_key] = parse_timeout(value)
                else:
                    # Global override - set all agent timeouts
                    timeout = parse_timeout(value)
                    for agent in ['parser', 'analyzer', 'formatter', 'validator']:
                        defaults[agent] = timeout

        return defaults

    except Exception as e:
        logger.error(f"Failed to load timeout config: {e}")
        return defaults


# ============================================================================
# Utility Functions
# ============================================================================

def display_timeout_error(
    agent_name: str,
    timeout: int,
    has_checkpoint: bool,
    elapsed: float,
    recovery_suggestions: Optional[list] = None
):
    """
    Display formatted timeout error with recovery options.

    Args:
        agent_name: Name of timed-out agent
        timeout: Timeout limit in seconds
        has_checkpoint: Whether checkpoint exists
        elapsed: Actual elapsed time
        recovery_suggestions: Optional list of recovery suggestions
    """
    print(f"\n❌ {agent_name.title()} timed out after {elapsed:.0f} seconds")
    print(f"\nTimeout Limit: {timeout}s ({timeout/60:.1f} minutes)")

    if has_checkpoint:
        print("\nCheckpoint Status:")
        print("  ✓ Checkpoint detected - agent was making progress")
        print("  → Consider extending timeout")
    else:
        print("\nCheckpoint Status:")
        print("  ✗ No checkpoint found - agent may be hung")
        print("  → Check for errors or reduce scope")

    print("\nRecovery Options:")
    if recovery_suggestions:
        for i, suggestion in enumerate(recovery_suggestions, 1):
            print(f"  {i}. {suggestion}")
    else:
        print(f"  1. Extend timeout: --{agent_name}-timeout {int(timeout * 1.5)}s")
        print(f"  2. Reduce scope: Analyze fewer files/paths")
        print(f"  3. Check logs: .claude/.coordinator-errors.log")
        print(f"  4. Resume: --resume (if checkpoint exists)")

    checkpoint_dir = Path(".claude/.checkpoints")
    checkpoints = list(checkpoint_dir.glob(f"{agent_name}-*.json"))
    if checkpoints:
        latest = max(checkpoints, key=lambda p: p.stat().st_mtime)
        print(f"\nLast Checkpoint:")
        print(f"  - File: {latest.name}")
        print(f"  - Time: {time.ctime(latest.stat().st_mtime)}")
