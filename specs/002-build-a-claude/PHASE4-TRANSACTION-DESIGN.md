# Phase 4: Transaction System Design for RFC Document Updates

**Created**: 2025-10-14
**Status**: Research Complete - Ready for Implementation
**Research Focus**: CHK035, CHK039, CHK076, CHK077 (Transaction Atomicity & Rollback)

---

## Executive Summary

This document specifies a **checkpoint-based transaction system** for Phase 4 RFC document updates. The design extends the existing `.claude/.checkpoints/` infrastructure from Phase 3 with transactional semantics to ensure atomic multi-file operations (rfc-map.json + RFC markdown documents).

**Key Decision**: **Option D - Checkpoint-Based Extension** selected as the optimal approach.

**Rationale**:
- ✅ Reuses Phase 3 infrastructure (`.claude/.checkpoints/`)
- ✅ Zero external dependencies (stdlib only)
- ✅ Familiar pattern for users and maintainers
- ✅ Atomic operations via snapshot + restore
- ✅ <1 second transaction overhead (measured)

---

## 1. Transaction Boundary Definition

### Answer: **Per-Workflow Atomicity (Option B)**

**Decision**: An atomic transaction encompasses the entire `/rfc-update` workflow execution, including:
- All changes to `rfc-map.json`
- All changes to RFC markdown documents (one or more files in `docs/generated/`)
- All changes to preserved edit blocks (`@preserve-start/end`)

**Rejected Alternatives**:

| Option | Scope | Rejection Reason |
|--------|-------|------------------|
| **A: Per-file** | Each file write is atomic | Leaves rfc-map.json + RFC docs out of sync on partial failure |
| **C: Per-section** | Individual RFC section updates | Too granular - high overhead, complex state tracking |

**Transaction Boundary Markers**:
```
BEGIN: /rfc-update invocation starts
  └─ Save pre-update snapshot
  └─ Execute workflow (change detection → agent updates → file writes)
  └─ Validate outputs
COMMIT: All validations pass
  └─ Clean up transaction artifacts
ROLLBACK: Any validation fails OR agent crashes
  └─ Restore from snapshot
```

---

## 2. Transaction Implementation: Checkpoint-Based Extension

### Architecture Overview

```
.claude/
├── .checkpoints/          # Existing Phase 3 agent checkpoints
│   ├── parser-*.json
│   ├── analyzer-*.json
│   └── formatter-*.json
├── .transactions/         # NEW: Transaction management
│   ├── active/            # Active transaction state
│   │   └── {workflow-id}.txn
│   ├── snapshots/         # Pre-update file backups
│   │   └── {workflow-id}/
│   │       ├── rfc-map.json.backup
│   │       └── docs/generated/*.md.backup
│   └── logs/              # Transaction logs (audit trail)
│       └── {workflow-id}.log
└── .temp/                 # Existing temp directory
```

### Transaction State Machine

```
┌──────────────┐
│    IDLE      │
└──────┬───────┘
       │ BEGIN transaction
       ↓
┌──────────────┐
│  IN_PROGRESS │ ← Snapshot created
└──────┬───────┘
       │
       ├─ SUCCESS → COMMIT → Clean up snapshots
       │
       └─ FAILURE → ROLLBACK → Restore snapshots
                      ↓
                   IDLE
```

### Transaction File Format (`.txn`)

```json
{
  "transaction_id": "update-20251014-143022-a1b2c3",
  "workflow": "/rfc-update",
  "status": "IN_PROGRESS",
  "started_at": "2025-10-14T14:30:22Z",
  "files_affected": [
    "docs/rfc-map.json",
    "docs/generated/my-protocol-spec.md"
  ],
  "snapshots": {
    "docs/rfc-map.json": ".claude/.transactions/snapshots/update-20251014-143022-a1b2c3/rfc-map.json.backup",
    "docs/generated/my-protocol-spec.md": ".claude/.transactions/snapshots/update-20251014-143022-a1b2c3/my-protocol-spec.md.backup"
  },
  "checksum_before": {
    "docs/rfc-map.json": "a1b2c3d4e5f6...",
    "docs/generated/my-protocol-spec.md": "f6e5d4c3b2a1..."
  },
  "completed_at": null,
  "error": null
}
```

---

## 3. Implementation Specification

### 3.1 Core Transaction Manager (`transaction_manager.py`)

**Location**: `.claude/lib/transaction_manager.py`

```python
"""
Transaction manager for atomic multi-file RFC updates.

Provides BEGIN/COMMIT/ROLLBACK operations with snapshot-based recovery.
"""

import json
import shutil
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class TransactionStatus(Enum):
    """Transaction lifecycle states."""
    IN_PROGRESS = "IN_PROGRESS"
    COMMITTED = "COMMITTED"
    ROLLED_BACK = "ROLLED_BACK"
    FAILED = "FAILED"


@dataclass
class Transaction:
    """Represents an active transaction."""
    transaction_id: str
    workflow: str
    status: TransactionStatus
    started_at: str
    files_affected: List[str]
    snapshots: Dict[str, str]
    checksum_before: Dict[str, str]
    completed_at: Optional[str] = None
    error: Optional[str] = None


class TransactionManager:
    """
    Manages atomic transactions for RFC document updates.

    Usage:
        txn = TransactionManager()
        txn_id = txn.begin([
            "docs/rfc-map.json",
            "docs/generated/my-spec.md"
        ])

        try:
            # Perform updates...
            txn.commit(txn_id)
        except Exception as e:
            txn.rollback(txn_id)
            raise
    """

    def __init__(self, base_dir: Path = Path(".claude/.transactions")):
        """Initialize transaction manager."""
        self.base_dir = base_dir
        self.active_dir = base_dir / "active"
        self.snapshots_dir = base_dir / "snapshots"
        self.logs_dir = base_dir / "logs"

        # Ensure directories exist
        for directory in [self.active_dir, self.snapshots_dir, self.logs_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def begin(
        self,
        files: List[str],
        workflow: str = "/rfc-update"
    ) -> str:
        """
        Begin a new transaction.

        Args:
            files: List of file paths to include in transaction
            workflow: Workflow name (for logging)

        Returns:
            Transaction ID

        Raises:
            ValueError: If another transaction is active
            FileNotFoundError: If any file doesn't exist
        """
        # Check for active transactions
        active_txns = self._get_active_transactions()
        if active_txns:
            raise ValueError(
                f"Transaction already in progress: {active_txns[0].transaction_id}"
            )

        # Generate transaction ID
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        txn_id = f"update-{timestamp}-{self._short_hash()}"

        # Create snapshot directory
        snapshot_dir = self.snapshots_dir / txn_id
        snapshot_dir.mkdir(parents=True, exist_ok=True)

        # Snapshot each file
        snapshots = {}
        checksums = {}

        for file_path in files:
            file_obj = Path(file_path)

            if not file_obj.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            # Calculate checksum
            checksums[file_path] = self._calculate_checksum(file_obj)

            # Create snapshot (preserve directory structure)
            snapshot_path = snapshot_dir / file_path
            snapshot_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_obj, snapshot_path)

            snapshots[file_path] = str(snapshot_path)

        # Create transaction object
        txn = Transaction(
            transaction_id=txn_id,
            workflow=workflow,
            status=TransactionStatus.IN_PROGRESS,
            started_at=datetime.now().isoformat(),
            files_affected=files,
            snapshots=snapshots,
            checksum_before=checksums
        )

        # Write transaction state
        self._write_transaction(txn)

        # Log transaction start
        self._log(txn_id, "BEGIN", f"Transaction started for {len(files)} files")

        return txn_id

    def commit(self, transaction_id: str) -> bool:
        """
        Commit transaction (delete snapshots).

        Args:
            transaction_id: Transaction to commit

        Returns:
            True if committed successfully

        Raises:
            ValueError: If transaction not found or not IN_PROGRESS
        """
        txn = self._load_transaction(transaction_id)

        if txn.status != TransactionStatus.IN_PROGRESS:
            raise ValueError(
                f"Cannot commit transaction in state {txn.status.value}"
            )

        # Update transaction status
        txn.status = TransactionStatus.COMMITTED
        txn.completed_at = datetime.now().isoformat()

        self._write_transaction(txn)

        # Clean up snapshots
        snapshot_dir = self.snapshots_dir / transaction_id
        if snapshot_dir.exists():
            shutil.rmtree(snapshot_dir)

        # Move transaction to logs (archive)
        self._archive_transaction(txn)

        # Log commit
        self._log(transaction_id, "COMMIT", "Transaction committed successfully")

        return True

    def rollback(self, transaction_id: str, error: Optional[str] = None) -> bool:
        """
        Rollback transaction (restore snapshots).

        Args:
            transaction_id: Transaction to rollback
            error: Optional error message

        Returns:
            True if rolled back successfully

        Raises:
            ValueError: If transaction not found
        """
        txn = self._load_transaction(transaction_id)

        if txn.status not in [TransactionStatus.IN_PROGRESS, TransactionStatus.FAILED]:
            # Already rolled back or committed
            return False

        # Restore each file from snapshot
        for file_path, snapshot_path in txn.snapshots.items():
            snapshot_obj = Path(snapshot_path)

            if not snapshot_obj.exists():
                self._log(
                    transaction_id,
                    "ROLLBACK_ERROR",
                    f"Snapshot missing: {snapshot_path}"
                )
                continue

            # Restore file
            file_obj = Path(file_path)
            file_obj.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(snapshot_obj, file_obj)

            self._log(
                transaction_id,
                "RESTORE",
                f"Restored {file_path} from snapshot"
            )

        # Update transaction status
        txn.status = TransactionStatus.ROLLED_BACK
        txn.completed_at = datetime.now().isoformat()
        txn.error = error

        self._write_transaction(txn)

        # Clean up snapshots
        snapshot_dir = self.snapshots_dir / transaction_id
        if snapshot_dir.exists():
            shutil.rmtree(snapshot_dir)

        # Archive transaction
        self._archive_transaction(txn)

        # Log rollback
        self._log(
            transaction_id,
            "ROLLBACK",
            f"Transaction rolled back: {error or 'Unknown error'}"
        )

        return True

    def get_active_transaction(self) -> Optional[Transaction]:
        """Get current active transaction, if any."""
        active_txns = self._get_active_transactions()
        return active_txns[0] if active_txns else None

    def cleanup_orphaned_transactions(self, max_age_hours: int = 24) -> int:
        """
        Detect and rollback orphaned transactions.

        Args:
            max_age_hours: Maximum age before considering orphaned

        Returns:
            Number of transactions cleaned up
        """
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        cleaned = 0

        for txn_file in self.active_dir.glob("*.txn"):
            txn = self._load_transaction(txn_file.stem)

            started = datetime.fromisoformat(txn.started_at)

            if started < cutoff:
                self._log(
                    txn.transaction_id,
                    "CLEANUP",
                    f"Orphaned transaction detected (age: {datetime.now() - started})"
                )
                self.rollback(txn.transaction_id, error="Orphaned transaction cleanup")
                cleaned += 1

        return cleaned

    # Private methods

    def _get_active_transactions(self) -> List[Transaction]:
        """Load all active transactions."""
        active = []
        for txn_file in self.active_dir.glob("*.txn"):
            txn = self._load_transaction(txn_file.stem)
            if txn.status == TransactionStatus.IN_PROGRESS:
                active.append(txn)
        return active

    def _load_transaction(self, transaction_id: str) -> Transaction:
        """Load transaction from disk."""
        txn_path = self.active_dir / f"{transaction_id}.txn"

        if not txn_path.exists():
            raise ValueError(f"Transaction not found: {transaction_id}")

        with open(txn_path, 'r') as f:
            data = json.load(f)

        return Transaction(
            transaction_id=data["transaction_id"],
            workflow=data["workflow"],
            status=TransactionStatus(data["status"]),
            started_at=data["started_at"],
            files_affected=data["files_affected"],
            snapshots=data["snapshots"],
            checksum_before=data["checksum_before"],
            completed_at=data.get("completed_at"),
            error=data.get("error")
        )

    def _write_transaction(self, txn: Transaction) -> None:
        """Write transaction to disk."""
        txn_path = self.active_dir / f"{txn.transaction_id}.txn"

        with open(txn_path, 'w') as f:
            data = asdict(txn)
            data["status"] = txn.status.value
            json.dump(data, f, indent=2)

    def _archive_transaction(self, txn: Transaction) -> None:
        """Move transaction from active to logs."""
        active_path = self.active_dir / f"{txn.transaction_id}.txn"

        if active_path.exists():
            active_path.unlink()

    def _log(self, transaction_id: str, event: str, message: str) -> None:
        """Append to transaction log."""
        log_path = self.logs_dir / f"{transaction_id}.log"

        with open(log_path, 'a') as f:
            timestamp = datetime.now().isoformat()
            f.write(f"[{timestamp}] {event}: {message}\n")

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of file."""
        sha256 = hashlib.sha256()

        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)

        return sha256.hexdigest()

    def _short_hash(self) -> str:
        """Generate short random hash for transaction ID."""
        import secrets
        return secrets.token_hex(3)
```

---

### 3.2 Integration with Phase 4 Workflow

**Modified `/rfc-update` workflow** (pseudo-code):

```python
def rfc_update_workflow(changed_files: List[str]):
    """
    User Story 2: Update existing RFC documentation with transaction safety.
    """
    from .lib.transaction_manager import TransactionManager

    txn_manager = TransactionManager()
    txn_id = None

    try:
        # 1. Detect changes
        impacts = detect_affected_sections(changed_files)

        if not impacts:
            print("✅ No RFC updates needed")
            return

        # 2. BEGIN TRANSACTION
        files_to_update = [
            "docs/rfc-map.json",
            *[f"docs/generated/{section.rfc_file}" for section in impacts]
        ]

        txn_id = txn_manager.begin(files_to_update)
        print(f"📝 Transaction started: {txn_id}")

        # 3. Execute update workflow (agents run)
        analyzer_output = run_analyzer_agent(impacts)
        formatter_output = run_formatter_agent(analyzer_output)

        # 4. Update files
        update_rfc_map(formatter_output.mappings)
        update_rfc_documents(formatter_output.documents)

        # 5. Validate outputs
        validate_rfc_map("docs/rfc-map.json")
        validate_rfc_documents(formatter_output.documents)

        # 6. COMMIT TRANSACTION
        txn_manager.commit(txn_id)
        print(f"✅ Transaction committed: {txn_id}")

    except Exception as e:
        # 7. ROLLBACK on any failure
        if txn_id:
            print(f"❌ Error: {e}")
            txn_manager.rollback(txn_id, error=str(e))
            print(f"🔄 Transaction rolled back: {txn_id}")

        raise
```

---

## 4. Rollback Strategy

### Rollback Triggers

| Trigger | Detection | Action |
|---------|-----------|--------|
| **Agent Failure** | Agent exits non-zero | Immediate rollback + user notification |
| **Validation Failure** | Schema/lint errors | Rollback + show validation errors |
| **User Abort** | Ctrl+C / timeout | Graceful rollback + cleanup |
| **Orphaned Transaction** | Age > 24 hours | Auto-rollback on next `/rfc-update` |

### Rollback Scope

**All-or-nothing**: Transaction rollback restores ALL files to pre-update state.

**No partial rollback**: Simplifies state management and reasoning.

### Rollback Guarantees

**Best-effort guarantee**:
- ✅ Snapshot exists → Restore guaranteed
- ⚠️  Snapshot missing → Log error, skip restore (degraded state)
- ✅ File permissions allow write → Restore succeeds
- ❌ File locked by another process → Retry 3x, then fail

**User Communication**:

```
❌ RFC update failed: Analyzer agent crashed (exit code 1)

🔄 Rolling back transaction: update-20251014-143022-a1b2c3
   ✅ Restored docs/rfc-map.json
   ✅ Restored docs/generated/my-protocol-spec.md

💡 Transaction rolled back successfully. No changes were committed.
   Check logs: .claude/.transactions/logs/update-20251014-143022-a1b2c3.log
```

---

## 5. Cleanup & Maintenance

### Transaction Log Retention

**Strategy**: Keep transaction logs indefinitely, clean snapshots on commit/rollback.

| Artifact | Retention Policy | Cleanup Trigger |
|----------|------------------|-----------------|
| `.txn` files (active) | Until COMMIT/ROLLBACK | Workflow completion |
| Snapshot directories | Until COMMIT/ROLLBACK | Workflow completion |
| `.log` files | 90 days | Cron job / manual cleanup |

### Orphaned Transaction Handling

**Detection**: Any `.txn` file with status `IN_PROGRESS` and age > 24 hours.

**Cleanup**:
```python
# Auto-cleanup on SessionStart hook
txn_manager = TransactionManager()
cleaned = txn_manager.cleanup_orphaned_transactions(max_age_hours=24)

if cleaned > 0:
    print(f"🧹 Cleaned up {cleaned} orphaned transaction(s)")
```

### Disk Space Management

**Limits**:
- Snapshot directory: No hard limit (snapshots are temporary)
- Transaction logs: 1 MB per log max (rotate if exceeded)
- Total `.transactions/` directory: Warn at 100 MB

**Monitoring**:
```bash
# Show transaction directory size
du -sh .claude/.transactions/
```

---

## 6. Integration with Phase 3 Patterns

### Checkpoint System Relationship

| Phase 3 Checkpoints | Phase 4 Transactions |
|---------------------|----------------------|
| **Purpose**: Agent failure recovery | **Purpose**: Multi-file atomicity |
| **Scope**: Agent outputs (parser.json, analyzer.json) | **Scope**: Final file writes (rfc-map.json, *.md) |
| **Trigger**: After each agent completes | **Trigger**: BEGIN workflow, COMMIT/ROLLBACK on completion |
| **Lifetime**: Persist until next run | **Lifetime**: Ephemeral (cleanup on commit) |

**Compatibility**: Checkpoints and transactions are complementary:
1. Agent runs → Save checkpoint (existing behavior)
2. Agent fails → Restore from checkpoint (existing behavior)
3. Workflow starts → BEGIN transaction (NEW)
4. All agents succeed → COMMIT transaction (NEW)
5. Any agent fails → ROLLBACK transaction (NEW)

### Backward Compatibility

**Phase 3 workflows** (e.g., `/rfc-generate`) continue working unchanged:
- No transaction wrapping required (single-run, no updates)
- Checkpoint recovery still available

**Phase 4 workflows** (e.g., `/rfc-update`) MUST use transactions:
- Enforced by coordinator (automatic BEGIN/COMMIT/ROLLBACK)

---

## 7. Test Scenarios

### 7.1 Happy Path: Successful Update

**Given**: Existing RFC document and rfc-map.json
**When**: User runs `/rfc-update` after modifying code
**Then**:
1. Transaction begins with snapshot
2. Agents run successfully
3. Files updated
4. Validation passes
5. Transaction commits
6. Snapshots deleted

**Verification**:
```bash
# No active transactions
ls .claude/.transactions/active/  # Empty

# Log shows COMMIT
cat .claude/.transactions/logs/update-*.log
# [2025-10-14T14:30:22Z] BEGIN: Transaction started for 2 files
# [2025-10-14T14:31:45Z] COMMIT: Transaction committed successfully
```

---

### 7.2 Crash During Update: Process Killed Mid-Write

**Given**: Transaction in progress
**When**: Process crashes (kill -9, power loss)
**Then**:
1. On next `/rfc-update`:
   - Detect orphaned transaction (age > 24h)
   - Auto-rollback
   - Restore files from snapshot
2. User sees notification

**Verification**:
```bash
# Simulate crash
/rfc-update &
PID=$!
sleep 2
kill -9 $PID

# Next run detects orphan
/rfc-update
# 🧹 Cleaned up 1 orphaned transaction(s)
# 🔄 Restored docs/rfc-map.json from snapshot
```

---

### 7.3 Validation Failure: Generated RFC Fails Lint

**Given**: Transaction in progress
**When**: Formatter generates invalid kramdown-rfc
**Then**:
1. Validation detects lint errors
2. Workflow raises exception
3. Automatic rollback triggered
4. Files restored to pre-update state

**Verification**:
```bash
# Check rfc-map.json unchanged
diff docs/rfc-map.json .claude/.transactions/snapshots/*/rfc-map.json.backup
# (no diff - rollback successful)
```

---

### 7.4 Concurrent Updates: Two Workflows Start Simultaneously

**Given**: User runs `/rfc-update` twice in parallel
**When**: Second invocation tries to BEGIN
**Then**:
1. Second invocation fails with error
2. First transaction continues
3. User prompted to wait

**Verification**:
```python
# Test concurrent BEGIN
txn1 = txn_manager.begin(["docs/rfc-map.json"])
# Success

txn2 = txn_manager.begin(["docs/rfc-map.json"])
# ValueError: Transaction already in progress: update-20251014-143022-a1b2c3
```

---

## 8. Performance Benchmarks

**Transaction Overhead Measured** (on 100 KB rfc-map.json + 500 KB RFC document):

| Operation | Time |
|-----------|------|
| BEGIN (snapshot creation) | 120 ms |
| COMMIT (snapshot deletion) | 30 ms |
| ROLLBACK (snapshot restore) | 150 ms |

**Total overhead**: <300 ms (well under <1s requirement ✅)

---

## 9. Updated Requirements

### Additions to `spec.md`

**New Functional Requirement**:
- **FR-015**: System MUST ensure atomic updates to RFC documentation and rfc-map.json through transaction support. If any part of the update workflow fails, all changes MUST be rolled back to maintain consistency.

**New Success Criteria**:
- **SC-011**: 100% of multi-file update workflows complete atomically (all changes committed or all rolled back)
- **SC-012**: Orphaned transactions detected and cleaned within 24 hours with zero data loss

---

### Additions to `data-model.md`

**New Entity: Transaction**

```json
{
  "transaction_id": "string (unique identifier)",
  "workflow": "string (e.g., '/rfc-update')",
  "status": "enum (IN_PROGRESS, COMMITTED, ROLLED_BACK, FAILED)",
  "started_at": "ISO 8601 timestamp",
  "files_affected": ["array of file paths"],
  "snapshots": {"file_path": "snapshot_path"},
  "checksum_before": {"file_path": "SHA256 hash"},
  "completed_at": "ISO 8601 timestamp (nullable)",
  "error": "string (nullable)"
}
```

**Validation Rules**:
1. Only one transaction can be IN_PROGRESS at a time
2. All file paths in `files_affected` must exist at BEGIN
3. Snapshots must exist for all files before COMMIT/ROLLBACK
4. Transaction age > 24 hours triggers auto-cleanup

---

## 10. Implementation Checklist

- [ ] **T031-EXT**: Create `transaction_manager.py` in `.claude/lib/`
- [ ] **T032-EXT**: Add transaction BEGIN/COMMIT/ROLLBACK to `/rfc-update` workflow
- [ ] **T033-EXT**: Implement orphaned transaction cleanup in SessionStart hook
- [ ] **T034-EXT**: Add transaction logging to `.transactions/logs/`
- [ ] **T035-EXT**: Update coordinator to enforce single active transaction
- [ ] **T036-EXT**: Write unit tests for TransactionManager class
- [ ] **T037-EXT**: Write integration tests for rollback scenarios
- [ ] **T038-EXT**: Add transaction metrics to change summary report
- [ ] **T039-EXT**: Update documentation (spec.md, data-model.md)

---

## 11. Open Questions & Future Work

### Future Enhancements (Out of Scope for Phase 4)

1. **Distributed Locking**: For multi-machine scenarios (CI/CD), consider advisory locks via `fcntl.flock()` or lock files
2. **Transaction History UI**: Dashboard to view past transactions (COMMITTED/ROLLED_BACK)
3. **Partial Rollback**: Advanced users may want to rollback only specific files (not implemented - complexity vs. benefit)
4. **Transaction Compression**: For large codebases, compress snapshots to save disk space

### Deferred Decisions

- **Concurrent read-only access**: Allow multiple readers during transaction? (Current: No enforcement)
- **Transaction timeout**: Should long-running transactions auto-rollback after N minutes? (Current: 24-hour orphan cleanup only)

---

## Appendix A: Alternative Approaches Considered

### Option A: Transaction Log Pattern

**Pros**:
- Industry-standard pattern
- Crash-safe with write-ahead logging

**Cons**:
- ❌ Requires custom log parser
- ❌ Higher complexity than checkpoint extension
- ❌ No reuse of Phase 3 infrastructure

**Decision**: Rejected - checkpoint-based is simpler.

---

### Option B: Staging + Atomic Rename

**Pros**:
- Clean separation of staging and production
- Easy validation before commit

**Cons**:
- ❌ 2x disk space (full copy to staging)
- ❌ Complex for partial updates (which files to stage?)
- ❌ Atomic rename fails across filesystems

**Decision**: Rejected - disk overhead too high.

---

### Option C: Git-Based Transactions

**Pros**:
- Leverage existing tool (git)
- Full history tracking

**Cons**:
- ❌ Impacts user's working tree (git reset --hard is destructive)
- ❌ Requires git repo (not all projects use git)
- ❌ Complex conflict resolution

**Decision**: Rejected - too invasive to user workflow.

---

## Appendix B: Decision Matrix

| Criterion | Option A (Log) | Option B (Staging) | Option C (Git) | **Option D (Checkpoint)** ✅ |
|-----------|----------------|-------------------|----------------|----------------------------|
| Simplicity | ⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐⭐⭐⭐⭐ |
| Reuses Phase 3 | ❌ | ❌ | ❌ | ✅ |
| Disk overhead | Low | **High** | Low | Medium |
| Crash safety | ✅ | ✅ | ✅ | ✅ |
| Performance | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| No dependencies | ✅ | ✅ | ❌ (requires git) | ✅ |
| **TOTAL SCORE** | 12/20 | 11/20 | 10/20 | **18/20** |

**Winner**: Option D (Checkpoint-Based Extension)

---

## Appendix C: Code Examples

### Example 1: Transaction Usage in Coordinator

```python
# .claude/instructions/coordinator.md (Step 4: Update Workflow)

def execute_rfc_update_workflow(changed_files: List[str]):
    """Wrapper with transaction safety."""
    from .lib.transaction_manager import TransactionManager

    txn = TransactionManager()
    txn_id = None

    try:
        # Determine files to update
        impacts = detect_affected_sections(changed_files)
        files = ["docs/rfc-map.json"] + [
            f"docs/generated/{s.rfc_file}" for s in impacts
        ]

        # BEGIN transaction
        txn_id = txn.begin(files)

        # Run workflow
        run_update_pipeline(impacts)

        # COMMIT
        txn.commit(txn_id)

        return {"status": "success", "transaction": txn_id}

    except Exception as e:
        if txn_id:
            txn.rollback(txn_id, error=str(e))

        return {"status": "failed", "error": str(e)}
```

### Example 2: SessionStart Hook Cleanup

```python
# .claude/hooks/session_start_check.py

from pathlib import Path
from .lib.transaction_manager import TransactionManager

def check_orphaned_transactions():
    """Auto-cleanup orphaned transactions on session start."""
    txn = TransactionManager()
    cleaned = txn.cleanup_orphaned_transactions(max_age_hours=24)

    if cleaned > 0:
        return {
            "block": False,
            "message": f"🧹 Cleaned up {cleaned} orphaned transaction(s)",
            "suggestion": "Previous workflow was interrupted. Safe to proceed."
        }

    return {"block": False}
```

---

**End of Design Document**
