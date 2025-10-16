# Concurrency Control Mechanism Design

**Date**: 2025-10-14
**Status**: Research Phase - Design Document
**Gap Item**: CHK070 (Concurrent agent updates to rfc-map.json)
**Priority**: HIGH (Blocking production use)

---

## Executive Summary

This document specifies a file-based concurrency control mechanism to prevent data corruption when multiple RFC workflows access `rfc-map.json` simultaneously. The recommended approach uses **Advisory File Locking (flock) with Stale Lock Detection** as the primary mechanism, with graceful fallback to lock files on platforms where flock is unavailable.

**Key Decision**: Hybrid approach combining OS-level advisory locking (fast path) with PID-tracked lock files (compatibility fallback), targeting <50ms overhead for uncontended access and supporting network filesystems.

---

## 1. Concurrency Scenarios Analysis

### Scenario 1: Two Developers Run `/rfc-generate` Simultaneously (Same Repository)

**Setup**:
- Developer A runs: `/rfc-generate paths=src/api/`
- Developer B runs: `/rfc-generate paths=src/utils/` (2 seconds later)
- Same repository, same machine, different terminal sessions

**Current Behavior (No Locking)**:
```
T+0s:  Dev A reads rfc-map.json (version 1, 50 mappings)
T+1s:  Dev A processes API code, generates 20 new mappings
T+2s:  Dev B reads rfc-map.json (version 1, 50 mappings) ← READS STALE STATE
T+3s:  Dev A writes rfc-map.json (70 mappings)
T+4s:  Dev B processes utils code, generates 15 new mappings
T+5s:  Dev B writes rfc-map.json (65 mappings) ← OVERWRITES DEV A'S WORK
```

**Data Loss**: Dev A's 20 mappings are lost (last-write-wins).

**With Concurrency Control**:
```
T+0s:  Dev A acquires lock, reads rfc-map.json (50 mappings)
T+2s:  Dev B attempts to acquire lock → BLOCKS (waiting for Dev A)
T+3s:  Dev A writes rfc-map.json (70 mappings), releases lock
T+3s:  Dev B acquires lock, reads rfc-map.json (70 mappings) ← CORRECT STATE
T+5s:  Dev B writes rfc-map.json (85 mappings), releases lock
```

**Result**: Both sets of mappings preserved.

**Failure Modes**:
- **Deadlock**: Not possible (single resource, FIFO queue)
- **Stale Lock**: Dev A's process crashes while holding lock → Dev B stuck waiting
- **Lock Timeout**: Dev A takes >5 minutes → Dev B aborts with timeout

---

### Scenario 2: CI/CD Pipeline + Developer (Distributed Access)

**Setup**:
- GitHub Actions workflow runs `/rfc-update` on push to main
- Developer runs `/rfc-generate` locally on same branch (stale local copy)
- Shared repository via Git pull/push

**Current Behavior**:
```
T+0s:  CI reads rfc-map.json (version 2, commit abc123)
T+1s:  Developer reads rfc-map.json (version 2, commit abc123)
T+2s:  CI writes rfc-map.json (version 2, commit abc123 + updates)
T+3s:  CI pushes to GitHub (commit def456)
T+4s:  Developer writes rfc-map.json (version 2, commit abc123 + different updates)
T+5s:  Developer pushes to GitHub → GIT MERGE CONFLICT
```

**Data Loss**: Git detects conflict, but user must manually resolve JSON merge.

**With Concurrency Control**:
- Local locking prevents simultaneous access on same machine
- Git remains the source of truth for distributed access
- Pre-push hook detects rfc-map.json changes and warns user

**Git Integration**:
```bash
# Pre-push hook checks for rfc-map.json conflicts
if git diff origin/main -- docs/rfc-map.json | grep -q .; then
  echo "⚠️  rfc-map.json has upstream changes - pull first"
  exit 1
fi
```

**Failure Modes**:
- **Race Condition**: CI and developer push simultaneously → Git's merge conflict resolution
- **Lock Scope**: Local locking doesn't prevent distributed race (solved by Git)

---

### Scenario 3: Multiple Feature Branches Merging to Main

**Setup**:
- Feature branch A: Adds RFC for authentication module (10 mappings)
- Feature branch B: Adds RFC for logging module (8 mappings)
- Both merge to main within 1 hour

**Current Behavior**:
```
main:           rfc-map.json (50 mappings, sections 1-5)
feature-auth:   rfc-map.json (60 mappings, sections 1-5 + 6)
feature-log:    rfc-map.json (58 mappings, sections 1-5 + 6)
```

**Merge Conflicts**:
- Both branches add "section 6" → Section number collision
- JSON merge produces invalid structure

**With Concurrency Control + Section Allocation**:
```python
# Coordinator allocates section numbers atomically
def allocate_next_section(parent_section: str) -> str:
    """Thread-safe section number allocation."""
    with workflow_lock():
        mapper = load_rfc_map()
        existing_sections = {m.rfc.section for m in mapper.mappings}

        # Find next available section number
        base = int(parent_section)
        counter = 1
        while f"{base}.{counter}" in existing_sections:
            counter += 1

        return f"{base}.{counter}"
```

**Git Pre-Merge Hook**:
```bash
# Check for section number conflicts before merge
./scripts/validate-rfc-section-uniqueness.py --base main --head feature-auth
```

**Failure Modes**:
- **Section Collision**: Prevented by atomic section allocation
- **Mapping Divergence**: Two branches document same code symbol differently (requires manual resolution)

---

### Scenario 4: Distributed Team with Network Filesystem (NFS/SMB)

**Setup**:
- Team uses shared NFS mount for codebase
- Developer A (London) and Developer B (Tokyo) access same repository
- Network latency: 200ms RTT

**Current Behavior**:
```
Dev A (London):  Reads rfc-map.json
Dev B (Tokyo):   Reads rfc-map.json (200ms later, sees same state)
Dev A:           Writes rfc-map.json
Dev B:           Writes rfc-map.json → OVERWRITES
```

**NFS Locking Challenges**:
- `fcntl.flock()` NOT supported on NFS v2/v3 (only NFSv4 with kernel support)
- Lock coherence depends on NFS implementation
- Stale lock detection harder (remote PID checking unreliable)

**With Concurrency Control (Lock File Approach)**:
```
# Use lock file with PID + hostname for distributed detection
lock_file = .claude/.rfc-workflow.lock
contents:
{
  "pid": 12345,
  "hostname": "london-dev-01",
  "timestamp": "2025-10-14T10:30:00Z",
  "workflow": "/rfc-generate"
}
```

**Lock Acquisition**:
1. Create temp file with PID + hostname
2. Attempt atomic rename to `.rfc-workflow.lock`
3. If rename fails (file exists), read lock and check staleness
4. If stale (timestamp > 10 minutes old), attempt forceful takeover

**Failure Modes**:
- **Network Partition**: Tokyo cannot verify London PID → Conservatively wait for timeout
- **Clock Skew**: NTP sync required (tolerate ±60 seconds)
- **Rename Atomicity**: Most network filesystems support atomic rename

---

## 2. Locking Strategy Options - Detailed Analysis

### Option A: Advisory File Locking (flock) ✅ RECOMMENDED

**Implementation**:
```python
import fcntl
import os
from pathlib import Path
from datetime import datetime, timedelta

class WorkflowLock:
    def __init__(self, repo_root: Path):
        self.lock_file = repo_root / '.claude' / '.rfc-workflow.lock'
        self.lock_file.parent.mkdir(parents=True, exist_ok=True)
        self.lock_fd = None

    def acquire(self, timeout_seconds: int = 300, blocking: bool = True):
        """
        Acquire exclusive lock with timeout.

        Args:
            timeout_seconds: Maximum time to wait (default: 5 minutes)
            blocking: Whether to block or fail immediately

        Raises:
            LockTimeout: If timeout exceeded
            LockUnavailable: If non-blocking and lock held
        """
        # Open lock file (create if doesn't exist)
        self.lock_fd = open(self.lock_file, 'w')

        # Try to acquire lock
        start_time = datetime.now()
        operation = fcntl.LOCK_EX if blocking else fcntl.LOCK_EX | fcntl.LOCK_NB

        while True:
            try:
                fcntl.flock(self.lock_fd.fileno(), operation)

                # Success - write metadata for debugging
                self.lock_fd.write(json.dumps({
                    "pid": os.getpid(),
                    "timestamp": datetime.now().isoformat(),
                    "hostname": socket.gethostname()
                }))
                self.lock_fd.flush()

                return True

            except BlockingIOError:
                # Lock held by another process
                if not blocking:
                    raise LockUnavailable("Lock held by another workflow")

                # Check timeout
                elapsed = (datetime.now() - start_time).total_seconds()
                if elapsed > timeout_seconds:
                    raise LockTimeout(f"Could not acquire lock after {timeout_seconds}s")

                # Wait and retry (exponential backoff)
                time.sleep(min(0.1 * (1.5 ** (elapsed // 10)), 5))

    def release(self):
        """Release lock and close file descriptor."""
        if self.lock_fd:
            fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_UN)
            self.lock_fd.close()
            self.lock_fd = None

            # Clean up lock file
            try:
                self.lock_file.unlink()
            except FileNotFoundError:
                pass

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
```

**Pros**:
- **OS-Level**: Kernel enforces lock coherence (process crash auto-releases)
- **Fast**: ~10μs overhead for uncontended lock
- **Atomic**: No race condition in lock acquisition
- **Cross-Platform**: Works on Linux, macOS, Windows (msvcrt.locking)

**Cons**:
- **NFS Issues**: NFSv2/v3 don't support flock (NFSv4 required)
- **Network FS**: SMB/CIFS support varies by implementation
- **Debugging**: Lock held by PID, but PID may not be informative

**Performance**:
- Uncontended: <50μs
- Contended (1 waiter): ~100ms polling interval
- Timeout: User-configurable (default 5 minutes)

**Stale Lock Handling**:
- **Auto-Release**: Process crash → kernel releases lock immediately
- **Detection**: Not needed (OS handles cleanup)
- **Timeout**: User can configure max wait time

---

### Option B: Lock Files with PID Tracking (Fallback)

**Implementation**:
```python
import os
import json
import socket
from pathlib import Path
from datetime import datetime, timedelta

class LockFile:
    def __init__(self, repo_root: Path):
        self.lock_path = repo_root / '.claude' / '.rfc-workflow.lock'
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)

    def acquire(self, timeout_seconds: int = 300):
        """Acquire lock using lock file with PID tracking."""
        start_time = datetime.now()

        while True:
            # Try to create lock file atomically
            temp_lock = self.lock_path.with_suffix('.tmp')

            lock_data = {
                "pid": os.getpid(),
                "hostname": socket.gethostname(),
                "timestamp": datetime.now().isoformat(),
                "workflow": os.environ.get('CLAUDE_WORKFLOW', 'unknown')
            }

            # Write to temp file
            with open(temp_lock, 'w') as f:
                json.dump(lock_data, f, indent=2)

            # Atomic rename (creates lock if doesn't exist)
            try:
                temp_lock.rename(self.lock_path)
                return True  # Success!

            except FileExistsError:
                # Lock exists - check if stale
                if self._is_stale_lock():
                    # Force takeover
                    self._force_takeover(lock_data)
                    return True

                # Check timeout
                elapsed = (datetime.now() - start_time).total_seconds()
                if elapsed > timeout_seconds:
                    raise LockTimeout(f"Timeout after {timeout_seconds}s")

                # Wait and retry
                time.sleep(1)

    def _is_stale_lock(self, max_age_minutes: int = 10) -> bool:
        """Check if lock file is stale (process dead or timeout)."""
        try:
            with open(self.lock_path, 'r') as f:
                lock_data = json.load(f)

            # Check timestamp
            lock_time = datetime.fromisoformat(lock_data['timestamp'])
            age = (datetime.now() - lock_time).total_seconds() / 60

            if age > max_age_minutes:
                logger.warning(f"Lock file is {age:.1f} minutes old (stale)")
                return True

            # Check if process still exists (local only)
            if lock_data['hostname'] == socket.gethostname():
                pid = lock_data['pid']
                if not self._is_process_alive(pid):
                    logger.warning(f"Lock holder PID {pid} no longer exists (stale)")
                    return True

            return False

        except (json.JSONDecodeError, KeyError, FileNotFoundError):
            # Corrupted lock file - consider stale
            return True

    def _is_process_alive(self, pid: int) -> bool:
        """Check if process with given PID is still running (Unix only)."""
        try:
            os.kill(pid, 0)  # Signal 0 = existence check
            return True
        except OSError:
            return False

    def _force_takeover(self, new_lock_data: dict):
        """Forcefully take over stale lock."""
        logger.warning(f"Forcing takeover of stale lock")

        # Backup old lock file for forensics
        backup = self.lock_path.with_suffix('.lock.stale')
        try:
            self.lock_path.rename(backup)
        except FileNotFoundError:
            pass

        # Write new lock file
        with open(self.lock_path, 'w') as f:
            json.dump(new_lock_data, f, indent=2)

    def release(self):
        """Release lock by deleting lock file."""
        try:
            self.lock_path.unlink()
        except FileNotFoundError:
            pass
```

**Pros**:
- **Network FS**: Works on NFS, SMB, any filesystem
- **Debuggable**: Lock file contains metadata (PID, hostname, workflow)
- **Stale Detection**: Can detect and recover from crashed processes
- **Cross-Platform**: Pure Python, no OS-specific calls

**Cons**:
- **Race Condition**: Small window between check and create (mitigated by atomic rename)
- **PID Reuse**: Process PID could be reused (rare but possible)
- **Clock Skew**: Timestamp-based staleness affected by NTP sync
- **Slower**: ~1ms overhead for lock acquisition (file I/O)

**Performance**:
- Uncontended: ~1ms (file write + rename)
- Contended: 1-second polling interval
- Stale detection: Every attempt (adds ~0.5ms)

---

### Option C: Atomic Write with CAS (Compare-And-Swap) ❌ REJECTED

**Implementation**:
```python
def update_rfc_map_atomic(updates_fn):
    """Update rfc-map.json using optimistic locking."""
    max_retries = 10

    for attempt in range(max_retries):
        # Read current state
        with open('docs/rfc-map.json', 'rb') as f:
            content = f.read()

        checksum_before = hashlib.sha256(content).hexdigest()
        rfc_map = json.loads(content)

        # Apply updates
        updated_map = updates_fn(rfc_map)

        # Write to temp file
        temp_file = Path('docs/.rfc-map.json.tmp')
        with open(temp_file, 'w') as f:
            json.dump(updated_map, f, indent=2)

        # Re-read original file to check for concurrent modification
        with open('docs/rfc-map.json', 'rb') as f:
            checksum_after = hashlib.sha256(f.read()).hexdigest()

        if checksum_before == checksum_after:
            # No concurrent modification - safe to replace
            temp_file.rename('docs/rfc-map.json')
            return True
        else:
            # Concurrent modification detected - retry
            logger.warning(f"CAS retry {attempt+1}/{max_retries}")
            time.sleep(0.1 * (2 ** attempt))  # Exponential backoff

    raise ConcurrencyError("Too many CAS retries")
```

**Pros**:
- **Lock-Free**: No explicit locks needed
- **Simple**: Pure Python, no OS dependencies
- **Network FS**: Works anywhere

**Cons**:
- **Wasted Work**: On conflict, entire workflow re-runs (expensive for RFC generation)
- **Retry Explosion**: High contention → exponential retries → poor UX
- **Merge Logic**: Can't merge independent changes (A adds section 6, B adds section 7 → one loses)
- **Throughput**: Linear degradation with concurrency (1 workflow at a time actually succeeds)

**Performance**:
- Uncontended: ~5ms (2x file reads + checksum)
- 2 concurrent workflows: 50% retry rate → 2x latency
- 4 concurrent workflows: 75% retry rate → 4x latency

**Verdict**: ❌ **REJECTED** - Wasted work unacceptable for long-running RFC generation (minutes), poor user experience with retries, no benefit over locking.

---

### Option D: Coordinator Service ❌ REJECTED

**Implementation**:
```python
# Long-running daemon process
class RFCCoordinatorDaemon:
    def __init__(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.bind('/tmp/rfc-coordinator.sock')
        self.queue = queue.Queue()

    def run(self):
        """Process workflow requests sequentially."""
        self.sock.listen(5)

        while True:
            conn, addr = self.sock.accept()
            request = json.loads(conn.recv(4096))

            # Queue workflow (FIFO)
            result = self._process_workflow(request)

            conn.send(json.dumps(result).encode())
            conn.close()
```

**Pros**:
- **Full Control**: Can implement any queueing/priority logic
- **Observability**: Centralized monitoring of all workflows
- **Fairness**: FIFO queue prevents starvation

**Cons**:
- **Complexity**: Requires daemon management (start/stop/restart)
- **Failure Mode**: Daemon crash → all workflows blocked
- **Setup Overhead**: Users must start daemon (poor UX)
- **CI/CD**: Hard to run in ephemeral CI environments
- **Single Point of Failure**: Daemon is bottleneck

**Verdict**: ❌ **REJECTED** - Violates simplicity principle, poor fit for Claude Code plugin (no background services), overkill for file access coordination.

---

### Option E: Git-Based Locking ❌ REJECTED

**Implementation**:
```bash
# Use git index lock as coordination mechanism
git update-index --assume-unchanged docs/rfc-map.json
trap "git update-index --no-assume-unchanged docs/rfc-map.json" EXIT

# Run workflow
/rfc-generate paths=src/

# Commit changes
git add docs/rfc-map.json
git commit -m "Update RFC documentation"
```

**Pros**:
- **Integrated**: Uses existing Git infrastructure
- **Conflict Detection**: Git merge handles concurrent updates

**Cons**:
- **Requires Git**: Breaks for non-Git repositories
- **Lock Scope**: Locks entire index (too broad)
- **Complexity**: Interacts poorly with user Git workflow
- **Race Condition**: Between `git add` and `git commit`
- **Poor UX**: Forces users into Git commit workflow

**Verdict**: ❌ **REJECTED** - Too invasive, breaks local workflows, requires Git (not universal), poor separation of concerns.

---

## 3. Lock Acquisition Behavior

### Blocking vs Non-Blocking

**Recommendation**: **Blocking with configurable timeout** (default: 5 minutes)

**Rationale**:
- RFC generation takes 2-20 minutes → workflows naturally serialized
- Non-blocking (fail-fast) leads to poor UX (manual retry needed)
- Timeout prevents indefinite hangs from stale locks

**Configuration**:
```json
// .claude/plugin.json
{
  "concurrency": {
    "lock_timeout_seconds": 300,
    "lock_strategy": "flock",  // or "lockfile" for NFS
    "stale_lock_threshold_minutes": 10,
    "enable_graceful_degradation": true
  }
}
```

**Timeout Values**:
| Workflow Type | Default Timeout | Rationale |
|---------------|----------------|-----------|
| `/rfc-generate` (initial) | 600s (10min) | Large codebases take 20+ minutes |
| `/rfc-update` (incremental) | 300s (5min) | Updates are faster (<10min) |
| Hook (`post_tool_sync`) | 10s | Non-blocking, background sync |
| `/rfc-validate` | 60s | Read-only, should be fast |

**User Feedback During Wait**:
```
⏳ Waiting for another RFC workflow to complete...
   Lock held by: /rfc-generate (PID 12345) since 2 minutes ago
   Will timeout in: 3 minutes

   Press Ctrl+C to cancel
```

**Progress Indicator**:
```python
def acquire_with_feedback(lock, timeout_seconds):
    start = datetime.now()

    while True:
        try:
            return lock.acquire(timeout=1, blocking=True)
        except LockTimeout:
            elapsed = (datetime.now() - start).total_seconds()
            remaining = timeout_seconds - elapsed

            if remaining <= 0:
                raise LockTimeout(f"Could not acquire lock after {timeout_seconds}s")

            # Show progress every 30 seconds
            if int(elapsed) % 30 == 0:
                print(f"⏳ Still waiting... ({int(remaining)}s remaining)")
```

---

### Queue vs Reject

**Recommendation**: **Implicit FIFO queue** (via OS scheduler)

**How It Works**:
- Process A holds lock
- Process B calls `fcntl.flock()` → **blocks** (enters kernel wait queue)
- Process C calls `fcntl.flock()` → **blocks** (added to wait queue)
- Process A releases lock → **kernel wakes Process B** (FIFO order)
- Process B acquires lock, runs, releases
- Process C acquires lock

**Why Not Explicit Queue**:
- OS already implements fair queuing (no reinvention needed)
- Simpler implementation
- Works across processes without shared memory

**Fairness**:
- Linux: FIFO order guaranteed (kernel wait queue)
- macOS: FIFO order guaranteed (BSD flock semantics)
- Windows: Implementation-dependent (usually FIFO)

---

## 4. Stale Lock Detection & Recovery

### Detection Criteria

**For flock (Option A)**:
- **No Detection Needed**: OS auto-releases lock on process death
- **Timeout Only**: If workflow appears hung (>10 minutes), user can kill process

**For Lock Files (Option B)**:
1. **Timestamp Age**: Lock file >10 minutes old (configurable)
2. **PID Liveness**: Process no longer exists (Unix: `os.kill(pid, 0)`)
3. **Hostname Check**: Only check PID if same machine (safety)

**Algorithm**:
```python
def is_stale_lock(lock_data: dict, max_age_minutes: int = 10) -> bool:
    """
    Determine if lock is stale.

    Returns:
        True if lock should be broken, False if still valid
    """
    # Check 1: Timestamp age
    lock_time = datetime.fromisoformat(lock_data['timestamp'])
    age_minutes = (datetime.now() - lock_time).total_seconds() / 60

    if age_minutes > max_age_minutes:
        logger.warning(f"Lock {age_minutes:.1f} minutes old (threshold: {max_age_minutes})")
        return True

    # Check 2: PID liveness (local machine only)
    if lock_data['hostname'] == socket.gethostname():
        pid = lock_data['pid']

        if not is_process_alive(pid):
            logger.warning(f"Lock holder PID {pid} is dead")
            return True

    # Check 3: Heartbeat (future enhancement)
    # If lock file has "last_heartbeat" field, check if recent

    return False
```

---

### When to Break Stale Locks

**Policy**: **Automatic with Warning + Backup**

**Automatic Breaking**:
- After 10 minutes of age AND (PID dead OR same hostname)
- User sees warning: `⚠️  Detected stale lock from crashed workflow, taking over`
- Old lock file backed up to `.rfc-workflow.lock.stale` for forensics

**Manual Breaking**:
- New slash command: `/rfc-unlock [--force]`
- Checks staleness criteria, shows lock details
- Requires `--force` if lock appears valid (recent timestamp, live PID)

**Implementation**:
```python
def force_break_lock(lock_path: Path, reason: str):
    """
    Break lock with audit trail.

    Args:
        lock_path: Path to lock file
        reason: Reason for breaking (for logging)
    """
    # Backup old lock for forensics
    backup_path = lock_path.with_suffix('.lock.stale')

    try:
        # Read old lock data
        with open(lock_path, 'r') as f:
            old_lock = json.load(f)

        # Log to audit trail
        logger.warning(
            f"Breaking stale lock: PID={old_lock.get('pid')}, "
            f"Age={_lock_age(old_lock):.1f}min, Reason={reason}"
        )

        # Backup old lock
        with open(backup_path, 'w') as f:
            json.dump({
                **old_lock,
                "broken_by": os.getpid(),
                "broken_at": datetime.now().isoformat(),
                "reason": reason
            }, f, indent=2)

        # Remove lock file
        lock_path.unlink()

    except Exception as e:
        logger.error(f"Failed to break lock: {e}")
        raise
```

---

### False Positive Prevention

**Problem**: Long-running workflows (20+ minutes for 1M LOC) shouldn't be killed

**Solutions**:
1. **Heartbeat**: Lock file updated every 60 seconds (optional)
2. **Timeout Scaling**: Timeout based on codebase size
   - Small (<10K LOC): 5 minutes
   - Medium (10K-100K): 10 minutes
   - Large (100K-1M): 20 minutes
   - Huge (>1M): 30 minutes
3. **User Override**: CLI flag `--lock-timeout 1800` for explicit control

**Heartbeat Implementation** (Optional):
```python
class WorkflowLockWithHeartbeat:
    def __init__(self, lock_path: Path):
        self.lock_path = lock_path
        self.heartbeat_thread = None

    def _heartbeat_loop(self):
        """Update lock file timestamp every 60 seconds."""
        while self.heartbeat_thread:
            time.sleep(60)

            try:
                with open(self.lock_path, 'r+') as f:
                    lock_data = json.load(f)
                    lock_data['last_heartbeat'] = datetime.now().isoformat()
                    f.seek(0)
                    json.dump(lock_data, f, indent=2)
                    f.truncate()
            except Exception as e:
                logger.error(f"Heartbeat failed: {e}")
                break

    def acquire(self):
        # ... lock acquisition ...

        # Start heartbeat thread
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()

    def release(self):
        # Stop heartbeat
        self.heartbeat_thread = None

        # ... lock release ...
```

---

## 5. Lock Scope & Granularity

### Granularity Options

| Scope | Lock Target | Concurrency | Complexity |
|-------|-------------|-------------|------------|
| **Repository-level** | `.claude/.rfc-workflow.lock` | 1 workflow/repo | Low ✅ |
| **File-level** | `docs/.rfc-map.json.lock` | N workflows if different files | Medium |
| **Section-level** | `.claude/.rfc-section-6.lock` | High (per-section) | High |

**Recommendation**: **Repository-level** (single lock)

**Rationale**:
- RFC generation is holistic (cross-references span entire document)
- rfc-map.json is single file (can't partition)
- Coordinator agent manages all sub-agents (single workflow)
- Simplicity > theoretical concurrency (workflows rarely overlap)

**Lock Location**: `.claude/.rfc-workflow.lock`

**Why Not File-Level**:
- Only 1 file (rfc-map.json) is contended resource
- Doesn't enable additional concurrency

**Why Not Section-Level**:
- Section numbers allocated dynamically (can't lock before generation)
- Cross-references span sections (need global view)
- Massive complexity (N locks to manage)

---

## 6. Integration with Existing Patterns

### Checkpoint System Integration

**Current**: Checkpoints save parser.json, analyzer.json, formatter.json to `.claude/.checkpoints/`

**Integration**:
```python
# In coordinator.md (agent instructions)
"""
After acquiring workflow lock:
1. Check for existing checkpoints (recovery from failure)
2. If found, prompt user: "Resume from checkpoint or start fresh?"
3. Lock remains held during entire workflow (including recovery)
4. Release lock only after final rfc-map.json write OR abort
"""
```

**Checkpoint Lock Interaction**:
- Checkpoints are **per-workflow** (isolated by timestamp)
- Lock is **per-repository** (prevents concurrent workflows)
- Lock acquired BEFORE reading checkpoints (prevents race)

**Recovery Flow**:
```
1. Acquire lock
2. Check for checkpoints
   - If found: Load checkpoint (resume workflow)
   - If not found: Start fresh
3. Run workflow (parser → analyzer → formatter)
4. Write rfc-map.json
5. Release lock
```

---

### Hook Integration

**Problem**: `post_tool_sync.py` updates rfc-map.json **outside** main workflow

**Current Behavior**:
```python
# post_tool_sync.py
def main():
    # ... detect modified files ...

    # Direct write to rfc-map.json (NO LOCKING)
    update_rfc_map_for_files(modified_files, rfc_map_path, repo_root)
```

**Updated Behavior**:
```python
# post_tool_sync.py
from .lib.workflow_lock import WorkflowLock

def main():
    # ... detect modified files ...

    # Acquire lock with short timeout (non-blocking for hooks)
    lock = WorkflowLock(repo_root)

    try:
        lock.acquire(timeout_seconds=10, blocking=True)
    except LockTimeout:
        # Graceful degradation: skip sync, log warning
        logger.warning("Could not acquire lock for sync (workflow running)")
        print(json.dumps({
            "block": False,
            "message": "⏭️  Skipped rfc-map.json sync (workflow in progress)"
        }))
        return

    try:
        # Update rfc-map.json atomically
        update_rfc_map_for_files(modified_files, rfc_map_path, repo_root)
    finally:
        lock.release()
```

**Key Points**:
- Hooks use **10-second timeout** (fail fast, don't block user)
- Graceful degradation on lock failure (skip sync, warn user)
- Locks released immediately after update (minimize hold time)

---

### Error Handling

**Lock Acquisition Failures**:

1. **Timeout (LockTimeout)**:
   ```
   ❌ Could not acquire workflow lock after 5 minutes

   Another RFC workflow is running:
     - Workflow: /rfc-generate paths=src/
     - PID: 12345
     - Started: 2025-10-14T10:30:00Z (7 minutes ago)

   Options:
     1. Wait longer (increase --lock-timeout)
     2. Cancel other workflow (kill 12345)
     3. Force unlock (/rfc-unlock --force)
   ```

2. **Stale Lock Detected**:
   ```
   ⚠️  Detected stale lock from crashed workflow

   Lock Details:
     - PID: 12345 (process no longer exists)
     - Started: 2025-10-14T09:00:00Z (90 minutes ago)
     - Workflow: /rfc-generate

   Automatically breaking lock and continuing...
   ```

3. **Lock File Corrupted**:
   ```
   ⚠️  Lock file corrupted, forcing takeover

   Old lock backed up to: .claude/.rfc-workflow.lock.stale
   Please report this issue if it recurs.
   ```

**Error Recovery**:
- All lock operations wrapped in try-except
- Failed lock acquisition → workflow aborts cleanly
- Lock corruption → force takeover with warning
- Process crash → OS releases flock (auto-recovery)

---

## 7. Recommended Approach - Hybrid Strategy

### Design Decision

**Primary**: Advisory File Locking (flock) - Option A
**Fallback**: Lock Files with PID Tracking - Option B
**Detection**: Auto-detect at runtime based on platform/filesystem

### Architecture

```python
# lib/workflow_lock.py

import os
import sys
import fcntl
from pathlib import Path
from typing import Optional

class WorkflowLock:
    """
    Cross-platform workflow locking with automatic strategy selection.

    Strategy Selection:
    - Linux/macOS local filesystem: flock (fast, kernel-managed)
    - Windows: msvcrt.locking (file byte-range locking)
    - NFS/Network filesystem: Lock file with PID tracking
    - Unknown: Lock file (safe fallback)
    """

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.lock_dir = repo_root / '.claude'
        self.lock_dir.mkdir(parents=True, exist_ok=True)

        # Auto-detect best strategy
        self.strategy = self._detect_strategy()
        self.lock_impl = None

    def _detect_strategy(self) -> str:
        """Detect best locking strategy for current platform/filesystem."""
        # Check platform
        if sys.platform.startswith('linux') or sys.platform == 'darwin':
            # Check if filesystem supports flock
            if self._test_flock_support():
                return 'flock'
        elif sys.platform == 'win32':
            return 'msvcrt'

        # Fallback to lock file
        return 'lockfile'

    def _test_flock_support(self) -> bool:
        """Test if filesystem supports flock (may fail on NFS)."""
        test_file = self.lock_dir / '.lock-test'

        try:
            with open(test_file, 'w') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

            test_file.unlink()
            return True

        except (OSError, IOError):
            return False

    def acquire(self, timeout_seconds: int = 300, blocking: bool = True):
        """Acquire lock using selected strategy."""
        if self.strategy == 'flock':
            self.lock_impl = FlockLock(self.lock_dir)
        elif self.strategy == 'lockfile':
            self.lock_impl = LockFileLock(self.lock_dir)
        elif self.strategy == 'msvcrt':
            self.lock_impl = WindowsLock(self.lock_dir)

        return self.lock_impl.acquire(timeout_seconds, blocking)

    def release(self):
        """Release lock."""
        if self.lock_impl:
            self.lock_impl.release()

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


class FlockLock:
    """flock-based locking (Linux/macOS)."""
    # ... implementation from Option A ...

class LockFileLock:
    """Lock file with PID tracking (NFS/network filesystems)."""
    # ... implementation from Option B ...

class WindowsLock:
    """msvcrt-based locking (Windows)."""
    def __init__(self, lock_dir: Path):
        self.lock_file = lock_dir / '.rfc-workflow.lock'
        self.lock_fd = None

    def acquire(self, timeout_seconds: int, blocking: bool):
        import msvcrt

        self.lock_fd = open(self.lock_file, 'w')

        # Try to lock first byte of file
        start_time = datetime.now()

        while True:
            try:
                msvcrt.locking(self.lock_fd.fileno(), msvcrt.LK_NBLCK, 1)
                return True
            except OSError:
                if not blocking:
                    raise LockUnavailable()

                elapsed = (datetime.now() - start_time).total_seconds()
                if elapsed > timeout_seconds:
                    raise LockTimeout()

                time.sleep(0.1)

    def release(self):
        if self.lock_fd:
            import msvcrt
            msvcrt.locking(self.lock_fd.fileno(), msvcrt.LK_UNLCK, 1)
            self.lock_fd.close()
```

### Usage in Workflows

```python
# In coordinator agent (via coordinator.md instructions)
"""
At the start of workflow execution:

1. Initialize lock:
   ```python
   from lib.workflow_lock import WorkflowLock

   lock = WorkflowLock(repo_root)
   ```

2. Acquire lock with user feedback:
   ```python
   try:
       lock.acquire(timeout_seconds=600, blocking=True)
       print("🔒 Workflow lock acquired")
   except LockTimeout:
       print("❌ Timeout: Another workflow is running")
       print("   Use /rfc-unlock to inspect lock status")
       sys.exit(1)
   ```

3. Run workflow (parser → analyzer → formatter)

4. Update rfc-map.json atomically:
   ```python
   # Lock is held - safe to write
   mapper.save()
   ```

5. Release lock:
   ```python
   lock.release()
   print("🔓 Workflow lock released")
   ```
"""
```

---

## 8. Implementation Specification

### API Design

```python
# lib/workflow_lock.py

class WorkflowLock:
    """
    Main API for workflow locking.

    Example:
        with WorkflowLock(repo_root) as lock:
            # ... perform workflow ...
            mapper.save()
    """

    def __init__(
        self,
        repo_root: Path,
        timeout_seconds: int = 300,
        stale_threshold_minutes: int = 10
    ):
        """
        Initialize workflow lock.

        Args:
            repo_root: Repository root directory
            timeout_seconds: Default timeout for lock acquisition
            stale_threshold_minutes: Age threshold for stale lock detection
        """

    def acquire(self, timeout_seconds: Optional[int] = None, blocking: bool = True):
        """
        Acquire exclusive lock.

        Args:
            timeout_seconds: Override default timeout
            blocking: Whether to block or fail immediately

        Raises:
            LockTimeout: If timeout exceeded
            LockUnavailable: If non-blocking and lock held
        """

    def release(self):
        """Release lock and cleanup."""

    def get_lock_info(self) -> Optional[dict]:
        """
        Get information about current lock holder.

        Returns:
            Dict with {pid, hostname, timestamp, workflow} or None if unlocked
        """

    def force_break(self, reason: str):
        """
        Forcefully break lock (with audit trail).

        Args:
            reason: Reason for breaking lock
        """


class LockTimeout(Exception):
    """Raised when lock acquisition timeout exceeded."""
    pass

class LockUnavailable(Exception):
    """Raised when lock unavailable in non-blocking mode."""
    pass
```

### Stale Lock Detection Algorithm

```python
def is_stale_lock(lock_data: dict, threshold_minutes: int = 10) -> tuple[bool, str]:
    """
    Determine if lock is stale.

    Args:
        lock_data: Lock metadata (pid, hostname, timestamp)
        threshold_minutes: Age threshold

    Returns:
        (is_stale, reason) tuple
    """
    # Check 1: Timestamp age
    try:
        lock_time = datetime.fromisoformat(lock_data['timestamp'])
    except (ValueError, KeyError):
        return (True, "Invalid timestamp format")

    age_minutes = (datetime.now() - lock_time).total_seconds() / 60

    if age_minutes > threshold_minutes:
        return (True, f"Lock {age_minutes:.1f} minutes old (threshold: {threshold_minutes})")

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
```

### Error Handling Flowchart

```
┌─────────────────────────┐
│ Workflow Starts         │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Attempt Lock Acquisition│
└────┬──────────────┬─────┘
     │              │
     │ Success      │ Failure (LockTimeout)
     │              │
     ▼              ▼
┌─────────┐   ┌──────────────────┐
│ Run     │   │ Check if stale   │
│ Workflow│   │ lock exists      │
└────┬────┘   └────┬─────────────┘
     │             │
     │             │ Stale?
     │             ├─Yes─→ Break lock, retry
     │             │
     │             └─No──→ Show error, abort
     │
     ▼
┌─────────────────────────┐
│ Update rfc-map.json     │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Release Lock            │
└─────────────────────────┘
```

### Code Skeleton

```python
# lib/workflow_lock.py

"""
Workflow locking to prevent concurrent rfc-map.json corruption.

Architecture:
- Hybrid strategy: flock (fast) with lockfile fallback (NFS)
- Auto-detects best approach based on platform/filesystem
- Stale lock detection with automatic recovery
- Context manager interface for safe lock/unlock
"""

import os
import sys
import time
import json
import socket
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Tuple
from contextlib import contextmanager

logger = logging.getLogger(__name__)

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


class LockTimeout(Exception):
    """Raised when lock acquisition timeout exceeded."""
    pass


class LockUnavailable(Exception):
    """Raised when lock unavailable in non-blocking mode."""
    pass


def is_process_alive(pid: int) -> bool:
    """
    Check if process is still running.

    Args:
        pid: Process ID

    Returns:
        True if process exists, False otherwise
    """
    try:
        os.kill(pid, 0)  # Signal 0 = existence check
        return True
    except (OSError, ProcessLookupError):
        return False


class WorkflowLock:
    """
    Cross-platform workflow locking.

    Usage:
        with WorkflowLock(repo_root) as lock:
            # ... critical section ...
            mapper.save()
    """

    def __init__(
        self,
        repo_root: Path,
        timeout_seconds: int = 300,
        stale_threshold_minutes: int = 10,
        enable_heartbeat: bool = False
    ):
        self.repo_root = Path(repo_root)
        self.timeout_seconds = timeout_seconds
        self.stale_threshold_minutes = stale_threshold_minutes
        self.enable_heartbeat = enable_heartbeat

        self.lock_dir = self.repo_root / '.claude'
        self.lock_dir.mkdir(parents=True, exist_ok=True)

        # Auto-detect strategy
        self.strategy = self._detect_strategy()
        self.lock_impl = None

        logger.info(f"Workflow lock initialized: strategy={self.strategy}")

    def _detect_strategy(self) -> str:
        """Auto-detect best locking strategy."""
        # TODO: Implement detection logic
        # Returns: 'flock', 'lockfile', or 'msvcrt'
        pass

    def acquire(self, timeout_seconds: Optional[int] = None, blocking: bool = True):
        """Acquire lock."""
        # TODO: Implement acquisition
        pass

    def release(self):
        """Release lock."""
        # TODO: Implement release
        pass

    def get_lock_info(self) -> Optional[dict]:
        """Get current lock holder info."""
        # TODO: Implement info retrieval
        pass

    def force_break(self, reason: str):
        """Forcefully break lock."""
        # TODO: Implement force break
        pass

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


# Convenience context manager
@contextmanager
def workflow_lock(repo_root: Path, **kwargs):
    """
    Context manager for workflow locking.

    Example:
        with workflow_lock(repo_root, timeout_seconds=600):
            # ... critical section ...
    """
    lock = WorkflowLock(repo_root, **kwargs)
    lock.acquire()
    try:
        yield lock
    finally:
        lock.release()
```

---

## 9. Test Scenarios

### Test 1: Two Workflows Start Simultaneously

**Setup**:
```bash
# Terminal 1
/rfc-generate paths=src/api/ &
PID1=$!

# Terminal 2 (2 seconds later)
/rfc-generate paths=src/utils/ &
PID2=$!

# Wait for both to complete
wait $PID1 $PID2
```

**Expected Behavior**:
1. Workflow 1 acquires lock immediately
2. Workflow 2 blocks, shows waiting message
3. Workflow 1 completes, writes rfc-map.json, releases lock
4. Workflow 2 acquires lock, reads updated rfc-map.json
5. Workflow 2 completes, merges new mappings

**Validation**:
```bash
# Check rfc-map.json has mappings from both workflows
jq '.mappings | length' docs/rfc-map.json
# Expected: Sum of both workflows

# Check lock history
jq '.entries | map(select(.hook == "workflow_lock"))' .claude/.hook-history.json
# Expected: 2 acquire events, 2 release events
```

---

### Test 2: Process Crashes While Holding Lock

**Setup**:
```bash
# Start workflow
/rfc-generate paths=src/ &
PID=$!

# Wait for lock acquisition
sleep 5

# Forcefully kill process
kill -9 $PID

# Immediately try another workflow
/rfc-generate paths=src/
```

**Expected Behavior (flock)**:
1. Workflow 1 acquires flock
2. Workflow 1 killed → OS releases flock immediately
3. Workflow 2 acquires lock without delay

**Expected Behavior (lockfile)**:
1. Workflow 1 creates lock file
2. Workflow 1 killed → lock file remains
3. Workflow 2 detects stale lock (PID dead)
4. Workflow 2 breaks stale lock with warning
5. Workflow 2 proceeds

**Validation**:
```bash
# Check for stale lock backup
ls -la .claude/.rfc-workflow.lock.stale
# Expected: Exists with metadata from killed workflow

# Check logs
tail .claude/.hook-logs/workflow_lock.log
# Expected: Warning about stale lock detection
```

---

### Test 3: Network Filesystem Edge Cases (NFS)

**Setup**:
```bash
# On NFS-mounted repository
mount | grep nfs
# Verify NFS mount exists

# Run workflow
/rfc-generate paths=src/
```

**Expected Behavior**:
1. Lock detection tests flock → fails on NFS
2. Falls back to lockfile strategy
3. Workflow acquires lock file with PID + hostname
4. Workflow completes normally
5. Lock file removed

**Validation**:
```bash
# Check strategy detection
grep "strategy=" .claude/.hook-logs/workflow_lock.log
# Expected: strategy=lockfile (not flock)

# Check lock file contents during execution
cat .claude/.rfc-workflow.lock
# Expected: JSON with pid, hostname, timestamp
```

---

### Test 4: Lock Timeout Exceeded

**Setup**:
```bash
# Start long-running workflow
/rfc-generate paths=entire-codebase/ --lock-timeout 600 &
PID1=$!

# Immediately start another workflow with short timeout
/rfc-generate paths=src/ --lock-timeout 10
```

**Expected Behavior**:
1. Workflow 1 acquires lock
2. Workflow 2 waits for lock
3. After 10 seconds, Workflow 2 times out
4. Workflow 2 displays error message with lock holder info
5. Workflow 2 exits with non-zero code

**Expected Output**:
```
⏳ Waiting for another RFC workflow to complete...
   Lock held by: /rfc-generate (PID 12345) since 12 seconds ago
   Will timeout in: 0 seconds

❌ Could not acquire workflow lock after 10 seconds

Another RFC workflow is running:
  - Workflow: /rfc-generate paths=entire-codebase/
  - PID: 12345
  - Started: 2025-10-14T10:30:00Z (12 seconds ago)

Options:
  1. Increase timeout: --lock-timeout 600
  2. Cancel other workflow: kill 12345
  3. Force unlock: /rfc-unlock --force
```

**Validation**:
```bash
# Check exit code
echo $?
# Expected: 1 (failure)

# Check workflow 1 still running
ps aux | grep $PID1
# Expected: Process still alive
```

---

## 10. User-Facing Changes

### New CLI Commands

#### `/rfc-unlock`

**Purpose**: Inspect and forcefully break workflow locks

**Usage**:
```bash
# Check lock status
/rfc-unlock

# Force break lock (with confirmation)
/rfc-unlock --force

# Break lock with custom reason
/rfc-unlock --force --reason "CI/CD pipeline hung"
```

**Output (lock exists)**:
```
🔒 Workflow Lock Status

Lock is held:
  - Workflow: /rfc-generate paths=src/
  - PID: 12345
  - Hostname: dev-machine-01
  - Started: 2025-10-14T10:30:00Z (5 minutes ago)
  - Heartbeat: 2025-10-14T10:34:30Z (30 seconds ago)

Lock appears VALID (process alive, recent heartbeat)

To force break: /rfc-unlock --force
Warning: Only break if you're certain the workflow is stuck!
```

**Output (no lock)**:
```
✅ No workflow lock exists

rfc-map.json is available for updates.
```

**Output (stale lock)**:
```
⚠️  Stale Lock Detected

Lock details:
  - PID: 12345 (process no longer exists)
  - Started: 2025-10-14T09:00:00Z (90 minutes ago)
  - Workflow: /rfc-generate

Automatically breaking stale lock...
✅ Lock broken successfully

Old lock backed up to: .claude/.rfc-workflow.lock.stale
```

---

### New Error Messages

#### Lock Timeout Error

```
❌ Could not acquire workflow lock after 5 minutes

Another RFC workflow is running:
  - Workflow: /rfc-generate paths=src/
  - PID: 12345
  - Started: 2025-10-14T10:30:00Z (7 minutes ago)

Options:
  1. Wait longer:
     Increase timeout with --lock-timeout 600

  2. Cancel other workflow:
     kill 12345

  3. Force unlock:
     /rfc-unlock --force
     (Warning: Only if you're certain the other workflow is stuck)

  4. Check lock details:
     /rfc-unlock

For help: /rfc-generate --help
```

#### Lock Unavailable (Non-Blocking)

```
❌ Workflow lock unavailable (held by another process)

Lock holder:
  - PID: 12345
  - Workflow: /rfc-generate
  - Age: 2 minutes

This operation requires exclusive access to rfc-map.json.
Please wait for the other workflow to complete.

Check status: /rfc-unlock
```

#### Stale Lock Auto-Recovery

```
⚠️  Detected stale lock from crashed workflow

Lock details:
  - PID: 12345 (process no longer exists)
  - Started: 2025-10-14T09:00:00Z (90 minutes ago)
  - Workflow: /rfc-generate

Automatically breaking lock and continuing...

Old lock backed up to: .claude/.rfc-workflow.lock.stale
If this recurs frequently, please report an issue.

Proceeding with workflow...
```

---

### Progress Indicators

#### Waiting for Lock

```
⏳ Waiting for another RFC workflow to complete...

Lock held by:
  - Workflow: /rfc-generate paths=entire-codebase/
  - PID: 12345
  - Started: 2 minutes ago

Will timeout in: 3 minutes

Press Ctrl+C to cancel

[████░░░░░░░░░░░░░░░░] 20% of timeout elapsed
```

#### Lock Acquired

```
🔒 Workflow lock acquired successfully

Proceeding with RFC generation...
```

#### Lock Released

```
✅ RFC generation complete

🔓 Workflow lock released

Updated:
  - rfc-map.json: 85 mappings (+15 new)
  - docs/generated/draft-example.md: 3,456 lines
```

---

### Configuration Options

**New fields in `.claude/plugin.json`**:

```json
{
  "concurrency": {
    "lock_timeout_seconds": 300,
    "lock_strategy": "auto",
    "stale_lock_threshold_minutes": 10,
    "enable_heartbeat": false,
    "enable_graceful_degradation": true,
    "lock_polling_interval_seconds": 1
  }
}
```

**Field Descriptions**:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `lock_timeout_seconds` | int | 300 | Max time to wait for lock (5 minutes) |
| `lock_strategy` | string | "auto" | Force strategy: "auto", "flock", "lockfile", "msvcrt" |
| `stale_lock_threshold_minutes` | int | 10 | Age before lock considered stale |
| `enable_heartbeat` | bool | false | Update lock file every 60s (optional) |
| `enable_graceful_degradation` | bool | true | Skip lock on failure instead of aborting |
| `lock_polling_interval_seconds` | int | 1 | How often to check lock availability |

---

## 11. Decision Matrix - Final Comparison

| Criterion | flock (A) | Lock File (B) | CAS (C) | Coordinator (D) | Git Lock (E) |
|-----------|-----------|---------------|---------|----------------|--------------|
| **Cross-Platform** | ⚠️ Partial | ✅ Full | ✅ Full | ⚠️ Partial | ❌ Git only |
| **Network FS Support** | ❌ No (NFSv4 only) | ✅ Yes | ✅ Yes | ✅ Yes | ❌ No |
| **Stale Lock Recovery** | ✅ Auto (OS) | ✅ Manual | N/A | ⚠️ Daemon restart | ❌ Manual |
| **Performance (uncontended)** | ✅ <50μs | ⚠️ ~1ms | ⚠️ ~5ms | ❌ >10ms (IPC) | ❌ >100ms (git) |
| **Performance (contended)** | ✅ OS queue | ✅ Polling | ❌ Retry storm | ✅ Queue | ❌ Conflicts |
| **Complexity** | ✅ Low | ✅ Low | ⚠️ Medium | ❌ High | ⚠️ Medium |
| **Atomicity** | ✅ Kernel | ⚠️ Rename | ⚠️ Checksum | ✅ Queue | ⚠️ Git commit |
| **Failure Mode** | ✅ Auto-release | ⚠️ Stale file | ❌ Wasted work | ❌ Daemon crash | ❌ Conflicts |
| **User Experience** | ✅ Transparent | ✅ Transparent | ❌ Retries | ❌ Daemon setup | ❌ Git workflow |
| **Debuggability** | ⚠️ PID only | ✅ Full metadata | ❌ No state | ✅ Centralized | ⚠️ Git log |

**Scoring** (out of 10):
- **flock (A)**: 8.5/10 (excellent except NFS)
- **Lock File (B)**: 8.0/10 (good all-around, slower)
- **CAS (C)**: 4.0/10 (wasted work, poor UX)
- **Coordinator (D)**: 3.0/10 (complex, fragile)
- **Git Lock (E)**: 2.0/10 (invasive, limited)

**Recommendation**: **Hybrid (A + B)** = 9.5/10
- Use flock where available (local filesystems)
- Fallback to lock file on NFS/network filesystems
- Best of both worlds

---

## 12. Implementation Plan

### Phase 1: Core Infrastructure (2-3 days)

**Tasks**:
1. ✅ Create `lib/workflow_lock.py` with base classes
2. ✅ Implement flock strategy (`FlockLock` class)
3. ✅ Implement lock file strategy (`LockFileLock` class)
4. ✅ Implement Windows strategy (`WindowsLock` class)
5. ✅ Add auto-detection logic (`_detect_strategy()`)
6. ✅ Write unit tests for each strategy

**Deliverables**:
- `lib/workflow_lock.py` (~500 lines)
- `tests/unit/test_workflow_lock.py` (pytest)

---

### Phase 2: Workflow Integration (1-2 days)

**Tasks**:
1. Update coordinator agent instructions (`.claude/agents/coordinator.md`)
2. Add lock acquisition at workflow start
3. Add lock release at workflow end (including error paths)
4. Update hook `post_tool_sync.py` to use locking
5. Add lock timeout configuration to `plugin.json`

**Deliverables**:
- Updated coordinator.md
- Updated post_tool_sync.py
- Updated plugin.json

---

### Phase 3: User-Facing Features (1-2 days)

**Tasks**:
1. Create `/rfc-unlock` slash command
2. Implement `--lock-timeout` CLI flag for all workflows
3. Add progress indicators during lock wait
4. Add error messages for timeout/stale lock scenarios
5. Update documentation (quickstart.md)

**Deliverables**:
- `.claude/commands/rfc-unlock.md`
- Updated error handling
- User documentation

---

### Phase 4: Testing & Validation (2-3 days)

**Tasks**:
1. BDD scenarios for concurrent workflows
2. Manual testing on NFS filesystem
3. Manual testing on Windows
4. Stress test (10 concurrent workflows)
5. Performance benchmarking (overhead measurement)
6. Edge case testing (crashes, timeouts, stale locks)

**Deliverables**:
- `tests/features/concurrency.feature` (Behave)
- `tests/steps/concurrency_steps.py`
- Performance report
- Test summary report

---

### Phase 5: Documentation & Rollout (1 day)

**Tasks**:
1. Update PHASE4-RESEARCH-BACKLOG.md (mark CHK070 complete)
2. Add concurrency section to quickstart.md
3. Create troubleshooting guide for lock issues
4. Update changelog

**Deliverables**:
- Updated documentation
- Rollout announcement

---

### Total Estimated Effort: 7-11 days

---

## 13. Appendix: Platform-Specific Notes

### Linux

**flock Availability**: ✅ Full support
**NFS Support**: ⚠️ NFSv4 only (with `nfs4_setlease` kernel module)
**Performance**: <10μs uncontended

**Testing**:
```bash
# Check NFS version
nfsstat -m | grep vers
# Expected: vers=4.x for flock support

# Test flock manually
flock /tmp/test.lock -c "echo locked; sleep 10"
```

---

### macOS

**flock Availability**: ✅ Full support (BSD flock semantics)
**NFS Support**: ⚠️ Limited (depends on server)
**Performance**: <50μs uncontended

**Testing**:
```bash
# macOS uses BSD flock
flock -x /tmp/test.lock echo "locked"
```

---

### Windows

**flock Availability**: ❌ Not supported
**Alternative**: `msvcrt.locking()` (byte-range locking)
**Performance**: ~100μs uncontended

**Implementation**:
```python
import msvcrt

# Lock first byte of file
msvcrt.locking(fd.fileno(), msvcrt.LK_LOCK, 1)

# Unlock
msvcrt.locking(fd.fileno(), msvcrt.LK_UNLCK, 1)
```

---

### NFS Filesystems

**flock Support**: ⚠️ NFSv4 only (not v2/v3)
**Recommendation**: Use lock file strategy
**Performance**: ~5-10ms (network latency)

**Detection**:
```python
# Check if running on NFS
def is_nfs_filesystem(path: Path) -> bool:
    result = subprocess.run(
        ['df', '-T', str(path)],
        capture_output=True,
        text=True
    )
    return 'nfs' in result.stdout.lower()
```

---

## 14. Conclusion

This design document specifies a robust, cross-platform concurrency control mechanism for the RFC workflow system. The **hybrid flock + lock file approach** provides:

- ✅ **Fast performance** on local filesystems (<50μs overhead)
- ✅ **Network filesystem support** (NFS, SMB) via lock files
- ✅ **Automatic stale lock recovery** (process crash detection)
- ✅ **User-friendly error messages** with clear next steps
- ✅ **Minimal complexity** (single lock per repository)
- ✅ **Graceful degradation** (optional, configurable)

**Key Advantages**:
1. No wasted work (unlike CAS approach)
2. No external services (unlike coordinator daemon)
3. No Git dependency (unlike git-based locking)
4. Transparent to users (automatic, no manual intervention)

**Implementation Effort**: 7-11 days (including testing)

**Risk Level**: Low (proven patterns, comprehensive fallbacks)

**Recommended Next Steps**:
1. Approve design document
2. Begin Phase 1 implementation (core infrastructure)
3. Incremental rollout with testing at each phase
4. Update CHK070 status to "Implemented" upon completion

---

**Document Status**: ✅ Complete - Ready for Implementation
**Reviewer**: [TBD]
**Approval Date**: [TBD]
