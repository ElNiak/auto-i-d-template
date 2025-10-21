"""
Helper functions for RFC update test scenarios.

This module contains utility functions used by update test steps,
including the legacy simulated execution function for backward compatibility.
"""

import os
from behave.runner import Context


def legacy_simulated_execution(context: Context, command: str) -> None:
    """
    Legacy simulated execution for backward compatibility.

    This function provides fallback behavior when real command execution
    is not available. It simulates the /rfc-update command behavior based
    on context attributes set by test scenarios.

    Args:
        context: Behave test context
        command: Command string to simulate
    """
    context.command_exit_code = 0
    context.command_output = []

    if '/rfc-update' in command:
        # Extract RFC path from command
        parts = command.split()
        rfc_path_arg = next((p for p in parts if p.endswith('.md')), None)

        if rfc_path_arg:
            full_path = os.path.join(str(context.test_repo), rfc_path_arg)

            # Check if file exists
            if not os.path.exists(full_path):
                context.command_exit_code = 1
                context.command_output.append("❌ Cannot update non-existent RFC. Run /rfc-generate first.")
                return

            # Check if rfc-map.json exists
            if not os.path.exists(context.rfc_map_path):
                context.command_exit_code = 1
                context.command_output.append("❌ No traceability map found. Cannot determine changed sections.")
                context.command_output.append("Regenerate from scratch: /rfc-generate src/")
                return

            # Check Serena MCP availability
            if not getattr(context, 'serena_mcp_available', True):
                context.command_exit_code = 1
                context.command_output.append("❌ Serena MCP required for code analysis")
                context.command_output.append("Ensure Serena MCP server is running")
                return

            # Check for code changes
            if not getattr(context, 'code_changed', True):
                context.command_output.append("✅ No code changes detected. RFC is up-to-date.")
                return

            # Check for overlapping preserve blocks (ERROR level)
            if hasattr(context, 'overlap_range1') and hasattr(context, 'overlap_range2'):
                with open(full_path, 'r') as f:
                    rfc_content = f.read()
                if '@preserve-start id:block2' in rfc_content:
                    context.command_exit_code = 1
                    context.command_output.append("❌ Preserve block conflicts detected")
                    r1, r2 = context.overlap_range1, context.overlap_range2
                    context.command_output.append(f"Overlapping preserve blocks: block1 (lines {r1[0]}-{r1[1]}) and block2 (lines {r2[0]}-{r2[1]})")
                    return

            # Check for preserve block conflicts with changed sections (WARNING level)
            preserve_conflict_warning = (
                hasattr(context, 'preserve_block_section') and
                hasattr(context, 'affected_section') and
                not ('--force' in command)
            )
            if preserve_conflict_warning:
                context.command_output.append("⚠️  Preserve block warnings:")
                context.command_output.append("Preserve block 'custom-notes' overlaps with changed section §3.1")
                context.command_output.append("Continue anyway? Preserve blocks will take precedence.")
                # In real implementation, would wait for user input
                # For tests, we'll just return here unless --force is used
                return

            # Generate change detection report if code was modified
            if getattr(context, 'code_changed', False) and getattr(context, 'modified_method', None):
                context.command_output.append("📊 Change Detection Report:")
                context.command_output.append("  - Files modified: 1")
                context.command_output.append("  - Affected RFC sections: 1 (§3.1)")
                context.command_output.append("  - Severity: 1 BREAKING")
                context.command_output.append("Method signature modified (added parameter)")
                context.command_output.append("")  # Blank line

            # Simulate successful update
            is_dry_run = '--dry-run' in command
            is_force = '--force' in command

            if is_dry_run:
                context.command_output.append("🔍 DRY RUN - No files modified")
                context.command_output.append("Would update:")
                context.command_output.append(f"  📄 {rfc_path_arg}")
                context.command_output.append("  🔗 docs/rfc-map.json")
                context.command_output.append("Section 3.1 Calculator.add: REGENERATED")
            else:
                context.command_output.append("✅ RFC Updated Successfully")
                context.command_output.append(f"Files Updated:")
                context.command_output.append(f"  📄 {rfc_path_arg}")
                context.command_output.append(f"  🔗 docs/rfc-map.json")
                context.command_output.append("Sections regenerated: 1 (§3.1)")
                context.command_output.append("Sections preserved: 4")

                # Check for preserve blocks
                if hasattr(context, 'preserve_block_id'):
                    context.command_output.append("Preserve blocks honored: 1")

                # Check for preservation priority scenarios
                if hasattr(context, 'modified_lines') and hasattr(context, 'preserve_block_has_manual_content'):
                    context.command_output.append("Conflicts resolved: 1 (preservation priority applied)")
