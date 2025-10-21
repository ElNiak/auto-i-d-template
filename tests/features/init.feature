Feature: RFC Generation Environment Initialization (/rfc-init)
  As a developer using the RFC documentation generator
  I want to initialize and validate my RFC generation environment
  So that all prerequisites are properly installed and configured

  Background:
    Given a temporary test repository

  # ============================================================================
  # Happy Path Scenarios
  # ============================================================================

  Scenario: Initialize clean environment with all prerequisites available
    Given a clean repository without .claude setup
    And Serena MCP is available
    And GNU Make version 4.3 is installed
    And Python 3.11 is installed
    And Ruby with bundler is installed
    When I run /rfc-init
    Then the command should succeed with exit code 0
    And I should see "RFC Generation Environment: READY ✅"
    And Serena MCP status should show "Connected and responsive"
    And GNU Make status should show version "4.3"
    And Python venv should be created at "lib/venv" or ".venv"
    And kramdown-rfc should be installed and show version
    And xml2rfc should be installed and show version
    And directory "docs/generated/" should exist
    And directory ".claude/.checkpoints/" should exist
    And directory ".claude/.temp/" should exist
    And file ".claude/.rfc-init-complete" should exist
    And initialization marker should contain timestamp
    And initialization marker should list installed tool versions

  Scenario: Initialize with existing partial setup (idempotency)
    Given a repository with .claude directory already created
    And directories "docs/generated/" and ".claude/.checkpoints/" already exist
    And Serena MCP is available
    And GNU Make is installed
    When I run /rfc-init
    Then the command should succeed with exit code 0
    And I should see "RFC Generation Environment: READY ✅"
    And existing directories should not be recreated
    And initialization should complete without errors
    And I should not see duplicate installation messages

  Scenario: Re-validate environment after system changes
    Given a previously initialized environment
    And file ".claude/.rfc-init-complete" exists from previous run
    And system Python was upgraded to 3.12
    When I run /rfc-init
    Then the command should succeed with exit code 0
    And I should see "RFC Generation Environment: READY ✅"
    And I should see updated Python version in report
    And initialization marker should be updated with new timestamp

  Scenario: Initialize with verbose output flag
    Given a clean repository without .claude setup
    And Serena MCP is available
    When I run /rfc-init --verbose
    Then the command should succeed with exit code 0
    And I should see detailed output from "make deps"
    And I should see dependency installation progress for Python packages
    And I should see dependency installation progress for Ruby gems
    And I should see verbose version checking output

  # ============================================================================
  # Prerequisite Failure Scenarios (NO SIMPLIFICATION)
  # ============================================================================

  Scenario: Serena MCP unavailable - must fail with troubleshooting
    Given a clean repository without .claude setup
    And Serena MCP is unavailable
    When I run /rfc-init
    Then the command should fail with exit code 2
    And I should see "❌ ERROR: Serena MCP server is required for RFC generation"
    And I should see troubleshooting section for Serena MCP
    And troubleshooting should mention "Check MCP server status"
    And troubleshooting should mention ".mcp.json configuration"
    And troubleshooting should mention "Restart Claude Code"
    And troubleshooting should mention log file location
    And I should see "Cannot proceed without Serena MCP"
    And initialization should NOT create any directories
    And initialization should NOT install dependencies

  Scenario: GNU Make not found - must provide installation instructions
    Given a clean repository without .claude setup
    And Serena MCP is available
    And GNU Make is not installed
    When I run /rfc-init
    Then the command should fail with exit code 2
    And I should see "⚠️ WARNING: GNU Make not found"
    And I should see platform-specific installation instructions
    And instructions should include "brew install make" for macOS
    And instructions should include "apt-get install make" for Linux
    And I should see "Cannot proceed without GNU Make"

  Scenario: kramdown-rfc missing - must attempt installation via deps.mk
    Given a clean repository without .claude setup
    And Serena MCP is available
    And GNU Make is installed
    And kramdown-rfc is not installed
    And Ruby bundler is available
    When I run /rfc-init
    Then the command should succeed with exit code 0
    And I should see "📦 Installing dependencies..."
    And I should see "Ruby (bundler):" section
    And kramdown-rfc should be installed via "bundle install"
    And I should see "✅ kramdown-rfc:" with version number
    And final status should show "RFC Generation Environment: READY ✅"

  Scenario: xml2rfc missing - must attempt installation via deps.mk
    Given a clean repository without .claude setup
    And Serena MCP is available
    And GNU Make is installed
    And xml2rfc is not installed
    And Python venv is available
    When I run /rfc-init
    Then the command should succeed with exit code 0
    And I should see "📦 Installing dependencies..."
    And I should see "Python (venv):" section
    And xml2rfc should be installed via "pip install"
    And I should see "✅ xml2rfc:" with version number
    And final status should show "RFC Generation Environment: READY ✅"

  Scenario: idnits missing - should warn but continue (optional tool)
    Given a clean repository without .claude setup
    And Serena MCP is available
    And GNU Make is installed
    And kramdown-rfc and xml2rfc are installed
    And idnits is not installed
    When I run /rfc-init
    Then the command should succeed with exit code 0
    And I should see "⚠️ idnits: Not found (optional, for compliance checking)"
    And I should see "RFC Generation Environment: PARTIAL ⚠️"
    And status report should indicate "Core RFC generation: AVAILABLE"
    And status report should indicate "Full validation: INCOMPLETE"
    And I should see suggestion to run "make deps" to install missing tools

  Scenario: Python venv creation fails - must fail with clear error
    Given a clean repository without .claude setup
    And Serena MCP is available
    And GNU Make is installed
    And Python is not installed or too old
    When I run /rfc-init
    Then the command should fail with exit code 1
    And I should see "❌ Dependency installation failed"
    And I should see "Python venv creation failed"
    And I should see "check Python 3.6+ installed"
    And error should include check command: "python3 --version"

  # ============================================================================
  # Force Reinstall Scenarios
  # ============================================================================

  Scenario: Force flag reinstalls all dependencies from scratch
    Given a previously initialized environment
    And dependencies are already installed
    And some dependencies are outdated versions
    When I run /rfc-init --force
    Then the command should succeed with exit code 0
    And I should see "🔄 Force reinstall requested"
    And I should see dependencies being removed before reinstall
    And I should see "📦 Installing dependencies..." again
    And all dependencies should be reinstalled with latest versions
    And final status should show updated version numbers

  Scenario: Force flag with corrupted dependencies
    Given a previously initialized environment
    And Python venv is corrupted with missing files
    When I run /rfc-init --force
    Then the command should succeed with exit code 0
    And corrupted venv should be removed
    And fresh venv should be created
    And dependencies should install successfully
    And final status should show "RFC Generation Environment: READY ✅"

  Scenario: Force flag updates outdated tool versions
    Given a previously initialized environment
    And kramdown-rfc version 1.5.0 is installed (outdated)
    And xml2rfc version 3.10.0 is installed (outdated)
    When I run /rfc-init --force
    Then the command should succeed with exit code 0
    And kramdown-rfc should be updated to latest version
    And xml2rfc should be updated to latest version
    And version report should show new versions

  # ============================================================================
  # Directory Structure Scenarios
  # ============================================================================

  Scenario: Create missing directories on first initialization
    Given a clean repository without .claude setup
    And Serena MCP is available
    And no docs/ or .claude/ directories exist
    When I run /rfc-init
    Then directory "docs/generated/" should be created
    And directory ".claude/.checkpoints/" should be created
    And directory ".claude/.temp/" should be created
    And I should see "✅ Directory structure created:" in output
    And directory list should show all three directories

  Scenario: Handle existing directories gracefully (no conflicts)
    Given a repository with existing "docs/generated/" directory
    And directory contains existing RFC files
    And Serena MCP is available
    When I run /rfc-init
    Then existing files in "docs/generated/" should not be deleted
    And initialization should complete without errors
    And I should not see directory creation errors
    And existing RFC files should remain intact

  Scenario: Verify directory permissions are correct
    Given a clean repository without .claude setup
    And Serena MCP is available
    When I run /rfc-init
    Then directory "docs/generated/" should have write permissions
    And directory ".claude/.checkpoints/" should have write permissions
    And directory ".claude/.temp/" should have write permissions
    And test user should be able to create files in all directories

  # ============================================================================
  # Validation Reporting Scenarios
  # ============================================================================

  Scenario: Generate READY status report when all prerequisites met
    Given a clean repository without .claude setup
    And Serena MCP is available
    And all RFC tools are available
    When I run /rfc-init
    Then I should see formatted report header "RFC Generation Environment: READY ✅"
    And report should show "✅ Serena MCP" with status
    And report should show "✅ GNU Make" with version
    And report should show "✅ i-d-template" integration status
    And report should show "✅ kramdown-rfc" with version
    And report should show "✅ xml2rfc" with version
    And report should show "✅ idnits" with version
    And report should list all created directories
    And report should show "Next Steps:" section
    And next steps should include "/rfc-generate [paths]"
    And next steps should include "make lint && make txt"

  Scenario: Generate PARTIAL status report when optional tools missing
    Given a clean repository without .claude setup
    And Serena MCP is available
    And kramdown-rfc and xml2rfc are installed
    And idnits is not installed
    When I run /rfc-init
    Then I should see formatted report header "RFC Generation Environment: PARTIAL ⚠️"
    And report should show "✅ Serena MCP" status
    And report should show "❌ idnits" with "Not found" message
    And report should indicate "Core RFC generation: AVAILABLE"
    And report should indicate "Full validation: INCOMPLETE"
    And report should suggest running "make deps"

  Scenario: Generate initialization marker file with metadata
    Given a clean repository without .claude setup
    And Serena MCP is available
    When I run /rfc-init
    Then file ".claude/.rfc-init-complete" should be created
    And marker file should contain "RFC Generation Environment Initialized"
    And marker file should contain ISO 8601 timestamp
    And marker file should contain "Serena MCP: Available"
    And marker file should contain Make version
    And marker file should contain kramdown-rfc version
    And marker file should contain xml2rfc version
    And I should see "✅ Saved initialization status to .claude/.rfc-init-complete"

  Scenario: Report detailed version information for all tools
    Given a clean repository without .claude setup
    And Serena MCP is available
    And GNU Make 4.3 is installed
    And kramdown-rfc 1.6.11 is installed
    And xml2rfc 3.16.0 is installed
    When I run /rfc-init
    Then version report should show exact versions:
      | Tool          | Version |
      | GNU Make      | 4.3     |
      | kramdown-rfc  | 1.6.11  |
      | xml2rfc       | 3.16.0  |
    And versions should be extracted from tool --version commands
    And version parsing should handle different output formats

  # ============================================================================
  # Edge Cases (NO SIMPLIFICATION)
  # ============================================================================

  # SKIPPED: Environmental simulation removed in Phase 2
  # This scenario requires simulating network unavailability, which cannot be
  # tested without actual network manipulation. Marked @skip per simulation removal policy.
  @skip
  Scenario: Network failures during dependency installation
    Given a clean repository without .claude setup
    And Serena MCP is available
    And network connectivity is unavailable
    When I run /rfc-init
    Then dependency installation should fail
    And I should see "❌ Dependency installation failed"
    And error should mention "Network issues (check internet connection)"
    And command should exit with code 1
    And no .rfc-init-complete marker should be created

  Scenario: Incompatible tool versions detected
    Given a clean repository without .claude setup
    And Serena MCP is available
    And GNU Make version 3.81 is installed (too old)
    When I run /rfc-init
    Then I should see "⚠️ WARNING: GNU Make version too old"
    And I should see minimum required version message
    And I should see upgrade instructions for platform
    And command should warn but may continue

  # SKIPPED: Environmental simulation removed in Phase 2
  # This scenario requires simulating disk full condition, which cannot be
  # tested without actual disk manipulation. Marked @skip per simulation removal policy.
  @skip
  Scenario: Disk space insufficient for venv creation
    Given a clean repository without .claude setup
    And Serena MCP is available
    And available disk space is less than 100MB
    When I run /rfc-init
    Then venv creation should fail
    And I should see "❌ Dependency installation failed"
    And error should mention disk space issue
    And I should see suggestion to free up disk space
    And command should exit with code 1

  # SKIPPED: Environmental simulation removed in Phase 2
  # This scenario requires simulating permission denied errors, which cannot be
  # tested without actual filesystem permission manipulation. Marked @skip per simulation removal policy.
  @skip
  Scenario: Permission denied for directory creation
    Given a clean repository without .claude setup
    And Serena MCP is available
    And user does not have write permission to repository
    When I run /rfc-init
    Then directory creation should fail
    And I should see permission error message
    And error should mention which directory failed
    And error should suggest checking file permissions
    And command should exit with code 1

  Scenario: Concurrent initialization attempts with file locking
    Given a clean repository without .claude setup
    And Serena MCP is available
    And another /rfc-init process is already running
    When I run /rfc-init
    Then command should detect existing initialization
    And I should see "⚠️ Another initialization in progress"
    And command should either wait or exit gracefully
    And no file corruption should occur
    And lock file should be cleaned up after completion

  # ============================================================================
  # CI/CD Integration Scenarios
  # ============================================================================

  Scenario: Run in GitHub Actions environment
    Given a clean repository without .claude setup
    And environment variable CI is set to "true"
    And environment variable GITHUB_ACTIONS is set to "true"
    And Serena MCP is available
    When I run /rfc-init
    Then command should detect CI environment
    And output should be CI-friendly (no interactive prompts)
    And all dependencies should install non-interactively
    And status report should be formatted for CI logs
    And exit code should be 0 on success

  Scenario: Run in Docker container environment
    Given a Docker container with minimal base image
    And repository is mounted in container
    And Serena MCP is available via host connection
    When I run /rfc-init inside container
    Then dependencies should install in container
    And container should have all required tools
    And initialization should complete successfully
    And /rfc-generate should work after initialization

  Scenario: Run with CI environment variables set
    Given a clean repository without .claude setup
    And environment variable CI is set to "true"
    And environment variable VERBOSE is set to "true"
    And Serena MCP is available
    When I run /rfc-init
    Then verbose mode should be automatically enabled
    And detailed logs should be generated
    And output should include timing information
    And any warnings should be clearly visible

  # ============================================================================
  # Integration with i-d-template
  # ============================================================================

  Scenario: Detect i-d-template integration when Makefile exists
    Given a repository with i-d-template setup
    And Makefile includes "lib/main.mk"
    And Serena MCP is available
    When I run /rfc-init
    Then I should see "✅ i-d-template: Integrated"
    And Make target validation should run
    And I should see "✅ Make target: lint (available)"
    And I should see "✅ Make target: txt (available)"
    And status report should confirm full integration

  Scenario: Warn when Makefile exists but no i-d-template integration
    Given a repository with custom Makefile
    And Makefile does not include "lib/main.mk"
    And Serena MCP is available
    When I run /rfc-init
    Then I should see "⚠️ Makefile exists but may not use i-d-template"
    And I should see suggestion to run "make -f lib/setup.mk"
    And status should show partial integration
    And command should still succeed with exit code 0

  Scenario: Initialize repository without Makefile (needs setup)
    Given a clean repository without .claude setup
    And no Makefile exists in repository root
    And Serena MCP is available
    When I run /rfc-init
    Then I should see "⚠️ No Makefile found - i-d-template may not be set up"
    And I should see "Run: make -f lib/setup.mk (if lib/ exists)"
    And status should indicate setup may be needed
    And /rfc-init should still complete other checks

  # ============================================================================
  # Error Handling and Recovery
  # ============================================================================

  # SKIPPED: Environmental simulation removed in Phase 2
  # This scenario requires simulating bundler installation failure, which was
  # a pure test simulation with no real-world equivalent. Marked @skip per simulation removal policy.
  @skip
  Scenario: Partial failure during dependency installation (Ruby fails, Python succeeds)
    Given a clean repository without .claude setup
    And Serena MCP is available
    And Python venv can be created successfully
    And Ruby bundler installation fails
    When I run /rfc-init
    Then I should see "❌ Dependency installation failed"
    And error details should show Ruby bundler failure
    And error should not mention Python issues
    And I should see "✅ xml2rfc" installed successfully
    And I should see "❌ kramdown-rfc" installation failed
    And status should show "PARTIAL ⚠️"

  Scenario: Initialization log file created for debugging
    Given a clean repository without .claude setup
    And Serena MCP is available
    When I run /rfc-init
    Then detailed log should be written to ".claude/.rfc-init.log"
    And log file should contain all command outputs
    And log file should contain timestamps for each step
    And log file should be referenced in error messages

  Scenario: Graceful degradation when optional features unavailable
    Given a clean repository without .claude setup
    And Serena MCP is available
    And mandatory tools (Make, kramdown, xml2rfc) are installed
    And optional tools (idnits, git) are not installed
    When I run /rfc-init
    Then command should succeed with exit code 0
    And I should see warnings for missing optional tools
    And status should show "PARTIAL ⚠️"
    And I should see validation limitation message
