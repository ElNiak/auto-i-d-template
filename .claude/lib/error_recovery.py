"""
Error recovery system for RFC documentation pipeline.

Provides:
- Error classification (transient vs permanent)
- Retry with exponential backoff
- Circuit breaker pattern
- Cleanup of orphaned artifacts
- User communication utilities

Integrates with transaction_manager.py for rollback functionality.
"""

import os
import sys
import time
import glob
import json
import shutil
import random
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Tuple, Optional, Callable, Any, Dict

logger = logging.getLogger(__name__)

# Public API
__all__ = [
    'classify_error',
    'retry_with_strategy',
    'CircuitBreaker',
    'get_circuit_breaker',
    'cleanup_orphaned_artifacts',
    'print_retry_status',
    'print_failure_report',
    'print_success_after_retry',
    'CircuitBreakerOpenError'
]


# ============================================================================
# Error Classification
# ============================================================================

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
    context: Dict
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


# ============================================================================
# Retry Strategy
# ============================================================================

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
    start_time = time.time()

    while attempt <= max_retries:
        try:
            if attempt > 0:
                logger.info(f"Retry attempt {attempt}/{max_retries} for {operation_name}")

            # Execute operation
            result = operation()

            # Success
            if attempt > 0:
                total_time = time.time() - start_time
                logger.info(f"✅ {operation_name} succeeded after {attempt} retries")
                print_success_after_retry(operation_name, attempt, total_time)

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

            # Print user-facing retry status
            print_retry_status(attempt, max_retries, e, delay, operation_name)

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


# ============================================================================
# Circuit Breaker
# ============================================================================

class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass


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


# ============================================================================
# Cleanup Functions
# ============================================================================

def cleanup_orphaned_artifacts():
    """
    Clean up orphaned artifacts on workflow start.

    Removes:
    - Old checkpoints (>7 days)
    - Old transaction backups (>7 days, COMMITTED or ROLLED_BACK)
    - Old temp files (>1 hour)
    """
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
        try:
            age_hours = (time.time() - os.path.getmtime(temp_file)) / 3600
            if age_hours > 1:
                size = os.path.getsize(temp_file)
                os.remove(temp_file)
                cleanup_stats['temp_files'] += 1
                cleanup_stats['total_space_freed'] += size
                logger.info(f"🗑️  Removed old temp file: {temp_file} ({age_hours:.1f}h old)")
        except Exception as e:
            logger.warning(f"Failed to remove temp file {temp_file}: {e}")

    # 2. Clean up old transaction backups (>7 days, finalized)
    transactions_dir = Path(".claude/.transactions")
    if transactions_dir.exists():
        for txn_dir in transactions_dir.iterdir():
            if not txn_dir.is_dir():
                continue

            try:
                # Read transaction metadata
                metadata_files = list(txn_dir.glob("*.txn"))
                if not metadata_files:
                    continue

                with open(metadata_files[0]) as f:
                    metadata = json.load(f)

                # Check if finalized and old
                if metadata.get('status') in ['COMMITTED', 'ROLLED_BACK']:
                    started_at = datetime.fromisoformat(metadata['started_at'])
                    age_days = (datetime.now() - started_at).days

                    if age_days > 7:
                        size = sum(f.stat().st_size for f in txn_dir.rglob('*') if f.is_file())
                        shutil.rmtree(txn_dir)
                        cleanup_stats['transactions'] += 1
                        cleanup_stats['total_space_freed'] += size
                        logger.info(f"🗑️  Removed old transaction: {txn_dir.name} ({age_days}d old)")
            except Exception as e:
                logger.warning(f"Failed to process transaction {txn_dir}: {e}")

    # 3. Clean up old checkpoints (>7 days)
    checkpoint_pattern = ".claude/.checkpoints/*.json"
    for checkpoint_file in glob.glob(checkpoint_pattern):
        # Skip invalid checkpoints (keep for debugging)
        if '-invalid-' in checkpoint_file:
            continue

        try:
            age_days = (time.time() - os.path.getmtime(checkpoint_file)) / 86400
            if age_days > 7:
                size = os.path.getsize(checkpoint_file)
                os.remove(checkpoint_file)
                cleanup_stats['checkpoints'] += 1
                cleanup_stats['total_space_freed'] += size
                logger.info(f"🗑️  Removed old checkpoint: {os.path.basename(checkpoint_file)} ({age_days:.1f}d old)")
        except Exception as e:
            logger.warning(f"Failed to remove checkpoint {checkpoint_file}: {e}")

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

    return cleanup_stats


# ============================================================================
# User Communication Functions
# ============================================================================

def print_retry_status(attempt: int, max_retries: int, error: Exception, delay: float, operation: str):
    """
    Print user-friendly retry status.

    Args:
        attempt: Current attempt number
        max_retries: Maximum retry attempts
        error: The exception that occurred
        delay: Delay before next retry (seconds)
        operation: Operation name
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

    if attempt < max_retries:
        print(f"   Retrying in {delay:.1f}s... (attempt {attempt + 1}/{max_retries + 1})")
    else:
        print(f"   Maximum retries ({max_retries}) reached")


def print_success_after_retry(operation_name: str, attempts: int, total_time: float):
    """
    Print success message highlighting retry behavior.

    Args:
        operation_name: Name of the operation
        attempts: Number of attempts taken
        total_time: Total time including retries (seconds)
    """
    print(f"\n✅ {operation_name} succeeded after {attempts} retries")
    print(f"   Total time: {total_time:.1f}s (including {attempts} retries)")
    print(f"   Resilience: Automatic recovery from transient failures\n")


def print_failure_report(agent_type: str, error: Exception, attempts: int):
    """
    Print comprehensive failure report with recovery suggestions.

    Args:
        agent_type: Type of agent that failed
        error: The exception that caused failure
        attempts: Number of attempts made
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
            print("   → Verify MCP is running")
            print("2. Restart MCP server if needed")
            print("3. Verify MCP configuration in plugin.json")

        elif 'Syntax' in str(error):
            print("**Suggested Actions**:")
            print("1. Check for syntax errors in your code")
            print("2. Fix syntax errors and retry")

        elif 'Permission' in str(error):
            print("**Suggested Actions**:")
            print("1. Check file permissions")
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
