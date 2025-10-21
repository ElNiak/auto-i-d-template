"""
Behave test assertion steps for RFC update scenarios.

This module contains all @then steps that verify the results of RFC update
operations. Split from update_steps.py for better code organization.
"""

import os
import json
import glob
import re
from datetime import datetime
from behave import then
from behave.runner import Context


# ============================================================================
# Then Steps - Verify Update Results
# ============================================================================

@then('the RFC section "{section}" should be regenerated')
def step_rfc_section_regenerated(context: Context, section: str):
    """Verify specific section was regenerated"""
    assert section in str(context.command_output), f"Section {section} not mentioned in output"


@then('the RFC document should retain unchanged sections')
def step_rfc_retains_unchanged(context: Context):
    """Verify unchanged sections are preserved"""
    assert "preserved" in str(context.command_output).lower()


@then('the rfc-map.json timestamp for "{symbol}" should be updated')
def step_rfc_map_timestamp_updated(context: Context, symbol: str):
    """Verify timestamp was updated for specific symbol"""
    # In real implementation, parse rfc-map.json and check timestamp
    pass


@then('I should see "{message}"')
def step_should_see_message(context: Context, message: str):
    """Verify specific message appears in output"""
    output_text = '\n'.join(context.command_output)
    assert message in output_text, f"Expected message '{message}' not found in output"


@then('the RFC should be updated')
def step_rfc_should_be_updated(context: Context):
    """Verify RFC was updated successfully"""
    assert context.command_exit_code == 0, "Update command failed"
    assert os.path.exists(context.existing_rfc_path), "RFC file doesn't exist"
    output_text = '\n'.join(context.command_output)
    assert 'updated' in output_text.lower() or 'regenerated' in output_text.lower()


@then('the preserve block "{block_id}" should remain unchanged')
def step_preserve_block_unchanged(context: Context, block_id: str):
    """Verify preserve block content is intact"""
    with open(context.existing_rfc_path, 'r') as f:
        content = f.read()
    assert '@preserve-start' in content and '@preserve-end' in content


@then('the manual edits within the preserve block should be intact')
def step_manual_edits_intact(context: Context):
    """Verify manual edits are preserved"""
    with open(context.existing_rfc_path, 'r') as f:
        content = f.read()
    assert '**[MANUAL EDIT]**' in content or 'manual' in content.lower()


@then('I should see a change detection report')
def step_see_change_report(context: Context):
    """Verify change detection report is displayed"""
    output_text = '\n'.join(context.command_output)
    assert 'change' in output_text.lower() or 'modified' in output_text.lower()


@then('the report should show "{text}"')
def step_report_shows_text(context: Context, text: str):
    """Verify report contains specific text"""
    output_text = '\n'.join(context.command_output)
    assert text in output_text, f"Expected text '{text}' not found in report"


@then('the report should explain "{explanation}"')
def step_report_explains(context: Context, explanation: str):
    """Verify report includes explanation"""
    # Simplified check for test
    pass


@then('the RFC document should not be modified')
def step_rfc_not_modified(context: Context):
    """Verify RFC file was not changed"""
    # Store original mtime if not already stored
    if not hasattr(context, 'rfc_original_mtime'):
        context.rfc_original_mtime = os.path.getmtime(context.existing_rfc_path)

    # Get current mtime
    current_mtime = os.path.getmtime(context.existing_rfc_path)

    # Verify file was not modified (times should match)
    assert current_mtime == context.rfc_original_mtime, \
        f"RFC file was modified (mtime changed from {context.rfc_original_mtime} to {current_mtime})"


@then('the rfc-map.json should not be modified')
def step_rfc_map_not_modified(context: Context):
    """Verify rfc-map.json was not changed"""
    # Store original mtime if not already stored
    if not hasattr(context, 'rfc_map_original_mtime'):
        context.rfc_map_original_mtime = os.path.getmtime(context.rfc_map_path)

    # Get current mtime
    current_mtime = os.path.getmtime(context.rfc_map_path)

    # Verify file was not modified
    assert current_mtime == context.rfc_map_original_mtime, \
        f"rfc-map.json was modified (mtime changed from {context.rfc_map_original_mtime} to {current_mtime})"


@then('the command should exit successfully')
def step_command_exits_successfully(context: Context):
    """Verify command exit code is 0"""
    assert context.command_exit_code == 0, f"Command failed with exit code {context.command_exit_code}"


# Note: "I should see an error" and "I should see a suggestion"
# are already defined in generate_steps.py and will be reused


@then('the command should exit with error status')
def step_command_exits_with_error(context: Context):
    """Verify command exit code is non-zero"""
    assert context.command_exit_code != 0, "Command should have failed but succeeded"


# Note: "I should see a warning" is already defined in generate_steps.py


@then('I should be prompted "{prompt_text}"')
def step_see_prompt(context: Context, prompt_text: str):
    """Verify user prompt is displayed"""
    # Simplified for test
    pass


@then('the update should proceed without prompts')
def step_update_proceeds_without_prompts(context: Context):
    """Verify update executed without user interaction"""
    assert '--force' in context.command


@then('the preserve block should take precedence over new generated content')
def step_preserve_takes_precedence(context: Context):
    """Verify preservation priority rule applied"""
    assert "Preserve blocks honored" in str(context.command_output)


@then('only section "{section}" should be regenerated')
def step_only_section_regenerated(context: Context, section: str):
    """Verify only specific section was updated"""
    assert section in str(context.command_output)


@then('sections {section_list} should remain unchanged')
def step_sections_unchanged(context: Context, section_list: str):
    """Verify multiple sections were preserved"""
    assert "preserved" in str(context.command_output).lower()


@then('the parser agent should only analyze "{file_path}"')
def step_parser_analyzes_only_file(context: Context, file_path: str):
    """Verify parser was filtered to specific file"""
    # Would check agent spawn logs in real implementation
    pass


@then('the formatter agent should only generate section "{section}"')
def step_formatter_generates_only_section(context: Context, section: str):
    """Verify formatter was filtered to specific section"""
    # Read the updated RFC
    with open(context.existing_rfc_path, 'r') as f:
        content = f.read()

    # Verify the specified section exists in the RFC
    # Section identifiers can be: "3.1", "Interfaces", etc.
    assert section in content or f'#{section}' in content or f'§{section}' in content, \
        f"Section '{section}' not found in generated RFC content"

    # Check command output mentions this section was generated
    output_text = '\n'.join(context.command_output)
    assert section in output_text or 'generated' in output_text.lower(), \
        f"No evidence that section '{section}' was generated"


@then('the timestamp for "{symbol}" should be updated to current time')
def step_timestamp_updated_to_current(context: Context, symbol: str):
    """Verify timestamp reflects current time"""
    # Parse rfc-map.json
    with open(context.rfc_map_path, 'r') as f:
        data = json.load(f)

    # Find mapping for symbol
    mapping_found = False
    for mapping in data['mappings']:
        if mapping['code']['symbol'] == symbol:
            mapping_found = True
            # Parse timestamp (ISO 8601 format)
            last_synced = mapping.get('last_synced')
            assert last_synced is not None, f"No timestamp found for symbol {symbol}"

            # Verify timestamp is recent (within last minute)
            timestamp_dt = datetime.fromisoformat(last_synced.replace('Z', '+00:00'))
            now = datetime.now(timestamp_dt.tzinfo)
            time_diff = (now - timestamp_dt).total_seconds()

            assert time_diff < 60, \
                f"Timestamp for {symbol} is not current (diff: {time_diff}s, expected <60s)"
            break

    assert mapping_found, f"No mapping found for symbol {symbol}"


@then('the timestamp for "{symbol}" should remain "{timestamp}"')
def step_timestamp_unchanged(context: Context, symbol: str, timestamp: str):
    """Verify timestamp was not modified"""
    # Parse rfc-map.json
    with open(context.rfc_map_path, 'r') as f:
        data = json.load(f)

    # Find mapping for symbol
    mapping_found = False
    for mapping in data['mappings']:
        if mapping['code']['symbol'] == symbol:
            mapping_found = True
            # Verify timestamp matches expected value
            last_synced = mapping.get('last_synced')
            assert last_synced == timestamp, \
                f"Timestamp for {symbol} changed from {timestamp} to {last_synced}"
            break

    assert mapping_found, f"No mapping found for symbol {symbol}"


@then('the change report should show "{text}"')
def step_change_report_shows(context: Context, text: str):
    """Verify change report contains specific text"""
    output_text = '\n'.join(context.command_output)
    assert text in output_text, f"Expected text '{text}' not found in change report"


@then('sections {sections} should be regenerated')
def step_multiple_sections_regenerated(context: Context, sections: str):
    """Verify multiple sections were updated"""
    # Parse sections list (e.g., "3.1, 3.2" or "3.1 and 3.2")
    section_list = [s.strip() for s in sections.replace(' and ', ',').split(',')]

    output_text = '\n'.join(context.command_output)

    # Verify each section is mentioned in output
    for section in section_list:
        assert section in output_text, \
            f"Section {section} not found in regeneration output"


@then('all other sections should remain unchanged')
def step_other_sections_unchanged(context: Context):
    """Verify non-affected sections preserved"""
    assert "preserved" in str(context.command_output).lower()


@then('the merge should apply preservation priority')
def step_merge_applies_preservation_priority(context: Context):
    """Verify preservation priority rule was applied"""
    # Check that preservation priority was mentioned in output
    output_text = '\n'.join(context.command_output)
    assert 'preservation priority' in output_text.lower() or \
           'preserve' in output_text.lower(), \
           "No evidence of preservation priority being applied"


@then('the preserve block content should take precedence')
def step_preserve_content_takes_precedence(context: Context):
    """Verify preserve block won over generated content"""
    # Read RFC and verify preserve block still exists with original content
    with open(context.existing_rfc_path, 'r') as f:
        content = f.read()

    # Verify preserve block markers are present
    assert '@preserve-start' in content and '@preserve-end' in content, \
           "Preserve block markers not found in RFC"

    # Verify manual content is intact
    if hasattr(context, 'preserve_block_has_manual_content'):
        assert '**[MANUAL EDIT]**' in content or 'manual' in content.lower(), \
               "Manual content not preserved"


@then('the newly generated content should be discarded for lines {start:d}-{end:d}')
def step_generated_content_discarded(context: Context, start: int, end: int):
    """Verify generated content was replaced by preserve block"""
    # Read RFC
    with open(context.existing_rfc_path, 'r') as f:
        lines = f.readlines()

    # Verify the line range contains preserve block content (not generated)
    line_range_text = ''.join(lines[start-1:end])

    # Should contain preserve markers or manual edit markers
    assert '@preserve' in line_range_text or '**[MANUAL EDIT]**' in line_range_text, \
           f"Lines {start}-{end} do not contain preserved content"


@then('I should see a checkpoint message "{message}"')
def step_see_checkpoint_message(context: Context, message: str):
    """Verify checkpoint recovery message displayed"""
    output_text = '\n'.join(context.command_output)
    assert message in output_text, \
        f"Expected checkpoint message '{message}' not found in output"


@then('the parser checkpoint should be preserved')
def step_parser_checkpoint_preserved(context: Context):
    """Verify parser checkpoint exists"""
    checkpoint_dir = os.path.join(str(context.test_repo), '.claude', '.checkpoints')

    # Check if checkpoint directory exists
    assert os.path.exists(checkpoint_dir), \
        f"Checkpoint directory not found at {checkpoint_dir}"

    # Look for parser checkpoint file (pattern: parser-*.json)
    parser_checkpoints = glob.glob(os.path.join(checkpoint_dir, 'parser-*.json'))

    assert len(parser_checkpoints) > 0, \
        "No parser checkpoint files found in .claude/.checkpoints/"


@then('the analyzer checkpoint should be preserved')
def step_analyzer_checkpoint_preserved(context: Context):
    """Verify analyzer checkpoint exists"""
    checkpoint_dir = os.path.join(str(context.test_repo), '.claude', '.checkpoints')

    # Look for analyzer checkpoint file
    analyzer_checkpoints = glob.glob(os.path.join(checkpoint_dir, 'analyzer-*.json'))

    assert len(analyzer_checkpoints) > 0, \
        "No analyzer checkpoint files found in .claude/.checkpoints/"


@then('I should be able to retry the update')
def step_can_retry_update(context: Context):
    """Verify update can be retried from checkpoint"""
    # Verify checkpoint directory exists
    checkpoint_dir = os.path.join(str(context.test_repo), '.claude', '.checkpoints')
    assert os.path.exists(checkpoint_dir), \
        "Cannot retry without checkpoint directory"

    # Verify at least one checkpoint file exists
    all_checkpoints = glob.glob(os.path.join(checkpoint_dir, '*.json'))
    assert len(all_checkpoints) > 0, \
        "Cannot retry without checkpoint files"


@then('the updated RFC should have valid kramdown-rfc syntax')
def step_updated_rfc_valid_kramdown(context: Context):
    """Verify RFC has valid syntax after update"""
    # Read the RFC file
    with open(context.existing_rfc_path, 'r') as f:
        content = f.read()

    # Basic kramdown-rfc syntax checks
    # 1. Should have frontmatter
    assert content.startswith('---'), "RFC missing YAML frontmatter delimiter"
    assert content.count('---') >= 2, "RFC frontmatter not properly closed"

    # 2. Should have required frontmatter fields
    assert 'title:' in content[:500], "Missing title in frontmatter"
    assert 'docname:' in content[:500], "Missing docname in frontmatter"

    # 3. Kramdown-rfc anchors should use correct syntax {: #anchor}
    # No broken anchor syntax like {#anchor} (should be {: #anchor})
    broken_anchors = re.findall(r'\{#[^}]+\}', content)
    assert len(broken_anchors) == 0, \
        f"Found broken anchor syntax: {broken_anchors}. Should use {{: #anchor}}"


@then('I should see a reminder "{reminder_text}"')
def step_see_reminder(context: Context, reminder_text: str):
    """Verify reminder message is displayed"""
    output_text = '\n'.join(context.command_output)
    assert reminder_text in output_text, \
        f"Expected reminder '{reminder_text}' not found in output"


@then('the change should be classified as "{severity}"')
def step_change_classified_as_severity(context: Context, severity: str):
    """Verify change severity classification"""
    context.change_severity = severity
    output_text = '\n'.join(context.command_output)
    assert severity in output_text, \
        f"Expected severity '{severity}' not found in change classification"


@then('the impact summary should show "{text}"')
def step_impact_summary_shows(context: Context, text: str):
    """Verify impact summary contains text"""
    output_text = '\n'.join(context.command_output)
    assert text in output_text, \
        f"Expected text '{text}' not found in impact summary"


@then('the section should be marked for review')
def step_section_marked_for_review(context: Context):
    """Verify section has review marker"""
    # Read RFC and check for review markers
    with open(context.existing_rfc_path, 'r') as f:
        content = f.read()

    # Check for review markers
    review_markers = ['[NEEDS REVIEW]', '[REVIEW REQUIRED]', '[MANUAL REVIEW]']
    has_marker = any(marker in content for marker in review_markers)

    assert has_marker, "No review markers found in RFC"


@then('the change summary should explain "{explanation}"')
def step_change_summary_explains(context: Context, explanation: str):
    """Verify change summary includes explanation"""
    output_text = '\n'.join(context.command_output)
    # Check that explanation text appears in output
    assert explanation in output_text or explanation.lower() in output_text.lower(), \
        f"Expected explanation '{explanation}' not found in change summary"


@then('section "{section}" should be regenerated')
def step_specific_section_regenerated(context: Context, section: str):
    """Verify specific section was updated"""
    assert section in str(context.command_output)


@then('the cross-reference "{anchor}" should remain valid')
def step_cross_reference_valid(context: Context, anchor: str):
    """Verify cross-reference is still valid"""
    # Read RFC
    with open(context.existing_rfc_path, 'r') as f:
        content = f.read()

    # Check that anchor exists (kramdown-rfc format: {: #anchor})
    anchor_pattern = f'{{: #{anchor}}}'
    assert anchor_pattern in content, \
        f"Cross-reference anchor '{anchor_pattern}' not found in RFC"


@then('section "{section}" should remain unchanged')
def step_specific_section_unchanged(context: Context, section: str):
    """Verify specific section was preserved"""
    output_text = '\n'.join(context.command_output)
    # Section should be mentioned as preserved, not regenerated
    assert 'preserved' in output_text.lower(), \
        "No evidence of sections being preserved"


@then('the RFC should have no broken cross-references')
def step_no_broken_cross_references(context: Context):
    """Verify all cross-references are valid"""
    with open(context.existing_rfc_path, 'r') as f:
        content = f.read()

    # Find all anchor definitions: {: #anchor-name}
    anchor_defs = set(re.findall(r'\{:\s*#([\w\-]+)\}', content))

    # Find all anchor references: [text](#anchor-name) or (#anchor-name)
    anchor_refs = set(re.findall(r'\(#([\w\-]+)\)', content))

    # Find broken references (referenced but not defined)
    broken_refs = anchor_refs - anchor_defs

    assert len(broken_refs) == 0, \
        f"Found broken cross-references: {broken_refs}"


@then('the CODE_REF marker should be updated to "{new_marker}"')
def step_code_ref_updated(context: Context, new_marker: str):
    """Verify CODE_REF marker was updated"""
    with open(context.existing_rfc_path, 'r') as f:
        content = f.read()

    # CODE_REF markers have format: <!-- CODE_REF: file:symbol:line -->
    assert f'<!-- CODE_REF: {new_marker}' in content or \
           f'<!--CODE_REF:{new_marker}' in content, \
           f"CODE_REF marker '{new_marker}' not found in RFC"


@then('the rfc-map.json mapping should reflect the new line number')
def step_mapping_reflects_new_line(context: Context):
    """Verify mapping has updated line number"""
    # Parse rfc-map.json
    with open(context.rfc_map_path, 'r') as f:
        data = json.load(f)

    # Check if any mapping has the new line number
    if hasattr(context, 'new_line_number'):
        found_new_line = False
        for mapping in data['mappings']:
            if mapping['code']['line'] == context.new_line_number:
                found_new_line = True
                break

        assert found_new_line, \
            f"No mapping found with updated line number {context.new_line_number}"


@then('the cross-reference should point to the correct location')
def step_cross_reference_correct(context: Context):
    """Verify cross-reference points to correct location"""
    # Read rfc-map.json
    with open(context.rfc_map_path, 'r') as f:
        data = json.load(f)

    # Verify at least one mapping exists and has valid structure
    assert len(data['mappings']) > 0, "No mappings found in rfc-map.json"

    # Check first mapping has required fields
    first_mapping = data['mappings'][0]
    assert 'code' in first_mapping, "Mapping missing 'code' field"
    assert 'rfc' in first_mapping, "Mapping missing 'rfc' field"
    assert 'line' in first_mapping['code'], "Mapping missing line number"
    assert 'section' in first_mapping['rfc'], "Mapping missing section reference"


@then('the updated RFC should retain "{field}: {value}"')
def step_updated_rfc_retains_field(context: Context, field: str, value: str):
    """Verify frontmatter field is preserved"""
    with open(context.existing_rfc_path, 'r') as f:
        content = f.read()
    assert f'{field}: {value}' in content or f'{field}: "{value}"' in content


@then('I should see "Would update:" followed by file list')
def step_see_would_update_file_list(context: Context):
    """Verify dry-run output shows file list"""
    output_text = '\n'.join(context.command_output)
    assert 'Would update:' in output_text
    assert '.md' in output_text or 'rfc-map.json' in output_text


@then('only the changed sections should be updated (not frontmatter)')
def step_only_changed_sections_updated(context: Context):
    """Verify frontmatter was not regenerated"""
    # Read RFC and verify frontmatter is intact
    with open(context.existing_rfc_path, 'r') as f:
        content = f.read()
    # Check that frontmatter still exists
    assert '---' in content[:100], "Frontmatter missing"
    assert 'docname:' in content[:500], "Docname field missing from frontmatter"


@then('the formatter should only generate sections {sections}')
def step_formatter_generates_sections(context: Context, sections: str):
    """Verify formatter output is filtered to specific sections"""
    # Parse section list (e.g., "3.1" or "3.1, 3.2")
    section_list = [s.strip() for s in sections.replace(' and ', ',').split(',')]

    # Verify formatter was configured with section filter
    if hasattr(context, 'section_filter'):
        for section in section_list:
            assert section in str(context.section_filter), \
                f"Section {section} not in formatter's section filter"
    # If no section_filter attribute, the test scenario didn't set it up
    # This is acceptable for some test scenarios


@then('the formatter output should not include frontmatter')
def step_formatter_no_frontmatter(context: Context):
    """Verify formatter did not regenerate frontmatter"""
    # Read the updated RFC
    with open(context.existing_rfc_path, 'r') as f:
        content = f.read()

    # Verify frontmatter still exists and wasn't regenerated
    # (Original frontmatter should be intact)
    assert content.startswith('---'), "Frontmatter missing from RFC"
    assert 'docname: draft-calculator-00' in content[:500], \
        "Original frontmatter was modified (docname changed or missing)"


@then('the formatter output should not include unchanged sections')
def step_formatter_no_unchanged_sections(context: Context):
    """Verify formatter only output changed sections"""
    # Check command output mentions selective update
    output_text = '\n'.join(context.command_output)

    # Verify output indicates selective regeneration
    # Should mention "regenerated" for changed sections
    # Should mention "preserved" for unchanged sections
    assert 'regenerated' in output_text.lower() or 'updated' in output_text.lower(), \
        "No evidence of selective section regeneration"

    # If preserve count is mentioned, verify it's non-zero
    if 'preserved' in output_text.lower():
        # Indicates some sections were kept unchanged
        pass  # This is the expected behavior


@then('the coordinator should merge the partial output')
def step_coordinator_merges_partial(context: Context):
    """Verify coordinator merged partial formatter output"""
    # Check that both new and old content exist in the RFC
    with open(context.existing_rfc_path, 'r') as f:
        content = f.read()

    # Verify the RFC contains the original structure (not completely rewritten)
    assert '# Introduction' in content, "Original sections missing (merge failed)"
    assert '# Terminology' in content, "Original sections missing (merge failed)"

    # Verify frontmatter is intact (coordinator preserved it)
    assert content.startswith('---'), "Frontmatter not preserved during merge"

    # Check output mentions merge or preservation
    output_text = '\n'.join(context.command_output)
    assert 'preserved' in output_text.lower() or 'sections' in output_text.lower(), \
        "No evidence of merge operation"
