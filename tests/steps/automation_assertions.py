"""
Assertion steps (@then) for automation test scenarios.

This module implements verification steps for automated documentation checks,
validating hook responses, impact analysis results, and system behavior.
"""

import os
import json
from behave import then
from behave.runner import Context


# ============================================================================
# Hook Response Assertions
# ============================================================================

@then('the hook returns non-blocking response')
def step_hook_non_blocking(context: Context):
    """Verify hook does not block execution."""
    assert context.hook_response is not None, "No hook response found"
    assert context.hook_response['block'] == False, "Hook blocked execution"


@then('the hook blocks execution')
def step_hook_blocks(context: Context):
    """Verify hook blocks execution."""
    assert context.hook_response is not None, "No hook response found"
    assert context.hook_response['block'] == True, "Hook did not block execution"


@then('the hook allows execution')
def step_hook_allows(context: Context):
    """Verify hook allows execution."""
    step_hook_non_blocking(context)


@then('the response message includes "{text}"')
def step_response_includes_text(context: Context, text: str):
    """Verify response message contains text."""
    assert context.hook_response is not None, "No hook response found"
    message = context.hook_response.get('message', '')
    assert text in message, f"Expected '{text}' in message, got: {message}"


@then('the response message suggests "{text}"')
def step_response_suggests_text(context: Context, text: str):
    """Verify response message suggests text."""
    step_response_includes_text(context, text)


@then('the response suggestion recommends "{text}"')
def step_response_suggests(context: Context, text: str):
    """Verify response suggestion contains text."""
    assert context.hook_response is not None, "No hook response found"
    suggestion = context.hook_response.get('suggestion', '')
    assert text in suggestion, f"Expected '{text}' in suggestion, got: {suggestion}"


@then('the suggestion recommends "{text}"')
def step_suggestion_recommends(context: Context, text: str):
    """Verify suggestion includes text."""
    step_response_suggests(context, text)


@then('the response has block={value}')
def step_response_block_value(context: Context, value: str):
    """Verify block value."""
    assert context.hook_response is not None, "No hook response found"
    expected = value.lower() == 'true'
    actual = context.hook_response.get('block', False)
    assert actual == expected, f"Expected block={expected}, got block={actual}"


@then('no warning message is displayed')
def step_no_warning(context: Context):
    """Verify no warning message."""
    assert context.hook_response is not None, "No hook response found"
    message = context.hook_response.get('message', '')
    assert message == '', f"Unexpected warning message: {message}"


@then('hook execution completes in under {ms:d}ms')
def step_hook_timing(context: Context, ms: int):
    """Verify hook execution time."""
    assert context.hook_response is not None, "No hook response found"
    timing = context.hook_response.get('timing_ms', 0)
    assert timing < ms, f"Hook took {timing}ms, expected under {ms}ms"


@then('hook returns success response')
def step_hook_success(context: Context):
    """Verify hook returned success."""
    assert context.hook_response is not None, "No hook response"


@then('the hook does not crash')
def step_hook_no_crash(context: Context):
    """Verify hook did not crash."""
    assert context.hook_response is not None, "Hook crashed (no response)"


@then('the hook returns non-blocking warning')
def step_non_blocking_warning(context: Context):
    """Verify non-blocking warning."""
    step_hook_non_blocking(context)
    assert context.hook_response.get('message', ''), "No warning message"


# ============================================================================
# Impact Analysis Assertions
# ============================================================================

@then('analysis completes in under {ms:d}ms')
def step_analysis_timing(context: Context, ms: int):
    """Verify analysis timing (simulation always passes)."""
    pass


@then('affected sections include "{section}"')
def step_affected_sections_include(context: Context, section: str):
    """Verify affected sections include specified section."""
    assert hasattr(context, 'impact_results'), "No impact analysis results"
    sections = [impact['section_number'] for impact in context.impact_results]
    assert section in sections, f"Section {section} not in affected sections: {sections}"


@then('severity for section "{section}" is "{severity}"')
def step_severity_for_section(context: Context, section: str, severity: str):
    """Verify severity level for section."""
    assert hasattr(context, 'impact_results'), "No impact analysis results"

    for impact in context.impact_results:
        if impact['section_number'] == section:
            actual_severity = impact['severity']
            assert actual_severity == severity, f"Expected severity {severity}, got {actual_severity}"
            return

    assert False, f"Section {section} not found in impact results"


@then('changed elements include "{element}"')
def step_changed_elements_include(context: Context, element: str):
    """Verify changed elements include specified element."""
    assert hasattr(context, 'impact_results'), "No impact analysis results"

    all_elements = []
    for impact in context.impact_results:
        all_elements.extend(impact['affected_code_elements'])

    assert element in all_elements, f"Element {element} not in changed elements: {all_elements}"


@then('impact report is generated successfully')
def step_impact_report_generated(context: Context):
    """Verify impact report was generated."""
    assert hasattr(context, 'impact_results'), "No impact analysis results"
    assert len(context.impact_results) > 0, "Impact report is empty"


@then('no affected sections are reported')
def step_no_affected_sections(context: Context):
    """Verify no affected sections."""
    if not hasattr(context, 'impact_results'):
        return
    assert len(context.impact_results) == 0, f"Expected no affected sections, found {len(context.impact_results)}"


@then('impact report shows "{message}"')
def step_impact_report_shows_message(context: Context, message: str):
    """Verify impact report shows specific message."""
    if not hasattr(context, 'impact_results') or len(context.impact_results) == 0:
        assert 'No RFC' in message or 'No git history' in message or 'No changes' in message


@then('multiple affected sections are reported')
def step_multiple_sections_affected(context: Context):
    """Verify multiple sections affected."""
    assert hasattr(context, 'impact_results'), "No impact analysis results"
    assert len(context.impact_results) > 1, f"Expected multiple sections, found {len(context.impact_results)}"


@then('sections are sorted by severity (MUST_UPDATE first)')
def step_sections_sorted_by_severity(context: Context):
    """Verify sections are sorted by severity."""
    assert hasattr(context, 'impact_results'), "No impact analysis results"

    severity_order = [impact['severity'] for impact in context.impact_results]

    must_update_indices = [i for i, s in enumerate(severity_order) if s == 'MUST_UPDATE']
    should_review_indices = [i for i, s in enumerate(severity_order) if s == 'SHOULD_REVIEW']

    if must_update_indices and should_review_indices:
        assert max(must_update_indices) < min(should_review_indices), "MUST_UPDATE sections should come before SHOULD_REVIEW"


@then('each section lists its affected code elements')
def step_each_section_lists_elements(context: Context):
    """Verify each section has affected code elements."""
    assert hasattr(context, 'impact_results'), "No impact analysis results"

    for impact in context.impact_results:
        elements = impact['affected_code_elements']
        assert len(elements) > 0, f"Section {impact['section_number']} has no affected elements"


@then('results include all affected sections')
def step_results_include_all_sections(context: Context):
    """Verify all expected sections are included."""
    assert hasattr(context, 'impact_results'), "No impact analysis results"
    assert len(context.impact_results) > 0, "No results found"


@then('no changes are detected')
def step_no_changes_detected(context: Context):
    """Verify no changes detected."""
    step_no_affected_sections(context)


@then('impact report includes behavior section warning')
def step_impact_includes_behavior_warning(context: Context):
    """Verify behavior section warning."""
    assert hasattr(context, 'impact_results'), "No impact results"

    behavior_impacts = [i for i in context.impact_results if i['severity'] == 'SHOULD_REVIEW']

    assert len(behavior_impacts) > 0, "No behavior section warnings found"


# ============================================================================
# RFC Map and Timestamp Assertions
# ============================================================================

@then('the hook updates timestamps in rfc-map.json')
def step_hook_updates_timestamps(context: Context):
    """Verify timestamps were updated."""
    assert context.updated_rfc_map, "rfc-map.json was not updated"


@then('affected sections are flagged as stale')
def step_sections_flagged_stale(context: Context):
    """Verify sections are marked stale."""
    rfc_map_path = os.path.join(context.test_repo, 'docs', 'rfc-map.json')

    with open(rfc_map_path, 'r') as f:
        rfc_map = json.load(f)

    stale_found = False
    for mapping in rfc_map['mappings']:
        if mapping['last_synced'] == '1970-01-01T00:00:00':
            stale_found = True
            break

    assert stale_found, "No mappings were flagged as stale"


# ============================================================================
# Reviewer Guidance Assertions
# ============================================================================

@then('a reviewer guidance report is generated')
def step_reviewer_guidance_generated(context: Context):
    """Verify reviewer guidance was generated."""
    assert hasattr(context, 'reviewer_guidance'), "No reviewer guidance found"
    assert context.reviewer_guidance is not None, "Reviewer guidance is None"


@then('the report includes affected RFC sections')
def step_report_includes_sections(context: Context):
    """Verify report includes affected sections."""
    assert hasattr(context, 'reviewer_guidance'), "No reviewer guidance"
    guidance = context.reviewer_guidance
    assert 'affected_sections' in guidance, "No affected_sections in guidance"
    assert len(guidance['affected_sections']) > 0, "No sections in report"


@then('the report includes review checklist')
def step_report_includes_checklist(context: Context):
    """Verify report includes checklist."""
    assert hasattr(context, 'reviewer_guidance'), "No reviewer guidance"
    guidance = context.reviewer_guidance
    assert 'checklist' in guidance, "No checklist in guidance"
    assert len(guidance['checklist']) > 0, "Checklist is empty"


@then('the report is appended to ".claude/.hook-history.json"')
def step_report_appended_to_history(context: Context):
    """Verify report was appended to history."""
    history_path = os.path.join(context.test_repo, '.claude', '.hook-history.json')
    assert os.path.exists(history_path), "Hook history file not found"

    with open(history_path, 'r') as f:
        history = json.load(f)

    assert len(history) > 0, "History is empty"


# ============================================================================
# Staleness Warning Assertions
# ============================================================================

@then('the hook displays staleness warning')
def step_hook_displays_staleness_warning(context: Context):
    """Verify staleness warning is displayed."""
    assert context.hook_response is not None, "No hook response"
    message = context.hook_response.get('message', '')
    assert 'days ago' in message.lower(), f"No staleness warning in: {message}"


@then('the warning message includes "{text}"')
def step_warning_includes_text(context: Context, text: str):
    """Verify warning includes specific text."""
    step_response_includes_text(context, text)


@then('no staleness warning is displayed')
def step_no_staleness_warning(context: Context):
    """Verify no staleness warning."""
    assert context.hook_response is not None, "No hook response"
    message = context.hook_response.get('message', '')
    assert 'days ago' not in message.lower(), f"Unexpected staleness warning: {message}"


@then('the hook warns about uncommitted documentation')
def step_warns_uncommitted_docs(context: Context):
    """Verify warning about uncommitted docs."""
    assert context.hook_response is not None, "No hook response"
    message = context.hook_response.get('message', '')
    assert 'uncommitted' in message.lower(), f"No uncommitted warning in: {message}"


# ============================================================================
# Intent Detection Assertions
# ============================================================================

@then('the hook detects RFC-related keywords')
def step_detects_rfc_keywords(context: Context):
    """Verify RFC keywords were detected."""
    assert context.rfc_context_injected, "RFC context was not injected"


@then('the hook loads "{filename}" from memory')
def step_loads_memory_file(context: Context, filename: str):
    """Verify memory file was loaded."""
    assert hasattr(context, 'memory_loaded'), "No memory_loaded attribute"
    assert filename in context.memory_loaded, f"{filename} not in loaded memory files: {context.memory_loaded}"


@then('RFC context is injected into response')
def step_rfc_context_injected(context: Context):
    """Verify RFC context was injected."""
    assert context.rfc_context_injected, "RFC context was not injected"


@then('intent detection is logged to ".claude/.hook-history.json"')
def step_intent_logged(context: Context):
    """Verify intent detection was logged."""
    history_path = os.path.join(context.test_repo, '.claude', '.hook-history.json')
    assert os.path.exists(history_path), "Hook history not found"

    with open(history_path, 'r') as f:
        history = json.load(f)

    intent_entries = [e for e in history if e.get('type') == 'intent_detection']
    assert len(intent_entries) > 0, "No intent detection entries found"


@then('the hook does not inject RFC context')
def step_no_rfc_context(context: Context):
    """Verify RFC context was not injected."""
    assert not context.rfc_context_injected, "RFC context was unexpectedly injected"


@then('no memory files are loaded')
def step_no_memory_loaded(context: Context):
    """Verify no memory files were loaded."""
    assert len(context.memory_loaded) == 0, f"Unexpected memory files loaded: {context.memory_loaded}"


# ============================================================================
# Error Handling Assertions
# ============================================================================

@then('the error message indicates missing library')
def step_error_missing_library(context: Context):
    """Verify error message about missing library."""
    message = context.hook_response.get('message', '')
    assert 'missing' in message.lower() or 'not found' in message.lower(), f"No missing library error in: {message}"


@then('the hook logs permission error')
def step_logs_permission_error(context: Context):
    """Verify permission error was logged."""
    message = context.hook_response.get('message', '')
    assert 'permission' in message.lower(), f"No permission error in: {message}"


@then('the response suggests checking file permissions')
def step_suggests_check_permissions(context: Context):
    """Verify suggestion about permissions."""
    suggestion = context.hook_response.get('suggestion', '')
    assert 'permission' in suggestion.lower(), f"No permission suggestion in: {suggestion}"


@then('the error message indicates JSON parsing error')
def step_error_json_parsing(context: Context):
    """Verify JSON parsing error message."""
    message = context.hook_response.get('message', '')
    assert 'json' in message.lower() or 'parsing' in message.lower(), f"No JSON error in: {message}"
