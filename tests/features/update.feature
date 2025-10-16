# Feature: RFC Document Update
# Purpose: Test incremental RFC document updates after code changes
# User Story 2: Update Existing RFC Documentation

Feature: RFC Document Update
  As a maintainer
  I want to update existing RFC documentation after code changes
  So that documentation stays in sync without duplicating unchanged content

  Background:
    Given a clean test repository
    And the RFC generator plugin is installed
    And an existing RFC document has been generated
    And an rfc-map.json file exists with code mappings

  Scenario: Update RFC after code changes
    Given an existing RFC document at "docs/generated/draft-calculator-00.md"
    And an rfc-map.json mapping "Calculator.add" to section "3.1"
    When I modify "src/calculator.py" method "Calculator.add" signature
    And I run "/rfc-update docs/generated/draft-calculator-00.md"
    Then the RFC section "3.1" should be regenerated
    And the RFC document should retain unchanged sections
    And the rfc-map.json timestamp for "Calculator.add" should be updated
    And I should see "Sections regenerated: 1 (§3.1)"
    And I should see "Sections preserved: 4"

  Scenario: Preserve manual edits during update
    Given an existing RFC with a "@preserve-start id:security-notes" block
    And the preserve block is in the "Security Considerations" section
    When I modify "src/calculator.py" method "Calculator.add"
    And I run "/rfc-update docs/generated/draft-calculator-00.md"
    Then the RFC should be updated
    And the preserve block "security-notes" should remain unchanged
    And I should see "Preserve blocks honored: 1"
    And the manual edits within the preserve block should be intact

  Scenario: Generate change summary with severity
    Given an existing RFC document
    And I modify "src/calculator.py" by adding a new parameter to "Calculator.add"
    When I run "/rfc-update docs/generated/draft-calculator-00.md"
    Then I should see a change detection report
    And the report should show "Files modified: 1"
    And the report should show "Affected RFC sections: 1 (§3.1)"
    And the report should show "Severity: 1 BREAKING"
    And the report should explain "Method signature modified (added parameter)"

  Scenario: Handle no changes gracefully
    Given an existing RFC document at "docs/generated/draft-calculator-00.md"
    And no code changes have been made since last RFC update
    When I run "/rfc-update docs/generated/draft-calculator-00.md"
    Then I should see "✅ No code changes detected. RFC is up-to-date."
    And the RFC document should not be modified
    And the rfc-map.json should not be modified
    And the command should exit successfully

  Scenario: Dry-run mode shows changes without writing
    Given an existing RFC document
    And I modify "src/calculator.py" method "Calculator.add"
    When I run "/rfc-update docs/generated/draft-calculator-00.md --dry-run"
    Then I should see "🔍 DRY RUN - No files modified"
    And I should see "Would update:" followed by file list
    And I should see "Section 3.1 Calculator.add: REGENERATED"
    But the RFC document should not be modified
    And the rfc-map.json should not be modified

  Scenario: Detect and abort on overlapping preserve blocks (ERROR)
    Given an existing RFC with nested "@preserve-start" markers
    And the preserve blocks overlap at lines 45-55 and 48-60
    When I run "/rfc-update docs/generated/draft-calculator-00.md"
    Then I should see an error "❌ Preserve block conflicts detected"
    And I should see "Overlapping preserve blocks: block1 (lines 45-55) and block2 (lines 48-60)"
    And the command should exit with error status
    And the RFC document should not be modified

  Scenario: Warn on preserve block conflicting with changed section (WARNING)
    Given an existing RFC with a preserve block in section "3.1"
    And I modify the code that maps to section "3.1"
    When I run "/rfc-update docs/generated/draft-calculator-00.md"
    Then I should see a warning "⚠️  Preserve block warnings:"
    And I should see "Preserve block 'custom-notes' overlaps with changed section §3.1"
    And I should be prompted "Continue anyway? Preserve blocks will take precedence."

  Scenario: Force update with conflicting preserve blocks
    Given an existing RFC with a preserve block in section "3.1"
    And I modify the code that maps to section "3.1"
    When I run "/rfc-update docs/generated/draft-calculator-00.md --force"
    Then the update should proceed without prompts
    And the preserve block should take precedence over new generated content
    And I should see "Preserve blocks honored: 1"

  Scenario: Validate deduplication - skip unchanged sections
    Given an existing RFC with 5 sections
    And I modify only "src/calculator.py" method "Calculator.add" (section 3.1)
    When I run "/rfc-update docs/generated/draft-calculator-00.md"
    Then only section "3.1" should be regenerated
    And sections "1", "2", "3.2", "4", "5" should remain unchanged
    And the parser agent should only analyze "src/calculator.py"
    And the formatter agent should only generate section "3.1"

  Scenario: Update rfc-map.json timestamps selectively
    Given an existing rfc-map.json with 3 mappings
    And mapping "Calculator.add" has timestamp "2025-10-13T10:00:00Z"
    And mapping "Calculator.subtract" has timestamp "2025-10-13T10:00:00Z"
    When I modify "src/calculator.py" method "Calculator.add"
    And I run "/rfc-update docs/generated/draft-calculator-00.md"
    Then the timestamp for "Calculator.add" should be updated to current time
    And the timestamp for "Calculator.subtract" should remain "2025-10-13T10:00:00Z"

  Scenario: Handle missing rfc-map.json file
    Given an existing RFC document at "docs/generated/draft-calculator-00.md"
    But the "docs/rfc-map.json" file is missing
    When I run "/rfc-update docs/generated/draft-calculator-00.md"
    Then I should see an error "❌ No traceability map found. Cannot determine changed sections."
    And I should see a suggestion "Regenerate from scratch: /rfc-generate src/"
    And the command should exit with error status

  Scenario: Handle missing RFC file
    Given no existing RFC document at "docs/generated/draft-nonexistent.md"
    When I run "/rfc-update docs/generated/draft-nonexistent.md"
    Then I should see an error "Cannot update non-existent RFC. Run /rfc-generate first."
    And the command should exit with error status

  Scenario: Update RFC after multiple files changed
    Given an existing RFC document
    And I modify "src/calculator.py" method "Calculator.add" (section 3.1)
    And I modify "src/calculator.py" method "Calculator.divide" (section 3.3)
    And I modify "src/utils.py" function "validate_input" (section 4.1)
    When I run "/rfc-update docs/generated/draft-calculator-00.md"
    Then the change report should show "Files modified: 2"
    And the change report should show "Affected RFC sections: 3 (§3.1, §3.3, §4.1)"
    And sections "3.1", "3.3", "4.1" should be regenerated
    And all other sections should remain unchanged

  Scenario: Validate preservation priority rule
    Given an existing RFC with preserve block "custom-impl" in lines 25-30
    And the preserve block contains manual implementation notes
    And I modify code that generates content for lines 25-30
    When I run "/rfc-update docs/generated/draft-calculator-00.md --force"
    Then the merge should apply preservation priority
    And the preserve block content should take precedence
    And the newly generated content should be discarded for lines 25-30
    And I should see "Conflicts resolved: 1 (preservation priority applied)"

  Scenario: Checkpoint recovery from failed update
    Given an existing RFC document
    And I modify "src/calculator.py"
    When I run "/rfc-update docs/generated/draft-calculator-00.md"
    And the formatter agent fails during execution
    Then I should see a checkpoint message "⚠️  Update failed. Resuming from checkpoint: parser-update-*.json"
    And the parser checkpoint should be preserved
    And the analyzer checkpoint should be preserved
    And I should be able to retry the update

  Scenario: Validate kramdown syntax after update
    Given an existing RFC document
    And I modify "src/calculator.py" method "Calculator.add"
    When I run "/rfc-update docs/generated/draft-calculator-00.md"
    Then the updated RFC should have valid kramdown-rfc syntax
    And I should see a reminder "⚠️  Run `make lint` to validate kramdown syntax"
    And I should see a reminder "⚠️  Run `make txt` to validate XML2RFC schema"

  Scenario: Update with breaking change detection
    Given an existing RFC documenting "Calculator.add(a, b)"
    When I change the signature to "Calculator.add(a, b, c)"
    And I run "/rfc-update docs/generated/draft-calculator-00.md"
    Then the change should be classified as "BREAKING"
    And the impact summary should show "BREAKING changes: 1"
    And the section should be marked for review
    And the change summary should explain "Method signature modified (added parameter 'c')"

  Scenario: Incremental update preserves cross-references
    Given an existing RFC with internal cross-references
    And section "3.1" references section "2.1" with anchor "{{terminology}}"
    When I modify code in section "3.1" only
    And I run "/rfc-update docs/generated/draft-calculator-00.md"
    Then section "3.1" should be regenerated
    And the cross-reference "{{terminology}}" should remain valid
    And section "2.1" should remain unchanged
    And the RFC should have no broken cross-references

  Scenario: Update preserves CODE_REF markers
    Given an existing RFC with "<!-- CODE_REF: src/calculator.py:Calculator.add:56 -->" markers
    When I modify "Calculator.add" (line number changes to 58)
    And I run "/rfc-update docs/generated/draft-calculator-00.md"
    Then the CODE_REF marker should be updated to "<!-- CODE_REF: src/calculator.py:Calculator.add:58 -->"
    And the rfc-map.json mapping should reflect the new line number
    And the cross-reference should point to the correct location

  Scenario: Update with Serena MCP unavailable
    Given an existing RFC document
    And I modify "src/calculator.py"
    But Serena MCP is not available
    When I run "/rfc-update docs/generated/draft-calculator-00.md"
    Then I should see an error "❌ Serena MCP required for code analysis"
    And I should see a suggestion "Ensure Serena MCP server is running"
    And the command should exit with error status
    And the RFC document should not be modified

  Scenario: Update preserves frontmatter metadata
    Given an existing RFC with frontmatter containing "docname: draft-calculator-00"
    And the frontmatter contains "author: John Doe"
    When I modify "src/calculator.py"
    And I run "/rfc-update docs/generated/draft-calculator-00.md"
    Then the updated RFC should retain "docname: draft-calculator-00"
    And the updated RFC should retain "author: John Doe"
    And only the changed sections should be updated (not frontmatter)

  Scenario: Update with section filter produces partial output
    Given an existing RFC document
    And I modify code affecting sections "3.1" and "4.2"
    When the formatter agent is spawned with section_filter ["3.1", "4.2"]
    Then the formatter should only generate sections "3.1" and "4.2"
    And the formatter output should not include frontmatter
    And the formatter output should not include unchanged sections
    And the coordinator should merge the partial output
