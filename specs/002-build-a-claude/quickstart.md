# Quick Start Guide: RFC Documentation Generator

## Installation

1. **Clone the plugin into your repository:**
```bash
cd your-project
cp -r path/to/rfc-generator/.claude .claude
```

2. **Verify installation:**
```bash
# Should show rfc-generate, rfc-update, rfc-validate commands
ls .claude/commands/
```

## Basic Usage

### Generate Initial RFC Documentation

```bash
# Generate RFC for entire codebase
/rfc-generate

# Generate RFC for specific paths
/rfc-generate src/ lib/ --output draft-myproject-spec-00.md

# Generate specific sections only
/rfc-generate src/ --sections interfaces,terminology
```

### Update Existing Documentation

```bash
# Update RFC after code changes
/rfc-update draft-myproject-spec-00.md

# Check what changed
git diff docs/generated/
```

### Validate RFC Compliance

```bash
# Validate generated RFC
/rfc-validate draft-myproject-spec-00.md

# This runs: make lint idnits rfclint
```

## How It Works

### Agent Workflow

1. **User invokes slash command** → `/rfc-generate src/`
2. **Coordinator agent spawned** → Orchestrates the workflow
3. **Parser agent analyzes code** → Uses Serena MCP tools:
   - `mcp__serena__get_symbols_overview` for structure
   - `mcp__serena__find_symbol` for details
4. **Analyzer agent finds patterns** → Extracts semantics
5. **Formatter agent generates RFC** → Creates kramdown-rfc markdown
6. **Validator agent checks compliance** → Runs Make targets

### Generated Files

```
docs/
├── generated/
│   └── draft-myproject-spec-00.md    # RFC document
└── rfc-map.json                       # Code ↔ RFC mappings
```

### Preservation of Manual Edits

Mark sections to preserve during updates:

```markdown
<!-- @preserve-start -->
This content will not be overwritten during updates.
You can add manual clarifications here.
<!-- @preserve-end -->
```

## Configuration

### Mandatory Sections

Configure in `/rfc-generate` command:
- Default: All IETF standard sections
- Options: `interfaces`, `terminology`, `behavior`, `security`

### Performance Tuning

For large codebases (>100K lines):
- Automatic chunking with 10K lines per chunk
- 500 line overlap for context preservation
- Incremental processing with caching

## Integration with i-d-template

The plugin generates kramdown-rfc format compatible with i-d-template:

```bash
# After generating RFC with plugin
cd docs/generated/

# Use i-d-template to create outputs
make txt html pdf

# Validate
make lint idnits

# When ready to submit
git tag -a draft-myproject-spec-00
make upload
```

## Common Workflows

### Initial Documentation

1. Start with clean codebase
2. Run `/rfc-generate` to create initial RFC
3. Review and add manual content in `@preserve` blocks
4. Run `make txt html` to generate outputs
5. Commit the generated RFC

### Continuous Updates

1. Make code changes
2. Pre-commit hook detects changes to public APIs
3. Run `/rfc-update` to update RFC
4. Review changes with `git diff`
5. Run validation with `make lint`
6. Commit updated RFC

### Code Review Integration

1. PR created with code changes
2. CI runs impact analysis
3. Affected RFC sections listed in PR comment
4. Reviewer checks documentation updates
5. Merge when both code and docs approved

## Troubleshooting

### "Serena MCP not available"
- Ensure Serena MCP server is running
- Check Claude-Code MCP configuration

### "No analyzable code found"
- Verify paths contain supported language files
- Check file permissions

### "Validation failed"
- Run `make fix-lint` for auto-fixes
- Check idnits output for specific issues
- Ensure all mandatory sections present

### "Manual edits lost"
- Check `@preserve-start/end` markers are correct
- Verify markers weren't accidentally deleted
- Check git history for the file

## Best Practices

1. **Start Simple**: Generate basic structure first, enhance manually
2. **Preserve Wisely**: Only preserve truly manual content
3. **Review Changes**: Always review `/rfc-update` output
4. **Validate Often**: Run validation before committing
5. **Use Git Tags**: Tag stable RFC versions

## Limitations

- Cannot infer design rationale (requires human input)
- Security considerations need manual review
- Normative language (MUST/SHOULD) requires human judgment
- Complex architectural decisions need human documentation

## Support

- Report issues: [GitHub Issues]
- Documentation: See `.claude/agents/` for agent details
- Constitution: Follow i-d-template constitution principles