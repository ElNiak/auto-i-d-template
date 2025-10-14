# rfc-map.json Schema Validation Report

## File: docs/rfc-map.json

### Root Level Validation

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| JSON valid | Valid JSON | ✅ Valid | PASS |
| Has "version" | Required | ✅ "1.0.0" | PASS |
| Version format | ^\d+\.\d+\.\d+$ | ✅ Matches | PASS |
| Has "mappings" | Required array | ✅ Array[10] | PASS |
| Extra fields | None (strict) | ⚠️ 4 extra fields | WARNING |

**Extra Fields Found**:
- `generated_at` (not in schema, but useful metadata)
- `rfc_file` (not in schema, but useful metadata)
- `source_paths` (not in schema, but useful metadata)
- `statistics` (not in schema, but useful metadata)

**Note**: Extra fields are non-breaking extensions for enhanced functionality.

---

### Mapping Entry Validation (10 entries)

#### Entry Structure Validation

| Field | Required | Present in All | Status |
|-------|----------|----------------|--------|
| code | Yes | ✅ 10/10 | PASS |
| code.file | Yes | ✅ 10/10 | PASS |
| code.symbol | Yes | ✅ 10/10 | PASS |
| code.line | Yes | ✅ 10/10 | PASS |
| rfc | Yes | ✅ 10/10 | PASS |
| rfc.section | Yes | ✅ 10/10 | PASS |
| rfc.heading | Yes | ✅ 10/10 | PASS |
| relationship | Yes | ✅ 10/10 | PASS |
| last_synced | Yes | ✅ 10/10 | PASS |
| file_checksum | Yes | ✅ 10/10 | PASS |
| staleness_status | Yes | ✅ 10/10 | PASS |
| git_commit | Optional | ✅ 10/10 | PASS |

---

#### Field Format Validation

| Field | Pattern/Type | Validation Result | Status |
|-------|--------------|-------------------|--------|
| code.line | >= 1 | ✅ All positive (24-119) | PASS |
| rfc.section | ^\d+(\.\d+)*$ | ✅ All valid (3.1-5.2) | PASS |
| relationship | Enum | ✅ All "implements" | PASS |
| last_synced | ISO 8601 | ✅ "2025-10-13T12:15:00Z" | PASS |
| file_checksum | ^[a-f0-9]{64}$ | ❌ "abc123def456" (12 chars) | **FAIL** |
| git_commit | ^[a-f0-9]{40}$ | ❌ "266cd94" (7 chars) | **FAIL** |
| staleness_status | Enum | ✅ All "fresh" | PASS |

---

### Schema Violations

#### Critical Issues

**1. file_checksum Format Invalid**
- **Expected**: SHA256 hash (64 hexadecimal characters)
- **Pattern**: `^[a-f0-9]{64}$`
- **Actual**: `"abc123def456"` (12 characters)
- **Impact**: **HIGH** - Staleness detection will not work correctly
- **Fix Required**: Generate actual SHA256 hash of source file

**2. git_commit Format Invalid**
- **Expected**: Full git commit hash (40 hexadecimal characters)
- **Pattern**: `^[a-f0-9]{40}$`
- **Actual**: `"266cd94"` (7 characters, short hash)
- **Impact**: **MEDIUM** - Git traceability incomplete
- **Fix Required**: Use full commit hash from `git rev-parse HEAD`

#### Non-Critical Issues

**3. Extra Root Fields**
- **Fields**: `generated_at`, `rfc_file`, `source_paths`, `statistics`
- **Impact**: **LOW** - Violates strict schema but provides useful metadata
- **Recommendation**: Document as schema extensions or make schema less strict

---

### Sample Entry Analysis

Entry #1 (Calculator.add):
```json
{
  "code": {
    "file": "tests/fixtures/sample-project/src/calculator.py",  ✅
    "symbol": "Calculator.add",                                  ✅
    "line": 56                                                   ✅ (positive int)
  },
  "rfc": {
    "section": "3.1",                                           ✅ (matches ^\d+(\.\d+)*$)
    "heading": "Addition Operation"                              ✅
  },
  "relationship": "implements",                                  ✅ (valid enum)
  "last_synced": "2025-10-13T12:15:00Z",                        ✅ (valid ISO 8601)
  "file_checksum": "abc123def456",                              ❌ (invalid SHA256)
  "git_commit": "266cd94",                                      ❌ (short hash)
  "staleness_status": "fresh"                                    ✅ (valid enum)
}
```

---

### Data Integrity Checks

| Check | Result | Status |
|-------|--------|--------|
| No duplicate mappings | ✅ All unique | PASS |
| Section numbering valid | ✅ Hierarchical (3.x, 4.x, 5.x) | PASS |
| Line numbers positive | ✅ All >= 1 | PASS |
| Timestamps valid | ✅ ISO 8601 format | PASS |
| All required fields present | ✅ 100% | PASS |
| Enum values valid | ✅ 100% | PASS |

---

### Coverage Analysis

**Code Coverage**:
- Files analyzed: 1 (calculator.py)
- Symbols documented: 10 methods
- Expected symbols: 11 (Calculator class + 11 methods)
- Missing: Constructor (`__init__`) may not be mapped

**RFC Coverage**:
- Sections mapped: 3.1-3.5, 4.1-4.3, 5.1-5.2 (10 sections)
- Expected major sections: ~7 (Introduction, Terminology, Interfaces, Behavior, Security, IANA, References)
- Actual mapped sections: 3 major (§3 Interfaces, §4 Memory, §5 History)

---

### Validation Summary

**Overall Status**: ⚠️ **PARTIAL COMPLIANCE**

**Pass**: 18/20 checks (90%)
**Fail**: 2/20 checks (10%)

**Critical Issues**:
1. ❌ Invalid file_checksum format (not SHA256)
2. ❌ Invalid git_commit format (short hash)

**Recommendations**:
1. **MUST FIX**: Generate proper SHA256 checksums using `hashlib.sha256()`
2. **MUST FIX**: Use full git commit hashes from `git rev-parse HEAD`
3. **SHOULD CONSIDER**: Document extra root fields as extensions or relax schema
4. **OPTIONAL**: Map constructor (`__init__`) if semantically relevant

---

### Production Readiness

| Aspect | Status | Notes |
|--------|--------|-------|
| Schema compliance (core) | ✅ 90% | Structure and required fields correct |
| Format compliance | ❌ 80% | Checksum/commit formats invalid |
| Data integrity | ✅ 100% | No duplicates, valid relationships |
| Coverage | ✅ Good | 10/11 methods mapped |
| Usability | ⚠️ Degraded | Staleness detection won't work |

**Verdict**: File is **functional for MVP** but needs checksum/commit fixes for production staleness detection.
