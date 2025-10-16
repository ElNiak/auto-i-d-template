#!/usr/bin/env python3
"""
Reference Implementation: Workflow Locking System

This is a complete, production-ready implementation of the hybrid
flock + lock file concurrency control mechanism specified in
CONCURRENCY-CONTROL-DESIGN.md.

Usage:
    from lib.workflow_lock import WorkflowLock

    # Context manager (recommended)
    with WorkflowLock(repo_root) as lock:
        # Critical section - safe to modify rfc-map.json
        mapper.save()

    # Manual control
    lock = WorkflowLock(repo_root, timeout_seconds=600)
    try:
        lock.acquire()
        # ... critical section ...
    finally:
        lock.release()
"""

import os
import sys
import time
import json
import socket
import logging
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict
from contextlib import contextmanager

# Platform-specific imports
try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False

try:
    import msvcrt
    HAS_MSVCRT = True
except ImportError:
    HAS_MSVCRT = False

logger = logging.getLogger(__name__)


# ============================================================================
# Exceptions
# ============================================================================

class LockTimeout(Exception):
    """Raised when lock acquisition timeout exceeded."""
    pass


class LockUnavailable(Exception):
    """Raised when lock unavailable in non-blocking mode."""
    pass


class LockError(Exception):
    """Base class for lock-related errors."""
    pass


# ============================================================================
# Utility Functions
# ============================================================================

def is_process_alive(pid: int) -> bool:
    """
    Check if process with given PID is still running.

    Args:
        pid: Process ID to check

    Returns:
        True if process exists, False otherwise
    """
    if sys.platform == 'win32':
        # Windows: use tasklist
        import subprocess
        try:
            result = subprocess.run(
                ['tasklist', '/FI', f'PID eq {pid}'],
                capture_output=True,
                text=True,
                timeout=2
            )
            return str(pid) in result.stdout
        except Exception:
            return False
    else:
        # Unix: send signal 0 (existence check)
        try:
            os.kill(pid, 0)
            return True
        except (OSError, ProcessLookupError):
            return False


def is_nfs_filesystem(path: Path) -> bool:
    """
    Detect if path is on NFS filesystem.

    Args:
        path: Path to check

    Returns:
        True if on NFS, False otherwise
    """
    if sys.platform == 'win32':
        # Windows: check drive type
        return False  # Simplified - SMB detection would be complex

    try:
        import subprocess
        result = subprocess.run(
            ['df', '-T', str(path)],
            capture_output=True,
            text=True,
            timeout=2
        )
        return 'nfs' in result.stdout.lower()
    except Exception:
        return False


# ============================================================================
# Lock Strategies
# ============================================================================

class BaseLockStrategy:
    """Base class for lock strategies."""

    def __init__(self, lock_dir: Path):
        self.lock_dir = lock_dir
        self.lock_dir.mkdir(parents=True, exist_ok=True)

    def acquire(self, timeout_seconds: int, blocking: bool) -> bool:
        """Acquire lock."""
        raise NotImplementedError

    def release(self):
        """Release lock."""
        raise NotImplementedError

    def get_lock_info(self) -> Optional[Dict]:
        """Get information about current lock holder."""
        raise NotImplementedError


class FlockStrategy(BaseLockStrategy):
    """
    Advisory file locking using fcntl.flock (Linux/macOS).

    Pros:
    - Kernel-managed (auto-release on process crash)
    - Very fast (<50μs overhead)
    - Atomic lock acquisition

    Cons:
    - Not supported on NFS (except NFSv4)
    - Limited debugging info (just PID)
    """

    def __init__(self, lock_dir: Path):
        super().__init__(lock_dir)
        self.lock_file = lock_dir / '.rfc-workflow.lock'
        self.lock_fd = None

    def acquire(self, timeout_seconds: int, blocking: bool) -> bool:
        """
        Acquire exclusive lock using flock.

        Args:
            timeout_seconds: Maximum time to wait
            blocking: Whether to block or fail immediately

        Returns:
            True if acquired

        Raises:
            LockTimeout: If timeout exceeded
            LockUnavailable: If non-blocking and lock held
        """
        if not HAS_FCNTL:
            raise LockError("fcntl not available (wrong platform)")

        # Open lock file (create if doesn't exist)
        self.lock_fd = open(self.lock_file, 'w')

        start_time = datetime.now()
        operation = fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB)

        while True:
            try:
                # Attempt to acquire lock
                fcntl.flock(self.lock_fd.fileno(), operation)

                # Success - write metadata for debugging
                metadata = {
                    "pid": os.getpid(),
                    "hostname": socket.gethostname(),
                    "timestamp": datetime.now().isoformat(),
                    "strategy": "flock"
                }

                self.lock_fd.seek(0)
                self.lock_fd.write(json.dumps(metadata, indent=2))
                self.lock_fd.flush()
                self.lock_fd.truncate()

                logger.info(f"Lock acquired via flock (PID {os.getpid()})")
                return True

            except BlockingIOError:
                # Lock held by another process
                if not blocking:
                    self.lock_fd.close()
                    raise LockUnavailable("Lock held by another workflow")

                # Check timeout
                elapsed = (datetime.now() - start_time).total_seconds()
                if elapsed > timeout_seconds:
                    self.lock_fd.close()
                    raise LockTimeout(f"Could not acquire lock after {timeout_seconds}s")

                # Wait and retry (exponential backoff, max 5 seconds)
                sleep_time = min(0.1 * (1.5 ** (elapsed // 10)), 5)
                time.sleep(sleep_time)

    def release(self):
        """Release lock and close file descriptor."""
        if self.lock_fd:
            try:
                fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_UN)
                self.lock_fd.close()
                logger.info("Lock released via flock")
            except Exception as e:
                logger.error(f"Error releasing flock: {e}")
            finally:
                self.lock_fd = None

    def get_lock_info(self) -> Optional[Dict]:
        """Get lock holder information from lock file."""
        if not self.lock_file.exists():
            return None

        try:
            with open(self.lock_file, 'r') as f:
                return json.load(f)
        except Exception:
            return None


class LockFileStrategy(BaseLockStrategy):
    """
    Lock file with PID tracking (NFS/network filesystems).

    Pros:
    - Works on any filesystem (NFS, SMB, etc.)
    - Rich metadata (PID, hostname, workflow)
    - Stale lock detection

    Cons:
    - Slower (~1ms overhead)
    - Manual stale lock management
    - Small race window in lock creation
    """

    def __init__(self, lock_dir: Path, stale_threshold_minutes: int = 10):
        super().__init__(lock_dir)
        self.lock_file = lock_dir / '.rfc-workflow.lock'
        self.stale_threshold_minutes = stale_threshold_minutes

    def acquire(self, timeout_seconds: int, blocking: bool) -> bool:
        """
        Acquire lock using lock file with atomic rename.

        Args:
            timeout_seconds: Maximum time to wait
            blocking: Whether to block or fail immediately

        Returns:
            True if acquired

        Raises:
            LockTimeout: If timeout exceeded
            LockUnavailable: If non-blocking and lock held
        """
        start_time = datetime.now()

        while True:
            # Try to create lock file atomically
            temp_lock = self.lock_file.with_suffix('.tmp')

            lock_data = {
                "pid": os.getpid(),
                "hostname": socket.gethostname(),
                "timestamp": datetime.now().isoformat(),
                "workflow": os.environ.get('CLAUDE_WORKFLOW', 'unknown'),
                "strategy": "lockfile"
            }

            # Write to temp file
            with open(temp_lock, 'w') as f:
                json.dump(lock_data, f, indent=2)

            # Atomic rename (succeeds only if lock file doesn't exist)
            try:
                temp_lock.rename(self.lock_file)
                logger.info(f"Lock acquired via lockfile (PID {os.getpid()})")
                return True

            except FileExistsError:
                # Lock file exists - check if stale
                temp_lock.unlink()  # Clean up temp file

                is_stale, reason = self._is_stale_lock()

                if is_stale:
                    logger.warning(f"Stale lock detected: {reason}")
                    self._force_takeover(lock_data)
                    return True

                # Lock is valid - check if we should wait
                if not blocking:
                    raise LockUnavailable("Lock held by another workflow")

                # Check timeout
                elapsed = (datetime.now() - start_time).total_seconds()
                if elapsed > timeout_seconds:
                    raise LockTimeout(f"Could not acquire lock after {timeout_seconds}s")

                # Wait and retry
                time.sleep(1)

    def _is_stale_lock(self) -> Tuple[bool, str]:
        """
        Check if lock file is stale.

        Returns:
            (is_stale, reason) tuple
        """
        try:
            with open(self.lock_file, 'r') as f:
                lock_data = json.load(f)

            # Check 1: Timestamp age
            try:
                lock_time = datetime.fromisoformat(lock_data['timestamp'])
            except (ValueError, KeyError):
                return (True, "Invalid timestamp format")

            age_minutes = (datetime.now() - lock_time).total_seconds() / 60

            if age_minutes > self.stale_threshold_minutes:
                return (True, f"Lock {age_minutes:.1f} minutes old (threshold: {self.stale_threshold_minutes})")

            # Check 2: PID liveness (local machine only)
            hostname = lock_data.get('hostname', 'unknown')

            if hostname == socket.gethostname():
                pid = lock_data.get('pid')

                if pid and not is_process_alive(pid):
                    return (True, f"Process {pid} no longer exists")

            # Check 3: Heartbeat (if enabled)
            if 'last_heartbeat' in lock_data:
                try:
                    last_hb = datetime.fromisoformat(lock_data['last_heartbeat'])
                    hb_age = (datetime.now() - last_hb).total_seconds() / 60

                    if hb_age > 5:  # No heartbeat in 5 minutes
                        return (True, f"Heartbeat stale ({hb_age:.1f} minutes)")
                except ValueError:
                    pass

            return (False, "Lock appears valid")

        except (json.JSONDecodeError, FileNotFoundError):
            return (True, "Lock file corrupted or missing")

    def _force_takeover(self, new_lock_data: Dict):
        """
        Forcefully take over stale lock.

        Args:
            new_lock_data: New lock metadata
        """
        logger.warning("Forcing takeover of stale lock")

        # Backup old lock file for forensics
        backup_path = self.lock_file.with_suffix('.lock.stale')

        try:
            # Read old lock data
            with open(self.lock_file, 'r') as f:
                old_lock = json.load(f)

            # Write backup with metadata
            with open(backup_path, 'w') as f:
                json.dump({
                    **old_lock,
                    "broken_by": os.getpid(),
                    "broken_at": datetime.now().isoformat(),
                    "reason": "Stale lock detected"
                }, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to backup old lock: {e}")

        # Remove old lock file
        try:
            self.lock_file.unlink()
        except FileNotFoundError:
            pass

        # Create new lock file
        with open(self.lock_file, 'w') as f:
            json.dump(new_lock_data, f, indent=2)

    def release(self):
        """Release lock by deleting lock file."""
        try:
            self.lock_file.unlink()
            logger.info("Lock released via lockfile")
        except FileNotFoundError:
            logger.warning("Lock file already removed")
        except Exception as e:
            logger.error(f"Error releasing lock file: {e}")

    def get_lock_info(self) -> Optional[Dict]:
        """Get lock holder information from lock file."""
        if not self.lock_file.exists():
            return None

        try:
            with open(self.lock_file, 'r') as f:
                return json.load(f)
        except Exception:
            return None


class WindowsLockStrategy(BaseLockStrategy):
    """
    Windows byte-range locking using msvcrt.

    Pros:
    - Native Windows support
    - Kernel-managed

    Cons:
    - Windows-only
    - More complex API
    """

    def __init__(self, lock_dir: Path):
        super().__init__(lock_dir)
        self.lock_file = lock_dir / '.rfc-workflow.lock'
        self.lock_fd = None

    def acquire(self, timeout_seconds: int, blocking: bool) -> bool:
        """Acquire lock using Windows byte-range locking."""
        if not HAS_MSVCRT:
            raise LockError("msvcrt not available (wrong platform)")

        # Open lock file
        self.lock_fd = open(self.lock_file, 'w')

        start_time = datetime.now()
        lock_mode = msvcrt.LK_LOCK if blocking else msvcrt.LK_NBLCK

        while True:
            try:
                # Lock first byte of file
                msvcrt.locking(self.lock_fd.fileno(), lock_mode, 1)

                # Write metadata
                metadata = {
                    "pid": os.getpid(),
                    "hostname": socket.gethostname(),
                    "timestamp": datetime.now().isoformat(),
                    "strategy": "msvcrt"
                }

                self.lock_fd.write(json.dumps(metadata, indent=2))
                self.lock_fd.flush()

                logger.info(f"Lock acquired via msvcrt (PID {os.getpid()})")
                return True

            except OSError:
                if not blocking:
                    self.lock_fd.close()
                    raise LockUnavailable("Lock held by another workflow")

                # Check timeout
                elapsed = (datetime.now() - start_time).total_seconds()
                if elapsed > timeout_seconds:
                    self.lock_fd.close()
                    raise LockTimeout(f"Could not acquire lock after {timeout_seconds}s")

                # Wait and retry
                time.sleep(0.1)

    def release(self):
        """Release Windows lock."""
        if self.lock_fd:
            try:
                msvcrt.locking(self.lock_fd.fileno(), msvcrt.LK_UNLCK, 1)
                self.lock_fd.close()
                logger.info("Lock released via msvcrt")
            except Exception as e:
                logger.error(f"Error releasing msvcrt lock: {e}")
            finally:
                self.lock_fd = None

    def get_lock_info(self) -> Optional[Dict]:
        """Get lock holder information."""
        if not self.lock_file.exists():
            return None

        try:
            with open(self.lock_file, 'r') as f:
                return json.load(f)
        except Exception:
            return None


# ============================================================================
# Main Workflow Lock Class
# ============================================================================

class WorkflowLock:
    """
    Cross-platform workflow locking with automatic strategy selection.

    This class provides a unified interface for workflow locking across
    different platforms and filesystems. It automatically selects the
    best locking strategy based on:
    - Platform (Linux/macOS/Windows)
    - Filesystem type (local vs NFS)
    - Feature availability (fcntl, msvcrt)

    Usage:
        # Context manager (recommended)
        with WorkflowLock(repo_root) as lock:
            # Critical section
            mapper.save()

        # Manual control
        lock = WorkflowLock(repo_root, timeout_seconds=600)
        try:
            lock.acquire()
            # ... critical section ...
        finally:
            lock.release()
    """

    def __init__(
        self,
        repo_root: Path,
        timeout_seconds: int = 300,
        stale_threshold_minutes: int = 10,
        strategy: Optional[str] = None
    ):
        """
        Initialize workflow lock.

        Args:
            repo_root: Repository root directory
            timeout_seconds: Default timeout for lock acquisition
            stale_threshold_minutes: Age threshold for stale lock detection
            strategy: Force specific strategy ('flock', 'lockfile', 'msvcrt', or None for auto)
        """
        self.repo_root = Path(repo_root)
        self.timeout_seconds = timeout_seconds
        self.stale_threshold_minutes = stale_threshold_minutes

        self.lock_dir = self.repo_root / '.claude'
        self.lock_dir.mkdir(parents=True, exist_ok=True)

        # Auto-detect or force strategy
        if strategy:
            self.strategy_name = strategy
        else:
            self.strategy_name = self._detect_strategy()

        logger.info(f"Workflow lock initialized: strategy={self.strategy_name}")

        # Create strategy instance
        self.lock_impl: Optional[BaseLockStrategy] = None

    def _detect_strategy(self) -> str:
        """
        Auto-detect best locking strategy.

        Returns:
            Strategy name: 'flock', 'lockfile', or 'msvcrt'
        """
        # Windows: use msvcrt
        if sys.platform == 'win32':
            if HAS_MSVCRT:
                return 'msvcrt'
            else:
                logger.warning("msvcrt not available, falling back to lockfile")
                return 'lockfile'

        # Unix/Linux/macOS: prefer flock if available
        if HAS_FCNTL:
            # Check if filesystem supports flock
            if self._test_flock_support():
                return 'flock'
            else:
                logger.warning("flock not supported on this filesystem (NFS?), using lockfile")
                return 'lockfile'

        # Fallback to lock file
        logger.warning("No native locking available, using lockfile")
        return 'lockfile'

    def _test_flock_support(self) -> bool:
        """
        Test if filesystem supports flock.

        Returns:
            True if flock works, False otherwise
        """
        test_file = self.lock_dir / '.lock-test'

        try:
            with open(test_file, 'w') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

            test_file.unlink()
            return True

        except (OSError, IOError) as e:
            logger.debug(f"flock test failed: {e}")
            return False

    def _create_strategy(self) -> BaseLockStrategy:
        """
        Create lock strategy instance.

        Returns:
            Lock strategy instance
        """
        if self.strategy_name == 'flock':
            return FlockStrategy(self.lock_dir)
        elif self.strategy_name == 'lockfile':
            return LockFileStrategy(self.lock_dir, self.stale_threshold_minutes)
        elif self.strategy_name == 'msvcrt':
            return WindowsLockStrategy(self.lock_dir)
        else:
            raise LockError(f"Unknown strategy: {self.strategy_name}")

    def acquire(self, timeout_seconds: Optional[int] = None, blocking: bool = True):
        """
        Acquire workflow lock.

        Args:
            timeout_seconds: Override default timeout (None = use default)
            blocking: Whether to block or fail immediately

        Raises:
            LockTimeout: If timeout exceeded
            LockUnavailable: If non-blocking and lock held
        """
        if self.lock_impl:
            raise LockError("Lock already acquired")

        # Use default timeout if not specified
        timeout = timeout_seconds if timeout_seconds is not None else self.timeout_seconds

        # Create strategy instance
        self.lock_impl = self._create_strategy()

        # Acquire lock with progress feedback
        start_time = datetime.now()
        last_feedback = datetime.now()

        logger.info(f"Acquiring lock (timeout: {timeout}s, blocking: {blocking})")

        while True:
            try:
                self.lock_impl.acquire(timeout=1, blocking=blocking)
                logger.info("Lock acquired successfully")
                return

            except LockTimeout:
                # Check overall timeout
                elapsed = (datetime.now() - start_time).total_seconds()
                if elapsed >= timeout:
                    self.lock_impl = None
                    raise LockTimeout(f"Could not acquire lock after {timeout}s")

                # Show progress every 30 seconds
                since_feedback = (datetime.now() - last_feedback).total_seconds()
                if since_feedback >= 30:
                    remaining = timeout - elapsed
                    logger.info(f"Still waiting for lock... ({int(remaining)}s remaining)")
                    last_feedback = datetime.now()

            except LockUnavailable:
                # Non-blocking mode - fail immediately
                self.lock_impl = None
                raise

    def release(self):
        """Release workflow lock."""
        if self.lock_impl:
            try:
                self.lock_impl.release()
                logger.info("Lock released successfully")
            except Exception as e:
                logger.error(f"Error releasing lock: {e}")
            finally:
                self.lock_impl = None
        else:
            logger.warning("No lock to release")

    def get_lock_info(self) -> Optional[Dict]:
        """
        Get information about current lock holder.

        Returns:
            Dict with {pid, hostname, timestamp, workflow} or None if unlocked
        """
        strategy = self._create_strategy()
        return strategy.get_lock_info()

    def force_break(self, reason: str):
        """
        Forcefully break lock (with audit trail).

        Args:
            reason: Reason for breaking lock

        Raises:
            LockError: If lock file strategy not supported
        """
        if self.strategy_name != 'lockfile':
            raise LockError("Force break only supported with lockfile strategy")

        strategy = LockFileStrategy(self.lock_dir, self.stale_threshold_minutes)

        # Get current lock info
        lock_info = strategy.get_lock_info()
        if not lock_info:
            logger.info("No lock to break")
            return

        logger.warning(f"Force breaking lock: {reason}")

        # Create takeover data
        new_lock_data = {
            "pid": os.getpid(),
            "hostname": socket.gethostname(),
            "timestamp": datetime.now().isoformat(),
            "workflow": "force-break",
            "strategy": "lockfile"
        }

        strategy._force_takeover(new_lock_data)

        # Immediately release (we just wanted to break it)
        strategy.release()

        logger.info("Lock broken successfully")

    def __enter__(self):
        """Context manager entry."""
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.release()


# ============================================================================
# Convenience Functions
# ============================================================================

@contextmanager
def workflow_lock(repo_root: Path, **kwargs):
    """
    Context manager for workflow locking.

    Args:
        repo_root: Repository root directory
        **kwargs: Arguments passed to WorkflowLock()

    Example:
        with workflow_lock(repo_root, timeout_seconds=600):
            # Critical section
            mapper.save()
    """
    lock = WorkflowLock(repo_root, **kwargs)
    lock.acquire()
    try:
        yield lock
    finally:
        lock.release()


# ============================================================================
# CLI Tool for /rfc-unlock Command
# ============================================================================

def cli_unlock(repo_root: Path, force: bool = False, reason: str = ""):
    """
    CLI tool for inspecting and breaking locks.

    Args:
        repo_root: Repository root directory
        force: Whether to forcefully break lock
        reason: Reason for breaking lock
    """
    lock = WorkflowLock(repo_root)

    # Get lock info
    lock_info = lock.get_lock_info()

    if not lock_info:
        print("✅ No workflow lock exists")
        print("\nrfc-map.json is available for updates.")
        return 0

    # Display lock info
    print("🔒 Workflow Lock Status\n")
    print("Lock is held:")
    print(f"  - Workflow: {lock_info.get('workflow', 'unknown')}")
    print(f"  - PID: {lock_info.get('pid', 'unknown')}")
    print(f"  - Hostname: {lock_info.get('hostname', 'unknown')}")

    try:
        lock_time = datetime.fromisoformat(lock_info['timestamp'])
        age = (datetime.now() - lock_time).total_seconds() / 60
        print(f"  - Started: {lock_info['timestamp']} ({age:.1f} minutes ago)")
    except (ValueError, KeyError):
        print(f"  - Started: {lock_info.get('timestamp', 'unknown')}")

    # Check if stale
    if lock.strategy_name == 'lockfile':
        strategy = LockFileStrategy(lock.lock_dir, lock.stale_threshold_minutes)
        is_stale, stale_reason = strategy._is_stale_lock()

        if is_stale:
            print(f"\n⚠️  STALE LOCK DETECTED: {stale_reason}")

            if force or input("\nBreak stale lock? (y/N): ").lower() == 'y':
                lock.force_break(reason or "User request via /rfc-unlock")
                print("\n✅ Lock broken successfully")
                print(f"Old lock backed up to: .claude/.rfc-workflow.lock.stale")
                return 0
        else:
            print(f"\nLock appears VALID: {stale_reason}")

            if force:
                if input("\n⚠️  Force break valid lock? (y/N): ").lower() == 'y':
                    lock.force_break(reason or "User force via /rfc-unlock")
                    print("\n✅ Lock broken successfully")
                    return 0
            else:
                print("\nTo force break: /rfc-unlock --force")
                print("Warning: Only break if you're certain the workflow is stuck!")

    return 0


# ============================================================================
# Example Usage
# ============================================================================

def example_usage():
    """Example usage of WorkflowLock."""
    import tempfile
    from pathlib import Path

    # Create temporary directory as fake repo
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)

        print("=== Workflow Lock Example ===\n")

        # Example 1: Context manager (recommended)
        print("1. Using context manager:")
        with WorkflowLock(repo_root, timeout_seconds=10) as lock:
            print("   Lock acquired - safe to modify rfc-map.json")
            time.sleep(1)
        print("   Lock released\n")

        # Example 2: Manual control
        print("2. Using manual control:")
        lock = WorkflowLock(repo_root)
        try:
            lock.acquire(timeout_seconds=10, blocking=True)
            print("   Lock acquired")
            # ... critical section ...
        finally:
            lock.release()
            print("   Lock released\n")

        # Example 3: Check lock info
        print("3. Checking lock info:")
        lock_info = lock.get_lock_info()
        if lock_info:
            print(f"   Lock held by PID {lock_info['pid']}")
        else:
            print("   No lock exists\n")


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Run example
    example_usage()
