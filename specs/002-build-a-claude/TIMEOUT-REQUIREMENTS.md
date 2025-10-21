# Timeout Requirements for Agent Operations
**RFC Documentation Generator for Claude-Code**

**Date**: 2025-10-14
**Gap Item**: CHK009 (timeout requirements for agent operations)
**Status**: Design Specification
**Context**: No timeout specifications currently exist. Long-running or hung agents can block workflows indefinitely with no user feedback.

---

## Executive Summary

This document specifies timeout requirements for all agent operations in the RFC documentation generator. The design balances responsiveness (prevent hung workflows) with flexibility (allow large codebases to complete) through a **hybrid timeout strategy**: static defaults for predictability with dynamic scaling based on codebase size.

**Key Decisions**:
- **Hybrid timeout approach**: Static base + dynamic scaling (e.g., `parser_timeout = 600s + (LOC / 10000) * 60s`)
- **Progress tracking**: Restart timeout when agents show activity (checkpoint updates, log output)
- **Configuration hierarchy**: CLI args > env vars > plugin config > defaults
- **Cross-platform**: Use `subprocess.run(timeout=N)` for compatibility
- **User experience**: Progress indicators at 50%, 75%, 90% thresholds with remaining time

**Implementation Complexity**: ~8 hours (timeout wrapper + coordinator integration + testing)

---

## 1. Timeout Specifications

### 1.1 Default Timeout Values

Based on Phase 3 validation data (calculator.py test fixture) and performance targets from spec.md:

| Agent/Operation | Default Timeout | Scaling Formula | Notes |
|-----------------|-----------------|-----------------|-------|
| **Parser Agent** | 600s (10min) | `600 + (LOC / 10000) * 60` | 1 min/10K LOC after base |
| **Analyzer Agent** | 360s (6min) | `360 + (symbols / 100) * 30` | Depends on relationship complexity |
| **Formatter Agent** | 180s (3min) | `180 + (sections * 15)` | Usually fast, scales with sections |
| **Validator Agent** | 120s (2min) | `120 + (RFC_size_KB / 100) * 10` | Depends on RFC size |
| **Workflow Total** | 1800s (30min) | Sum of agent timeouts | Overall workflow limit |
| **Serena MCP Call** | 30s | Fixed | Network/LSP timeout |
| **File Parse** | 10s | Fixed | Single file should be fast |
| **Make Target** | 60s | Fixed | Existing behavior (hook_utils.py uses 10s, increase to 60s) |

**Rationale**:
- **Parser (10min base)**: Phase 3 test (1 file, 11 methods) completed in <1min. 10min base allows for larger files with many symbols. Scales with LOC for massive codebases.
- **Analyzer (6min base)**: Relationship analysis is slower than parsing. Test completed quickly, but cross-project analysis can be intensive.
- **Formatter (3min base)**: Fastest agent (text generation). Even large RFCs should complete quickly.
- **Validator (2min base)**: Make targets (`lint`, `txt`) typically complete in <1min per Phase 3 tests.
- **Workflow (30min)**: Covers 100K LOC target (spec.md: "100,000 lines under 20 minutes") with safety margin.

### 1.2 Timeout Calculation Examples

**Small Codebase (1K LOC, 50 symbols, 10 sections, 20KB RFC)**:
```
Parser:    600 + (1000/10000)*60    = 606s  (~10min)
Analyzer:  360 + (50/100)*30        = 375s  (~6min)
Formatter: 180 + (10*15)            = 330s  (~6min)
Validator: 120 + (20/100)*10        = 122s  (~2min)
---------------------------------------------------
Total:                              = 1433s (~24min)
```

**Medium Codebase (50K LOC, 2000 symbols, 30 sections, 200KB RFC)**:
```
Parser:    600 + (50000/10000)*60   = 900s  (~15min)
Analyzer:  360 + (2000/100)*30      = 960s  (~16min)
Formatter: 180 + (30*15)            = 630s  (~11min)
Validator: 120 + (200/100)*10       = 140s  (~2min)
---------------------------------------------------
Total:                              = 2630s (~44min)
```

**Large Codebase (1M LOC, 40000 symbols, 100 sections, 2MB RFC)**:
```
Parser:    600 + (1000000/10000)*60 = 6600s  (~110min)
Analyzer:  360 + (40000/100)*30     = 12360s (~206min)
Formatter: 180 + (100*15)           = 1680s  (~28min)
Validator: 120 + (2000/100)*10      = 320s   (~5min)
---------------------------------------------------
Total:                              = 20960s (~349min / 5.8hrs)
```

**Issue Identified**: Large codebase analyzer timeout (206min) exceeds reasonable limits. Analyzer scaling needs revision (see Section 1.3).

### 1.3 Revised Analyzer Scaling (After Analysis)

**Problem**: Linear scaling `360 + (symbols/100)*30` produces unrealistic timeouts for large codebases.

**Solution**: Cap analyzer timeout and recommend chunking for massive codebases:
```python
base = 360  # 6 minutes
scale_factor = min(symbols / 100, 60)  # Cap at 60x multiplier (2000 symbols max before capping)
analyzer_timeout = base + (scale_factor * 30)  # Max: 360 + 1800 = 2160s (36min)
```

**Result**: Analyzer timeout capped at 36 minutes. For codebases >100K LOC, recommend chunking (Phase 4).

### 1.4 Progress-Based Timeout Reset

**Mechanism**: Timeout resets when agent shows progress:
- **Checkpoint updates**: Agent writes to `.claude/.checkpoints/agent-{timestamp}.json`
- **Log output**: Agent produces stdout/stderr (if Task tool supports streaming)
- **File writes**: Agent creates intermediate files

**Example**:
```
Parser starts at T=0, timeout=600s
  T=300s: Parser writes checkpoint → timeout resets to T=300+600=900s
  T=700s: Parser writes checkpoint → timeout resets to T=700+600=1300s
  T=1100s: Parser completes → no timeout
```

**Benefit**: Handles long-but-progressing operations without false timeouts.

**Limitation**: If Task tool doesn't support streaming output, only checkpoint writes reset timeout.

---

## 2. Timeout Action Strategies

### 2.1 When Timeout Occurs

**Decision Tree**:
```
Timeout detected
├─ Has agent written checkpoint? (file exists in .claude/.checkpoints/)
│  ├─ YES → Option B: Warn user, offer to extend timeout
│  └─ NO → Likely hung, proceed to Option A
└─ Option A: Abort immediately, display error, save partial results
```

**Option A: Immediate Abort (Default)**
- Kill agent process (if possible with Task tool)
- Mark agent as "timed_out" in workflow state
- Display clear error message with timeout duration
- Save any partial results to `.claude/.draft-failed.json`
- Offer recovery options (see Section 2.3)

**Option B: Warn User, Offer Extension (If Checkpoint Exists)**
- Display: "Parser approaching timeout (9m 45s / 10m 00s). Checkpoint detected - agent is progressing."
- Prompt: "Extend timeout? (y/n) [default: y, 5 minutes]"
- If user confirms: Extend timeout by 50% of original (e.g., 10min → +5min)
- If user declines: Proceed to Option A
- **Non-interactive mode**: Auto-extend once if checkpoint exists

**Implementation Note**: If Claude Code Task tool doesn't support interactive prompts, default to auto-extend once (Option B becomes automatic).

### 2.2 Cascading Timeout Behavior

**Question**: If parser times out, should downstream agents run with partial results?

**Decision**: **Fail Fast** - Abort workflow immediately if critical agents timeout.

**Rationale**:
- Parser failure → No structural data → Analyzer/Formatter produce garbage
- Analyzer failure → Partial relationships → Formatter can proceed with structure only (warn user)
- Formatter failure → No RFC → Critical failure, abort
- Validator failure → RFC exists but unvalidated → Non-critical, warn and continue

**Cascading Rules**:
```
Parser timeout:     ABORT workflow, display error
Analyzer timeout:   WARN user, proceed with parser data only (structure, no relationships)
Formatter timeout:  ABORT workflow, display error (no RFC generated)
Validator timeout:  WARN user, write unvalidated RFC (user must validate manually)
```

### 2.3 Timeout Recovery Options

**When Critical Agent Times Out** (Parser, Formatter):
1. **Retry with extended timeout**: `/rfc-generate --parser-timeout 20m`
2. **Reduce scope**: `/rfc-generate src/core/` (fewer paths)
3. **Resume from checkpoint**: `/rfc-generate --resume` (if checkpoint exists)
4. **Report bug**: Provide `.claude/.checkpoints/` and logs for debugging

**When Non-Critical Agent Times Out** (Analyzer, Validator):
1. **Continue without analysis**: Accept structure-only RFC
2. **Run analyzer separately**: `/rfc-analyze-impact` (standalone command)
3. **Validate manually**: Run `make lint && make txt` after generation

---

## 3. User Experience Design

### 3.1 Progress Indicators

**Terminal Output** (during workflow):
```
✓ Prerequisites validated (1/5)
✓ Parser agent complete (2/5) - 1m 23s
  Analyzer agent running... (3/5)
  Progress: 75% (4m 30s / 6m 00s) ⏱️
  [██████████████████░░░░░░] Analyzing relationships...
```

**Threshold Warnings** (at 75%, 90% of timeout):
```
⚠️  Analyzer approaching timeout (5m 24s / 6m 00s)
   - Agent is progressing (last checkpoint: 23s ago)
   - Consider reducing scope or extending timeout
```

**Timeout Error Message**:
```
❌ Parser timed out after 10 minutes

Cause:
  - Large codebase (estimated 50K LOC)
  - Timeout insufficient for scope

Recovery Options:
  1. Extend timeout: /rfc-generate --parser-timeout 20m
  2. Reduce scope: /rfc-generate src/core/
  3. Resume from checkpoint: /rfc-generate --resume
  4. Report issue: Submit .claude/.checkpoints/parser-*.json

Last Checkpoint:
  - File: .claude/.checkpoints/parser-1734123456.json
  - Time: 2025-10-14T10:45:32Z
  - Symbols processed: 1234 / ~2000 (estimated)
```

### 3.2 Non-Interactive Mode (CI/CD)

**Environment Variable**: `CI=true` (auto-detected by hooks)

**Behavior Changes**:
- **No prompts**: Auto-extend timeout once if checkpoint exists (Option B becomes automatic)
- **No progress bars**: Use log-style output (`[2025-10-14 10:45:32] Analyzer: 75% complete`)
- **Warnings logged**: Write to `.claude/.workflow.log` instead of stderr
- **Failure = Exit Code**: Non-zero exit on timeout (CI pipeline fails)

**Example CI Log**:
```
[2025-10-14 10:45:00] Starting RFC generation workflow
[2025-10-14 10:45:02] ✓ Prerequisites validated
[2025-10-14 10:45:05] ✓ Parser complete (1m 23s)
[2025-10-14 10:47:30] ⚠️ Analyzer approaching timeout (75%)
[2025-10-14 10:48:00] ⚠️ Analyzer checkpoint detected, auto-extending timeout (+3min)
[2025-10-14 10:50:15] ✓ Analyzer complete (5m 13s)
[2025-10-14 10:51:00] ✓ Formatter complete (0m 45s)
[2025-10-14 10:51:30] ✓ Validator complete (0m 30s)
[2025-10-14 10:51:32] ✅ RFC generation complete (6m 32s total)
```

---

## 4. Timeout Configuration

### 4.1 Configuration Hierarchy (Precedence Order)

**1. CLI Arguments** (highest priority):
```bash
/rfc-generate --parser-timeout 15m --analyzer-timeout 10m
/rfc-generate --workflow-timeout 60m  # Overall limit
/rfc-generate --timeout 20m           # Shorthand: sets all agents
```

**2. Environment Variables**:
```bash
export RFC_PARSER_TIMEOUT=900      # 15 minutes (seconds)
export RFC_ANALYZER_TIMEOUT=10m    # 10 minutes (human-readable)
export RFC_WORKFLOW_TIMEOUT=1h     # 1 hour
export RFC_TIMEOUT=20m             # Shorthand: sets all agents
```

**3. Plugin Configuration** (`.claude/plugin.json`):
```json
{
  "timeouts": {
    "parser": 600,
    "analyzer": 360,
    "formatter": 180,
    "validator": 120,
    "workflow": 1800,
    "serena_call": 30,
    "make_target": 60,
    "auto_extend": true,
    "extend_factor": 0.5
  }
}
```

**4. Hardcoded Defaults** (lowest priority):
```python
DEFAULT_TIMEOUTS = {
    'parser': 600,
    'analyzer': 360,
    'formatter': 180,
    'validator': 120,
    'workflow': 1800,
    'serena_call': 30,
    'make_target': 60
}
```

### 4.2 Timeout Syntax

**Accepted Formats**:
- **Seconds**: `300`, `300s`
- **Minutes**: `5m`, `5min`
- **Hours**: `1h`, `1hour`, `1hr`
- **Special**: `infinity`, `none`, `0` (disable timeout)

**Validation**:
- **Minimum**: 30s (prevent impossibly short timeouts)
- **Maximum**: 24h (sanity check)
- **Warnings**:
  - `timeout < 60s`: "Warning: Very short timeout ({value}s) may cause failures"
  - `timeout > 7200s` (2hrs): "Warning: Long timeout ({value}) may hide hung processes"

**Parser** (in coordinator):
```python
def parse_timeout(value: str) -> int:
    """
    Parse timeout string to seconds.

    Args:
        value: Timeout string (e.g., "5m", "300s", "1h")

    Returns:
        Timeout in seconds

    Raises:
        ValueError: If format invalid or out of range
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
```

### 4.3 Configuration Schema (plugin.json)

**Complete Schema**:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "RFC Generator Plugin Configuration",
  "type": "object",
  "properties": {
    "timeouts": {
      "type": "object",
      "description": "Timeout configurations for agents and operations",
      "properties": {
        "parser": {
          "type": "integer",
          "description": "Parser agent timeout in seconds (default: 600)",
          "minimum": 30,
          "maximum": 86400
        },
        "analyzer": {
          "type": "integer",
          "description": "Analyzer agent timeout in seconds (default: 360)",
          "minimum": 30,
          "maximum": 86400
        },
        "formatter": {
          "type": "integer",
          "description": "Formatter agent timeout in seconds (default: 180)",
          "minimum": 30,
          "maximum": 86400
        },
        "validator": {
          "type": "integer",
          "description": "Validator agent timeout in seconds (default: 120)",
          "minimum": 30,
          "maximum": 86400
        },
        "workflow": {
          "type": "integer",
          "description": "Overall workflow timeout in seconds (default: 1800)",
          "minimum": 30,
          "maximum": 86400
        },
        "serena_call": {
          "type": "integer",
          "description": "Individual Serena MCP call timeout in seconds (default: 30)",
          "minimum": 5,
          "maximum": 300
        },
        "make_target": {
          "type": "integer",
          "description": "Make target timeout in seconds (default: 60)",
          "minimum": 10,
          "maximum": 600
        },
        "auto_extend": {
          "type": "boolean",
          "description": "Auto-extend timeout once if checkpoint exists (default: true)"
        },
        "extend_factor": {
          "type": "number",
          "description": "Factor to multiply timeout by when extending (default: 0.5 = +50%)",
          "minimum": 0.1,
          "maximum": 2.0
        },
        "enable_scaling": {
          "type": "boolean",
          "description": "Enable dynamic timeout scaling based on codebase size (default: true)"
        }
      }
    }
  }
}
```

**Example Configuration**:
```json
{
  "name": "rfc-generator",
  "version": "1.0.0",
  "timeouts": {
    "parser": 900,
    "analyzer": 600,
    "formatter": 300,
    "validator": 180,
    "workflow": 3600,
    "serena_call": 30,
    "make_target": 60,
    "auto_extend": true,
    "extend_factor": 0.5,
    "enable_scaling": true
  },
  "mandatory_sections": ["abstract", "terminology", "interfaces", "behavior", "security"],
  "hooks": {
    "preToolUse": [
      {"name": "pre_tool_validate", "enabled": true, "matcher": "Write|Edit"},
      {"name": "pre_bash_enforce", "enabled": true, "matcher": "Bash"}
    ]
  }
}
```

---

## 5. Implementation Approach

### 5.1 Python Timeout Mechanism (Recommended)

**Use `subprocess.run(timeout=N)` for Cross-Platform Compatibility**:

**Pros**:
- ✅ Works on Windows, macOS, Linux
- ✅ Simple API: `subprocess.run(cmd, timeout=N)`
- ✅ Raises `subprocess.TimeoutExpired` exception
- ✅ Already used in `hook_utils.py` (line 413-418)

**Cons**:
- ❌ Requires agents to run as subprocesses (not in-process)
- ❌ No built-in progress tracking (must poll checkpoint files)

**Alternative Rejected: `signal.alarm()`**:
- ❌ Unix-only (not Windows)
- ❌ Conflicts with other signal handlers
- ❌ Not thread-safe

**Alternative Rejected: `threading.Timer()`**:
- ❌ Adds threading complexity
- ❌ Race conditions possible
- ❌ Cleanup on exception is error-prone

### 5.2 Agent Wrapper Implementation

**Approach**: Wrap Task tool calls with timeout monitoring.

**Code Example** (`.claude/lib/agent_runner.py`):
```python
import subprocess
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class AgentTimeoutError(Exception):
    """Raised when agent exceeds timeout."""
    pass

class AgentRunner:
    """
    Wrapper for running agents with timeout and progress tracking.
    """

    def __init__(self, agent_name: str, timeout: int, checkpoint_dir: str = ".claude/.checkpoints"):
        self.agent_name = agent_name
        self.timeout = timeout
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def run(self, agent_path: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run agent with timeout and progress tracking.

        Args:
            agent_path: Path to agent markdown file
            input_data: Input data for agent

        Returns:
            Agent output dictionary

        Raises:
            AgentTimeoutError: If agent exceeds timeout
        """
        start_time = time.time()
        checkpoint_pattern = f"{self.agent_name}-*.json"
        initial_checkpoints = set(self.checkpoint_dir.glob(checkpoint_pattern))

        # Write input to temp file
        input_file = self.checkpoint_dir / f"{self.agent_name}-input.json"
        with open(input_file, 'w') as f:
            json.dump(input_data, f, indent=2)

        # Build command for Task tool (conceptual - actual Task API may differ)
        cmd = [
            'claude-task',
            'spawn',
            agent_path,
            '--input', str(input_file),
            '--timeout', str(self.timeout)
        ]

        try:
            # Run agent as subprocess with timeout
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

                if new_checkpoints:
                    latest_checkpoint = max(new_checkpoints, key=lambda p: p.stat().st_mtime)
                    checkpoint_age = time.time() - latest_checkpoint.stat().st_mtime

                    if checkpoint_age < poll_interval * 2:
                        # Recent checkpoint = progress, reset timeout
                        logger.debug(f"{self.agent_name} checkpoint detected, resetting timeout")
                        remaining_timeout = self.timeout
                        start_time = time.time()  # Reset start time

                # Report progress
                elapsed = time.time() - start_time
                progress_pct = (elapsed / self.timeout) * 100

                if progress_pct >= 75 and progress_pct < 90:
                    logger.warning(
                        f"{self.agent_name} at 75% timeout "
                        f"({elapsed:.0f}s / {self.timeout}s)"
                    )
                elif progress_pct >= 90:
                    logger.warning(
                        f"{self.agent_name} at 90% timeout "
                        f"({elapsed:.0f}s / {self.timeout}s)"
                    )

                # Sleep and decrement timeout
                time.sleep(poll_interval)
                remaining_timeout -= poll_interval

            # Timeout exceeded
            process.terminate()
            time.sleep(1)
            if process.poll() is None:
                process.kill()

            elapsed = time.time() - start_time
            raise AgentTimeoutError(
                f"{self.agent_name} timed out after {elapsed:.0f}s "
                f"(limit: {self.timeout}s)"
            )

        except subprocess.TimeoutExpired:
            elapsed = time.time() - start_time
            raise AgentTimeoutError(
                f"{self.agent_name} timed out after {elapsed:.0f}s "
                f"(limit: {self.timeout}s)"
            )

    def _parse_output(self, stdout: str) -> Dict[str, Any]:
        """Parse agent output from stdout."""
        try:
            return json.loads(stdout)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse {self.agent_name} output: {e}")
            return {"error": "Invalid JSON output", "raw": stdout}
```

**Integration with Coordinator**:
```python
# In rfc-generate.md coordinator logic (conceptual)
from .lib.agent_runner import AgentRunner, AgentTimeoutError

# Calculate dynamic timeout
parser_timeout = calculate_timeout('parser', codebase_size)

# Run parser with timeout
runner = AgentRunner('parser', parser_timeout)
try:
    parser_output = runner.run('.claude/agents/parser.md', input_data)
except AgentTimeoutError as e:
    logger.error(str(e))
    display_timeout_error('parser', parser_timeout, has_checkpoint=True)
    # Offer recovery options
    raise
```

### 5.3 Checkpoint Integration

**Checkpoint Format** (`.claude/.checkpoints/parser-{timestamp}.json`):
```json
{
  "agent": "parser",
  "timestamp": "2025-10-14T10:45:32Z",
  "status": "in_progress",
  "progress": {
    "files_processed": 123,
    "files_total": 189,
    "symbols_extracted": 1234,
    "current_file": "src/api/handlers.py"
  },
  "checksum": "abc123...",
  "elapsed_seconds": 345
}
```

**Timeout Reset Logic**:
- Monitor `.claude/.checkpoints/` directory for new files
- If checkpoint modified within last `2 * poll_interval` seconds → reset timeout
- Log: "Checkpoint detected, resetting timeout (progress: 123/189 files)"

### 5.4 Testing Strategy

**Challenge**: Testing timeouts without waiting (e.g., don't wait 10 minutes for timeout).

**Solution**: Mock clocks and fast-forward time.

**Test Scenarios**:

**1. Normal Completion (No Timeout)**:
```python
def test_agent_completes_before_timeout():
    """Agent completes successfully within timeout."""
    runner = AgentRunner('parser', timeout=60)

    # Mock agent that completes in 5 seconds
    with patch('subprocess.Popen') as mock_popen:
        mock_process = MagicMock()
        mock_process.poll.side_effect = [None, None, 0]  # Running, then done
        mock_process.communicate.return_value = ('{"result": "ok"}', '')
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        result = runner.run('agent.md', {})

        assert result == {"result": "ok"}
        assert mock_process.terminate.not_called()
```

**2. Timeout with No Progress**:
```python
def test_agent_timeout_no_progress():
    """Agent times out with no checkpoint updates."""
    runner = AgentRunner('parser', timeout=10)  # Short timeout for test

    with patch('subprocess.Popen') as mock_popen, \
         patch('time.sleep'):  # Mock sleep to avoid actual waiting

        mock_process = MagicMock()
        mock_process.poll.return_value = None  # Never completes
        mock_popen.return_value = mock_process

        with pytest.raises(AgentTimeoutError, match="timed out after"):
            runner.run('agent.md', {})

        assert mock_process.terminate.called
```

**3. Timeout Reset on Checkpoint**:
```python
def test_agent_timeout_reset_on_checkpoint():
    """Timeout resets when checkpoint is written."""
    runner = AgentRunner('parser', timeout=20)

    # Create fake checkpoint during execution
    checkpoint_file = Path(runner.checkpoint_dir) / "parser-123.json"

    def write_checkpoint_on_second_poll(*args):
        if mock_process.poll.call_count == 2:
            checkpoint_file.write_text('{"status": "in_progress"}')
        return None

    with patch('subprocess.Popen') as mock_popen, \
         patch('time.sleep'), \
         patch('time.time', side_effect=[0, 5, 10, 15, 20]):  # Simulate time progression

        mock_process = MagicMock()
        mock_process.poll.side_effect = write_checkpoint_on_second_poll
        mock_popen.return_value = mock_process

        # Agent should NOT timeout because checkpoint was written
        # (In real implementation, timeout would reset)
        # This test verifies checkpoint detection logic
```

**4. Progress Warnings at Thresholds**:
```python
def test_progress_warnings():
    """Warning messages at 75% and 90% thresholds."""
    runner = AgentRunner('parser', timeout=100)

    with patch('subprocess.Popen') as mock_popen, \
         patch('time.sleep'), \
         patch('time.time', side_effect=range(0, 100, 5)), \
         patch('logging.Logger.warning') as mock_warning:

        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        try:
            runner.run('agent.md', {})
        except AgentTimeoutError:
            pass

        # Verify warnings at 75% and 90%
        warning_calls = [call[0][0] for call in mock_warning.call_args_list]
        assert any("75%" in msg for msg in warning_calls)
        assert any("90%" in msg for msg in warning_calls)
```

**5. Timeout in CI Mode**:
```python
def test_timeout_ci_mode_auto_extend():
    """In CI mode, timeout auto-extends once if checkpoint exists."""
    runner = AgentRunner('parser', timeout=60)

    # Simulate CI environment
    with patch.dict('os.environ', {'CI': 'true'}), \
         patch('subprocess.Popen'):

        # Create checkpoint to trigger auto-extend
        checkpoint = Path(runner.checkpoint_dir) / "parser-123.json"
        checkpoint.write_text('{"status": "in_progress"}')

        # Test auto-extend logic
        # (Implementation would extend timeout from 60s to 90s automatically)
```

---

## 6. Production Readiness Checklist

**Implementation Tasks**:
- [ ] Create `agent_runner.py` module with `AgentRunner` class
- [ ] Add timeout parsing function with validation
- [ ] Integrate timeout config into `plugin.json` schema
- [ ] Update `rfc-generate.md` to use `AgentRunner` wrapper
- [ ] Implement checkpoint monitoring for timeout reset
- [ ] Add progress indicator at 50%, 75%, 90% thresholds
- [ ] Write unit tests for timeout scenarios
- [ ] Update `hook_utils.py` Make timeout from 10s to 60s
- [ ] Document timeout configuration in quickstart.md
- [ ] Add timeout troubleshooting guide

**Testing Requirements**:
- [ ] Test normal completion (no timeout)
- [ ] Test timeout with no progress (abort)
- [ ] Test timeout with checkpoint (auto-extend)
- [ ] Test progress warnings (75%, 90%)
- [ ] Test timeout in CI mode (non-interactive)
- [ ] Test configuration hierarchy (CLI > env > config > default)
- [ ] Test timeout parsing (5m, 300s, 1h, infinity)
- [ ] Test validation (min 30s, max 24h)

**Documentation Requirements**:
- [ ] Add timeout section to quickstart.md
- [ ] Document CLI arguments (`--timeout`, `--parser-timeout`, etc.)
- [ ] Document environment variables (`RFC_TIMEOUT`, etc.)
- [ ] Add troubleshooting section for timeout errors
- [ ] Update spec.md success criteria with timeout targets

**Estimated Implementation Time**: ~8 hours
- `agent_runner.py` implementation: 3 hours
- Coordinator integration: 2 hours
- Unit tests: 2 hours
- Documentation: 1 hour

---

## 7. Profiling & Baseline Recommendations

**Current Profiling Data** (from Phase 3):
- **Test Fixture**: `calculator.py` (1 file, 11 methods, 119 LOC)
- **Parser Duration**: <1 minute (estimated, not explicitly logged)
- **Analyzer Duration**: <1 minute (estimated)
- **Formatter Duration**: <1 minute (estimated)
- **Validator Duration**: <1 minute (Make `txt` target)
- **Total Workflow**: ~3-5 minutes (end-to-end)

**Profiling Gaps**:
- ❌ No exact timing data for individual agents
- ❌ No data for medium (10K LOC) or large (100K LOC) codebases
- ❌ No data for relationship analysis complexity (analyzer)

**Recommended Profiling Approach** (Phase 4):
1. **Add timing instrumentation** to each agent:
   ```python
   start_time = time.time()
   # ... agent work ...
   elapsed = time.time() - start_time
   logger.info(f"{agent_name} completed in {elapsed:.2f}s")
   ```

2. **Create test fixtures** for different sizes:
   - Small: 1K LOC, 50 symbols (existing calculator.py)
   - Medium: 10K LOC, 500 symbols (mock project)
   - Large: 100K LOC, 5000 symbols (real project, e.g., i-d-template itself)

3. **Measure percentiles** (p50, p95, p99):
   ```
   Codebase Size | Parser p50 | Parser p95 | Analyzer p50 | Analyzer p95
   1K LOC        | 10s        | 30s        | 15s          | 45s
   10K LOC       | 120s       | 300s       | 90s          | 240s
   100K LOC      | 600s       | 1200s      | 480s         | 1080s
   ```

4. **Set defaults based on p95 + 50% safety margin**:
   ```
   Parser default: 600s (p95 for 10K LOC = 300s, +50% = 450s, rounded to 600s)
   Analyzer default: 360s (p95 for 10K LOC = 240s, +50% = 360s)
   ```

**Post-Profiling Adjustment**:
- If defaults are too conservative (90% of runs complete in <50% of timeout): Reduce defaults
- If defaults are too aggressive (>10% of runs timeout): Increase defaults
- Consider codebase-specific recommendations in error messages

---

## 8. Open Questions & Future Work

**Open Questions**:
1. **Does Claude Code Task tool support streaming output?**
   - **Impact**: If yes, can monitor stdout for progress. If no, rely on checkpoint files only.
   - **Resolution**: Check Task tool documentation or test empirically.

2. **Can Task tool accept timeout parameter directly?**
   - **Impact**: If yes, simpler implementation (pass `timeout=N` to Task). If no, use subprocess wrapper.
   - **Resolution**: Check Task tool API.

3. **How to handle timeout in interactive vs non-interactive mode?**
   - **Current Design**: Auto-extend in CI mode, prompt user otherwise.
   - **Alternative**: Always auto-extend once (no prompts).
   - **Resolution**: User testing feedback.

4. **Should analyzer timeout scale with LOC or with symbol count?**
   - **Current Design**: Scales with symbol count (more accurate for relationship analysis).
   - **Alternative**: Scale with LOC (simpler, no pre-count needed).
   - **Resolution**: Profiling data will reveal correlation.

**Future Enhancements** (Phase 5+):
1. **Adaptive Timeouts** (learn from history):
   - Track agent durations in `.claude/.performance-history.json`
   - Calculate running average and p95
   - Set timeout = `p95 * 1.5` (self-tuning)
   - **Benefit**: Handles project-specific characteristics
   - **Complexity**: Requires persistent storage and statistical logic

2. **Parallel Agent Execution** (reduce total time):
   - Run analyzer and formatter in parallel (if parser output is partitionable)
   - **Benefit**: Cut total time by ~30%
   - **Complexity**: Requires coordination logic and partial result handling

3. **Incremental Timeout Scaling** (checkpoint-based):
   - Instead of fixed timeout, allocate time budget (e.g., 1000s)
   - Each checkpoint consumes budget based on actual time
   - Remaining budget = adaptive timeout for next phase
   - **Benefit**: Fair allocation across variable-complexity phases
   - **Complexity**: Requires budget tracking and dynamic reallocation

4. **Timeout Profiler Tool** (`/rfc-profile`):
   - Command to measure agent durations for current codebase
   - Output recommended timeouts
   - **Example**:
     ```
     /rfc-profile

     Profiling Results (based on 3 runs):
     - Parser: avg 4m 32s, p95 5m 45s → Recommend: 9m timeout
     - Analyzer: avg 3m 12s, p95 4m 20s → Recommend: 7m timeout

     Add to .claude/plugin.json:
     {
       "timeouts": {
         "parser": 540,
         "analyzer": 420
       }
     }
     ```

---

## 9. Summary & Recommendations

### Key Takeaways

1. **Hybrid Timeout Strategy**: Static base + dynamic scaling balances predictability with flexibility.
2. **Progress Tracking**: Checkpoint-based timeout reset prevents false timeouts for long-but-progressing agents.
3. **User Experience**: Clear progress indicators and actionable error messages improve usability.
4. **Configuration Flexibility**: CLI > env > config > defaults hierarchy supports diverse use cases.
5. **Cross-Platform Compatibility**: `subprocess.run(timeout=N)` works everywhere.

### Immediate Actions (Ready to Implement)

1. **Create `agent_runner.py`** with timeout wrapper (3 hours)
2. **Integrate into `rfc-generate.md` coordinator** (2 hours)
3. **Add timeout tests** (mock clocks, fast-forward) (2 hours)
4. **Update `plugin.json` schema** with timeout config (1 hour)

**Total Effort**: ~8 hours

### Phase 4 Actions (Post-MVP)

1. **Profiling Campaign**: Measure actual agent durations on real codebases
2. **Refine Defaults**: Adjust timeout values based on profiling data
3. **Adaptive Timeouts**: Implement history-based timeout tuning
4. **Parallel Agents**: Explore parallelization to reduce total workflow time

### Success Metrics

- ✅ **Zero hung workflows**: All operations complete or timeout within predictable time
- ✅ **<5% false timeouts**: Legitimate long operations complete without timeout
- ✅ **Clear recovery path**: Users know what to do when timeout occurs
- ✅ **CI/CD compatible**: Non-interactive mode works reliably

---

**Document Version**: 1.0
**Last Updated**: 2025-10-14
**Next Review**: After Phase 4 profiling campaign
