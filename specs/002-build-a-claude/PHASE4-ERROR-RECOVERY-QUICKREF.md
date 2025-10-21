# Phase 4: Error Recovery System - Quick Reference

**For**: Implementers of CHK074 (Error recovery across pipeline)
**See**: `PHASE4-ERROR-RECOVERY-DESIGN.md` for full specification

---

## TL;DR

- **What**: Automatic retry + rollback for RFC pipeline failures
- **Why**: 95% of transient errors recover automatically (no user intervention)
- **How**: Exponential backoff retry → Transaction-based rollback → Artifact cleanup
- **Overhead**: <1% for successful workflows

---

## Quick Decision Matrix

| If Error Is... | Action | Retries | User Impact |
|---------------|--------|---------|-------------|
| **Network timeout** | Retry with exponential backoff | 3x (2s, 4s, 8s) | Transparent recovery |
| **File lock** | Retry with linear backoff | 5x (1s intervals) | Brief delay |
| **Syntax error** | Abort immediately | 0 | Error report with fix suggestions |
| **Permission denied** | Abort immediately | 0 | Check permissions message |
| **Unknown error** | Retry once conservatively | 1x | Cautious recovery attempt |

---

## Key Implementation Points

### 1. Error Classification (Section 1)

```python
from error_recovery import classify_error

# Returns: (classification, max_retries, reason)
classification, retries, reason = classify_error(
    error=caught_exception,
    context={'agent_type': 'parser', 'previous_success': True}
)
```

**3 Categories**:
- `"transient"` → Retry (network, locks, memory)
- `"permanent"` → Abort (syntax, permissions, config)
- `"ambiguous"` → Conditional retry (file not found, timeouts)

### 2. Retry Strategy (Section 2)

```python
from error_recovery import retry_with_strategy

# Wrap agent spawning
result = retry_with_strategy(
    operation=lambda: spawn_parser_agent(paths),
    operation_name="Parser Agent",
    agent_type="parser",
    max_retries=3,
    backoff_type='exponential'  # or 'linear' or 'constant'
)
```

**Retry Scopes** (RECOMMENDED = Option A):
- **Option A**: Retry failed agent only, reuse checkpoints ✅
- **Option B**: Retry entire pipeline (wasteful, only for schema errors)
- **Option C**: Retry from last checkpoint (Phase 5+, too complex)

### 3. Transaction & Rollback (Section 3)

```python
from transaction_manager import TransactionLog

txn = TransactionLog()

try:
    # Backup + write files
    txn.write_file('docs/generated/draft.md', rfc_content)
    txn.write_file('docs/rfc-map.json', json.dumps(mappings))

    # Validate
    validate_rfc_syntax('docs/generated/draft.md')

    # Commit
    txn.commit()

except Exception as e:
    # Rollback on failure
    txn.rollback()
    raise
```

**Rollback Triggers**:
- All retries exhausted
- Permanent error
- Validation failure
- User abort (Ctrl+C)

### 4. Cleanup (Section 4)

```python
from error_recovery import cleanup_orphaned_artifacts

# Run at workflow start
cleanup_orphaned_artifacts()
```

**Retention Periods**:
- Checkpoints: 7 days
- Invalid outputs: 30 days (debugging)
- Transactions: 7 days (after COMMIT/ROLLBACK)
- Temp files: 1 hour

**Manual Cleanup**: `/rfc-cleanup` command

### 5. Circuit Breaker (Section 2.3)

```python
from error_recovery import get_circuit_breaker

breaker = get_circuit_breaker('parser')

try:
    result = breaker.call(
        operation=lambda: retry_with_strategy(...),
        operation_name="Parser Agent"
    )
except CircuitBreakerOpenError:
    # Circuit open after 5 consecutive failures
    print("⛔ Parser circuit breaker OPEN - check system health")
```

**States**:
- **CLOSED**: Normal operation
- **OPEN**: Paused after 5 failures, wait 5 minutes
- **HALF_OPEN**: Testing recovery, allow 1 attempt

---

## Configuration Quick Start

**Minimal** (`.claude/plugin.json`):
```json
{
  "config": {
    "error_recovery": {
      "retry": {"enabled": true, "max_retries": 3}
    }
  }
}
```

**Per-Agent Overrides**:
```json
{
  "config": {
    "error_recovery": {
      "per_agent_overrides": {
        "parser": {"max_retries": 5, "timeout_seconds": 300}
      }
    }
  }
}
```

**Environment Variables**:
```bash
export RFC_RETRY_ENABLED=false       # Disable retry (CI)
export RFC_MAX_RETRIES=10            # Increase retries
export RFC_CLEANUP_RETENTION_DAYS=1  # Aggressive cleanup
```

---

## User-Facing Messages

### During Retry
```
🔄 Attempt 1 of Parser Agent failed:
   Error: TimeoutError: Serena MCP timed out after 30s
   Retrying in 2.0s... (attempt 2/3)
```

### After Success
```
✅ Parser Agent succeeded after 2 retries
   Total time: 8.5s (including 1 retry)
```

### After Failure
```
❌ Parser Agent failed after 3 attempts

**Error Type**: ConnectionError
**This appears to be a transient error, but retries were exhausted.**

**Suggested Actions**:
1. Check Serena MCP server status
2. Wait a few minutes and retry
3. Review .claude/.coordinator-errors.log
```

---

## Coordinator Workflow Integration

**Add to `.claude/instructions/coordinator.md`**:

1. **Before Step 1** (Add Step 0):
   ```python
   cleanup_orphaned_artifacts()  # Clean old artifacts
   ```

2. **Wrap Steps 2-4** (Agent spawning):
   ```python
   breaker = get_circuit_breaker('parser')
   parser_results = breaker.call(
       operation=lambda: retry_with_strategy(
           operation=lambda: spawn_parser_agent(paths),
           operation_name="Parser Agent",
           max_retries=3
       ),
       operation_name="Parser Agent"
   )
   ```

3. **Wrap Step 8** (File writes):
   ```python
   txn = TransactionLog()
   try:
       txn.write_file(rfc_path, content)
       txn.write_file(map_path, mappings)
       validate_rfc_syntax(rfc_path)
       txn.commit()
   except:
       txn.rollback()
       raise
   ```

---

## Test Scenarios (BDD)

```gherkin
Scenario: Transient error recovers with retry
  Given Serena MCP will timeout on first call
  When I run "/rfc-generate"
  Then parser should retry once and succeed
  And console shows "✅ succeeded after 1 retry"

Scenario: Permanent error fails immediately
  Given code has syntax error
  When I run "/rfc-generate"
  Then parser should not retry
  And error report should suggest "Check for syntax errors"

Scenario: Transaction rollback on validation failure
  Given formatter generates invalid RFC
  When I run "/rfc-generate"
  Then both RFC and rfc-map.json should be restored
  And transaction state should be ROLLED_BACK
```

---

## Performance Budget

| Operation | Overhead | Status |
|-----------|----------|--------|
| Retry setup | 0.5s | ✅ 0.4% of 120s parser |
| Transaction backup | 0.2s | ✅ 10% of 2s write (acceptable) |
| Cleanup | 1s | ✅ Startup only |
| **Total** | **2.2s** | **✅ 0.6% of 362s workflow** |

**Goal**: <5% overhead ✅ **PASS**

---

## Files to Create

1. **`.claude/lib/error_recovery.py`** (Section 8.1)
   - `classify_error()`
   - `retry_with_strategy()`
   - `CircuitBreaker` class
   - User message functions

2. **`.claude/lib/transaction_manager.py`** (Section 8.2)
   - `TransactionLog` class
   - `cleanup_old_transactions()`

3. **`.claude/commands/rfc-cleanup.md`** (Section 4.2)
   - `/rfc-cleanup` slash command

4. **Update `.claude/instructions/coordinator.md`** (Section 8.3)
   - Add Step 0 (cleanup)
   - Wrap agents in retry
   - Wrap writes in transaction

5. **Update `.claude/plugin.json`** (Section 7.1)
   - Add `error_recovery` config section

---

## Dependencies

**Blocks**:
- T038 (update rfc-map.json)
- T039 (validate preservation)
- T040 (error handling)

**Requires**:
- CHK035, CHK039, CHK076, CHK077 (transaction system) - **Implemented in this design**
- CHK009 (timeouts) - **Specified in Section 7.3**

**Integrates With**:
- Phase 3 checkpoint system (extends, doesn't replace)
- Hook system (hooks don't retry, workflows do)

---

## Common Pitfalls

❌ **Don't**: Retry inside hooks (hooks should be fast validators)
✅ **Do**: Retry only in coordinator workflow

❌ **Don't**: Silent retries (confuses users)
✅ **Do**: Always print retry status

❌ **Don't**: Rollback partial success (keep valid checkpoints)
✅ **Do**: Only rollback file writes

❌ **Don't**: Delete artifacts <1 hour old (might be active)
✅ **Do**: Respect retention periods + age checks

---

## Decision Summary

| Decision Point | Choice | Rationale |
|----------------|--------|-----------|
| **Retry scope** | Option A (failed agent only) | Minimal waste, fast recovery |
| **Rollback mechanism** | Transaction backup | Simple, no git dependency |
| **Partial rollback** | Keep checkpoints, rollback files | Preserve debugging info |
| **Circuit breaker** | Enabled by default | Prevent resource exhaustion |
| **Default retries** | 3 attempts | Balance reliability vs speed |
| **Backoff strategy** | Exponential | Standard for network errors |
| **Cleanup timing** | On start + manual | Prevent buildup, user control |

---

## Implementation Estimate

- **error_recovery.py**: 4-5 hours
- **transaction_manager.py**: 3-4 hours
- **Coordinator integration**: 2-3 hours
- **Config + tests**: 3-4 hours
- **Total**: **12-16 hours**

---

**Next Step**: Implement `error_recovery.py` before T038 (update rfc-map.json)
**Full Spec**: See `PHASE4-ERROR-RECOVERY-DESIGN.md` (50 pages)
