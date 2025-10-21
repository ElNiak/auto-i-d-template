# Manual Validation: /rfc-update Command

**Purpose**: Validate the incremental RFC update workflow before creating automated BDD tests.

**Test Fixture**: `tests/fixtures/sample-project/src/calculator.py`

---

## Test Scenario: Update RFC After Code Change

### 1. Initial State (Before Code Change)

#### 1.1 Existing RFC Document
**File**: `tests/fixtures/sample-project/docs/generated/draft-calculator-00.md`

```markdown
---
title: "Calculator Technical Specification"
docname: draft-calculator-00
category: info
---

--- abstract

This specification defines the Calculator API for basic arithmetic operations.

--- middle

# Introduction

This document specifies the Calculator service interface and behavior.

# Terminology

Calculator:
: A service that performs arithmetic operations on numeric values

Memory:
: Persistent storage for a single numeric value across operations

<!-- CODE_REF: src/calculator.py:Calculator:11 -->

# Interfaces {: #interfaces}

## Arithmetic Operations {: #arithmetic-ops}

### Calculator.add {: #calc-add}

<!-- CODE_REF: src/calculator.py:Calculator.add:56 -->

The service MUST support addition of two numeric values.

Parameters:
- `a` (float): First operand
- `b` (float): Second operand

Returns:
- `float`: Sum of a and b

### Calculator.subtract {: #calc-subtract}

<!-- CODE_REF: src/calculator.py:Calculator.subtract:71 -->

The service MUST support subtraction operations.

Parameters:
- `a` (float): Minuend
- `b` (float): Subtrahend

Returns:
- `float`: Difference of a minus b

# Behavior {: #behavior}

## Operation History

The Calculator MUST maintain a history of all operations performed.

<!-- CODE_REF: src/calculator.py:Calculator.history:22 -->

# Security Considerations {: #security}

@preserve-start id:security-notes

**[MANUAL EDIT]** The Calculator service processes user-provided numeric inputs.
Implementations MUST validate input types and ranges to prevent:

1. **Integer Overflow**: Reject values exceeding platform limits
2. **Division by Zero**: The divide() method includes explicit checks (§3.3)
3. **Type Confusion**: All inputs MUST be validated as numeric types

These security requirements were reviewed with the security team on 2025-10-10.

@preserve-end

--- back

# References
```

#### 1.2 Existing rfc-map.json
**File**: `tests/fixtures/sample-project/docs/rfc-map.json`

```json
{
  "version": "1.0.0",
  "mappings": [
    {
      "code": {
        "file": "src/calculator.py",
        "symbol": "Calculator",
        "line": 11
      },
      "rfc": {
        "section": "2",
        "heading": "Terminology"
      },
      "relationship": "describes",
      "last_synced": "2025-10-13T10:00:00Z",
      "confidence": 1.0
    },
    {
      "code": {
        "file": "src/calculator.py",
        "symbol": "Calculator.add",
        "line": 56
      },
      "rfc": {
        "section": "3.1",
        "heading": "Calculator.add"
      },
      "relationship": "implements",
      "last_synced": "2025-10-13T10:00:00Z",
      "confidence": 1.0
    },
    {
      "code": {
        "file": "src/calculator.py",
        "symbol": "Calculator.subtract",
        "line": 71
      },
      "rfc": {
        "section": "3.2",
        "heading": "Calculator.subtract"
      },
      "relationship": "implements",
      "last_synced": "2025-10-13T10:00:00Z",
      "confidence": 1.0
    }
  ]
}
```

---

### 2. Code Modification (Simulate Developer Change)

**Modify**: `src/calculator.py` lines 56-69

**Before**:
```python
def add(self, a: float, b: float) -> float:
    """
    Add two numbers

    Args:
        a: First number
        b: Second number

    Returns:
        float: Sum of a and b
    """
    result = a + b
    self.history.append(('add', a, b, result))
    return result
```

**After** (add optional `c` parameter):
```python
def add(self, a: float, b: float, c: float = 0.0) -> float:
    """
    Add two or three numbers

    Args:
        a: First number
        b: Second number
        c: Optional third number (default: 0.0)

    Returns:
        float: Sum of a, b, and optionally c
    """
    result = a + b + c
    self.history.append(('add', a, b, c, result))
    return result
```

**Git commit**:
```bash
git add src/calculator.py
git commit -m "feat: Add optional third parameter to Calculator.add()"
```

---

### 3. Run /rfc-update Command

```bash
/rfc-update docs/generated/draft-calculator-00.md
```

---

### 4. Expected Workflow Execution

#### Step 1: Load Existing State
```
✅ Loading existing RFC: docs/generated/draft-calculator-00.md
✅ Loading rfc-map.json: docs/rfc-map.json (3 mappings)
📝 Found 1 preserve block:
  - Line 45-55: @preserve-start id:security-notes
```

#### Step 2: Detect Changed Code
```
📊 Change Detection Report:
  - Files modified: 1 (src/calculator.py)
  - Affected RFC sections: 1 (§3.1)
  - Severity: 1 BREAKING, 0 COMPATIBLE, 0 MINOR
  - Unchanged sections: 4 (will be preserved)

Affected Sections:
  § 3.1 Calculator.add - BREAKING
    - src/calculator.py:Calculator.add (line 56)
    - Change: Method signature modified (added parameter 'c')
    - Changed lines: 56-69
```

#### Step 3: Validate Preserve Blocks
```
✅ No preserve block conflicts detected
✅ Preserve block 'security-notes' (lines 45-55) validated
```

#### Step 4: Spawn Agents (Filtered)
```
🤖 Spawning parser agent (filtered to src/calculator.py only)...
✅ Parser checkpoint: .claude/.checkpoints/parser-update-1697198400.json

🤖 Spawning analyzer agent (filtered to Calculator.add only)...
✅ Analyzer checkpoint: .claude/.checkpoints/analyzer-update-1697198400.json

🤖 Spawning formatter agent (section filter: ["3.1"])...
✅ Formatter checkpoint: .claude/.checkpoints/formatter-update-1697198400.json
```

#### Step 5: Merge with Preserved Content
```
🔀 Merge Summary:
  - Sections updated: 1 (§3.1)
  - Sections preserved: 4 (§1, §2, §3.2, §4, §5)
  - Preserve blocks honored: 1 (security-notes)
  - Conflicts resolved: 0
```

#### Step 6: Update rfc-map.json
```
✅ Updated timestamp for src/calculator.py:Calculator.add
✅ Saved rfc-map.json (3 mappings, 1 updated)
```

#### Step 7: Write Outputs
```
✅ RFC Updated Successfully

Files Updated:
  📄 docs/generated/draft-calculator-00.md
  🔗 docs/rfc-map.json
  📊 .claude/.checkpoints/ (3 checkpoints)

Changes:
  - Sections regenerated: 1 (§3.1 Calculator.add)
  - Sections preserved: 4
  - Preserve blocks honored: 1 (security-notes)
  - Manual edits retained: ✅

Impact Summary:
  - BREAKING changes: 1 (§3.1 Method signature changed)
  - COMPATIBLE changes: 0

Validation:
  ⚠️  Run `make lint` to validate kramdown syntax
  ⚠️  Run `make txt` to validate XML2RFC schema

Next Steps:
  1. Review regenerated section: §3.1
  2. Validate: make txt html
  3. Compare: git diff docs/generated/draft-calculator-00.md
  4. Commit: git add docs/ && git commit -m "docs: Update RFC after Calculator.add() change"
```

---

### 5. Expected Output: Updated RFC Document

**File**: `docs/generated/draft-calculator-00.md` (after update)

**Changed Section** (§3.1 only):
```markdown
### Calculator.add {: #calc-add}

<!-- CODE_REF: src/calculator.py:Calculator.add:56 -->

The service MUST support addition of two or three numeric values.

Parameters:
- `a` (float): First operand
- `b` (float): Second operand
- `c` (float): Optional third operand (default: 0.0)

Returns:
- `float`: Sum of a, b, and optionally c

Example:
~~~python
>>> calc = Calculator()
>>> calc.add(1.0, 2.0)
3.0
>>> calc.add(1.0, 2.0, 3.0)
6.0
~~~
```

**Unchanged Sections**:
- Abstract (preserved)
- Introduction (preserved)
- Terminology (preserved)
- §3.2 Calculator.subtract (preserved)
- Behavior section (preserved)
- **Security Considerations** (preserved with @preserve block intact):
  ```markdown
  @preserve-start id:security-notes

  **[MANUAL EDIT]** The Calculator service processes user-provided numeric inputs.
  Implementations MUST validate input types and ranges to prevent:

  1. **Integer Overflow**: Reject values exceeding platform limits
  2. **Division by Zero**: The divide() method includes explicit checks (§3.3)
  3. **Type Confusion**: All inputs MUST be validated as numeric types

  These security requirements were reviewed with the security team on 2025-10-10.

  @preserve-end
  ```

---

### 6. Expected Output: Updated rfc-map.json

**Changed**:
```json
{
  "code": {
    "file": "src/calculator.py",
    "symbol": "Calculator.add",
    "line": 56
  },
  "rfc": {
    "section": "3.1",
    "heading": "Calculator.add"
  },
  "relationship": "implements",
  "last_synced": "2025-10-15T14:30:00Z",  ← UPDATED TIMESTAMP
  "confidence": 1.0
}
```

**Unchanged** (other 2 mappings retain old timestamps):
```json
{
  "last_synced": "2025-10-13T10:00:00Z"  ← OLD TIMESTAMP (not changed)
}
```

---

## Validation Checklist

### ✅ Functional Requirements

- [ ] **FR-001**: Detect code changes via git diff
- [ ] **FR-002**: Load existing RFC and rfc-map.json
- [ ] **FR-003**: Extract and validate @preserve blocks
- [ ] **FR-004**: Identify affected RFC sections (only §3.1 in this case)
- [ ] **FR-005**: Spawn agents with filtered inputs (only changed files)
- [ ] **FR-006**: Regenerate only affected sections (not entire RFC)
- [ ] **FR-007**: Preserve manual edits within @preserve blocks
- [ ] **FR-008**: Update rfc-map.json timestamps selectively
- [ ] **FR-009**: Maintain unchanged sections verbatim

### ✅ Error Handling

- [ ] **EH-001**: Abort if RFC file doesn't exist
- [ ] **EH-002**: Abort if rfc-map.json doesn't exist
- [ ] **EH-003**: Abort on overlapping @preserve blocks (ERROR)
- [ ] **EH-004**: Warn on @preserve block conflicts (WARNING)
- [ ] **EH-005**: Provide actionable error messages

### ✅ Preservation Priority

- [ ] **PP-001**: @preserve blocks take precedence over generated content
- [ ] **PP-002**: Preserved content survives merge operation
- [ ] **PP-003**: apply_preservation_priority() safety check passes

### ✅ Performance

- [ ] **PF-001**: Only parse changed files (not entire codebase)
- [ ] **PF-002**: Only analyze changed symbols
- [ ] **PF-003**: Only format changed sections
- [ ] **PF-004**: Deduplication prevents unnecessary work

---

## Edge Cases to Test

### Edge Case 1: No Changes Detected
**Input**: No code changes since last RFC update
**Expected**: Early exit with message "✅ No code changes detected. RFC is up-to-date."

### Edge Case 2: Overlapping @preserve Blocks
**Input**: RFC with overlapping preserve markers
```markdown
@preserve-start id:block1
Content A
  @preserve-start id:block2  ← NESTED, INVALID
  Content B
  @preserve-end
Content C
@preserve-end
```
**Expected**: ERROR + abort with message:
```
❌ Preserve block conflicts detected:
  - Overlapping preserve blocks: block1 (lines 10-20) and block2 (lines 12-18)

Fix preserve blocks and try again.
```

### Edge Case 3: @preserve Block Overlaps with Changed Section
**Input**: Manual edits in §3.1, but §3.1 needs regeneration
**Expected**: WARNING + prompt (or --force to continue)
```
⚠️  Preserve block warnings:
  - Preserve block 'custom-notes' (lines 25-30) overlaps with changed section §3.1

Continue anyway? Preserve blocks will take precedence. (Use --force to skip)
```

### Edge Case 4: Missing rfc-map.json
**Input**: RFC exists but rfc-map.json was deleted
**Expected**: ERROR + guidance
```
❌ No traceability map found. Cannot determine changed sections.

Options:
  1. Regenerate from scratch: /rfc-generate src/
  2. Restore rfc-map.json from git history
```

### Edge Case 5: Multiple Files Changed
**Input**: Changes in src/calculator.py and src/utils.py
**Expected**: Detect all affected sections, regenerate multiple sections
```
📊 Change Detection Report:
  - Files modified: 2 (src/calculator.py, src/utils.py)
  - Affected RFC sections: 3 (§3.1, §3.3, §4.1)
  - Severity: 1 BREAKING, 2 COMPATIBLE

Affected Sections:
  § 3.1 Calculator.add - BREAKING
  § 3.3 Calculator.divide - COMPATIBLE
  § 4.1 Validation Utilities - COMPATIBLE
```

---

## Next Steps

1. **Manual Testing** (if possible):
   - Set up test fixture with generated RFC
   - Make code change
   - Run `/rfc-update` command
   - Verify outputs match expectations

2. **Create BDD Tests** (T028-T029):
   - Convert this validation scenario to Behave feature file
   - Implement step definitions
   - Add edge case scenarios
   - Automate regression testing

---

**Status**: Ready for BDD test implementation (T028-T029)
**Created**: 2025-10-15
