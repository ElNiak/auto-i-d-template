# Phase 4: Transaction System - Quick Implementation Guide

**For**: Developers implementing Phase 4 User Story 2
**Prerequisites**: Read `PHASE4-TRANSACTION-DESIGN.md` for full specification
**Estimated Time**: 8-12 hours (with testing)

---

## Implementation Checklist

### Step 1: Core Library (2-3 hours)

- [ ] **Create `transaction_manager.py`**
  - Location: `.claude/lib/transaction_manager.py`
  - Copy implementation from `PHASE4-TRANSACTION-DESIGN.md` Section 3.1
  - 200 lines of code (LOC)
  - Dependencies: `json`, `shutil`, `hashlib`, `pathlib` (stdlib only)

- [ ] **Create directory structure**
  ```bash
  mkdir -p .claude/.transactions/{active,snapshots,logs}
  ```

- [ ] **Test basic operations**
  ```python
  # Quick smoke test
  from .claude.lib.transaction_manager import TransactionManager

  txn = TransactionManager()
  txn_id = txn.begin(["docs/rfc-map.json"])
  # ... modify file ...
  txn.commit(txn_id)  # or txn.rollback(txn_id)
  ```

---

### Step 2: Workflow Integration (2-3 hours)

- [ ] **Update `/rfc-update` command**
  - Location: `.claude/commands/rfc-update.md` (create new command)
  - Add transaction wrapping (see Section 3.2 in design doc)
  - Pattern:
    ```python
    txn_id = txn_manager.begin(files)
    try:
        run_update_workflow()
        txn_manager.commit(txn_id)
    except Exception as e:
        txn_manager.rollback(txn_id, error=str(e))
        raise
    ```

- [ ] **Update coordinator instructions**
  - Location: `.claude/instructions/coordinator.md`
  - Add Step 0: "BEGIN transaction before updates"
  - Add Step 6: "COMMIT transaction after validation"
  - Add error handling: "ROLLBACK on any failure"

---

### Step 3: Hooks Integration (1-2 hours)

- [ ] **Add orphaned transaction cleanup**
  - Location: `.claude/hooks/session_start_check.py`
  - Add at start of hook:
    ```python
    from .lib.transaction_manager import TransactionManager

    txn = TransactionManager()
    cleaned = txn.cleanup_orphaned_transactions(max_age_hours=24)

    if cleaned > 0:
        return {
            "block": False,
            "message": f"🧹 Cleaned up {cleaned} orphaned transaction(s)"
        }
    ```

- [ ] **Add transaction logging to hook history**
  - Update `.claude/.hook-history.json` format to include transaction IDs

---

### Step 4: Unit Tests (2-3 hours)

**Location**: `tests/unit/test_transaction_manager.py` (create new file)

- [ ] **Test 1: Happy path (BEGIN → COMMIT)**
  ```python
  def test_begin_commit():
      txn = TransactionManager()
      txn_id = txn.begin(["test-file.txt"])
      assert txn.get_active_transaction() is not None
      txn.commit(txn_id)
      assert txn.get_active_transaction() is None
  ```

- [ ] **Test 2: Rollback restores files**
  ```python
  def test_rollback_restores():
      # Create file with original content
      # BEGIN transaction
      # Modify file
      # ROLLBACK
      # Assert file has original content
  ```

- [ ] **Test 3: Concurrent transactions fail**
  ```python
  def test_concurrent_transactions_blocked():
      txn = TransactionManager()
      txn_id1 = txn.begin(["file1.txt"])

      with pytest.raises(ValueError, match="already in progress"):
          txn_id2 = txn.begin(["file2.txt"])
  ```

- [ ] **Test 4: Orphaned transaction cleanup**
  ```python
  def test_cleanup_orphaned():
      # Create transaction with old timestamp
      # Run cleanup
      # Assert transaction rolled back
  ```

- [ ] **Test 5: Checksum validation**
  ```python
  def test_checksum_detection():
      # BEGIN transaction
      # Modify file outside transaction
      # Assert checksum mismatch detected
  ```

- [ ] **Test 6: Transaction log creation**
  ```python
  def test_transaction_logging():
      txn_id = txn.begin(["file.txt"])
      log_path = Path(f".claude/.transactions/logs/{txn_id}.log")
      assert log_path.exists()
  ```

---

### Step 5: Integration Tests (2-3 hours)

**Location**: `tests/features/update.feature` (create new BDD feature)

- [ ] **Scenario 1: Successful update with transaction**
  ```gherkin
  Scenario: Update RFC documentation with transaction safety
    Given an existing RFC document "my-spec.md"
    And rfc-map.json exists with 5 mappings
    When I run "/rfc-update" after modifying code
    Then the transaction commits successfully
    And rfc-map.json is updated atomically
    And the RFC document is updated atomically
    And no snapshot files remain in .transactions/snapshots/
  ```

- [ ] **Scenario 2: Validation failure triggers rollback**
  ```gherkin
  Scenario: RFC update validation fails
    Given an existing RFC document
    When I run "/rfc-update" and validation fails
    Then the transaction rolls back automatically
    And rfc-map.json is unchanged
    And the RFC document is unchanged
    And I see a rollback confirmation message
  ```

- [ ] **Scenario 3: Orphaned transaction cleanup**
  ```gherkin
  Scenario: Orphaned transaction detected on session start
    Given a transaction that was interrupted 25 hours ago
    When I start a new Claude Code session
    Then the orphaned transaction is detected
    And files are restored from snapshots
    And I see a cleanup notification
  ```

- [ ] **Scenario 4: Concurrent update attempts blocked**
  ```gherkin
  Scenario: Concurrent RFC updates are prevented
    Given a transaction is in progress
    When I attempt to start another "/rfc-update"
    Then I receive an error "transaction already in progress"
    And the second update does not start
  ```

---

### Step 6: Documentation Updates (1 hour)

- [ ] **Update `spec.md`**
  - Add FR-015 (atomic updates requirement)
  - Add SC-011 (atomicity success criteria)
  - Add SC-012 (orphaned transaction cleanup)

- [ ] **Update `data-model.md`**
  - Add Transaction entity schema
  - Add validation rules for transactions
  - Add transaction lifecycle state machine

- [ ] **Update `README.md`** (if exists in project root)
  - Add section on transaction safety
  - Add troubleshooting guide for rollback scenarios

- [ ] **Create user guide**: `docs/transaction-system-guide.md`
  - How transactions work (user-facing explanation)
  - What to do if rollback occurs
  - How to inspect transaction logs

---

## Quick Reference: Key Files

### Core Implementation

```
.claude/lib/transaction_manager.py          # Core transaction logic (200 LOC)
```

### Integration Points

```
.claude/commands/rfc-update.md              # Workflow with transactions
.claude/instructions/coordinator.md         # Add BEGIN/COMMIT/ROLLBACK steps
.claude/hooks/session_start_check.py        # Orphaned cleanup
```

### Test Files

```
tests/unit/test_transaction_manager.py      # Unit tests (6 tests)
tests/features/update.feature               # BDD integration tests (4 scenarios)
tests/steps/update_steps.py                 # Step implementations
```

### Documentation

```
specs/002-build-a-claude/spec.md            # Updated requirements
specs/002-build-a-claude/data-model.md      # Transaction entity
docs/transaction-system-guide.md            # User guide
```

---

## Common Pitfalls to Avoid

### ❌ Don't: Create transactions for read-only workflows
```python
# BAD: /rfc-generate doesn't need transactions (creates new files)
txn_id = txn.begin(["docs/new-spec.md"])
```

### ✅ Do: Only use transactions for updates
```python
# GOOD: /rfc-update modifies existing files
txn_id = txn.begin(["docs/rfc-map.json", "docs/existing-spec.md"])
```

---

### ❌ Don't: Forget to handle exceptions
```python
# BAD: No rollback on failure
txn_id = txn.begin(files)
run_workflow()
txn.commit(txn_id)
```

### ✅ Do: Always use try/except
```python
# GOOD: Rollback on any exception
txn_id = txn.begin(files)
try:
    run_workflow()
    txn.commit(txn_id)
except Exception as e:
    txn.rollback(txn_id, error=str(e))
    raise
```

---

### ❌ Don't: Modify files outside transaction scope
```python
# BAD: File not in transaction
txn_id = txn.begin(["docs/rfc-map.json"])
update_file("docs/other-file.md")  # Not tracked!
txn.commit(txn_id)
```

### ✅ Do: Include all affected files in transaction
```python
# GOOD: All files in transaction
txn_id = txn.begin([
    "docs/rfc-map.json",
    "docs/other-file.md"
])
update_files()
txn.commit(txn_id)
```

---

### ❌ Don't: Leave snapshots on disk
```python
# BAD: Snapshots remain after commit
txn.commit(txn_id)
# .transactions/snapshots/{txn_id}/ still exists!
```

### ✅ Do: TransactionManager handles cleanup automatically
```python
# GOOD: Snapshots deleted in commit()
txn.commit(txn_id)
# Snapshots automatically cleaned up ✅
```

---

## Performance Optimization Tips

### 1. Minimize Files in Transaction
```python
# GOOD: Only include changed files
impacts = detect_affected_sections()
files = ["docs/rfc-map.json"] + [s.rfc_file for s in impacts]
txn_id = txn.begin(files)

# BAD: Include all RFC files (slow snapshots)
txn_id = txn.begin(glob("docs/generated/*.md"))
```

### 2. Use Checksum Validation Sparingly
```python
# Checksums calculated at BEGIN (automatic)
# Don't recalculate manually - trust snapshots
```

### 3. Cleanup Old Logs Periodically
```bash
# Weekly cron job
find .claude/.transactions/logs/ -mtime +90 -delete
```

---

## Debugging Checklist

### Transaction Won't Begin

- [ ] Check for active transaction: `ls .claude/.transactions/active/`
- [ ] Check file permissions: Ensure files are writable
- [ ] Check disk space: `df -h`

### Rollback Failed

- [ ] Verify snapshots exist: `ls .claude/.transactions/snapshots/{txn-id}/`
- [ ] Check transaction log: `cat .claude/.transactions/logs/{txn-id}.log`
- [ ] Manually restore: `cp .claude/.transactions/snapshots/{txn-id}/... docs/`

### Orphaned Transaction Not Cleaned

- [ ] Check transaction age: Must be > 24 hours
- [ ] Verify SessionStart hook runs: Check `.claude/.hook-logs/session_start_check.log`
- [ ] Manually trigger cleanup:
  ```python
  from .claude.lib.transaction_manager import TransactionManager
  txn = TransactionManager()
  txn.cleanup_orphaned_transactions(max_age_hours=0)  # Force cleanup
  ```

---

## Success Criteria Verification

After implementation, verify:

- [ ] **SC-011**: Run 10 `/rfc-update` workflows → 100% commit or rollback (no partial states)
- [ ] **SC-012**: Interrupt workflow → Wait 24h → SessionStart detects orphan → Auto-rollback
- [ ] **Performance**: Transaction overhead < 1 second (measure with `time` command)
- [ ] **Backward Compatibility**: `/rfc-generate` still works without transactions
- [ ] **User Experience**: Rollback messages are clear and actionable

---

## Example Workflow: Full Transaction Lifecycle

```bash
# 1. User modifies code
vim src/api.py

# 2. Run update
/rfc-update

# Output:
# 📝 Detecting changes...
# 🔍 Found 3 affected sections
# 📝 Transaction started: update-20251014-143022-a1b2c3
# 🤖 Running analyzer agent...
# ✅ Analyzer complete
# 🤖 Running formatter agent...
# ✅ Formatter complete
# ✔️  Validating outputs...
# ✅ Validation passed
# 💾 Updating files...
#    - docs/rfc-map.json (12 mappings updated)
#    - docs/generated/my-protocol-spec.md (Section 3.2 updated)
# ✅ Transaction committed: update-20251014-143022-a1b2c3

# 3. Verify transaction cleaned up
ls .claude/.transactions/active/
# (empty - transaction completed)

ls .claude/.transactions/logs/
# update-20251014-143022-a1b2c3.log (audit trail)
```

---

## Getting Help

- **Design Questions**: Review `PHASE4-TRANSACTION-DESIGN.md`
- **Implementation Questions**: Review `PHASE4-RESEARCH-SUMMARY.md`
- **Test Failures**: Check `.claude/.transactions/logs/` for transaction logs
- **Performance Issues**: Benchmark with small files first, then scale up

---

**Ready to implement!** Start with Step 1 (Core Library) and work sequentially through the checklist.

**Estimated Timeline**:
- Day 1: Steps 1-2 (Core library + workflow integration)
- Day 2: Steps 3-4 (Hooks + unit tests)
- Day 3: Steps 5-6 (Integration tests + documentation)

**Total**: 3 days (or 1 day if working full-time on this feature)

---

**END OF IMPLEMENTATION GUIDE**
