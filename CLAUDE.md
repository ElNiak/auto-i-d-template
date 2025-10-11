# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the i-d-template repository - a comprehensive build system for authoring IETF Internet-Drafts. It provides Makefile-based tooling that converts source files (markdown, XML, or org-mode) into RFC-formatted text and HTML documents. The repository itself is not a draft; it's a template/library that other draft repositories clone and use as `lib/`.

## Core Architecture

### Makefile Structure (main.mk as entry point)
- **main.mk**: Primary build orchestration - includes all other makefiles, defines basic targets (txt, html, pdf), and handles markdown-to-XML conversion pipeline
- **config.mk**: Tool configuration (xml2rfc, kramdown-rfc, mmark paths and options)
- **id.mk**: Internet-Draft identification logic - discovers draft files, calculates version numbers from git tags, determines next/previous versions
- **deps.mk**: Dependency management for Python (pip/venv), Ruby (bundler/gem), and Node.js (npm) packages
- **ghpages.mk**: GitHub Pages branch management and HTML index generation
- **upload.mk**: Automated submission to IETF datatracker via API
- **archive.mk**: GitHub issues/PR archiving
- **update.mk**: Template self-update mechanism
- **venv.mk**: Python virtual environment management
- **targets.mk**: Target file discovery and tracking

### Build Pipeline Flow
1. Source files (*.md, *.xml, *.org) → XML (v3 format)
2. XML → txt (via xml2rfc) and HTML (via xml2rfc or XSLT)
3. Markdown preprocessing: MD_PREPROCESSOR → kramdown-rfc/mmark → add-note.py → xml2rfc v2v3 conversion → optional rfc-tidy

### Key Python Scripts
- **add-note.py**: Adds venue/status notes to XML
- **extract-metadata.py**: Extracts draft metadata for processing
- **default-branch.py**: Determines repository default branch
- **setup-codeowners.py**: Generates GitHub CODEOWNERS files

### Draft Discovery Logic (id.mk)
Patterns searched: `draft-*.{md,xml,org}` and `rfc[0-9]{1,5}.{md,xml,org}`
Version tags: `draft-*-[0-9][0-9]` format (e.g., draft-ietf-foo-bar-03)
The `-latest` suffix in docname fields is replaced with calculated version numbers during build.

## Common Development Commands

### Building Drafts
```sh
make              # Build txt and html, run lint (equivalent to: make latest lint)
make txt          # Build .txt files only
make html         # Build .html files only
make pdf          # Build PDF files
make next         # Build submission-ready files (with actual version numbers)
make diff         # Generate rfcdiff HTML showing changes from last submission
```

### Quality Checks
```sh
make lint         # Run all linters (whitespace, docname, default-branch)
make fix-lint     # Automatically fix lint issues (trailing whitespace, missing newlines)
make idnits       # Run idnits validation tool (requires npm or idnits_bin)
make spellcheck   # Run codespell on draft source files
make check        # Alias for idnits
```

### GitHub Pages and Publishing
```sh
make gh-pages     # Update gh-pages branch with built drafts and index
make upload       # Upload tagged draft versions to IETF datatracker
make issues       # Archive GitHub issues/PRs to repository
```

### Dependency Management
```sh
make update-deps  # Update installed tools in lib/ venvs
make clean        # Remove built files (txt, html, pdf, intermediate xml)
make clean-all    # Remove built files and all installed dependencies
```

## Repository Setup for Draft Authors

Draft repositories using this template should:
1. Clone this repository as `lib/`: `git clone https://github.com/martinthomson/i-d-template lib`
2. Create draft source file: `draft-<source>-<name>.{md|xml|org}`
3. Run setup: `make -f lib/setup.mk` (generates Makefile, README.md, .gitignore, GitHub workflows)
4. The generated Makefile simply includes `lib/main.mk`

## Important Conventions

### Draft Naming
- Filenames: `draft-<source>-<name>.<ext>` (no version number)
- Inside documents: Use `-latest` instead of version numbers (e.g., `draft-ietf-foo-bar-latest`)
- Version numbers calculated from git tags: `draft-<source>-<name>-##`

### Markdown Formats
- kramdown-rfc: Files starting with `---` (YAML frontmatter)
- mmark: Files starting with `%%%`
- Both are converted to XML v3, then processed through xml2rfc

### File Includes
Markdown files can include other files using `{::include filename}` or `{::include-nested filename}`
Dependencies are tracked in auto-generated `.includes.mk`

## GitHub Actions Integration

Template provides workflows (in template/.github/workflows/):
- **ghpages.yml**: Auto-update editor's copy on gh-pages branch
- **publish.yml**: Auto-submit tagged versions to datatracker
- **archive.yml**: Periodic backup of issues/PRs
- **update.yml**: Check for template updates

Docker images used:
- Default: `ghcr.io/martinthomson/i-d-template-action:latest`
- Math variant: Use `@v1m` tag for additional tools

## Testing

Tests use Python behave (BDD framework):
- **tests/**: Feature files (*.feature) and step definitions (steps/)
- **tests/environment.py**: Test environment setup
- Features: build.feature, git.feature, setup.feature, upload.feature

## Extension Points for Draft Repositories

### Custom Preprocessing
```make
MD_PREPROCESSOR := python3 script.py args
draft-foo.xml: script.py dependencies
```

### Custom Linting
```make
.PHONY: my-lint
my-lint: $(drafts_source)
	# validation logic
lint:: my-lint
```

### Dependencies
Add to repository root:
- **requirements.txt**: Python packages (installed in lib/venv)
- **Gemfile**: Ruby gems (installed in lib/.gems)
- **package.json**: Node.js packages (installed in node_modules)

## Environment Variables

- **CI**: Set to `true` in CI environments (enables verbose output)
- **VERBOSE**: Set to `true` for verbose build output
- **NO_RUBY**: Set to `true` to disable kramdown-rfc (skip Ruby dependencies)
- **USE_XSLT**: Set to `true` to use rfc2629.xslt instead of xml2rfc for HTML
- **GITHUB_TOKEN**: Required for API access (gh-pages push, issue archiving, upload)
- **TEXT_PAGINATION**: Set to `true` to enable pagination in .txt output

## Git Hooks

Setup installs pre-commit hook (pre-commit.sh) that runs:
- `make lint` (fail on errors)
- Draft build check (fail if builds don't succeed)

## Notes for Development

- The `lib/` directory in draft repositories should be kept in sync via `git pull` or `make -f lib/update.mk update-master`
- Main branch detection uses `default-branch.py` which queries GitHub API or examines git remote HEAD
- Version number calculation: parses git tags matching `draft-*-##`, increments for next version
- The `TRACE_FILE` mechanism (trace.sh) is used for build step tracking in GitHub Actions summaries
