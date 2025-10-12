# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **i-d-template** repository - a Makefile-driven build system for authoring IETF Internet-Drafts (RFCs). It enables authors to write drafts in Markdown or XML and automatically generate standards-compliant text/HTML outputs, manage versions, and submit to the IETF datatracker.

**Core Philosophy**: Build automation through GNU Make. All RFC transformations (markdown→XML→txt/html) go through the Makefile infrastructure. Never reimplement build logic - always invoke existing Make targets.

## Architecture

### Build Pipeline

```
Draft Source (*.md or *.xml)
    ↓
main.mk (orchestrator)
    ↓
kramdown-rfc/mmark → xml2rfc → txt/html outputs
    ↓
validation (idnits, lint)
    ↓
publishing (datatracker upload, gh-pages)
```

**Key Makefiles**:
- `main.mk`: Entry point, orchestrates all build targets
- `id.mk`: Draft identification and version numbering
- `setup.mk`: Repository initialization (NOT included by main.mk - standalone)
- `deps.mk`: Dependency management (Python venv, Ruby bundler, npm)
- `ghpages.mk`: GitHub Pages automation
- `upload.mk`: IETF datatracker submission

### Directory Structure

```
lib/                    # This repository (cloned into draft repos)
├── *.mk               # Makefile modules
├── *.py               # Python helper scripts
├── *.sh               # Bash helper scripts
├── template/          # Files copied to draft repositories on setup
│   ├── Makefile       # Stub that includes lib/main.mk
│   ├── .github/workflows/  # CI automation
│   └── .gitignore
└── docker/            # Docker images for CI

template/              # Template files for new draft repos
example/               # Example draft files
doc/                   # Documentation
tests/                 # BDD tests (behave framework)
specs/                 # Feature specifications (new plugin development)
```

## Common Commands

### Building Drafts

```bash
make                    # Build txt and html, run lint
make txt                # Generate .txt output only
make html               # Generate .html output only
make pdf                # Generate PDF from txt
make clean              # Remove generated files
```

### Validation and Quality

```bash
make lint               # Check formatting (whitespace, docname)
make fix-lint           # Auto-fix lint issues
make idnits             # Run IETF idnits checker
make diff               # Show diff vs last submitted version
```

### Repository Setup

```bash
# In a NEW draft repository:
make -f lib/setup.mk    # Full setup (creates files, gh-pages branch)
make -f lib/setup.mk setup-default-branch  # Setup without pushing gh-pages
```

### Publishing Workflow

```bash
make gh-pages           # Update gh-pages branch with latest HTML
git tag -a draft-name-version-02
make upload             # Upload tagged version to IETF datatracker
```

### Dependency Management

```bash
make update-deps        # Update xml2rfc, kramdown-rfc, etc.
```

## Development Workflow

### When Modifying Makefiles

1. **Test with existing test suite**:
   ```bash
   cd tests
   behave                # Run all BDD scenarios
   behave features/build.feature  # Run specific feature
   ```

2. **Understand Make module boundaries**:
   - `main.mk` handles core build logic
   - `setup.mk` is standalone (not included by main.mk)
   - New features should go in appropriate `.mk` file or create new module

3. **Preserve backward compatibility**:
   - Existing draft repositories must continue working
   - Check `PRE_SETUP` flag for pre/post-setup behavior differences
   - Test with both submodule and cloned lib scenarios

### When Adding Python Scripts

- **Environment**: Scripts run in Python 3.6+ venv (created in `lib/venv`)
- **Dependencies**: Add to `requirements.txt` (auto-installed by deps.mk)
- **Invocation**: Scripts are called from Makefiles via `$(python)` variable
- **Pattern**: See `extract-metadata.py`, `setup-codeowners.py` for examples

### When Adding Shell Scripts

- **Shebang**: Use `#!/usr/bin/env bash` (portability)
- **Error handling**: Use `set -e` to fail on errors
- **Tracing**: Use `$(trace)` Make variable for verbose output
- **Pattern**: See `setup-readme.sh`, `build-index.sh` for examples

## Key Concepts

### Draft Naming Convention

- **File name**: `draft-source-name.md` (no version number)
- **Internal docname**: `draft-source-name-latest` (replaced with version by tools)
- **Tagged version**: `draft-source-name-02` (git tag)

### Template vs. Draft Repository

- **This repository (i-d-template)**: Contains build tools (`lib/`)
- **Draft repository**: Author's repo with draft source and `lib/` (clone or submodule)
- **Setup process**: Copies `template/` files to draft repo, creates stub Makefile

### CI Automation (GitHub Actions)

- **ghpages.yml**: Auto-update editor's copy on push
- **publish.yml**: Auto-upload tagged versions to datatracker
- **archive.yml**: Periodic backup of issues/PRs
- Defined in `template/.github/workflows/`

### Trace System

- `TRACE_FILE` environment variable: Path to trace output file
- `$(trace)` Make function: Wrapper for command invocation with timing/status
- `format-trace.sh`: Formats trace output for GitHub Actions summaries

## Testing

### BDD Tests (Behave)

```bash
cd tests
behave                  # Run all scenarios
behave --tags=@wip      # Run work-in-progress scenarios
```

- **Framework**: Python behave (Gherkin syntax)
- **Features**: `tests/*.feature` files
- **Steps**: `tests/steps/*.py` files
- **Environment**: `tests/environment.py` (setup/teardown)

### Test Patterns

- Tests create temporary git repos in `$TMPDIR`
- Fixtures copy template files to test repos
- Scenarios verify build outputs, error handling, CI behavior

## Plugin Development (specs/001-claude-code-plugin)

**Active Feature**: RFC generation plugin for Claude Code that leverages i-d-template in external projects.

**Architecture Principles**:
- MUST invoke existing Makefile targets (no reimplementation)
- MUST NOT break backward compatibility
- Uses Python 3.11+ for hooks, Bash for Make integration
- Follows test-driven development

**Key Files**:
- `specs/001-claude-code-plugin/spec.md`: Feature specification
- `specs/001-claude-code-plugin/plan.md`: Implementation plan
- `specs/001-claude-code-plugin/tasks.md`: Ordered task list (to be generated)

## Environment Variables

- `LIBDIR`: Path to i-d-template lib (default: `lib`)
- `CI`: Set to `true` in CI environments
- `VERBOSE`: Set to `true` for detailed output
- `NO_RUBY`: Set to `true` to skip Ruby dependencies
- `NO_NODEJS`: Set to `true` to skip Node.js dependencies
- `GITHUB_TOKEN`: For authenticated GitHub API calls

## Common Pitfalls

- **Don't modify `main.mk` directly in draft repos** - changes belong in this repository
- **Git hooks require symlink** - `make setup-precommit` creates `.git/hooks/pre-commit` symlink
- **Version tags need `-a` flag** - `git tag -a draft-name-02` (annotated tags required)
- **Setup.mk is standalone** - Not included by main.mk, run with `make -f lib/setup.mk`
- **Intermediate XML files are auto-deleted** - Mark as `.SECONDARY` in Makefile if needed

## Dependencies

**Required**:
- GNU Make (Mac users: `brew install make` for newer version)
- Python 3.6+ with pip and venv
- Ruby with gem and bundler (for kramdown-rfc)

**Optional**:
- mmark (for `%%%`-style markdown)
- Node.js/npm (for additional tools like aasvg)
- xml2rfc, idnits (auto-installed by deps.mk)

**Virtual Environments**:
- Python: `lib/venv/` (created by venv.mk)
- Ruby: `lib/.gems/` (managed by bundler)
- Node: `node_modules/` (managed by npm)

## Contributing

- **Pull Requests**: Test with BDD suite before submitting
- **Backward Compatibility**: Verify existing draft repos still work
- **Documentation**: Update relevant doc/*.md files
- **Constitution**: For plugin development, follow specs/001-claude-code-plugin/plan.md principles
