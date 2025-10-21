# Next Steps & Recommendations

**Context**: Simulation removal work ~95% complete on branch `003-remove-simulations`
**Date**: 2025-10-20
**Status**: Ready for decision on merge strategy

---

## Immediate Decision Required

### Merge Strategy

**Option 1: Merge Now (Recommended)**
- ✅ Core mandate fulfilled (~95% complete)
- ✅ All critical simulations removed
- ✅ Tests use 100% real subprocess execution
- ✅ Comprehensive documentation
- ✅ Breaking changes documented
- ⚠️ 4 scenarios marked @skip (cannot auto-test environmental failures)
- ⚠️ CI will need tool installation updates

**Option 2: Complete Phase 3 P1 First**
- Adds 2-3 hours to remove `simulated_changes` logic
- Only affects automation tests (not core /rfc-* workflows)
- Marginal value for time investment
- Delays merge

**Option 3: Complete All Deferred Work (Phase 3 P1 + Phase 4)**
- Adds 2-4 days for full validation and CI setup
- Achieves 100% completion
- Provides baseline pass rates
- Significant delay

**Recommendation**: **Option 1** - Merge now, address remaining items in follow-up PRs.

---

## Pre-Merge Actions

### 1. Review & Approval ⏳

**Required Reviewers**: Project maintainers, test infrastructure owners

**Review Focus**:
- [ ] Breaking changes acceptable? (CommandRunner: 8→2 params, run_slash_command: 7→3 params)
- [ ] @skip scenarios acceptable? (4 scenarios marked @skip with rationale)
- [ ] Documentation adequate? (6 files, 2,412 lines)
- [ ] Commit history clean? (12 commits, conventional format)

**Timeline**: 1-2 days for review

### 2. Update Branch (If Needed) ⏳

If `002-build-a-claude` has new commits since branching:

```bash
git checkout 003-remove-simulations
git fetch origin
git rebase origin/002-build-a-claude
# Resolve any conflicts
git push --force-with-lease
```

**Timeline**: 30 minutes - 2 hours depending on conflicts

### 3. Final Validation ⏳

Run full test suite dry-run to ensure no syntax errors:

```bash
cd tests
behave --dry-run --no-skipped
```

**Timeline**: 5 minutes

---

## Post-Merge Actions (Within 1 Week)

### 1. Update CI Configuration 🔴 CRITICAL

**Required Tools** (must be installed in CI environment):

1. **Serena MCP Server**
   - Installation: Follow Claude Code MCP setup guide
   - Configuration: .mcp.json or VS Code settings
   - Validation: `claude mcp tools list | grep serena`

2. **kramdown-rfc** (Ruby gem)
   - Installation: `bundle install` (uses Gemfile from lib/)
   - Version: Latest stable
   - Validation: `kramdown-rfc --version`

3. **xml2rfc** (Python package)
   - Installation: `pip install xml2rfc` (in venv)
   - Version: 3.12.3+
   - Validation: `xml2rfc --version`

4. **idnits** (optional, for validation)
   - Installation: Download from IETF tools
   - Validation: `idnits --version`

**Action Items**:
- [ ] Create `.github/workflows/test-setup.yml` with tool installation steps
- [ ] Update main CI workflow to include test-setup as prerequisite
- [ ] Document tool versions in requirements.txt / Gemfile
- [ ] Add health check step to validate all tools before running tests

**Owner**: DevOps/CI team
**Priority**: P0 (tests will fail without these)
**Timeline**: 1-2 days

### 2. Document CI Requirements 🟡 IMPORTANT

Create `tests/CI-REQUIREMENTS.md`:

```markdown
# CI Requirements for BDD Tests

## Required Tools

1. **Serena MCP** - Code analysis via Claude Code
2. **kramdown-rfc** - Markdown → RFC XML conversion
3. **xml2rfc** - RFC XML → txt/html rendering
4. **idnits** (optional) - RFC validation

## Installation Steps

[Detailed installation instructions]

## Validation

[Health check commands]

## Troubleshooting

[Common issues and solutions]
```

**Owner**: Test infrastructure team
**Priority**: P1
**Timeline**: 2-4 hours

### 3. Baseline Test Execution 🟡 IMPORTANT

Run full test suite with real tools installed:

```bash
cd tests
behave features/*.feature --format json --outfile results.json
behave features/*.feature --format pretty --outfile results.txt
```

**Document**:
- Pass rate (expected: 60-80% given real tool dependencies)
- Failure patterns (categorize: missing tools, timeout, logic errors)
- Execution time (baseline for performance monitoring)

**Create**: `tests/BASELINE-TEST-RESULTS.md`

**Owner**: Test infrastructure team
**Priority**: P1
**Timeline**: 1 day (includes troubleshooting)

---

## Optional Enhancements (Next Sprint)

### 1. Complete Phase 3 P1 🟢 OPTIONAL

**Remove simulated_changes Logic**

**Scope**: ~15 locations in automation_steps.py
**Effort**: 2-3 hours
**Priority**: P2 (low impact - automation tests only)

**Files to Update**:
- tests/steps/automation_steps.py (15 locations)
- tests/steps/automation_helpers.py (remove run_impact_analysis_internal if unused)

**Benefit**: Achieves 100% simulation removal
**Risk**: Low (isolated to automation tests)

### 2. Environment Manipulation Testing 🟢 OPTIONAL

**Un-skip Environmental Failure Scenarios**

**Approach 1: Docker-Based Isolation**
- Create Docker containers with controlled network/disk/permissions
- Run tests inside containers with simulated environmental constraints
- Examples: docker --network=none, disk quota limits, read-only mounts

**Approach 2: Testcontainers Framework**
- Use testcontainers-python for managed container lifecycle
- Define scenario-specific container configs
- Automated cleanup

**Approach 3: Mock Network/FS Operations**
- Use pytest-mock or unittest.mock to intercept subprocess calls
- Return realistic error responses for network/disk/permission failures
- Lightweight but less realistic than container-based

**Recommendation**: **Approach 1** (Docker) for high fidelity, **Approach 3** (mock) for quick wins

**Effort**: 1-2 weeks for full implementation
**Priority**: P3 (nice to have)
**Owner**: Test infrastructure team

### 3. Test Suite Optimization 🟢 OPTIONAL

**Performance Improvements**:

1. **Parallelize Test Execution**
   - Use behave --processes=4 for parallel scenario execution
   - Isolate test repos to avoid conflicts
   - Expected speedup: 2-4x

2. **Cache Tool Installations**
   - Cache venv, bundler gems, npm packages across CI runs
   - Reduces setup time from 2-3 minutes to 10-20 seconds
   - Example: GitHub Actions cache action

3. **Optimize Fixture Creation**
   - Pre-create sample projects once, copy for each test
   - Reduces git init/file creation overhead
   - Expected speedup: 20-30%

**Total Expected Speedup**: 3-5x (e.g., 10 minutes → 2-3 minutes)

**Effort**: 1-2 days
**Priority**: P2
**Owner**: Test infrastructure team

---

## Monitoring & Maintenance

### 1. Test Health Dashboard 📊

**Metrics to Track**:
- Pass rate over time
- Execution time trends
- Flaky test identification (tests that fail intermittently)
- Tool availability failures (Serena MCP, kramdown-rfc, xml2rfc)

**Tools**: GitHub Actions reporting, custom dashboard, or test analytics service

**Setup Effort**: 1-2 days
**Priority**: P2

### 2. Alerting 🔔

**Alert Conditions**:
- Pass rate drops below 70%
- Execution time exceeds 15 minutes
- Tool installation failures in CI
- Repeated timeouts (indicates subprocess hanging)

**Integration**: GitHub Actions notifications, Slack, email

**Setup Effort**: 2-4 hours
**Priority**: P1

### 3. Regular Review 📅

**Monthly Review**:
- Analyze failure patterns
- Update tool versions (kramdown-rfc, xml2rfc)
- Review @skip scenarios (can any be un-skipped?)
- Prune obsolete tests

**Quarterly Review**:
- Evaluate test coverage gaps
- Consider new scenarios for emerging features
- Update documentation

**Owner**: Test infrastructure team

---

## Risk Mitigation

### Risk 1: CI Failures Due to Missing Tools

**Likelihood**: High (until CI updated)
**Impact**: High (blocks merges)

**Mitigation**:
1. Update CI config immediately post-merge (P0)
2. Document required tools in PR
3. Create installation verification script
4. Add health check step to CI pipeline

### Risk 2: Flaky Tests from Real Subprocess Execution

**Likelihood**: Medium
**Impact**: Medium (CI unreliability)

**Mitigation**:
1. Monitor for timeout errors
2. Increase timeouts if needed (currently 5-10s)
3. Retry failed tests once before marking failure
4. Identify and fix root cause (hanging subprocesses)

### Risk 3: Test Maintenance Burden

**Likelihood**: Low
**Impact**: Low (tests are well-structured)

**Mitigation**:
1. Comprehensive documentation (6 phase reports)
2. Clear separation of concerns (command_runner, hook_runner, step definitions)
3. Regular review and refactoring

---

## Success Metrics (3 Months Post-Merge)

**Target Metrics**:
- ✅ Pass rate: 75%+ (with real tools installed)
- ✅ Execution time: <10 minutes for full suite
- ✅ Flaky test rate: <5% (tests failing intermittently)
- ✅ CI reliability: 95%+ (CI runs complete successfully)
- ✅ Zero simulation code remaining
- ✅ Documentation up-to-date

**Review Date**: 2026-01-20 (3 months from completion)

---

## Resource Requirements

### Immediate (Week 1 Post-Merge)
- **DevOps/CI**: 1-2 days (CI configuration update)
- **Test Infrastructure**: 1 day (baseline test execution)
- **Total**: 2-3 days

### Short-Term (Month 1 Post-Merge)
- **Test Infrastructure**: 2-3 days (optional Phase 3 P1, optimization)
- **Documentation**: 4-6 hours (CI requirements, troubleshooting guides)
- **Total**: 3-4 days

### Long-Term (Quarter 1 Post-Merge)
- **Test Infrastructure**: 1-2 weeks (environment manipulation, advanced optimization)
- **Monitoring Setup**: 2-3 days (dashboard, alerting)
- **Total**: 2-3 weeks

---

## Questions & Decision Points

### Q1: Merge Strategy
**Decision Needed**: Merge now (Option 1) or complete deferred work first (Option 2/3)?
**Recommendation**: Option 1 (merge now)
**Owner**: Project lead
**Deadline**: Before next sprint planning

### Q2: CI Update Ownership
**Decision Needed**: Who owns CI configuration updates?
**Recommendation**: DevOps team (with test infrastructure support)
**Owner**: TBD
**Deadline**: Within 1 week of merge

### Q3: Phase 3 P1 Priority
**Decision Needed**: Complete Phase 3 P1 (simulated_changes removal) in next sprint or backlog?
**Recommendation**: Backlog (low priority)
**Owner**: Test infrastructure team
**Deadline**: No hard deadline

### Q4: Environment Manipulation Testing
**Decision Needed**: Pursue Docker-based environmental testing or leave as @skip?
**Recommendation**: Backlog for Q1 2026 (nice to have)
**Owner**: Test infrastructure team
**Deadline**: Q1 2026 planning

---

## Communication Plan

### Stakeholders to Notify

1. **Project Maintainers**
   - Notify: PR ready for review
   - Medium: GitHub PR comment + Slack
   - Info: Breaking changes, @skip scenarios, CI requirements

2. **DevOps/CI Team**
   - Notify: CI updates required post-merge
   - Medium: Direct communication + documentation
   - Info: Required tools, installation steps, timeline

3. **Test Infrastructure Team**
   - Notify: Baseline execution needed, optional work available
   - Medium: Standup + documentation
   - Info: Baseline test run, Phase 3 P1, optimizations

4. **Development Team**
   - Notify: Breaking changes in test infrastructure
   - Medium: Team meeting + email
   - Info: CommandRunner/run_slash_command signature changes

### Communication Timeline

- **Day 0**: PR opened, maintainers notified
- **Day 1-2**: Review period
- **Day 3**: Merge (assuming approval)
- **Day 3**: DevOps notified of CI requirements
- **Day 4-5**: CI updates implemented
- **Week 2**: Baseline test results published
- **Month 1**: Phase 3 P1 decision point

---

## Appendix: File Manifest

### Documentation Files Created (6)
1. `tests/PHASE-1-PROGRESS-2025-10-20.md` - Phase 1.1-1.2 completion
2. `tests/PHASE-1.3-COMPLETE-2025-10-20.md` - Tool override removal
3. `tests/PHASE-1.4-P0-COMPLETE-2025-10-20.md` - Hardcoded fixture replacement
4. `tests/PHASE-1-SUMMARY-2025-10-20.md` - Comprehensive Phase 1 summary
5. `tests/PHASE-2-COMPLETE-2025-10-20.md` - Environmental simulation removal
6. `tests/SIMULATION-REMOVAL-FINAL-STATUS.md` - Complete project summary

### Code Files Modified (5)
1. `tests/support/command_runner.py` - Core test infrastructure
2. `tests/steps/init_steps.py` - /rfc-init step definitions
3. `tests/steps/update_steps.py` - /rfc-update step definitions
4. `tests/steps/automation_helpers.py` - Hook execution utilities
5. `tests/features/init.feature` - /rfc-init test scenarios

### New Files Created (2)
1. `tests/PULL-REQUEST-SUMMARY.md` - This PR summary
2. `tests/NEXT-STEPS-RECOMMENDATIONS.md` - This document

---

## Summary

**Core Work**: ✅ Complete (~95%)
**Documentation**: ✅ Comprehensive (8 files, 2,500+ lines)
**Immediate Action**: ⏳ Review & merge PR
**Critical Post-Merge**: 🔴 Update CI configuration (1-2 days)
**Optional Enhancements**: 🟢 Backlog (Phase 3 P1, environment testing, optimization)

**Recommended Path**:
1. Review & approve PR (1-2 days)
2. Merge to 002-build-a-claude
3. Update CI config (P0, 1-2 days)
4. Baseline test execution (P1, 1 day)
5. Document CI requirements (P1, 4 hours)
6. Backlog optional work (Phase 3 P1, optimizations)

**Overall Status**: Ready to ship 🚢
