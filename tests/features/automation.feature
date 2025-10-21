# Feature: Automated Documentation Checks
# Purpose: Test Claude Code native hooks for automated RFC documentation quality checks
# User Story 3: Automated Documentation Checks (Phase 5)

Feature: Automated Documentation Checks
  As a team lead
  I want automated documentation quality checks during development workflows
  So that documentation remains accurate without manual intervention

  Background:
    Given a clean test repository
    And the RFC generator plugin is installed

  # =========================================================================
  # PreToolUse Hook: Pre-commit Validation
  # =========================================================================

  @hook @pretool
  Scenario: PreToolUse hook warns about RFC-tracked file modifications
    Given a project with RFC documentation and rfc-map.json
    And the file "src/api.py" is tracked in rfc-map.json with section "3.2"
    When PreToolUse hook is triggered for Write tool on "src/api.py"
    Then the hook returns non-blocking response
    And the response message includes "Affects RFC §3.2"
    And the response suggestion recommends "/rfc-analyze-impact"
    And hook execution completes in under 100ms

  @hook @pretool @blocking
  Scenario: PreToolUse hook blocks direct kramdown-rfc execution
    Given a project with RFC documentation
    When PreToolUse hook is triggered for Bash tool "kramdown-rfc draft-spec.md"
    Then the hook blocks execution
    And the response message suggests "Use 'make txt' instead"
    And the response has block=true

  @hook @pretool
  Scenario: PreToolUse hook allows Make target execution
    Given a project with RFC documentation
    When PreToolUse hook is triggered for Bash tool "make txt"
    Then the hook allows execution
    And the response has block=false
    And no warning message is displayed

  @hook @pretool @graceful
  Scenario: PreToolUse hook degrades gracefully without rfc-map.json
    Given a project without RFC documentation
    When PreToolUse hook is triggered for Write tool on "src/api.py"
    Then the hook returns non-blocking response
    And the response message suggests "Run /rfc-generate first"
    And the response has block=false

  # =========================================================================
  # Impact Analysis: API Change Detection
  # =========================================================================

  @impact @api
  Scenario: Impact analyzer detects public API changes requiring MUST_UPDATE
    Given a project with RFC documentation
    And "src/api.py::authenticate" is mapped to RFC section "3.2" type "interfaces"
    When code changes modify line 10 in "src/api.py"
    And impact analysis is triggered with git diff
    Then affected sections include "3.2"
    And severity for section "3.2" is "MUST_UPDATE"
    And changed elements include "authenticate"
    And impact report is generated successfully

  @impact @behavior
  Scenario: Impact analyzer detects behavior changes requiring SHOULD_REVIEW
    Given a project with RFC documentation
    And "src/statemachine.py::OrderStateMachine" is mapped to RFC section "4.1" type "behavior"
    When code changes modify lines 15-20 in "src/statemachine.py"
    And impact analysis is triggered with git diff
    Then affected sections include "4.1"
    And severity for section "4.1" is "SHOULD_REVIEW"
    And impact report includes behavior section warning

  @impact @untracked
  Scenario: Impact analyzer ignores changes to untracked code
    Given a project with RFC documentation
    And "tests/test_utils.py" is NOT tracked in rfc-map.json
    When code changes modify "tests/test_utils.py"
    And impact analysis is triggered with git diff
    Then no affected sections are reported
    And impact report shows "No RFC documentation impact detected"

  @impact @multiple
  Scenario: Impact analyzer handles multiple file changes
    Given a project with RFC documentation
    And multiple files are tracked in rfc-map.json across sections
    When code changes modify "src/api.py" and "src/models.py"
    And impact analysis is triggered with git diff
    Then multiple affected sections are reported
    And sections are sorted by severity (MUST_UPDATE first)
    And each section lists its affected code elements

  @impact @performance
  Scenario: Impact analyzer completes quickly for hook responsiveness
    Given a project with RFC documentation
    And 10 files are tracked in rfc-map.json
    When code changes modify 3 tracked files
    And impact analysis is triggered with git diff
    Then analysis completes in under 100ms
    And results include all affected sections

  # =========================================================================
  # PostToolUse Hook: Reviewer Guidance
  # =========================================================================

  @hook @posttool
  Scenario: PostToolUse hook updates rfc-map.json after code changes
    Given a project with RFC documentation
    And "src/api.py" is tracked in rfc-map.json
    When PostToolUse hook is triggered after Write tool modified "src/api.py"
    Then the hook updates timestamps in rfc-map.json
    And affected sections are flagged as stale
    And hook returns success response

  @hook @posttool @guidance
  Scenario: PostToolUse hook generates reviewer guidance report
    Given a project with RFC documentation
    And multiple files are tracked in rfc-map.json
    When PostToolUse hook is triggered after Bash tool "git commit -m 'Update API'"
    And git diff shows changes to tracked files
    Then a reviewer guidance report is generated
    And the report includes affected RFC sections
    And the report includes review checklist
    And the report is appended to ".claude/.hook-history.json"

  # =========================================================================
  # SessionStart Hook: Staleness Detection
  # =========================================================================

  @hook @session @staleness
  Scenario: SessionStart hook detects stale RFC documentation
    Given a project with RFC documentation
    And rfc-map.json was last updated 45 days ago
    When SessionStart hook is triggered
    Then the hook displays staleness warning
    And the warning message includes "45 days ago"
    And the suggestion recommends "/rfc-update"
    And the response has block=false

  @hook @session
  Scenario: SessionStart hook does not warn for recent documentation
    Given a project with RFC documentation
    And rfc-map.json was updated 5 days ago
    When SessionStart hook is triggered
    Then no staleness warning is displayed
    And the response has block=false

  @hook @session @uncommitted
  Scenario: SessionStart hook detects uncommitted documentation changes
    Given a project with RFC documentation
    And "docs/generated/draft-spec.md" has uncommitted changes
    When SessionStart hook is triggered
    Then the hook warns about uncommitted documentation
    And the suggestion recommends "git add docs/"
    And the response has block=false

  # =========================================================================
  # UserPromptSubmit Hook: Intent Detection
  # =========================================================================

  @hook @userprompt @intent
  Scenario: UserPromptSubmit hook detects RFC-related intent
    Given a project with RFC documentation
    And memory files exist in ".claude/memory/"
    When UserPromptSubmit hook receives prompt "How do I update the RFC?"
    Then the hook detects RFC-related keywords
    And the hook loads "codebase-overview.md" from memory
    And RFC context is injected into response
    And intent detection is logged to ".claude/.hook-history.json"

  @hook @userprompt
  Scenario: UserPromptSubmit hook ignores non-RFC prompts
    Given a project with RFC documentation
    When UserPromptSubmit hook receives prompt "Fix the login bug"
    Then the hook does not inject RFC context
    And no memory files are loaded
    And the response has block=false

  # =========================================================================
  # Edge Cases and Error Handling
  # =========================================================================

  @edge @error
  Scenario: Hooks handle missing impact_analyzer.py gracefully
    Given a project with RFC documentation
    But ".claude/lib/impact_analyzer.py" is missing
    When PreToolUse hook is triggered for Write tool
    Then the hook returns non-blocking warning
    And the error message indicates missing library
    And the hook does not crash

  @edge @git
  Scenario: Impact analyzer handles no git history
    Given a project with RFC documentation
    But the repository has no commits
    When impact analysis is triggered
    Then no changes are detected
    And impact report shows "No git history found"

  @edge @permission
  Scenario: Hooks handle permission errors gracefully
    Given a project with RFC documentation
    And "docs/rfc-map.json" is read-only
    When PostToolUse hook attempts to update rfc-map.json
    Then the hook logs permission error
    And the hook returns non-blocking warning
    And the response suggests checking file permissions

  @edge @json
  Scenario: Hooks handle malformed rfc-map.json gracefully
    Given a project with invalid JSON in "docs/rfc-map.json"
    When PreToolUse hook is triggered for Write tool
    Then the hook returns non-blocking warning
    And the error message indicates JSON parsing error
    And the suggestion recommends "/rfc-validate"
