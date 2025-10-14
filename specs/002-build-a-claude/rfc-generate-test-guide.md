# RFC Generation End-to-End Test Guide

## ✅ Infrastructure Status

**Make Targets**: OPERATIONAL
- ✅ `make lint` - PASS
- ✅ `make txt` - Generated 3.7K file
- ✅ `make html` - Generated 37K file
- ✅ Dependencies installed (xml2rfc, kramdown-rfc, idnits)

**Test Files**:
- ✅ Root Makefile created (2 lines)
- ✅ Test draft: `draft-plugin-test-latest.md` (validated successfully)

## 📋 Testing /rfc-generate Command

### Test Scenario 1: Generate RFC for Plugin Libraries

The plugin has 4 Python libraries (~1,739 LOC) that are perfect for testing:

```
.claude/lib/impact_analyzer.py    (463 lines)
.claude/lib/preserve_edits.py     (391 lines)
.claude/lib/rfc_mapper.py         (548 lines)
.claude/lib/schema_validator.py   (337 lines)
```

**Command to run**:
```bash
/rfc-generate .claude/lib/ --output draft-plugin-libraries-latest.md
```

**Expected workflow** (from rfc-generate.md):
1. ✅ Parse arguments (paths: .claude/lib/, output: draft-plugin-libraries-latest.md)
2. ✅ Validate Serena MCP availability
3. ✅ Scout phase (discover .py files, estimate LOC)
4. ✅ Spawn Parser agent (extract classes, functions, types)
5. ✅ Spawn Analyzer agent (find relationships, behaviors)
6. ✅ Spawn Formatter agent (generate kramdown-rfc)
7. ✅ **Validation phase (NOW WORKING)**:
   - Step 6a: Kramdown syntax validation via `make lint`
   - Step 6b: XML2RFC schema validation via `make txt`
   - Step 6c: Quality gates (sections, cross-refs, RFC keywords)
8. ✅ Write outputs:
   - `docs/generated/draft-plugin-libraries-latest.md`
   - `docs/rfc-map.json`

**Expected outputs**:
- RFC with sections: Abstract, Terminology, Interfaces, Behavior
- Cross-references linking code to RFC sections
- Mappings in rfc-map.json (code ↔ RFC section)

### Test Scenario 2: Generate RFC for Smaller Subset

If full library generation is too large, test with a single file:

```bash
/rfc-generate .claude/lib/rfc_mapper.py --output draft-rfc-mapper-latest.md
```

### Test Scenario 3: Validate Existing Draft

Test the validation pipeline directly:

```bash
# Generate draft first
/rfc-generate .claude/lib/ --output test-draft.md

# Then validate with Make
cd docs/generated/
make lint
make txt
make html
```

## 🔍 Verification Checklist

After running `/rfc-generate`, verify:

1. **Output files created**:
   - [ ] `docs/generated/draft-*.md` exists
   - [ ] `docs/rfc-map.json` exists
   - [ ] `.claude/.checkpoints/` contains parser/analyzer/formatter JSON

2. **Validation passed**:
   - [ ] Kramdown syntax valid (no lint errors)
   - [ ] XML2RFC schema valid (no schema violations)
   - [ ] Quality gates passed (all required sections present)

3. **Content quality**:
   - [ ] Frontmatter has correct docname (ends with -latest)
   - [ ] Abstract summarizes the code
   - [ ] Terminology section has definitions
   - [ ] Interfaces section documents public APIs
   - [ ] Behavior section describes workflows
   - [ ] Cross-references use correct syntax (`{: #anchor}`, `{{anchor}}`)
   - [ ] Security section has `**[REVIEW REQUIRED]**` marker

4. **Build pipeline works**:
   ```bash
   cd docs/generated/
   make txt  # Should generate .txt file
   make html # Should generate .html file
   ```

## 🐛 Troubleshooting

### Issue: "Serena MCP not available"
**Solution**: Check Serena MCP server is running in Claude Code

### Issue: "No analyzable code found"
**Solution**: Verify path contains .py/.js/.ts files

### Issue: Make validation fails
**Solution**: This was the original issue - NOW FIXED with root Makefile

### Issue: "Validation failed"
**Expected**: Some warnings are normal (e.g., manual review markers)
**Action**: Review validation report, fix critical errors only

## 📊 Success Criteria

PHASE 3 is fully operational when:
- ✅ `/rfc-generate` command completes without errors
- ✅ Validation phase (Step 6) runs successfully
- ✅ RFC document is generated in kramdown-rfc format
- ✅ `make txt` and `make html` produce outputs
- ✅ rfc-map.json contains code-to-RFC mappings

## Next Steps After Successful Test

1. **Review generated RFC**: Check quality of auto-generated content
2. **Test preservation**: Add `**[REVIEW REQUIRED]**` markers, re-run to verify they're preserved
3. **Proceed to Phase 4**: Test `/rfc-update` command (User Story 2)
4. **Optional**: Generate RFC for entire plugin codebase

---

**Current Status**: Infrastructure complete, ready for end-to-end testing ✅
