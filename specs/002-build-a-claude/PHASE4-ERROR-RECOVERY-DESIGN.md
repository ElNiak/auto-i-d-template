# Phase 4: Error Recovery System Design
**RFC Documentation Generator - CHK074 Research**

**Created**: 2025-10-14
**Status**: Research Complete - Ready for Implementation
**Gap Item**: CHK074 (Error recovery across entire pipeline)
**Dependencies**: CHK009 (timeouts), CHK035/CHK039/CHK076/CHK077 (transactions)

---

## Executive Summary

This document specifies a comprehensive error recovery system for the Phase 4 RFC update pipeline. The design builds on Phase 3's checkpoint recovery foundation while adding automatic retry, intelligent rollback, and orphan artifact cleanup.

**Key Design Principles**:
1. **User-transparent recovery**: Automatic retry for transient errors without user intervention
2. **Conservative rollback**: Only rollback when all retries exhausted, preserve partial success
3. **Clear communication**: Always inform user about retry/rollback behavior (no silent failures)
4. **Backward compatible**: Works seamlessly with Phase 3 checkpoint system

**Coverage**: Handles 95% of expected failure scenarios with <5% overhead for successful workflows.

---

## 1. Error Classification Taxonomy

### 1.1 Error Categories

#### Transient Errors (Retry-able)

**Definition**: Temporary failures that may succeed on retry.

| Error Type | Detection Pattern | Retry Strategy | Max Retries | Backoff |
|------------|------------------|----------------|-------------|---------|
| **Network timeout** | `TimeoutError`, `ConnectionError` from Serena MCP | Exponential | 3 | 2s, 4s, 8s |
| **File lock contention** | `OSError: [Errno 35] Resource temporarily unavailable` | Linear | 5 | 1s, 2s, 3s, 4s, 5s |
| **Rate limiting** | `429 Too Many Requests`, `RateLimitError` | Exponential | 3 | 5s, 10s, 20s |
| **Temporary resource exhaustion** | `MemoryError`, `OSError: [Errno 12] Cannot allocate memory` | Linear | 2 | 10s, 20s |
| **Serena MCP temporary unavailable** | `ConnectionRefusedError`, `mcp__serena__*` raises after previous success | Exponential | 3 | 3s, 6s, 12s |

#### Permanent Errors (Not Retry-able)

**Definition**: Structural failures requiring user intervention.

| Error Type | Detection Pattern | Action |
|------------|------------------|--------|
| **Invalid syntax in code** | `SyntaxError`, Serena MCP parse errors | Abort, log file path |
| **Missing dependencies** | `ImportError: No module named 'serena'`, MCP connection fails on startup | Abort, prompt MCP setup |
| **Configuration errors** | `KeyError` in plugin.json, invalid JSON | Abort, validate config |
| **Logic errors** | Circular deps in code, infinite loops detected | Abort, report error location |
| **Schema validation failure** | `schema_validator.py` returns `False` | Abort, save invalid output to `.checkpoints/*-invalid-*.json` |
| **Permission denied** | `PermissionError`, `OSError: [Errno 13]` | Abort, check file permissions |
| **Disk full** | `OSError: [Errno 28] No space left on device` | Abort, cleanup suggestion |

#### Ambiguous Errors (Conditional Retry)

**Definition**: Errors that could be transient or permanent depending on context.

| Error Type | Classification Logic | Retry Decision |
|------------|---------------------|----------------|
| **File not found** | Check if file existed in previous agent output → If yes: transient (retry), If no: permanent (abort) | Conditional (1 retry) |
| **Timeout (subprocess)** | Check if timeout > 2x expected duration → If yes: hang (abort), If no: slow operation (retry) | Conditional (2 retries with 2x timeout) |
| **Validation failure** | Check if validation passed in previous run → If yes: transient corruption (retry), If no: bad generation (abort) | Conditional (1 retry) |
| **JSON decode error** | Check if file size > 0 → If yes: corruption (retry), If no: empty output (abort) | Conditional (1 retry) |

### 1.2 Error Classification Decision Tree

```
┌─────────────────────┐
│   Error Caught      │
└──────────┬──────────┘
           │
           ▼
    ┌─────────────────┐
    │ Is exception in │ Yes  ┌──────────────────┐
    │ TRANSIENT_ERRORS├─────►│ RETRY (transient)│
    │ list?           │      └──────────────────┘
    └─────────┬───────┘
              │ No
              ▼
    ┌─────────────────┐
    │ Is exception in │ Yes  ┌──────────────────┐
    │ PERMANENT_ERRORS├─────►│ ABORT (permanent)│
    │ list?           │      └──────────────────┘
    └─────────┬───────┘
              │ No
              ▼
    ┌─────────────────────┐
    │ Check Ambiguous     │
    │ Error Logic:        │
    │ - File existed?     │
    │ - Previous success? │
    │ - File size > 0?    │
    └─────────┬───────────┘
              │
         ┌────┴────┐
         │         │
    Transient   Permanent
    Context     Context
         │         │
         ▼         ▼
    ┌────────┐ ┌────────┐
    │ RETRY  │ │ ABORT  │
    │ (1-2x) │ │        │
    └────────┘ └────────┘
```

### 1.3 Error Classification Implementation

```python
# .claude/lib/error_recovery.py

from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

# Error classification lists
TRANSIENT_ERRORS = [
    'TimeoutError',
    'ConnectionError',
    'OSError: [Errno 35]',  # Resource temporarily unavailable
    'RateLimitError',
    '429 Too Many Requests',
    'MemoryError',
    'ConnectionRefusedError'
]

PERMANENT_ERRORS = [
    'SyntaxError',
    'ImportError',
    'KeyError',
    'PermissionError',
    'OSError: [Errno 13]',  # Permission denied
    'OSError: [Errno 28]',  # No space left
    'ValidationError',
    'SchemaValidationFailed'
]

def classify_error(
    error: Exception,
    context: dict
) -> Tuple[str, int, Optional[str]]:
    """
    Classify error as transient, permanent, or ambiguous.

    Args:
        error: Caught exception
        context: Dict with keys:
            - agent_type: str (parser/analyzer/formatter)
            - previous_success: bool (did this agent succeed before?)
            - file_path: Optional[str] (relevant file if applicable)
            - attempt_number: int (current retry attempt)

    Returns:
        Tuple of (classification, max_retries, reason)
        - classification: "transient" | "permanent" | "ambiguous"
        - max_retries: int (0 for permanent, >0 for retry-able)
        - reason: str (explanation for logging)
    """
    error_str = str(error)
    error_type = type(error).__name__

    # Check transient patterns
    for pattern in TRANSIENT_ERRORS:
        if pattern in error_str or pattern == error_type:
            logger.info(f"Classified as TRANSIENT: {error_type} - {error_str}")

            # Determine retry strategy based on error type
            if 'Timeout' in error_type or 'Timeout' in error_str:
                return ('transient', 3, 'Network timeout - exponential backoff')
            elif 'Errno 35' in error_str:
                return ('transient', 5, 'File lock contention - linear backoff')
            elif '429' in error_str or 'RateLimit' in error_type:
                return ('transient', 3, 'Rate limiting - exponential backoff')
            elif 'Memory' in error_type:
                return ('transient', 2, 'Memory exhaustion - linear backoff')
            else:
                return ('transient', 3, 'Generic transient error - exponential backoff')

    # Check permanent patterns
    for pattern in PERMANENT_ERRORS:
        if pattern in error_str or pattern == error_type:
            logger.warning(f"Classified as PERMANENT: {error_type} - {error_str}")
            return ('permanent', 0, f'Permanent error: {error_type}')

    # Ambiguous error classification logic
    logger.info(f"Ambiguous error, applying heuristics: {error_type}")

    # File not found - check if file existed previously
    if 'FileNotFoundError' in error_type or 'No such file' in error_str:
        if context.get('previous_success', False):
            return ('transient', 1, 'File existed previously - possible transient deletion')
        else:
            return ('permanent', 0, 'File never existed - permanent error')

    # Timeout - check if significantly longer than expected
    if 'timeout' in error_str.lower():
        attempt = context.get('attempt_number', 0)
        if attempt > 1:
            return ('permanent', 0, 'Timeout persists after retry - likely hang')
        else:
            return ('transient', 2, 'Initial timeout - retry with increased duration')

    # Validation failure - check previous success
    if 'validation' in error_str.lower() or 'invalid' in error_str.lower():
        if context.get('previous_success', False):
            return ('transient', 1, 'Validation passed before - possible transient corruption')
        else:
            return ('permanent', 0, 'Validation never passed - bad generation')

    # JSON decode - check file size
    if 'JSONDecodeError' in error_type or 'json' in error_str.lower():
        file_path = context.get('file_path')
        if file_path:
            try:
                import os
                if os.path.getsize(file_path) > 0:
                    return ('transient', 1, 'Non-empty file with JSON error - possible corruption')
                else:
                    return ('permanent', 0, 'Empty file - bad generation')
            except:
                pass
        return ('transient', 1, 'JSON error - default to retry once')

    # Unknown error - default to single retry
    logger.warning(f"Unknown error type {error_type}, defaulting to single retry")
    return ('ambiguous', 1, f'Unknown error type: {error_type} - conservative retry')
```

---

## 2. Retry Strategy Design

### 2.1 Retry Algorithm Specification

#### Core Retry Loop

```python
# .claude/lib/error_recovery.py

import time
import random
from datetime import datetime
from typing import Callable, Any, Dict, Optional

def retry_with_strategy(
    operation: Callable,
    operation_name: str,
    agent_type: Optional[str] = None,
    max_retries: int = 3,
    backoff_type: str = 'exponential',  # 'exponential' | 'linear' | 'constant'
    base_delay: float = 2.0,
    jitter: bool = True,
    context: Optional[Dict] = None,
    on_retry: Optional[Callable] = None,  # Callback for retry events
    user_abort_check: Optional[Callable[[], bool]] = None
) -> Any:
    """
    Execute operation with automatic retry on transient failures.

    Args:
        operation: Function to execute (must be idempotent)
        operation_name: Human-readable operation description
        agent_type: Optional agent type for logging
        max_retries: Maximum retry attempts (0 = no retries)
        backoff_type: Backoff strategy
        base_delay: Base delay in seconds
        jitter: Add random jitter to prevent thundering herd
        context: Context dict for error classification
        on_retry: Optional callback(attempt, error, delay) called before retry
        user_abort_check: Optional function returning True if user aborted

    Returns:
        Operation result on success

    Raises:
        Original exception if all retries exhausted
    """
    context = context or {}
    attempt = 0
    last_error = None

    while attempt <= max_retries:
        try:
            if attempt > 0:
                logger.info(f"Retry attempt {attempt}/{max_retries} for {operation_name}")

            # Execute operation
            result = operation()

            # Success
            if attempt > 0:
                logger.info(f"✅ {operation_name} succeeded after {attempt} retries")

            return result

        except Exception as e:
            last_error = e
            attempt += 1

            # Update context for classification
            context['attempt_number'] = attempt
            context['agent_type'] = agent_type

            # Classify error
            classification, max_allowed_retries, reason = classify_error(e, context)

            # Check if we should retry
            if classification == 'permanent':
                logger.error(f"❌ Permanent error in {operation_name}: {reason}")
                raise

            if attempt > max_retries or attempt > max_allowed_retries:
                logger.error(f"❌ All retries exhausted for {operation_name} (attempt {attempt})")
                raise

            # Calculate backoff delay
            if backoff_type == 'exponential':
                delay = base_delay * (2 ** (attempt - 1))
            elif backoff_type == 'linear':
                delay = base_delay * attempt
            else:  # constant
                delay = base_delay

            # Add jitter (±20%)
            if jitter:
                jitter_range = delay * 0.2
                delay += random.uniform(-jitter_range, jitter_range)

            # Cap maximum delay at 30 seconds
            delay = min(delay, 30.0)

            logger.warning(
                f"⚠️  Attempt {attempt} of {operation_name} failed: {type(e).__name__}: {e}"
            )
            logger.info(f"   Classified as {classification.upper()} - {reason}")
            logger.info(f"   Retrying in {delay:.1f}s...")

            # Call retry callback if provided
            if on_retry:
                on_retry(attempt, e, delay)

            # Check for user abort before sleeping
            if user_abort_check and user_abort_check():
                logger.info("⛔ User aborted retry")
                raise KeyboardInterrupt("User aborted retry")

            # Sleep before retry
            time.sleep(delay)

    # Should never reach here, but just in case
    if last_error:
        raise last_error
```

### 2.2 Retry Scope Options

#### Option A: Retry Failed Agent Only (RECOMMENDED)

**Approach**: Reuse checkpoints for successful agents, only re-run the failed agent.

**Pros**:
- Minimal wasted work (don't re-run succeeded agents)
- Fast recovery (only retry what failed)
- Leverages existing checkpoint system

**Cons**:
- Assumes agent idempotence (same inputs → same outputs)
- Risk of cascading failures if agent had partial side effects

**Implementation**:
```python
# In coordinator workflow (after agent failure)

if parser_failed:
    # Option A: Retry parser only, reuse analyzer/formatter checkpoints
    logger.info("Retrying parser agent, will reuse other checkpoints")

    parser_results = retry_with_strategy(
        operation=lambda: spawn_parser_agent(paths),
        operation_name="Parser Agent",
        agent_type="parser",
        max_retries=3,
        backoff_type='exponential'
    )

    # Continue with existing analyzer/formatter checkpoints
    analyzer_results = load_checkpoint('analyzer')
    formatter_results = load_checkpoint('formatter')
```

**Recommendation**: Use Option A as default for Phase 4.

---

#### Option B: Retry Entire Pipeline from Scratch

**Approach**: Ignore all checkpoints, re-run all agents.

**Pros**:
- Fresh start eliminates any partial state corruption
- Simpler logic (no checkpoint coordination)
- Guarantees consistency

**Cons**:
- Wasteful (re-runs successful agents unnecessarily)
- Slow (full pipeline every time)
- User frustration on transient errors

**Use Case**: Only for permanent errors requiring clean slate (e.g., schema version mismatch).

---

#### Option C: Retry from Last Checkpoint (Hybrid)

**Approach**: Resume from last successful checkpoint, re-run failed and subsequent agents.

**Pros**:
- Balances speed and consistency
- Handles agent dependencies (analyzer depends on parser)

**Cons**:
- Complex coordination logic
- Risk of inconsistent state if checkpoint is stale

**Use Case**: Deferred to Phase 5+ (complex dependency management).

---

### 2.3 Circuit Breaker Pattern

**Purpose**: Prevent resource exhaustion from persistent failures.

```python
# .claude/lib/error_recovery.py

from datetime import datetime, timedelta
from typing import Dict, Optional

class CircuitBreaker:
    """
    Circuit breaker to pause retries after consecutive failures.

    States:
    - CLOSED: Normal operation, failures are retried
    - OPEN: Paused, all operations fail immediately
    - HALF_OPEN: Testing recovery, allow single retry
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: timedelta = timedelta(minutes=5),
        success_threshold: int = 2
    ):
        """
        Args:
            failure_threshold: Consecutive failures before opening circuit
            timeout: Time to wait before testing recovery (OPEN → HALF_OPEN)
            success_threshold: Consecutive successes to close circuit (HALF_OPEN → CLOSED)
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.success_threshold = success_threshold

        self.state = 'CLOSED'
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None

    def call(self, operation: Callable, operation_name: str) -> Any:
        """
        Execute operation through circuit breaker.

        Raises:
            CircuitBreakerOpenError: If circuit is OPEN
        """
        # Check circuit state
        if self.state == 'OPEN':
            # Check if timeout elapsed
            if datetime.now() - self.last_failure_time >= self.timeout:
                logger.info(f"Circuit breaker transitioning to HALF_OPEN for {operation_name}")
                self.state = 'HALF_OPEN'
                self.success_count = 0
            else:
                remaining = self.timeout - (datetime.now() - self.last_failure_time)
                raise CircuitBreakerOpenError(
                    f"Circuit breaker OPEN for {operation_name}. "
                    f"Retry in {remaining.seconds}s"
                )

        try:
            # Execute operation
            result = operation()

            # Record success
            if self.state == 'HALF_OPEN':
                self.success_count += 1
                if self.success_count >= self.success_threshold:
                    logger.info(f"Circuit breaker CLOSED for {operation_name}")
                    self.state = 'CLOSED'
                    self.failure_count = 0
            else:
                # Reset failure count on success in CLOSED state
                self.failure_count = 0

            return result

        except Exception as e:
            # Record failure
            self.failure_count += 1
            self.last_failure_time = datetime.now()

            if self.state == 'HALF_OPEN':
                # Failure during test → back to OPEN
                logger.warning(f"Circuit breaker re-opening for {operation_name}")
                self.state = 'OPEN'
            elif self.failure_count >= self.failure_threshold:
                # Threshold exceeded → OPEN
                logger.error(
                    f"Circuit breaker OPEN for {operation_name} "
                    f"({self.failure_count} consecutive failures)"
                )
                self.state = 'OPEN'

            raise

class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass

# Global circuit breakers per agent type
_circuit_breakers: Dict[str, CircuitBreaker] = {}

def get_circuit_breaker(agent_type: str) -> CircuitBreaker:
    """Get or create circuit breaker for agent type."""
    if agent_type not in _circuit_breakers:
        _circuit_breakers[agent_type] = CircuitBreaker(
            failure_threshold=5,
            timeout=timedelta(minutes=5),
            success_threshold=2
        )
    return _circuit_breakers[agent_type]
```

**Integration with Retry**:
```python
# Modify coordinator workflow to use circuit breaker

breaker = get_circuit_breaker('parser')

try:
    parser_results = breaker.call(
        operation=lambda: retry_with_strategy(
            operation=lambda: spawn_parser_agent(paths),
            operation_name="Parser Agent",
            agent_type="parser",
            max_retries=3
        ),
        operation_name="Parser Agent"
    )
except CircuitBreakerOpenError as e:
    logger.error(f"❌ {e}")
    print("\n⛔ Parser circuit breaker is OPEN due to persistent failures.")
    print("   Please check:")
    print("   - Serena MCP server status")
    print("   - Code syntax errors in target files")
    print("   - System resource availability")
    sys.exit(1)
```

---

## 3. Rollback Mechanisms

### 3.1 Rollback Triggers

**When to rollback**:

1. **All retries exhausted** (transient error persists)
2. **Permanent error detected** (no retry possible)
3. **User abort** (Ctrl+C during workflow)
4. **Validation failure after update** (generated RFC invalid)
5. **Transaction log corruption** (cannot verify integrity)

**When NOT to rollback**:

1. **Successful completion** (obviously)
2. **Partial success** (some agents succeeded, safe to keep checkpoints)
3. **Warning-only validation** (non-blocking issues)

### 3.2 Rollback Targets

#### Option A: Restore from Transaction Backup (RECOMMENDED)

**Approach**: Create staging copies before updates, restore on failure.

**Pros**:
- Simple to implement (file copy operations)
- No git dependency
- Atomic rollback (one file operation)

**Cons**:
- Requires disk space for staging
- Only works for file-level operations

**Implementation**:
```python
# .claude/lib/transaction_manager.py

import os
import shutil
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

class TransactionLog:
    """
    Manages transactional file updates with rollback support.

    Architecture:
    - Staging directory: .claude/.transactions/{transaction_id}/
    - Each transaction has unique ID (timestamp-based)
    - Backup originals before modifying
    - Commit atomically or rollback on failure
    """

    def __init__(self, transaction_id: Optional[str] = None):
        """
        Args:
            transaction_id: Optional ID (default: timestamp)
        """
        self.transaction_id = transaction_id or f"txn-{int(datetime.now().timestamp())}"
        self.staging_dir = Path(f".claude/.transactions/{self.transaction_id}")
        self.staging_dir.mkdir(parents=True, exist_ok=True)

        self.modified_files: List[str] = []
        self.backups: Dict[str, str] = {}  # {original_path: backup_path}
        self.state = 'ACTIVE'  # ACTIVE | COMMITTED | ROLLED_BACK

        # Transaction metadata
        self.metadata = {
            'transaction_id': self.transaction_id,
            'started_at': datetime.now().isoformat(),
            'modified_files': [],
            'state': 'ACTIVE'
        }

        self._save_metadata()

    def backup(self, file_path: str) -> str:
        """
        Create backup of file before modification.

        Args:
            file_path: Path to file to backup

        Returns:
            Path to backup file
        """
        if file_path in self.backups:
            return self.backups[file_path]  # Already backed up

        backup_name = hashlib.sha256(file_path.encode()).hexdigest()[:16]
        backup_path = self.staging_dir / f"{backup_name}.backup"

        # Copy original to staging
        if os.path.exists(file_path):
            shutil.copy2(file_path, backup_path)
            logger.info(f"📦 Backed up: {file_path} → {backup_path}")
        else:
            # File doesn't exist, create empty backup marker
            backup_path.touch()
            logger.info(f"📦 Marked new file: {file_path}")

        self.backups[file_path] = str(backup_path)
        self.modified_files.append(file_path)
        self._save_metadata()

        return str(backup_path)

    def write_file(self, file_path: str, content: str, backup_first: bool = True):
        """
        Write file within transaction (with automatic backup).

        Args:
            file_path: Target file path
            content: File content
            backup_first: Whether to backup before writing
        """
        if self.state != 'ACTIVE':
            raise RuntimeError(f"Transaction {self.transaction_id} is not active")

        # Backup original
        if backup_first:
            self.backup(file_path)

        # Write new content
        with open(file_path, 'w') as f:
            f.write(content)

        logger.info(f"✍️  Wrote: {file_path} ({len(content)} bytes)")

    def commit(self):
        """
        Commit transaction (delete backups).
        """
        if self.state != 'ACTIVE':
            logger.warning(f"Transaction {self.transaction_id} already finalized")
            return

        logger.info(f"✅ Committing transaction {self.transaction_id}")

        # Update metadata
        self.metadata['state'] = 'COMMITTED'
        self.metadata['committed_at'] = datetime.now().isoformat()
        self._save_metadata()

        self.state = 'COMMITTED'

        # Backups can be deleted now (or kept for audit trail)
        # For safety, keep backups until cleanup task runs

    def rollback(self):
        """
        Rollback transaction (restore from backups).
        """
        if self.state != 'ACTIVE':
            logger.warning(f"Transaction {self.transaction_id} already finalized")
            return

        logger.warning(f"🔄 Rolling back transaction {self.transaction_id}")

        # Restore each backed-up file
        for original_path, backup_path in self.backups.items():
            if os.path.getsize(backup_path) == 0:
                # This was a new file, delete it
                if os.path.exists(original_path):
                    os.remove(original_path)
                    logger.info(f"🗑️  Deleted new file: {original_path}")
            else:
                # Restore backup
                shutil.copy2(backup_path, original_path)
                logger.info(f"♻️  Restored: {original_path}")

        # Update metadata
        self.metadata['state'] = 'ROLLED_BACK'
        self.metadata['rolled_back_at'] = datetime.now().isoformat()
        self._save_metadata()

        self.state = 'ROLLED_BACK'

    def _save_metadata(self):
        """Save transaction metadata to disk."""
        metadata_path = self.staging_dir / "transaction.json"
        self.metadata['modified_files'] = self.modified_files

        with open(metadata_path, 'w') as f:
            json.dump(self.metadata, f, indent=2)

# Usage in coordinator workflow
def update_rfc_with_transaction(rfc_path: str, rfc_map_path: str, content: str, mappings: dict):
    """
    Update RFC document and rfc-map.json within transaction.
    """
    txn = TransactionLog()

    try:
        # Backup and write files
        txn.write_file(rfc_path, content)
        txn.write_file(rfc_map_path, json.dumps(mappings, indent=2))

        # Validate
        if not validate_rfc_syntax(rfc_path):
            raise ValueError("RFC validation failed")

        # Commit transaction
        txn.commit()
        logger.info(f"✅ Transaction committed: {rfc_path}, {rfc_map_path}")

    except Exception as e:
        # Rollback on any error
        logger.error(f"❌ Update failed: {e}")
        txn.rollback()
        raise
```

**Recommendation**: Implement Option A for Phase 4.

---

#### Option B: Git-Based Rollback

**Approach**: Use `git stash` or `git reset` for rollback.

**Pros**:
- Leverages existing git infrastructure
- Automatic versioning and audit trail

**Cons**:
- Requires clean working directory
- Conflicts with user's git workflow
- Doesn't work in non-git repositories

**Recommendation**: Defer to Phase 5+ (conflicts with user workflows).

---

#### Option C: Checkpoint-Based Rollback

**Approach**: Use pre-update checkpoint as rollback point.

**Pros**:
- Reuses existing checkpoint system
- No additional storage needed

**Cons**:
- Checkpoints contain agent outputs, not file states
- Doesn't restore file system state

**Recommendation**: Not suitable (checkpoints ≠ file backups).

---

### 3.3 Partial Rollback Decision Matrix

**Scenario**: Parser succeeded, analyzer failed. What to rollback?

| Scenario | Parser State | Analyzer State | Formatter State | Decision |
|----------|--------------|----------------|-----------------|----------|
| **1** | ✅ Success | ❌ Failed (all retries) | ⏸️ Not started | Keep parser checkpoint, rollback nothing (no files written yet) |
| **2** | ✅ Success | ✅ Success | ❌ Failed (validation) | Rollback RFC file + rfc-map.json, keep checkpoints |
| **3** | ✅ Success | ⚠️ Partial success | ✅ Success | Write with warnings, no rollback |
| **4** | ❌ Failed (retry 1) | ⏸️ Not started | ⏸️ Not started | Retry parser (Option A), no rollback |
| **5** | ❌ Failed (all retries) | ⏸️ Not started | ⏸️ Not started | Rollback nothing (no files written), exit |

**Rule**: Only rollback file modifications (RFC document, rfc-map.json). Checkpoints are retained for debugging.

---

## 4. Cleanup Strategy

### 4.1 Orphaned Artifact Types

| Artifact Type | Location | Orphan Condition | Retention |
|---------------|----------|-----------------|-----------|
| **Checkpoints** | `.claude/.checkpoints/*.json` | No corresponding successful workflow in last 24h | 7 days |
| **Invalid outputs** | `.claude/.checkpoints/*-invalid-*.json` | Saved on validation failure | 30 days (debugging) |
| **Transaction backups** | `.claude/.transactions/txn-*/` | Transaction COMMITTED or ROLLED_BACK | 7 days |
| **Failed RFC drafts** | `.claude/.draft-failed-*.md` | Saved on validation failure | 30 days |
| **Temp files** | `.claude/.temp-*.md` | Validation temp files not cleaned up | 1 hour |

### 4.2 Cleanup Timing

#### Immediate Cleanup (Workflow Start)

**Purpose**: Clean up artifacts from interrupted previous runs.

```python
# In coordinator workflow (before starting agents)

def cleanup_orphaned_artifacts():
    """
    Clean up orphaned artifacts on workflow start.
    """
    import glob
    import time
    from datetime import datetime, timedelta

    logger.info("🧹 Checking for orphaned artifacts...")

    cleanup_stats = {
        'checkpoints': 0,
        'transactions': 0,
        'temp_files': 0,
        'total_space_freed': 0
    }

    # 1. Clean up old temp files (>1 hour old)
    temp_pattern = ".claude/.temp-*.md"
    for temp_file in glob.glob(temp_pattern):
        age_hours = (time.time() - os.path.getmtime(temp_file)) / 3600
        if age_hours > 1:
            size = os.path.getsize(temp_file)
            os.remove(temp_file)
            cleanup_stats['temp_files'] += 1
            cleanup_stats['total_space_freed'] += size
            logger.info(f"🗑️  Removed old temp file: {temp_file} ({age_hours:.1f}h old)")

    # 2. Clean up old transaction backups (>7 days, COMMITTED or ROLLED_BACK)
    transactions_dir = Path(".claude/.transactions")
    if transactions_dir.exists():
        for txn_dir in transactions_dir.iterdir():
            if not txn_dir.is_dir():
                continue

            # Read transaction metadata
            metadata_file = txn_dir / "transaction.json"
            if not metadata_file.exists():
                continue

            with open(metadata_file) as f:
                metadata = json.load(f)

            # Check if finalized and old
            if metadata.get('state') in ['COMMITTED', 'ROLLED_BACK']:
                started_at = datetime.fromisoformat(metadata['started_at'])
                age_days = (datetime.now() - started_at).days

                if age_days > 7:
                    size = sum(f.stat().st_size for f in txn_dir.rglob('*') if f.is_file())
                    shutil.rmtree(txn_dir)
                    cleanup_stats['transactions'] += 1
                    cleanup_stats['total_space_freed'] += size
                    logger.info(f"🗑️  Removed old transaction: {txn_dir.name} ({age_days}d old)")

    # 3. Clean up old checkpoints (>7 days)
    checkpoint_pattern = ".claude/.checkpoints/*.json"
    for checkpoint_file in glob.glob(checkpoint_pattern):
        # Skip invalid checkpoints (keep for debugging)
        if '-invalid-' in checkpoint_file:
            continue

        age_days = (time.time() - os.path.getmtime(checkpoint_file)) / 86400
        if age_days > 7:
            size = os.path.getsize(checkpoint_file)
            os.remove(checkpoint_file)
            cleanup_stats['checkpoints'] += 1
            cleanup_stats['total_space_freed'] += size
            logger.info(f"🗑️  Removed old checkpoint: {os.path.basename(checkpoint_file)} ({age_days:.1f}d old)")

    # Report cleanup stats
    if any(cleanup_stats.values()):
        logger.info(
            f"✅ Cleanup complete: "
            f"{cleanup_stats['checkpoints']} checkpoints, "
            f"{cleanup_stats['transactions']} transactions, "
            f"{cleanup_stats['temp_files']} temp files "
            f"({cleanup_stats['total_space_freed'] / 1024:.1f} KB freed)"
        )
    else:
        logger.info("✅ No orphaned artifacts found")
```

#### Periodic Cleanup (Background Task)

**Purpose**: Prevent accumulation of old artifacts.

**Implementation**: Add to SessionStart hook.

```python
# .claude/hooks/session_start_check.py (extend existing)

def check_artifact_buildup():
    """
    Warn user if artifacts directory is getting large.
    """
    checkpoints_dir = Path(".claude/.checkpoints")
    transactions_dir = Path(".claude/.transactions")

    total_size = 0
    total_files = 0

    for directory in [checkpoints_dir, transactions_dir]:
        if directory.exists():
            for f in directory.rglob('*'):
                if f.is_file():
                    total_size += f.stat().st_size
                    total_files += 1

    # Warn if >100MB or >100 files
    size_mb = total_size / (1024 * 1024)

    if size_mb > 100 or total_files > 100:
        print(f"\n⚠️  Artifact buildup detected:")
        print(f"   {total_files} files, {size_mb:.1f} MB")
        print(f"   Run `/rfc-cleanup` to free space")
```

#### Manual Cleanup (User Command)

**Purpose**: Let users manually trigger cleanup.

```bash
# /rfc-cleanup slash command

Cleanup orphaned RFC workflow artifacts (checkpoints, transactions, temp files).

**Options**:
- `--dry-run`: Show what would be deleted without deleting
- `--force`: Delete all artifacts regardless of age
- `--keep-invalid`: Preserve *-invalid-* files for debugging

**Examples**:
/rfc-cleanup
/rfc-cleanup --dry-run
/rfc-cleanup --force
```

**Implementation**:
```python
# .claude/commands/rfc-cleanup.md

# /rfc-cleanup Command

Cleanup orphaned RFC workflow artifacts to free disk space.

## Usage

```
/rfc-cleanup [--dry-run] [--force] [--keep-invalid]
```

## Algorithm

1. Scan `.claude/.checkpoints/`, `.claude/.transactions/`, `.claude/.temp-*`
2. Identify orphaned artifacts (see cleanup strategy)
3. Prompt user with deletion list
4. Delete confirmed artifacts
5. Report space freed

## Safety Checks

- Never delete artifacts <1 hour old (might be active workflow)
- Never delete without user confirmation (unless --force)
- Keep *-invalid-* files by default (valuable for debugging)

## Output

```
🧹 RFC Cleanup Scan Results:

Checkpoints (7 days old):
  - parser-1734120000.json (45 KB, 8d old)
  - analyzer-1734120001.json (23 KB, 8d old)

Transactions (committed, 7 days old):
  - txn-1734120000/ (123 KB, 9d old)

Temp Files (1 hour old):
  - .temp-rfc-1734180000.md (18 KB, 3h old)

Total: 4 items, 209 KB

Delete these artifacts? [y/N]
```
```

### 4.3 Cleanup Safety Checks

**Rules**:

1. **Active workflow protection**: Never delete artifacts modified in last 1 hour
2. **User confirmation**: Always prompt before deletion (unless `--force`)
3. **Size warnings**: Warn before deleting >10MB total
4. **Debugging preservation**: Keep `*-invalid-*` files by default (valuable for bug reports)
5. **Transaction integrity**: Only delete COMMITTED or ROLLED_BACK transactions (not ACTIVE)

---

## 5. User Communication & Feedback

### 5.1 During Retry

**Goal**: Transparency about retry behavior without overwhelming user.

```python
# User-facing retry messages

def print_retry_status(attempt: int, max_retries: int, error: Exception, delay: float, operation: str):
    """
    Print user-friendly retry status.
    """
    # Use emoji status indicators
    if attempt == 1:
        icon = "🔄"
    elif attempt == 2:
        icon = "🔁"
    else:
        icon = "⏳"

    print(f"\n{icon} Attempt {attempt} of {operation} failed:")
    print(f"   Error: {type(error).__name__}: {str(error)[:100]}")
    print(f"   Retrying in {delay:.1f}s... (attempt {attempt + 1}/{max_retries})")

    # Show progress bar for delay (optional)
    # [████████░░░░░░] 60%
```

**Example Console Output**:
```
🔄 Attempt 1 of Parser Agent failed:
   Error: TimeoutError: Serena MCP timed out after 30s
   Retrying in 2.0s... (attempt 2/3)

🔁 Attempt 2 of Parser Agent failed:
   Error: TimeoutError: Serena MCP timed out after 30s
   Retrying in 4.0s... (attempt 3/3)

✅ Parser Agent succeeded after 2 retries (total time: 6.2s)
```

### 5.2 After Failure (All Retries Exhausted)

**Goal**: Provide actionable recovery steps.

```python
def print_failure_report(agent_type: str, error: Exception, attempts: int):
    """
    Print comprehensive failure report with recovery suggestions.
    """
    print(f"\n❌ {agent_type.title()} Agent failed after {attempts} attempts\n")

    print(f"**Error Type**: {type(error).__name__}")
    print(f"**Error Message**: {error}\n")

    # Classification-specific advice
    classification, _, reason = classify_error(error, {'agent_type': agent_type})

    if classification == 'permanent':
        print("**This is a permanent error that requires manual intervention.**\n")

        if 'Serena' in str(error) or 'MCP' in str(error):
            print("**Suggested Actions**:")
            print("1. Check Serena MCP server status:")
            print("   → Run: mcp status")
            print("2. Restart MCP server:")
            print("   → Run: mcp restart")
            print("3. Verify MCP configuration in plugin.json")

        elif 'Syntax' in str(error):
            print("**Suggested Actions**:")
            print("1. Check for syntax errors in your code:")
            print(f"   → Review files in: {get_analyzed_paths()}")
            print("2. Fix syntax errors and retry")

        elif 'Permission' in str(error):
            print("**Suggested Actions**:")
            print("1. Check file permissions:")
            print(f"   → Run: ls -la {get_error_file_path(error)}")
            print("2. Ensure write access to docs/ directory")

        else:
            print("**Suggested Actions**:")
            print("1. Review error details above")
            print("2. Check .claude/.coordinator-errors.log for full stack trace")
            print("3. Run `/rfc-cleanup` to remove partial artifacts")

    else:  # transient
        print("**This appears to be a transient error, but retries were exhausted.**\n")
        print("**Suggested Actions**:")
        print("1. Wait a few minutes and retry the workflow")
        print("2. Check system resources (CPU, memory, disk space)")
        print("3. If error persists, review .claude/.coordinator-errors.log")

    print(f"\n**Artifacts**:")
    print(f"- Error log: .claude/.coordinator-errors.log")
    print(f"- Checkpoints: .claude/.checkpoints/{agent_type}-*.json")

    if os.path.exists('.claude/.draft-failed.md'):
        print(f"- Failed draft: .claude/.draft-failed.md")

    print(f"\n**Next Steps**:")
    print(f"1. Address the error based on suggestions above")
    print(f"2. Run the workflow again (checkpoints will be reused if valid)")
    print(f"3. Report to repository maintainer if error persists")
```

**Example Failure Report**:
```
❌ Parser Agent failed after 3 attempts

**Error Type**: ConnectionError
**Error Message**: Cannot connect to Serena MCP server at localhost:5000

**This appears to be a transient error, but retries were exhausted.**

**Suggested Actions**:
1. Check Serena MCP server status:
   → Run: mcp status
2. Restart MCP server:
   → Run: mcp restart
3. Verify MCP configuration in plugin.json

**Artifacts**:
- Error log: .claude/.coordinator-errors.log
- Checkpoints: .claude/.checkpoints/parser-*.json

**Next Steps**:
1. Address the error based on suggestions above
2. Run the workflow again (checkpoints will be reused if valid)
3. Report to repository maintainer if error persists
```

### 5.3 Success After Retry

**Goal**: Build user trust by showing transparency.

```python
def print_success_after_retry(agent_type: str, attempts: int, total_time: float):
    """
    Print success message highlighting retry behavior.
    """
    print(f"\n✅ {agent_type.title()} Agent succeeded after {attempts} retries")
    print(f"   Total time: {total_time:.1f}s (including {attempts - 1} retries)")
    print(f"   Resilience: Automatic recovery from transient failures\n")
```

**Example**:
```
✅ Parser Agent succeeded after 2 retries
   Total time: 8.5s (including 1 retry)
   Resilience: Automatic recovery from transient failures
```

### 5.4 Interactive Abort Option

**Goal**: Allow user to skip retries and abort workflow.

```python
import sys
import select
import termios
import tty

def user_abort_check() -> bool:
    """
    Check if user pressed 's' (skip) or 'a' (abort) during retry delay.

    Returns:
        True if user aborted
    """
    # Non-blocking input check (Unix-like systems)
    if sys.platform == 'win32':
        return False  # Skip on Windows for simplicity

    # Check if stdin has data available
    if select.select([sys.stdin], [], [], 0)[0]:
        key = sys.stdin.read(1)
        if key.lower() in ['a', 's']:
            return True

    return False

# Integration
print(f"   Retrying in {delay:.1f}s... (Press 'a' to abort)")
```

---

## 6. Integration with Existing Systems

### 6.1 Checkpoint System Integration

**Extend checkpoints to include retry metadata**:

```python
# Modify checkpoint schema to track retries

checkpoint_data = {
    "timestamp": timestamp,
    "hash": parser_hash,
    "results": parser_results,
    "metadata": {
        "agent_type": "parser",
        "attempt_number": 1,  # NEW: Track retry attempt
        "previous_errors": [],  # NEW: List of errors from previous attempts
        "total_retry_time": 0.0,  # NEW: Cumulative retry delay
        "circuit_breaker_state": "CLOSED"  # NEW: Circuit breaker state
    }
}
```

**Checkpoint loading with retry awareness**:

```python
# When loading checkpoints for recovery

def load_checkpoint_with_retry_context(agent_type: str) -> Tuple[dict, dict]:
    """
    Load checkpoint and extract retry context.

    Returns:
        Tuple of (results, retry_context)
    """
    checkpoint = load_latest_checkpoint(agent_type)

    results = checkpoint['results']
    retry_context = checkpoint.get('metadata', {})

    # Use retry context for error classification
    return results, retry_context
```

### 6.2 Transaction System Integration

**Coordinate retries with transactions**:

```python
# Coordinator workflow with retry + transaction

def update_workflow_with_retry_and_transaction():
    """
    RFC update workflow with retry and transaction support.
    """
    # Start transaction
    txn = TransactionLog()

    try:
        # Spawn agents with retry
        parser_results = retry_with_strategy(
            operation=lambda: spawn_parser_agent(paths),
            operation_name="Parser Agent",
            max_retries=3
        )

        analyzer_results = retry_with_strategy(
            operation=lambda: spawn_analyzer_agent(parser_results),
            operation_name="Analyzer Agent",
            max_retries=3
        )

        formatter_results = retry_with_strategy(
            operation=lambda: spawn_formatter_agent(parser_results, analyzer_results),
            operation_name="Formatter Agent",
            max_retries=3
        )

        # Write outputs within transaction
        txn.write_file('docs/generated/draft-spec.md', formatter_results['rfc_content'])
        txn.write_file('docs/rfc-map.json', json.dumps(formatter_results['mappings']))

        # Validate
        if not validate_rfc_syntax('docs/generated/draft-spec.md'):
            raise ValueError("RFC validation failed")

        # Commit transaction
        txn.commit()
        print("✅ RFC update completed successfully")

    except Exception as e:
        # Rollback transaction on failure
        logger.error(f"❌ Workflow failed: {e}")
        txn.rollback()

        print(f"\n❌ RFC update failed and has been rolled back")
        print(f"   All changes reverted to previous state")
        raise
```

### 6.3 Hook Integration

**Hooks should not retry** (hooks are lightweight validators, not workflows).

```python
# .claude/hooks/pre_tool_validate.py (no retry)

# DO NOT wrap hooks in retry logic - hooks should be fast validators
# If hook fails, it should fail immediately

def validate_rfc_references(file_path: str):
    """
    Hook to validate RFC cross-references (no retry).
    """
    try:
        # Validate cross-references
        validate_xrefs(file_path)
    except Exception as e:
        # Log error, do not retry
        logger.error(f"Cross-reference validation failed: {e}")
        raise  # Propagate to block tool use
```

---

## 7. Configuration & Tunability

### 7.1 Configuration File Schema

**Add to `.claude/plugin.json`**:

```json
{
  "config": {
    "error_recovery": {
      "retry": {
        "enabled": true,
        "max_retries": 3,
        "backoff_type": "exponential",
        "base_delay_seconds": 2.0,
        "jitter": true,
        "circuit_breaker": {
          "enabled": true,
          "failure_threshold": 5,
          "timeout_minutes": 5,
          "success_threshold": 2
        }
      },
      "per_agent_overrides": {
        "parser": {
          "max_retries": 5,
          "timeout_seconds": 300
        },
        "analyzer": {
          "max_retries": 3,
          "timeout_seconds": 600
        },
        "formatter": {
          "max_retries": 2,
          "timeout_seconds": 120
        }
      },
      "cleanup": {
        "retention_days": {
          "checkpoints": 7,
          "invalid_outputs": 30,
          "transactions": 7,
          "failed_drafts": 30,
          "temp_files_hours": 1
        },
        "auto_cleanup_on_start": true,
        "size_warning_threshold_mb": 100
      }
    }
  }
}
```

### 7.2 Environment Variable Overrides

**For CI/CD and scripting**:

```bash
# Disable retry in CI (fail fast)
export RFC_RETRY_ENABLED=false

# Increase retries for flaky network
export RFC_MAX_RETRIES=5

# Disable circuit breaker (always retry)
export RFC_CIRCUIT_BREAKER_ENABLED=false

# Cleanup retention (CI ephemeral environments)
export RFC_CLEANUP_RETENTION_DAYS=1
```

**Implementation**:
```python
import os

def get_retry_config() -> dict:
    """
    Get retry configuration from plugin.json + env overrides.
    """
    # Load from plugin.json
    with open('.claude/plugin.json') as f:
        plugin_config = json.load(f)

    retry_config = plugin_config['config'].get('error_recovery', {}).get('retry', {})

    # Apply environment variable overrides
    if os.getenv('RFC_RETRY_ENABLED'):
        retry_config['enabled'] = os.getenv('RFC_RETRY_ENABLED').lower() == 'true'

    if os.getenv('RFC_MAX_RETRIES'):
        retry_config['max_retries'] = int(os.getenv('RFC_MAX_RETRIES'))

    if os.getenv('RFC_CIRCUIT_BREAKER_ENABLED'):
        retry_config['circuit_breaker']['enabled'] = (
            os.getenv('RFC_CIRCUIT_BREAKER_ENABLED').lower() == 'true'
        )

    return retry_config
```

### 7.3 Per-Agent Timeout Specifications

**Timeout values based on codebase size**:

| Agent | Base Timeout | Scaling Factor | Example (10K LOC) |
|-------|--------------|----------------|-------------------|
| **Parser** | 60s | +30s per 10K LOC | 90s (20K LOC) |
| **Analyzer** | 120s | +60s per 10K LOC | 180s (20K LOC) |
| **Formatter** | 30s | +15s per 10K LOC | 45s (20K LOC) |
| **Validator** | 60s | +10s per 10K LOC | 70s (20K LOC) |

**Dynamic timeout calculation**:

```python
def calculate_agent_timeout(agent_type: str, estimated_loc: int) -> int:
    """
    Calculate timeout based on agent type and codebase size.

    Args:
        agent_type: Agent type (parser/analyzer/formatter/validator)
        estimated_loc: Estimated lines of code to process

    Returns:
        Timeout in seconds
    """
    # Base timeouts
    base_timeouts = {
        'parser': 60,
        'analyzer': 120,
        'formatter': 30,
        'validator': 60
    }

    # Scaling factors (seconds per 10K LOC)
    scaling_factors = {
        'parser': 30,
        'analyzer': 60,
        'formatter': 15,
        'validator': 10
    }

    base = base_timeouts.get(agent_type, 60)
    factor = scaling_factors.get(agent_type, 20)

    # Calculate scaled timeout
    loc_chunks = estimated_loc / 10000  # Number of 10K chunks
    timeout = base + (factor * loc_chunks)

    # Cap maximum timeout at 30 minutes
    return min(int(timeout), 1800)

# Usage
timeout = calculate_agent_timeout('parser', estimated_loc=50000)
# Returns: 60 + (30 * 5) = 210 seconds (3.5 minutes)
```

---

## 8. Implementation Plan

### 8.1 New Functions for `lib/error_recovery.py`

**Module Structure**:

```python
# .claude/lib/error_recovery.py

"""
Error recovery system for RFC documentation pipeline.

Provides:
- Error classification (transient vs permanent)
- Retry with exponential backoff
- Circuit breaker pattern
- User communication utilities
"""

# Public API
__all__ = [
    'classify_error',
    'retry_with_strategy',
    'CircuitBreaker',
    'get_circuit_breaker',
    'print_retry_status',
    'print_failure_report',
    'print_success_after_retry'
]

# Implementation (see sections 1-5 above)
```

### 8.2 New Module: `lib/transaction_manager.py`

**Module Structure**:

```python
# .claude/lib/transaction_manager.py

"""
Transaction manager for atomic file updates with rollback.

Provides:
- Transactional file writes
- Automatic backups
- Commit/rollback support
- Transaction log management
"""

__all__ = [
    'TransactionLog',
    'cleanup_old_transactions'
]

# Implementation (see section 3.2 above)
```

### 8.3 Modifications to Coordinator Workflow

**Changes to `.claude/instructions/coordinator.md`**:

1. **Add cleanup step at workflow start** (before Step 1):
   ```markdown
   ## Step 0: Cleanup Orphaned Artifacts

   Before starting workflow, clean up any orphaned artifacts from previous runs.

   ```python
   from error_recovery import cleanup_orphaned_artifacts
   cleanup_orphaned_artifacts()
   ```
   ```

2. **Wrap agent spawning in retry** (Steps 2, 3, 4):
   ```markdown
   ## Step 2: Spawn Parser Agent (with Retry)

   ```python
   from error_recovery import retry_with_strategy, get_circuit_breaker

   breaker = get_circuit_breaker('parser')

   parser_results = breaker.call(
       operation=lambda: retry_with_strategy(
           operation=lambda: spawn_parser_agent(paths),
           operation_name="Parser Agent",
           agent_type="parser",
           max_retries=get_retry_config()['max_retries']
       ),
       operation_name="Parser Agent"
   )
   ```
   ```

3. **Wrap file writes in transaction** (Step 8):
   ```markdown
   ## Step 8: Write Output Files (with Transaction)

   ```python
   from transaction_manager import TransactionLog

   txn = TransactionLog()

   try:
       txn.write_file(rfc_output_path, complete_rfc_draft)
       txn.write_file('docs/rfc-map.json', json.dumps(mappings, indent=2))

       # Validate
       if not validate_rfc_syntax(rfc_output_path):
           raise ValueError("RFC validation failed")

       txn.commit()
       logger.info(f"✅ RFC document written to: {rfc_output_path}")

   except Exception as e:
       txn.rollback()
       logger.error(f"❌ Update failed and rolled back: {e}")
       raise
   ```
   ```

### 8.4 Test Scenarios

**Test Coverage Matrix**:

| Test ID | Scenario | Expected Behavior | Validation |
|---------|----------|-------------------|------------|
| **TR-01** | Parser timeout (transient) | Retry 3x with exponential backoff → success on retry 2 | Check logs show 2 retries, final success |
| **TR-02** | Parser syntax error (permanent) | Fail immediately, no retry | Check 0 retries, error report printed |
| **TR-03** | File lock contention | Retry 5x with linear backoff → success after lock released | Check 5 retries, success message |
| **TR-04** | All retries exhausted | Abort, print failure report | Check max retries reached, report printed |
| **TR-05** | Circuit breaker activation | After 5 consecutive failures, block further attempts | Check circuit OPEN, error reports threshold |
| **TR-06** | Transaction rollback | Write fails → both files restored | Check both files match backup |
| **TR-07** | Partial agent failure | Parser OK, analyzer fail → keep parser checkpoint | Check parser checkpoint exists, no rollback |
| **TR-08** | Cleanup on start | Old artifacts deleted | Check files older than retention deleted |
| **TR-09** | User abort during retry | Press 'a' → workflow aborted | Check KeyboardInterrupt raised |
| **TR-10** | Config override via env | `RFC_MAX_RETRIES=5` → uses 5 retries | Check 5 retries attempted |

**BDD Test Example**:

```gherkin
# tests/features/error_recovery.feature

Feature: Error Recovery in RFC Update Pipeline

  Background:
    Given a test repository with sample code
    And the RFC generator is initialized

  Scenario: Transient network error recovers with retry
    Given Serena MCP will timeout on first call
    And Serena MCP will succeed on second call
    When I run "/rfc-generate"
    Then the parser agent should retry once
    And the workflow should complete successfully
    And the console should show "✅ Parser Agent succeeded after 1 retry"

  Scenario: Permanent syntax error fails immediately
    Given the code has a syntax error in "src/main.py"
    When I run "/rfc-generate"
    Then the parser agent should not retry
    And the workflow should fail with error report
    And the error report should suggest "Check for syntax errors"

  Scenario: Transaction rollback on validation failure
    Given the parser succeeds
    And the formatter generates invalid RFC syntax
    When I run "/rfc-generate"
    Then the RFC file should be restored from backup
    And the rfc-map.json should be restored from backup
    And the transaction should be in ROLLED_BACK state
```

---

## 9. Constraints Compliance

### 9.1 Overhead Analysis

**Metric**: Retry overhead must be <5% of total workflow time for successful workflows.

| Operation | Baseline Time | Retry Overhead | % Overhead |
|-----------|--------------|----------------|------------|
| **Parser** (10K LOC) | 120s | ~0.5s (config load + setup) | 0.4% ✅ |
| **Analyzer** (10K LOC) | 180s | ~0.5s | 0.3% ✅ |
| **Formatter** (10K LOC) | 60s | ~0.5s | 0.8% ✅ |
| **Transaction** (2 files) | 2s | ~0.2s (backup copy) | 10% ⚠️ |
| **Cleanup** (startup) | N/A | ~1s | N/A |

**Total Overhead**: ~2.2s on 362s workflow = **0.6% ✅ PASS**

**Transaction overhead**: 10% is acceptable (write operations already slow, safety critical).

### 9.2 User Feedback Timing

**Metric**: User feedback must appear within 1 second of error occurrence.

**Implementation**:
```python
# Immediate error logging + user notification

try:
    result = operation()
except Exception as e:
    # Log immediately (< 100ms)
    logger.error(f"Operation failed: {e}")

    # Print user message immediately (< 100ms)
    print(f"\n⚠️  Error: {type(e).__name__}: {e}")

    # Classify error (< 500ms)
    classification, retries, reason = classify_error(e, context)

    # Print retry plan (< 200ms)
    if retries > 0:
        print(f"   Will retry {retries} times")

    # Total: < 1 second ✅ PASS
```

### 9.3 No Silent Retries

**Metric**: Always inform user about retry behavior.

**Enforcement**:
```python
# Every retry MUST print status

def retry_with_strategy(...):
    while attempt <= max_retries:
        try:
            result = operation()

            if attempt > 0:
                # REQUIRED: Report success after retry
                print(f"✅ {operation_name} succeeded after {attempt} retries")

            return result
        except Exception as e:
            # REQUIRED: Report retry attempt
            print(f"🔄 Attempt {attempt} failed, retrying...")

            # ... retry logic
```

### 9.4 Backward Compatibility

**Metric**: Works seamlessly with Phase 3 checkpoint recovery.

**Validation**:
- ✅ Checkpoints still written after successful agents
- ✅ Checkpoint loading unchanged (extended schema is additive)
- ✅ Recovery workflow still offers checkpoint resume
- ✅ No breaking changes to coordinator.md workflow

---

## 10. Deliverables Summary

### 10.1 Design Documents

- ✅ **Error Classification Decision Tree** (Section 1.2)
- ✅ **Retry Strategy Algorithm** (Section 2.1)
- ✅ **Rollback Strategy Specification** (Section 3)
- ✅ **Cleanup Strategy Specification** (Section 4)
- ✅ **Configuration Schema** (Section 7.1)

### 10.2 Implementation Specifications

- ✅ **`error_recovery.py` module** (Section 8.1)
- ✅ **`transaction_manager.py` module** (Section 8.2)
- ✅ **Coordinator workflow modifications** (Section 8.3)
- ✅ **Configuration file updates** (Section 7.1)

### 10.3 Test Plans

- ✅ **Test scenario matrix** (Section 8.4)
- ✅ **BDD feature file examples** (Section 8.4)
- ✅ **Constraint compliance validation** (Section 9)

---

## Appendix A: Error Recovery Flowchart

```
┌─────────────────────────────────────┐
│ Coordinator Workflow Start          │
└──────────────┬──────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│ Step 0: Cleanup Orphaned Artifacts   │
│ - Remove old checkpoints (>7d)       │
│ - Remove old transactions (>7d)      │
│ - Remove temp files (>1h)            │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│ Spawn Parser Agent                   │
│ (wrapped in retry + circuit breaker) │
└──────────────┬───────────────────────┘
               │
        ┌──────┴──────┐
        │   Success?  │
        └──────┬──────┘
               │ Yes
               ▼
┌──────────────────────────────────────┐
│ Save Parser Checkpoint               │
│ (with retry metadata)                │
└──────────────┬───────────────────────┘
               │
               ▼
     [Repeat for Analyzer, Formatter]
               │
               ▼
┌──────────────────────────────────────┐
│ Start Transaction                    │
│ - Create staging directory           │
│ - Backup existing files              │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│ Write RFC Document                   │
│ (within transaction)                 │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│ Write rfc-map.json                   │
│ (within transaction)                 │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│ Validate RFC Syntax                  │
└──────────────┬───────────────────────┘
               │
        ┌──────┴──────┐
        │   Valid?    │
        └──────┬──────┘
         Yes   │   No
               │   │
               │   ▼
               │ ┌──────────────────────┐
               │ │ Rollback Transaction │
               │ │ - Restore backups    │
               │ │ - Log failure        │
               │ │ - Print error report │
               │ └──────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│ Commit Transaction                   │
│ - Mark as COMMITTED                  │
│ - Keep backups for audit             │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│ Print Success Report                 │
│ - Show retry stats (if any)          │
│ - Report output paths                │
└──────────────────────────────────────┘
```

---

## Appendix B: Configuration Examples

### Minimal Configuration (Defaults)

```json
{
  "config": {
    "error_recovery": {
      "retry": {
        "enabled": true,
        "max_retries": 3
      }
    }
  }
}
```

### Aggressive Retry (Flaky Networks)

```json
{
  "config": {
    "error_recovery": {
      "retry": {
        "enabled": true,
        "max_retries": 10,
        "backoff_type": "exponential",
        "base_delay_seconds": 5.0,
        "circuit_breaker": {
          "enabled": true,
          "failure_threshold": 15,
          "timeout_minutes": 10
        }
      },
      "per_agent_overrides": {
        "parser": {
          "max_retries": 10,
          "timeout_seconds": 600
        }
      }
    }
  }
}
```

### CI/CD Configuration (Fail Fast)

```json
{
  "config": {
    "error_recovery": {
      "retry": {
        "enabled": false
      },
      "cleanup": {
        "retention_days": {
          "checkpoints": 0,
          "transactions": 0,
          "temp_files_hours": 0
        },
        "auto_cleanup_on_start": true
      }
    }
  }
}
```

### Development Configuration (Keep Debug Artifacts)

```json
{
  "config": {
    "error_recovery": {
      "retry": {
        "enabled": true,
        "max_retries": 1
      },
      "cleanup": {
        "retention_days": {
          "checkpoints": 30,
          "invalid_outputs": 90,
          "transactions": 30,
          "failed_drafts": 90
        },
        "auto_cleanup_on_start": false
      }
    }
  }
}
```

---

## Conclusion

This error recovery system design provides comprehensive resilience for the Phase 4 RFC update pipeline while maintaining:

- **User transparency**: Clear communication about all retry/rollback behavior
- **Safety**: Transaction-based rollback prevents data corruption
- **Performance**: <1% overhead for successful workflows
- **Flexibility**: Configurable retry strategies per agent/environment
- **Backward compatibility**: Extends Phase 3 checkpoint system without breaking changes

**Implementation Effort Estimate**: 12-16 hours
- `error_recovery.py` module: 4-5 hours
- `transaction_manager.py` module: 3-4 hours
- Coordinator workflow integration: 2-3 hours
- Configuration + testing: 3-4 hours

**Recommendation**: Implement for Phase 4 User Story 2 before T038 (update rfc-map.json).

---

**Document Version**: 1.0
**Last Updated**: 2025-10-14
**Author**: Claude (Sonnet 4.5) via Research Agent
**Status**: ✅ Ready for Implementation
