"""
Transaction manager for atomic multi-file RFC updates.

Provides BEGIN/COMMIT/ROLLBACK operations with snapshot-based recovery.
Extends Phase 3 checkpoint infrastructure for Phase 4 transactional workflows.

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

    Provides snapshot-based transaction support for /rfc-update workflows.
    Ensures multi-file operations (rfc-map.json + RFC docs) complete atomically.
    """

    def __init__(self, base_dir: Path = Path(".claude/.transactions")):
        """
        Initialize transaction manager.

        Args:
            base_dir: Base directory for transaction artifacts
        """
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

        Creates snapshots of all files before modification. Only one transaction
        can be active at a time to prevent concurrent modification conflicts.

        Args:
            files: List of file paths to include in transaction
            workflow: Workflow name (for logging)

        Returns:
            Transaction ID (unique identifier)

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

        Finalizes the transaction, cleaning up snapshot files. Only commits
        if transaction is IN_PROGRESS.

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

        Restores all files to their pre-transaction state using snapshots.
        This is the recovery mechanism for failed workflows.

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
        """
        Get current active transaction, if any.

        Returns:
            Active transaction or None
        """
        active_txns = self._get_active_transactions()
        return active_txns[0] if active_txns else None

    def cleanup_orphaned_transactions(self, max_age_hours: int = 24) -> int:
        """
        Detect and rollback orphaned transactions.

        Called on SessionStart to recover from crashes or interrupted workflows.
        Transactions older than max_age_hours are considered orphaned.

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
