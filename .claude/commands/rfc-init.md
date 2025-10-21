---
description: Initialize RFC generation environment and validate prerequisites
argument-hint: [--force] [--verbose]
---

# /rfc-init - Initialize RFC Generation Environment

Validates and sets up all prerequisites required for RFC document generation, including Serena MCP connection, build tools, and dependencies.

## Arguments Provided

```
$ARGUMENTS
```

## Overview

This command performs a comprehensive check of the RFC generation environment and installs missing dependencies. It validates:

1. **Serena MCP Server**: Code analysis capability
2. **Build System**: GNU Make and i-d-template integration
3. **Dependencies**: Python venv, Ruby gems, Node.js packages
4. **RFC Tools**: kramdown-rfc, xml2rfc, idnits
5. **Directory Structure**: Required folders for checkpoints and output

## Workflow

### Step 1: Parse Arguments

Extract optional flags:
- `--force`: Reinstall dependencies even if present
- `--verbose`: Show detailed output from installation commands

### Step 2: Check Serena MCP Availability

**Purpose**: Verify code analysis capability

**Test Command**:
```python
try:
    result = mcp__serena__list_dir(relative_path=".", recursive=false)
    serena_available = True
    print("✅ Serena MCP: Connected and responsive")
except Exception as e:
    serena_available = False
    print(f"❌ Serena MCP: Not available - {e}")
```

**If Unavailable**:
```
❌ ERROR: Serena MCP server is required for RFC generation

Troubleshooting:
1. Check MCP server status: Claude Code menu → MCP Servers
2. Verify .mcp.json configuration exists
3. Restart Claude Code to reload MCP servers
4. Check logs: ~/.claude/logs/mcp-serena.log

Documentation: https://docs.claude.com/en/docs/claude-code/mcp

Cannot proceed without Serena MCP. Please resolve and run /rfc-init again.
```

**Action**: STOP if Serena MCP unavailable

---

### Step 3: Check Build System

#### 3a. Verify GNU Make

**Test Command**:
```bash
make --version 2>&1 | head -1
```

**Expected**: `GNU Make 4.x` or higher

**If Missing**:
```
⚠️  WARNING: GNU Make not found or version too old

macOS: brew install make
Linux: sudo apt-get install make (Debian/Ubuntu)
       sudo yum install make (Red Hat/CentOS)
```

#### 3b. Check i-d-template Integration

**Test**: Look for Makefile in repository root

```bash
if [ -f "Makefile" ]; then
    echo "✅ Build System: Makefile found"

    # Check if it includes i-d-template
    if grep -q "include.*main.mk" Makefile; then
        echo "✅ i-d-template: Integrated"
    else
        echo "⚠️  Makefile exists but may not use i-d-template"
    fi
else
    echo "⚠️  No Makefile found - i-d-template may not be set up"
    echo "   Run: make -f lib/setup.mk (if lib/ exists)"
fi
```

---

### Step 4: Install Dependencies

**Approach**: Leverage existing `deps.mk` infrastructure (Makefile-first principle)

**Command**:
```bash
make deps
```

This installs:
- **Python packages** from `requirements.txt` (xml2rfc, idnits, etc.)
- **Ruby gems** from `Gemfile` (kramdown-rfc2629, etc.)
- **Node.js packages** from `package.json` (if present)

**Progress Reporting**:
```
📦 Installing dependencies...

Python (venv):
  - xml2rfc==3.x.x
  - kramdown-rfc==1.x.x
  - idnits==2.x.x

Ruby (bundler):
  - kramdown-rfc2629
  - kramdown-parser-gfm

✅ Dependencies installed successfully
```

**Error Handling**:
```bash
if make deps 2>&1 | grep -q "error\|Error\|ERROR"; then
    echo "❌ Dependency installation failed"
    echo "   Check logs above for details"
    echo "   Common issues:"
    echo "   - Python venv creation failed (check Python 3.6+ installed)"
    echo "   - Ruby bundler not available (install: gem install bundler)"
    echo "   - Network issues (check internet connection)"
    exit 1
fi
```

---

### Step 5: Validate RFC Tools

Test each tool individually with version check:

#### 5a. kramdown-rfc

```bash
if command -v kramdown-rfc2629 &> /dev/null; then
    version=$(kramdown-rfc2629 --version 2>&1 | head -1)
    echo "✅ kramdown-rfc: $version"
else
    echo "❌ kramdown-rfc: Not found after installation"
    echo "   Try: bundle exec kramdown-rfc2629 --version"
fi
```

#### 5b. xml2rfc

```bash
if command -v xml2rfc &> /dev/null; then
    version=$(xml2rfc --version 2>&1 | head -1)
    echo "✅ xml2rfc: $version"
else
    echo "❌ xml2rfc: Not found in PATH"
    echo "   Check Python venv: source .venv/bin/activate"
fi
```

#### 5c. Make Targets

Test dry-run of critical Make targets:

```bash
# Test lint target (dry-run, no actual execution)
if make -n lint &> /dev/null; then
    echo "✅ Make target: lint (available)"
else
    echo "⚠️  Make target: lint (not available - check Makefile)"
fi

# Test txt target
if make -n txt &> /dev/null; then
    echo "✅ Make target: txt (available)"
else
    echo "⚠️  Make target: txt (not available)"
fi
```

---

### Step 6: Create Directory Structure

Create required directories for RFC generation workflow:

```bash
mkdir -p docs/generated/
mkdir -p .claude/.checkpoints/
mkdir -p .claude/.temp/

echo "✅ Directory structure created:"
echo "   - docs/generated/ (RFC output)"
echo "   - .claude/.checkpoints/ (agent recovery)"
echo "   - .claude/.temp/ (build artifacts)"
```

---

### Step 7: Generate Initialization Report

**Success Report**:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  RFC Generation Environment: READY ✅
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Prerequisites:
  ✅ Serena MCP         Connected (semantic analysis)
  ✅ GNU Make           4.3 (build orchestration)
  ✅ i-d-template       Integrated (RFC pipeline)

RFC Tools:
  ✅ kramdown-rfc       1.6.11 (Markdown → XML)
  ✅ xml2rfc            3.16.0 (XML → txt/html)
  ✅ idnits             2.17.1 (compliance checker)

Directory Structure:
  ✅ docs/generated/     (RFC outputs)
  ✅ .claude/.checkpoints/ (recovery)
  ✅ .claude/.temp/      (build artifacts)

Next Steps:
  1. Generate RFC: /rfc-generate [paths]
  2. Validate: make lint && make txt
  3. Review: open docs/generated/draft-*.md

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Save Initialization Marker**:
```bash
cat > .claude/.rfc-init-complete <<EOF
# RFC Generation Environment Initialized
# Date: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
# Serena MCP: Available
# Make: $(make --version | head -1)
# kramdown-rfc: $(kramdown-rfc2629 --version 2>&1 | head -1)
# xml2rfc: $(xml2rfc --version 2>&1 | head -1)
EOF

echo "✅ Saved initialization status to .claude/.rfc-init-complete"
```

---

### Step 8: Partial Success Handling

If some components are missing but core tools work:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  RFC Generation Environment: PARTIAL ⚠️
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Prerequisites:
  ✅ Serena MCP         Connected
  ✅ GNU Make           4.3
  ⚠️  i-d-template       Not detected (may need setup)

RFC Tools:
  ✅ kramdown-rfc       1.6.11
  ✅ xml2rfc            3.16.0
  ❌ idnits             Not found (optional, for compliance checking)

Status:
  Core RFC generation: AVAILABLE
  Full validation:      INCOMPLETE

You can proceed with /rfc-generate, but some validation
steps may be skipped. Run 'make deps' to install missing tools.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Error Handling

### Critical Errors (Must Stop)

1. **Serena MCP Unavailable**:
   - Error: Cannot proceed without code analysis capability
   - Action: Display troubleshooting steps, EXIT 1

2. **No Make Available**:
   - Error: Build system required
   - Action: Display installation instructions, EXIT 1

3. **Dependency Installation Fails**:
   - Error: Cannot install kramdown-rfc or xml2rfc
   - Action: Display error logs, suggest manual installation, EXIT 1

### Non-Critical Warnings (Can Continue)

1. **idnits Not Found**:
   - Warning: Compliance checking will be limited
   - Action: Continue, note in report

2. **i-d-template Not Integrated**:
   - Warning: May need manual Make setup
   - Action: Continue, suggest `make -f lib/setup.mk`

---

## Use Cases

### First-Time Setup

```bash
# User runs on fresh repository
/rfc-init

# Output: Installs everything, creates directories, validates
# Result: Ready to generate RFCs
```

### Re-validation After System Changes

```bash
# User upgraded Python or Ruby
/rfc-init

# Output: Checks versions, confirms tools still work
# Result: Reports any issues
```

### Force Reinstall

```bash
# User suspects corrupted dependencies
/rfc-init --force

# Output: Reinstalls all dependencies from scratch
# Result: Clean environment
```

### CI/CD Integration

```bash
# In GitHub Actions workflow
- name: Initialize RFC Environment
  run: claude-code /rfc-init

- name: Generate RFC
  run: claude-code /rfc-generate src/
```

---

## Configuration Checks

The command also validates these configuration files exist:

**Optional (warn if missing)**:
- `requirements.txt` (Python dependencies)
- `Gemfile` (Ruby dependencies)
- `package.json` (Node.js dependencies)

**Created if missing**:
- `.gitignore` (adds `.venv/`, `node_modules/`, `.gems/`)

---

## Troubleshooting Guide

Include inline help for common issues:

### Issue: "Serena MCP not available"

**Symptoms**: Test call to `mcp__serena__list_dir` fails

**Solutions**:
1. Check `.mcp.json` exists and has serena configuration
2. Restart Claude Code
3. Check MCP server logs: `~/.claude/logs/`
4. Verify Serena MCP is enabled in Claude Code settings

### Issue: "kramdown-rfc not found"

**Symptoms**: `kramdown-rfc2629 --version` fails

**Solutions**:
1. Check Ruby bundler installed: `gem install bundler`
2. Check Gemfile exists in project root
3. Run: `bundle install --gemfile=lib/Gemfile`
4. Try: `bundle exec kramdown-rfc2629 --version`

### Issue: "xml2rfc not found"

**Symptoms**: `xml2rfc --version` fails

**Solutions**:
1. Check Python venv activated
2. Check requirements.txt exists
3. Run: `pip install -r requirements.txt`
4. Check PATH includes `.venv/bin`

---

## Implementation Notes

**Makefile-First Principle**:
- Use `make deps` for installation (don't reimplement)
- Use `make -n` for dry-run validation
- Delegate to Make targets where possible

**Error Reporting**:
- Use clear, actionable error messages
- Include troubleshooting steps inline
- Log detailed errors to `.claude/.rfc-init.log`

**Idempotency**:
- Safe to run multiple times
- Checks before installing
- Updates `.rfc-init-complete` marker with timestamp

**Platform Support**:
- macOS: Uses homebrew suggestions
- Linux: Uses apt/yum suggestions
- Windows: WSL assumed (bash required)

---

## Example Output

```
$ /rfc-init

🔍 Checking RFC Generation Prerequisites...

[1/5] Serena MCP Server
  ✅ Connected and responsive

[2/5] Build System
  ✅ GNU Make 4.3
  ✅ i-d-template integrated

[3/5] Installing Dependencies
  📦 Python packages (venv)...
     - xml2rfc 3.16.0 ✅
     - idnits 2.17.1 ✅
  📦 Ruby gems (bundler)...
     - kramdown-rfc2629 1.6.11 ✅

[4/5] Validating RFC Tools
  ✅ kramdown-rfc 1.6.11
  ✅ xml2rfc 3.16.0
  ✅ idnits 2.17.1
  ✅ Make targets: lint, txt, html

[5/5] Directory Structure
  ✅ docs/generated/
  ✅ .claude/.checkpoints/
  ✅ .claude/.temp/

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  RFC Generation Environment: READY ✅
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

All prerequisites satisfied. You can now:
  • Generate RFCs: /rfc-generate [paths]
  • Validate output: make lint && make txt
  • View documentation: docs/generated/

Environment saved to: .claude/.rfc-init-complete
```

---

## References

- **deps.mk**: Dependency management infrastructure
- **setup.mk**: Repository initialization
- **Serena MCP**: Code analysis tools
- **i-d-template docs**: doc/SETUP.md, doc/TOOLS.md
