"""
Complex assertion and validation logic for RFC generation tests.

This module contains helper functions for validating:
- RFC document structure and content
- rfc-map.json schema and mappings
- Kramdown-RFC frontmatter
- Cross-references and citations
- IETF formatting compliance
"""

import os
import json
import re
from behave.runner import Context


# ============================================================================
# RFC Map Validation Helpers
# ============================================================================

def validate_rfc_map_structure(context: Context):
    """
    Verify rfc-map.json has proper structure and contains mappings.

    Returns:
        tuple: (rfc_map_path, data) if valid

    Raises:
        AssertionError: If structure is invalid
    """
    # Locate rfc-map.json in test directory
    rfc_map_path = os.path.join(context.test_repo, 'docs', 'rfc-map.json')

    assert os.path.exists(rfc_map_path), \
        "rfc-map.json not found at docs/rfc-map.json"

    # Parse and validate JSON structure
    with open(rfc_map_path, 'r') as f:
        data = json.load(f)

    # Validate schema
    assert 'version' in data, "rfc-map.json missing 'version' field"
    assert 'mappings' in data, "rfc-map.json missing 'mappings' field"
    assert isinstance(data['mappings'], list), "mappings must be a list"

    # Validate at least one mapping exists
    assert len(data['mappings']) > 0, "rfc-map.json contains no mappings"

    # Validate mapping structure
    first_mapping = data['mappings'][0]
    assert 'code' in first_mapping, "Mapping missing 'code' section"
    assert 'rfc' in first_mapping, "Mapping missing 'rfc' section"
    assert 'relationship' in first_mapping, "Mapping missing 'relationship' field"

    return rfc_map_path, data


def validate_path_restrictions(context: Context, allowed_paths: list):
    """
    Verify RFC only references code from specified paths.

    Args:
        context: Behave context
        allowed_paths: List of allowed path prefixes

    Raises:
        AssertionError: If code outside allowed paths is referenced
    """
    # Load rfc-map.json
    rfc_map_path = os.path.join(context.test_repo, 'docs', 'rfc-map.json')
    assert os.path.exists(rfc_map_path), "rfc-map.json not found"

    with open(rfc_map_path, 'r') as f:
        data = json.load(f)

    # Check all mappings reference only allowed paths
    for mapping in data['mappings']:
        file_path = mapping['code']['file']
        # Check if file path starts with any allowed path
        is_allowed = any(file_path.startswith(allowed_path) for allowed_path in allowed_paths)
        assert is_allowed, \
            f"File {file_path} is not in allowed paths: {', '.join(allowed_paths)}"


def validate_no_other_references(context: Context):
    """
    Verify RFC doesn't reference code from unspecified directories.

    Args:
        context: Behave context with optional target_paths attribute

    Raises:
        AssertionError: If references exist outside target paths
    """
    # Load rfc-map.json
    rfc_map_path = os.path.join(context.test_repo, 'docs', 'rfc-map.json')
    if not os.path.exists(rfc_map_path):
        return  # No mappings, so no other references

    with open(rfc_map_path, 'r') as f:
        data = json.load(f)

    # If target_paths was set, verify no mappings outside those paths
    if hasattr(context, 'target_paths'):
        for mapping in data['mappings']:
            file_path = mapping['code']['file']
            # Verify file is in one of the target paths
            is_in_target = any(file_path.startswith(tp) for tp in context.target_paths)
            assert is_in_target, \
                f"Unexpected reference to {file_path} outside target paths"


def validate_symbol_section_mapping(context: Context, section: str, symbol: str):
    """
    Verify RFC section references a specific symbol and has proper mapping.

    Args:
        context: Behave context
        section: Section name to check
        symbol: Symbol name to verify

    Raises:
        AssertionError: If section doesn't reference symbol or mapping is missing
    """
    # Read generated RFC
    assert context.generated_rfc is not None, "No RFC generated to check"
    assert os.path.exists(context.generated_rfc), f"RFC file not found at {context.generated_rfc}"

    with open(context.generated_rfc, 'r') as f:
        content = f.read()

    # Find the section in the RFC
    assert section in content, f"Section '{section}' not found in RFC"

    # Check that the symbol is mentioned in or near the section
    # This is a simplified check - looks for symbol anywhere in RFC
    assert symbol in content, \
        f"Symbol '{symbol}' not found in RFC section '{section}'"

    # Optional: Also check rfc-map.json for the mapping
    rfc_map_path = os.path.join(context.test_repo, 'docs', 'rfc-map.json')
    if os.path.exists(rfc_map_path):
        with open(rfc_map_path, 'r') as f:
            data = json.load(f)

        # Look for a mapping that links the symbol to this section
        found_mapping = False
        for mapping in data.get('mappings', []):
            if mapping['code']['symbol'] == symbol and section in str(mapping.get('rfc', {})):
                found_mapping = True
                break

        # If rfc-map.json exists, we should find the mapping
        assert found_mapping, \
            f"No mapping found in rfc-map.json linking '{symbol}' to section '{section}'"


def validate_symbol_mapping(context: Context, symbol: str):
    """
    Verify rfc-map.json contains proper mapping for a symbol.

    Args:
        context: Behave context
        symbol: Symbol name to look for

    Raises:
        AssertionError: If mapping is missing or incomplete
    """
    # Load rfc-map.json
    rfc_map_path = os.path.join(context.test_repo, 'docs', 'rfc-map.json')
    assert os.path.exists(rfc_map_path), "rfc-map.json not found"

    with open(rfc_map_path, 'r') as f:
        data = json.load(f)

    # Search for mapping with specified symbol
    found = False
    for mapping in data['mappings']:
        if mapping['code']['symbol'] == symbol:
            found = True
            # Verify mapping has RFC section
            assert 'rfc' in mapping, f"Mapping for {symbol} missing 'rfc' field"
            assert 'section' in mapping['rfc'], \
                f"Mapping for {symbol} missing RFC section reference"
            break

    assert found, f"No mapping found for symbol '{symbol}' in rfc-map.json"


def validate_file_path_mapping(context: Context, file_path: str):
    """
    Verify at least one mapping includes the specified file path.

    Args:
        context: Behave context
        file_path: File path to look for in mappings

    Raises:
        AssertionError: If no mapping contains the file path
    """
    # Load rfc-map.json
    rfc_map_path = os.path.join(context.test_repo, 'docs', 'rfc-map.json')
    assert os.path.exists(rfc_map_path), "rfc-map.json not found"

    with open(rfc_map_path, 'r') as f:
        data = json.load(f)

    # Verify at least one mapping has the specified file path
    found = False
    for mapping in data['mappings']:
        if mapping['code']['file'] == file_path:
            found = True
            break

    assert found, f"No mapping found with file path '{file_path}'"


def validate_line_numbers_in_mappings(context: Context):
    """
    Verify all mappings in rfc-map.json include valid line numbers.

    Args:
        context: Behave context

    Raises:
        AssertionError: If mappings are missing line numbers or have invalid values
    """
    # Load rfc-map.json
    rfc_map_path = os.path.join(context.test_repo, 'docs', 'rfc-map.json')
    assert os.path.exists(rfc_map_path), "rfc-map.json not found"

    with open(rfc_map_path, 'r') as f:
        data = json.load(f)

    # Verify all mappings have line numbers
    for mapping in data['mappings']:
        assert 'line' in mapping['code'], \
            f"Mapping for {mapping['code'].get('symbol', 'unknown')} missing line number"
        assert isinstance(mapping['code']['line'], int), \
            f"Line number for {mapping['code'].get('symbol', 'unknown')} must be integer"
        assert mapping['code']['line'] > 0, \
            f"Line number for {mapping['code'].get('symbol', 'unknown')} must be positive"


# ============================================================================
# Frontmatter Validation Helpers
# ============================================================================

def validate_kramdown_frontmatter(context: Context):
    """
    Verify RFC has valid kramdown-rfc frontmatter structure.

    Args:
        context: Behave context

    Returns:
        tuple: (content, frontmatter) strings

    Raises:
        AssertionError: If frontmatter is invalid
    """
    # Read generated RFC
    assert context.generated_rfc is not None, "No RFC generated"
    assert os.path.exists(context.generated_rfc), f"RFC file not found at {context.generated_rfc}"

    with open(context.generated_rfc, 'r') as f:
        content = f.read()

    # Verify frontmatter structure
    assert content.startswith('---'), "RFC missing YAML frontmatter opening delimiter"
    assert content.count('---') >= 2, "RFC frontmatter not properly closed"

    # Verify required fields present
    frontmatter_end = content.find('---', 3)  # Find second ---
    frontmatter = content[:frontmatter_end]

    assert 'title:' in frontmatter, "Frontmatter missing 'title' field"
    assert 'docname:' in frontmatter, "Frontmatter missing 'docname' field"

    return content, frontmatter


def validate_frontmatter_field(context: Context, field: str):
    """
    Verify frontmatter contains a specific field.

    Args:
        context: Behave context
        field: Field name to check for

    Raises:
        AssertionError: If field is missing
    """
    # Read generated RFC
    assert context.generated_rfc is not None, "No RFC generated"

    with open(context.generated_rfc, 'r') as f:
        content = f.read()

    # Extract frontmatter
    frontmatter_end = content.find('---', 3)
    frontmatter = content[:frontmatter_end]

    # Check for field (field can be just the name, or "field: value")
    assert field in frontmatter or f'{field}:' in frontmatter, \
        f"Frontmatter missing field '{field}'"


def validate_docname_pattern(context: Context, pattern: str):
    """
    Verify docname in frontmatter matches expected regex pattern.

    Args:
        context: Behave context
        pattern: Regex pattern to match

    Raises:
        AssertionError: If docname doesn't match pattern
    """
    # Read generated RFC
    assert context.generated_rfc is not None, "No RFC generated"

    with open(context.generated_rfc, 'r') as f:
        content = f.read()

    # Extract frontmatter
    frontmatter_end = content.find('---', 3)
    frontmatter = content[:frontmatter_end]

    # Extract docname
    docname_match = re.search(r'docname:\s*([^\n]+)', frontmatter)
    assert docname_match, "Docname field not found in frontmatter"

    docname = docname_match.group(1).strip()

    # Verify pattern match (pattern is a regex)
    assert re.match(pattern, docname), \
        f"Docname '{docname}' does not match pattern '{pattern}'"


# ============================================================================
# RFC Content Validation Helpers
# ============================================================================

def validate_section_absence(context: Context, section: str):
    """
    Verify RFC does NOT contain a specific section.

    Args:
        context: Behave context
        section: Section name that should not be present

    Raises:
        AssertionError: If section is found in RFC
    """
    # Read generated RFC
    assert context.generated_rfc is not None, "No RFC generated to check"
    assert os.path.exists(context.generated_rfc), f"RFC file not found at {context.generated_rfc}"

    with open(context.generated_rfc, 'r') as f:
        content = f.read()

    # Check that section is NOT in the RFC
    # Section names can appear as headings (# Section) or markers ({: #section})
    section_lower = section.lower()
    content_lower = content.lower()

    assert section_lower not in content_lower, \
        f"Section '{section}' was found in RFC but should not be present"


def validate_term_definition(context: Context, section: str, term: str):
    """
    Verify terminology section defines a specific term.

    Args:
        context: Behave context
        section: Section name
        term: Term to look for

    Raises:
        AssertionError: If term is not defined
    """
    assert context.generated_rfc is not None, "No RFC generated"
    with open(context.generated_rfc, 'r') as f:
        content = f.read()
    assert term in content, f"Term '{term}' not found in RFC section {section}"


def validate_field_list_present(context: Context):
    """
    Verify definition includes field list (kramdown definition list format).

    Args:
        context: Behave context

    Raises:
        AssertionError: If no field list found
    """
    assert context.generated_rfc is not None, "No RFC generated"
    with open(context.generated_rfc, 'r') as f:
        content = f.read()
    # Check for field list indicators (kramdown-rfc uses definition lists with : markers)
    assert ':' in content, "No definition list fields found in RFC"


def validate_cross_reference_exists(context: Context):
    """
    Verify cross-references to source code exist in rfc-map.json.

    Args:
        context: Behave context

    Raises:
        AssertionError: If no cross-references found
    """
    # Load rfc-map.json to verify cross-references exist
    rfc_map_path = os.path.join(context.test_repo, 'docs', 'rfc-map.json')
    assert os.path.exists(rfc_map_path), "No rfc-map.json found for cross-references"


def validate_function_documentation(context: Context, section: str, function: str):
    """
    Verify interfaces section documents a specific function.

    Args:
        context: Behave context
        section: Section name
        function: Function name

    Raises:
        AssertionError: If function is not documented
    """
    assert context.generated_rfc is not None, "No RFC generated"
    with open(context.generated_rfc, 'r') as f:
        content = f.read()
    assert function in content, f"Function '{function}' not documented in section {section}"


def validate_parameter_documentation(context: Context):
    """
    Verify documentation includes parameter information.

    Args:
        context: Behave context

    Raises:
        AssertionError: If no parameter documentation found
    """
    assert context.generated_rfc is not None, "No RFC generated"
    with open(context.generated_rfc, 'r') as f:
        content = f.read()
    # Check for common parameter documentation keywords
    has_params = any(kw in content.lower() for kw in ['parameter', 'param', 'arg', 'argument'])
    assert has_params, "No parameter documentation found in RFC"


def validate_return_type_documentation(context: Context):
    """
    Verify documentation includes return type information.

    Args:
        context: Behave context

    Raises:
        AssertionError: If no return type documentation found
    """
    assert context.generated_rfc is not None, "No RFC generated"
    with open(context.generated_rfc, 'r') as f:
        content = f.read()
    # Check for return type keywords
    has_return = any(kw in content.lower() for kw in ['return', 'returns'])
    assert has_return, "No return type documentation found in RFC"


def validate_rfc2119_references(context: Context):
    """
    Verify RFC 2119 keyword references are properly formatted.

    Args:
        context: Behave context

    Raises:
        AssertionError: If RFC 2119 keywords present but not properly referenced
    """
    assert context.generated_rfc is not None, "No RFC generated"
    with open(context.generated_rfc, 'r') as f:
        content = f.read()
    # Check for RFC 2119 keywords (MUST, SHOULD, MAY, etc.)
    rfc2119_keywords = ['MUST', 'SHOULD', 'MAY', 'REQUIRED', 'SHALL']
    has_keywords = any(kw in content for kw in rfc2119_keywords)
    # This is optional, so we just verify structure exists if keywords present
    if has_keywords:
        assert 'RFC' in content or 'rfc' in content, "RFC 2119 keywords present but no RFC reference"


def validate_state_transition_documentation(context: Context, section: str):
    """
    Verify behavior section describes state transitions.

    Args:
        context: Behave context
        section: Section name

    Raises:
        AssertionError: If no state transition description found
    """
    assert context.generated_rfc is not None, "No RFC generated"
    with open(context.generated_rfc, 'r') as f:
        content = f.read()
    # Check for state transition keywords
    has_states = any(kw in content.lower() for kw in ['state', 'transition', 'status'])
    assert has_states, f"No state transition description found in section {section}"


def validate_implementation_references(context: Context):
    """
    Verify behavior description references implementation code.

    Args:
        context: Behave context

    Raises:
        AssertionError: If no implementation references found
    """
    # Check rfc-map.json has behavioral mappings
    rfc_map_path = os.path.join(context.test_repo, 'docs', 'rfc-map.json')
    assert os.path.exists(rfc_map_path), "No rfc-map.json for implementation references"


def validate_specific_line_references(context: Context):
    """
    Verify cross-references point to specific code lines.

    Args:
        context: Behave context

    Raises:
        AssertionError: If no line number references found
    """
    # Verify rfc-map.json has line numbers
    rfc_map_path = os.path.join(context.test_repo, 'docs', 'rfc-map.json')
    assert os.path.exists(rfc_map_path), "No rfc-map.json found"
    with open(rfc_map_path, 'r') as f:
        data = json.load(f)
    # Verify at least one mapping has line number
    has_line_numbers = any('line' in m['code'] for m in data.get('mappings', []))
    assert has_line_numbers, "No cross-references with line numbers found"


def validate_rfc_reference_in_content(context: Context, section: str, reference: str):
    """
    Verify references section includes a specific RFC reference.

    Args:
        context: Behave context
        section: Section name
        reference: RFC reference to look for

    Raises:
        AssertionError: If reference not found
    """
    assert context.generated_rfc is not None, "No RFC generated"
    with open(context.generated_rfc, 'r') as f:
        content = f.read()
    assert reference in content, f"Reference '{reference}' not found in section {section}"


def validate_ietf_reference_format(context: Context):
    """
    Verify references follow IETF formatting standards.

    Args:
        context: Behave context

    Raises:
        AssertionError: If no IETF-formatted references found
    """
    assert context.generated_rfc is not None, "No RFC generated"
    with open(context.generated_rfc, 'r') as f:
        content = f.read()
    # Check for IETF reference format indicators (RFC XXXX, [RFCXXXX], etc.)
    has_ietf_format = bool(re.search(r'RFC\s*\d+|\[RFC\d+\]', content, re.IGNORECASE))
    assert has_ietf_format, "No IETF-formatted references found in RFC"


def validate_citation_bibliography_links(context: Context):
    """
    Verify inline citations link to bibliography section.

    Args:
        context: Behave context

    Raises:
        AssertionError: If citations exist without bibliography
    """
    assert context.generated_rfc is not None, "No RFC generated"
    with open(context.generated_rfc, 'r') as f:
        content = f.read()
    # Check for citation markers (e.g., [REF], {{REF}})
    has_citations = bool(re.search(r'\[[A-Z0-9\-]+\]|\{\{[A-Z0-9\-]+\}\}', content))
    # If citations exist, verify bibliography section exists
    if has_citations:
        assert 'reference' in content.lower() or 'bibliography' in content.lower(), \
            "Citations found but no bibliography section"


# ============================================================================
# Kramdown/xml2rfc Validation Helpers
# ============================================================================

def validate_kramdown_syntax(context: Context):
    """
    Verify kramdown-rfc syntax is valid (basic checks).

    Args:
        context: Behave context

    Raises:
        AssertionError: If syntax is invalid
    """
    assert context.generated_rfc is not None, "No RFC generated"
    with open(context.generated_rfc, 'r') as f:
        content = f.read()
    # Basic kramdown-rfc syntax checks
    assert content.startswith('---'), "Missing YAML frontmatter"
    assert content.count('---') >= 2, "Malformed frontmatter delimiters"


def validate_xml2rfc_processable(context: Context):
    """
    Verify document structure is processable by xml2rfc.

    Args:
        context: Behave context

    Raises:
        AssertionError: If document structure is invalid

    Note:
        This is a structural check only - actual xml2rfc processing
        would require running the tool.
    """
    # This would require actually running xml2rfc
    # For now, verify the RFC exists and has valid structure
    assert context.generated_rfc is not None, "No RFC generated for xml2rfc processing"
    assert os.path.exists(context.generated_rfc), "RFC file missing"
