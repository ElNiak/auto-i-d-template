# Feature: RFC Document Generation
# Purpose: Test initial RFC document generation from source code
# User Story 1: Generate Initial RFC Documentation

Feature: RFC Document Generation
  As a developer
  I want to generate RFC documentation from my source code
  So that I can create standards-compliant specifications

  Background:
    Given a clean test repository
    And the RFC generator plugin is installed

  Scenario: Generate RFC from clean repository with default settings
    Given a sample project with known structure
    When I run "/rfc-generate" command
    Then an RFC document should be created in "docs/generated/"
    And the RFC document should contain "Abstract" section
    And the RFC document should contain "Introduction" section
    And the RFC document should contain "Terminology" section
    And the RFC document should contain "Interfaces" section
    And the RFC document should contain "Behavior" section
    And a "docs/rfc-map.json" file should be created
    And the rfc-map.json should contain code-to-section mappings

  Scenario: Generate RFC for specific paths
    Given a sample project with multiple directories
    And I want to document only "src/" and "lib/" directories
    When I run "/rfc-generate src/ lib/ --output draft-myproject-00.md"
    Then an RFC document should be created at "docs/generated/draft-myproject-00.md"
    And the RFC should only reference code from "src/" and "lib/"
    And the RFC should not reference code from other directories

  Scenario: Generate RFC with specific sections filter
    Given a sample project with known structure
    When I run "/rfc-generate --sections interfaces,terminology"
    Then an RFC document should be created
    And the RFC document should contain "Terminology" section
    And the RFC document should contain "Interfaces" section
    And the RFC document should not contain "Behavior" section
    And the RFC document should not contain "Security Considerations" section

  Scenario: Verify cross-references accuracy
    Given a sample project with function "calculateTotal" in "src/calculator.py"
    And the function is a public API
    When I run "/rfc-generate src/"
    Then the RFC "Interfaces" section should reference "calculateTotal"
    And the rfc-map.json should map "calculateTotal" to an RFC section
    And the mapping should include file path "src/calculator.py"
    And the mapping should include line numbers

  Scenario: Handle empty paths gracefully
    Given an empty project directory
    When I run "/rfc-generate"
    Then I should see a warning "No analyzable code found"
    And no RFC document should be created
    And the command should exit with status code 1

  Scenario: Handle Serena MCP unavailable
    Given a sample project with known structure
    But Serena MCP is not available
    When I run "/rfc-generate"
    Then I should see an error "Serena MCP not available"
    And I should see a suggestion "Ensure Serena MCP server is running"
    And the command should exit with status code 2

  Scenario: Generate RFC with kramdown-rfc frontmatter
    Given a sample project with metadata
    When I run "/rfc-generate --output draft-myproject-00.md"
    Then the RFC should have valid kramdown-rfc frontmatter
    And the frontmatter should include "docname"
    And the frontmatter should include "title"
    And the frontmatter should include "author"
    And the frontmatter should include "category"
    And the docname should match pattern "draft-[a-z0-9-]+-latest"

  Scenario: Extract terminology from type definitions
    Given a sample project with TypeScript interfaces
    And the project has interface "User" with fields
    When I run "/rfc-generate"
    Then the RFC "Terminology" section should define "User"
    And the definition should list the interface fields
    And the cross-reference should link to the source code

  Scenario: Document public APIs in interfaces section
    Given a sample project with public function "authenticate"
    And the function has parameters and return type
    When I run "/rfc-generate"
    Then the RFC "Interfaces" section should document "authenticate"
    And the documentation should include parameters
    And the documentation should include return type
    And the documentation should reference RFC 2119 keywords if present

  Scenario: Describe behavioral patterns
    Given a sample project with state machine logic
    When I run "/rfc-generate"
    Then the RFC "Behavior" section should describe the state transitions
    And the behavior description should reference the implementation
    And the cross-reference should point to specific code lines

  Scenario: Generate RFC with external standard references
    Given a sample project that implements "OAuth 2.0"
    And the code includes comments referencing "RFC 6749"
    When I run "/rfc-generate"
    Then the RFC "References" section should include "RFC 6749"
    And the reference should be formatted per IETF standards
    And inline citations should link to the bibliography

  Scenario: Validate generated RFC structure
    Given a sample project with known structure
    When I run "/rfc-generate"
    And I run "make lint" on the generated RFC
    Then the linter should pass without errors
    And kramdown-rfc syntax should be valid
    And xml2rfc should be able to process the document
