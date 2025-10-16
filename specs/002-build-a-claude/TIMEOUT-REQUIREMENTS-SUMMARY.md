# Timeout Requirements Summary
**Quick Reference Guide**

**Full Specification**: [TIMEOUT-REQUIREMENTS.md](./TIMEOUT-REQUIREMENTS.md)
**Date**: 2025-10-14
**Status**: Ready for Implementation

---

## Quick Decision Summary

### Chosen Timeout Strategy

**Hybrid Approach**: Static base timeout + dynamic scaling based on codebase size

**Why**: Balances predictability (users know baseline) with flexibility (scales for large codebases).

### Default Timeouts

| Agent | Base Timeout | Formula |
|-------|-------------|---------|
| Parser | 10 minutes | `600s + (LOC / 10000) * 60` |
| Analyzer | 6 minutes | `360s + min(symbols/100, 60) * 30` (capped at 36min) |
| Formatter | 3 minutes | `180s + (sections * 15)` |
| Validator | 2 minutes | `120s + (RFC_KB / 100) * 10` |
| **Workflow Total** | 30 minutes | Sum of agents (safety margin included) |

### Configuration Hierarchy

```
CLI Arguments  (--parser-timeout 15m)
    ↓
Environment Variables  (RFC_PARSER_TIMEOUT=900)
    ↓
Plugin Config  (.claude/plugin.json → "timeouts": {"parser": 600})
    ↓
Hardcoded Defaults
```

### Timeout Actions

```
Timeout occurs
├─ Has checkpoint? (agent wrote progress file)
│  ├─ YES → Auto-extend once (+50% of original timeout)
│  └─ NO  → Abort immediately (likely hung)
└─ Display error + recovery options
```

---

## CLI Reference

### Basic Usage

```bash
# Use defaults (10min parser, 6min analyzer, etc.)
/rfc-generate

# Override specific agent timeout
/rfc-generate --parser-timeout 15m

# Override all agent timeouts
/rfc-generate --timeout 20m

# Override workflow total timeout
/rfc-generate --workflow-timeout 60m

# Disable timeout (use with caution!)
/rfc-generate --timeout infinity
```

### Environment Variables

```bash
# Set parser timeout to 15 minutes
export RFC_PARSER_TIMEOUT=15m

# Set all agent timeouts to 20 minutes
export RFC_TIMEOUT=20m

# Set workflow total timeout to 1 hour
export RFC_WORKFLOW_TIMEOUT=1h
```

### Plugin Configuration

Add to `.claude/plugin.json`:

```json
{
  "timeouts": {
    "parser": 900,
    "analyzer": 600,
    "formatter": 300,
    "validator": 180,
    "workflow": 3600,
    "auto_extend": true,
    "extend_factor": 0.5
  }
}
```

---

## Progress Indicators

### During Execution

```
✓ Prerequisites validated (1/5)
✓ Parser agent complete (2/5) - 1m 23s
  Analyzer agent running... (3/5)
  Progress: 75% (4m 30s / 6m 00s) ⏱️
  [██████████████████░░░░░░] Analyzing relationships...
```

### Warning Messages

**At 75% of timeout**:
```
⚠️  Analyzer approaching timeout (5m 24s / 6m 00s)
   - Agent is progressing (last checkpoint: 23s ago)
   - Consider reducing scope or extending timeout
```

**At 90% of timeout**:
```
⚠️  Analyzer near timeout limit (5m 54s / 6m 00s)
   - Agent still active
   - Will auto-extend if checkpoint exists
```

### Timeout Error

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
  - Symbols processed: 1234 / ~2000 (estimated)
```

---

## Timeout Syntax Reference

**Accepted Formats**:
- Seconds: `300`, `300s`
- Minutes: `5m`, `5min`
- Hours: `1h`, `1hour`
- Special: `infinity`, `none` (disable timeout)

**Validation**:
- **Minimum**: 30s
- **Maximum**: 24h
- **Warnings**:
  - `< 60s`: "Very short timeout"
  - `> 2h`: "May hide hung processes"

**Examples**:
```bash
/rfc-generate --parser-timeout 15m      # 15 minutes
/rfc-generate --analyzer-timeout 600s   # 10 minutes (600 seconds)
/rfc-generate --timeout 1h              # 1 hour for all agents
/rfc-generate --workflow-timeout 90m    # 1.5 hours total
```

---

## Cascading Timeout Behavior

| Agent Times Out | Action | Rationale |
|-----------------|--------|-----------|
| **Parser** | ABORT workflow | No structure = garbage output |
| **Analyzer** | WARN, continue | Can proceed with structure only |
| **Formatter** | ABORT workflow | No RFC = critical failure |
| **Validator** | WARN, continue | RFC exists, user validates manually |

---

## Implementation Checklist

**Core Components** (8 hours total):
- [ ] Create `agent_runner.py` with timeout wrapper (3h)
- [ ] Integrate into `rfc-generate.md` coordinator (2h)
- [ ] Write unit tests (mock clocks) (2h)
- [ ] Update `plugin.json` schema (1h)

**Testing Scenarios**:
- [ ] Normal completion (no timeout)
- [ ] Timeout with no progress (abort)
- [ ] Timeout with checkpoint (auto-extend)
- [ ] Progress warnings (75%, 90%)
- [ ] CI mode (non-interactive)
- [ ] Configuration hierarchy
- [ ] Timeout parsing validation

**Documentation**:
- [ ] Add timeout section to quickstart.md
- [ ] Document CLI arguments
- [ ] Document environment variables
- [ ] Add troubleshooting guide

---

## Known Limitations & Future Work

### Current Limitations

1. **No profiling data yet**: Defaults based on Phase 3 test (small fixture). May need adjustment after testing on real codebases.
2. **Fixed scaling formula**: Dynamic scaling uses simple linear formula. May not fit all codebase characteristics.
3. **No parallel execution**: Agents run sequentially. Total time = sum of agent times.

### Future Enhancements (Phase 5+)

1. **Adaptive Timeouts**: Learn from history, auto-tune based on project characteristics
2. **Parallel Agents**: Run analyzer + formatter in parallel (reduce total time ~30%)
3. **Timeout Profiler**: `/rfc-profile` command to measure and recommend timeouts
4. **Budget-Based Allocation**: Dynamic time budget instead of fixed timeouts

---

## Troubleshooting

### "Parser timed out after 10 minutes"

**Cause**: Codebase too large for default timeout.

**Solutions**:
1. **Extend timeout**: `/rfc-generate --parser-timeout 20m`
2. **Reduce scope**: `/rfc-generate src/core/` (analyze fewer files)
3. **Check checkpoint**: If `.claude/.checkpoints/parser-*.json` exists, agent was progressing. Extend timeout and retry.

### "Analyzer timed out after 6 minutes"

**Cause**: Complex relationships (many cross-references).

**Solutions**:
1. **Extend timeout**: `/rfc-generate --analyzer-timeout 15m`
2. **Skip analysis**: `/rfc-generate --sections interfaces,terminology` (skip behavior analysis)
3. **Check for hung process**: If no checkpoint, agent may be stuck. Report issue.

### "Workflow timed out after 30 minutes"

**Cause**: Total time across all agents exceeded limit.

**Solutions**:
1. **Extend workflow timeout**: `/rfc-generate --workflow-timeout 60m`
2. **Increase individual agent timeouts**: `/rfc-generate --parser-timeout 20m --analyzer-timeout 15m`
3. **Reduce scope**: Analyze fewer paths or sections

### CI/CD Builds Timing Out

**Cause**: CI environment may be slower (limited resources).

**Solutions**:
1. **Increase timeouts in CI config**:
   ```yaml
   # .github/workflows/rfc-generate.yml
   env:
     RFC_PARSER_TIMEOUT: 20m
     RFC_ANALYZER_TIMEOUT: 15m
     RFC_WORKFLOW_TIMEOUT: 60m
   ```
2. **Cache Serena MCP index**: Reuse analysis between CI runs
3. **Use incremental generation**: Only regenerate changed sections

---

## Quick Tips

✅ **DO**:
- Start with defaults, adjust if needed
- Use `--timeout` shorthand for quick overrides
- Check `.claude/.checkpoints/` if timeout occurs (shows progress)
- Configure timeouts in `plugin.json` for consistent behavior
- Extend timeouts incrementally (10min → 15min → 20min)

❌ **DON'T**:
- Set timeouts < 60s (too short for any real codebase)
- Use `infinity` in CI/CD (workflows may hang forever)
- Ignore timeout warnings (75%/90% warnings predict imminent timeout)
- Skip checkpoint analysis (shows if agent is hung vs progressing)

---

## Examples by Codebase Size

### Small Codebase (1K LOC)

**Expected Time**: ~2-3 minutes total

**Recommended Timeouts**: Use defaults
```bash
/rfc-generate
```

### Medium Codebase (10-50K LOC)

**Expected Time**: ~10-15 minutes total

**Recommended Timeouts**: Extend parser and analyzer
```bash
/rfc-generate --parser-timeout 15m --analyzer-timeout 10m
```

Or via environment:
```bash
export RFC_PARSER_TIMEOUT=15m
export RFC_ANALYZER_TIMEOUT=10m
/rfc-generate
```

### Large Codebase (100K+ LOC)

**Expected Time**: ~30-60 minutes total

**Recommended Timeouts**: Aggressive extension + workflow limit
```bash
/rfc-generate --parser-timeout 30m --analyzer-timeout 20m --workflow-timeout 90m
```

Or via plugin config (`.claude/plugin.json`):
```json
{
  "timeouts": {
    "parser": 1800,
    "analyzer": 1200,
    "formatter": 600,
    "validator": 300,
    "workflow": 5400
  }
}
```

---

**Document Version**: 1.0
**Companion**: [TIMEOUT-REQUIREMENTS.md](./TIMEOUT-REQUIREMENTS.md)
**Last Updated**: 2025-10-14
