"""
Library for generating reviewer guidance reports for RFC documentation updates.

This module creates actionable documentation impact reports for code reviewers,
helping them understand which RFC sections need review after code changes.
"""

import json
import logging
from typing import List, Dict, Set, Optional
from dataclasses import dataclass
from pathlib import Path

from .impact_analyzer import SectionImpact

logger = logging.getLogger(__name__)


@dataclass
class ReviewGuidance:
    """Complete reviewer guidance report."""
    title: str
    summary: Dict[str, int]  # severity -> count
    affected_sections: List[SectionImpact]
    review_checklist: List[str]
    missing_sections: List[str]
    recommendations: List[str]


def load_plugin_config(config_path: str = ".claude/plugin.json") -> Dict:
    """
    Load plugin configuration to get mandatory sections.

    Args:
        config_path: Path to plugin.json

    Returns:
        Configuration dictionary
    """
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"Plugin config not found at {config_path}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in plugin config: {e}")
        return {}


def load_rfc_map(rfc_map_path: str = "docs/rfc-map.json") -> Dict:
    """
    Load rfc-map.json for section information.

    Args:
        rfc_map_path: Path to rfc-map.json

    Returns:
        RFC map dictionary
    """
    try:
        with open(rfc_map_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"RFC map not found at {rfc_map_path}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in rfc-map.json: {e}")
        return {}


def identify_missing_sections(
    rfc_map: Dict,
    mandatory_sections: List[str]
) -> List[str]:
    """
    Check if any mandatory RFC sections are missing from documentation.

    Args:
        rfc_map: Parsed rfc-map.json
        mandatory_sections: List of required section names

    Returns:
        List of missing mandatory section names
    """
    if not rfc_map or not mandatory_sections:
        return []

    # Extract documented sections from rfc-map
    documented_sections = set()
    for mapping in rfc_map.get('mappings', []):
        section_type = mapping.get('rfc', {}).get('type', '')
        if section_type:
            documented_sections.add(section_type)

    # Also check metadata for documented sections
    metadata_sections = set()
    for section in rfc_map.get('metadata', {}).get('sections', []):
        section_type = section.get('type', '')
        if section_type:
            metadata_sections.add(section_type)

    documented_sections.update(metadata_sections)

    # Find missing mandatory sections
    missing = []
    for required in mandatory_sections:
        if required not in documented_sections:
            missing.append(required)

    if missing:
        logger.info(f"Missing mandatory sections: {missing}")

    return missing


def generate_review_checklist(impacts: List[SectionImpact]) -> List[str]:
    """
    Generate actionable review checklist based on affected sections.

    Args:
        impacts: List of SectionImpact objects

    Returns:
        List of checklist items
    """
    checklist = []

    # Group by severity
    critical = [i for i in impacts if i.severity == 'MUST_UPDATE']
    review = [i for i in impacts if i.severity == 'SHOULD_REVIEW']

    if critical:
        checklist.append("**Critical Updates Required**:")
        for impact in critical:
            checklist.append(
                f"  - [ ] Verify §{impact.section_number} ({impact.section_heading}) "
                f"reflects changes to {', '.join(impact.affected_code_elements[:3])}"
            )
            if len(impact.affected_code_elements) > 3:
                checklist.append(
                    f"        ...and {len(impact.affected_code_elements) - 3} more elements"
                )

    if review:
        checklist.append("")
        checklist.append("**Review Recommended**:")
        for impact in review:
            checklist.append(
                f"  - [ ] Review §{impact.section_number} ({impact.section_heading}) "
                f"for accuracy"
            )

    # General checks
    checklist.extend([
        "",
        "**General Validation**:",
        "  - [ ] Run `/rfc-validate` to check compliance",
        "  - [ ] Verify all cross-references are valid",
        "  - [ ] Check that examples match code behavior",
        "  - [ ] Ensure security considerations are updated if needed"
    ])

    return checklist


def generate_recommendations(
    impacts: List[SectionImpact],
    missing_sections: List[str]
) -> List[str]:
    """
    Generate recommendations for documentation updates.

    Args:
        impacts: List of SectionImpact objects
        missing_sections: List of missing mandatory sections

    Returns:
        List of recommendation strings
    """
    recommendations = []

    # Severity-based recommendations
    critical_count = len([i for i in impacts if i.severity == 'MUST_UPDATE'])
    if critical_count > 0:
        recommendations.append(
            f"🔴 {critical_count} section(s) require immediate updates before merge"
        )

    review_count = len([i for i in impacts if i.severity == 'SHOULD_REVIEW'])
    if review_count > 0:
        recommendations.append(
            f"🟡 {review_count} section(s) should be reviewed for accuracy"
        )

    # Missing sections
    if missing_sections:
        recommendations.append(
            f"⚠️  Missing mandatory sections: {', '.join(missing_sections)}"
        )
        recommendations.append(
            "   Consider running `/rfc-generate` to create missing sections"
        )

    # Deep analysis recommendation
    if critical_count > 2 or (critical_count > 0 and review_count > 5):
        recommendations.append(
            "💡 Consider running `/rfc-analyze-impact` for detailed semantic analysis"
        )

    # Update command
    if impacts:
        recommendations.append(
            "📝 Run `/rfc-update` to regenerate affected sections"
        )

    return recommendations


def generate_reviewer_guidance(
    impacts: List[SectionImpact],
    config_path: str = ".claude/plugin.json",
    rfc_map_path: str = "docs/rfc-map.json"
) -> ReviewGuidance:
    """
    Generate complete reviewer guidance report.

    Args:
        impacts: List of SectionImpact objects from impact analysis
        config_path: Path to plugin.json
        rfc_map_path: Path to rfc-map.json

    Returns:
        ReviewGuidance object with complete report data
    """
    # Load configuration
    config = load_plugin_config(config_path)
    rfc_map = load_rfc_map(rfc_map_path)

    # Get mandatory sections from config
    mandatory_sections = config.get('mandatory_sections', [
        'abstract',
        'introduction',
        'terminology',
        'interfaces',
        'behavior'
    ])

    # Count by severity
    summary = {
        'MUST_UPDATE': len([i for i in impacts if i.severity == 'MUST_UPDATE']),
        'SHOULD_REVIEW': len([i for i in impacts if i.severity == 'SHOULD_REVIEW']),
        'MAY_IGNORE': len([i for i in impacts if i.severity == 'MAY_IGNORE'])
    }

    # Identify missing sections
    missing_sections = identify_missing_sections(rfc_map, mandatory_sections)

    # Generate checklist and recommendations
    checklist = generate_review_checklist(impacts)
    recommendations = generate_recommendations(impacts, missing_sections)

    return ReviewGuidance(
        title="RFC Documentation Review Guidance",
        summary=summary,
        affected_sections=impacts,
        review_checklist=checklist,
        missing_sections=missing_sections,
        recommendations=recommendations
    )


def format_guidance_report(guidance: ReviewGuidance) -> str:
    """
    Format reviewer guidance as markdown for display.

    Args:
        guidance: ReviewGuidance object

    Returns:
        Markdown-formatted report string suitable for hook output
    """
    lines = [
        f"# {guidance.title}\n",
        "---\n",
        ""
    ]

    # Summary
    lines.append("## Summary\n")
    lines.append(f"- **Critical Updates**: {guidance.summary['MUST_UPDATE']}")
    lines.append(f"- **Review Recommended**: {guidance.summary['SHOULD_REVIEW']}")
    lines.append(f"- **Minor Changes**: {guidance.summary['MAY_IGNORE']}")
    lines.append(f"- **Total Sections Affected**: {len(guidance.affected_sections)}")
    lines.append("")

    # Affected sections
    if guidance.affected_sections:
        lines.append("## Affected RFC Sections\n")
        for impact in guidance.affected_sections:
            severity_icon = {
                'MUST_UPDATE': '🔴',
                'SHOULD_REVIEW': '🟡',
                'MAY_IGNORE': '🟢'
            }.get(impact.severity, '⚪')

            lines.append(
                f"### {severity_icon} §{impact.section_number}: {impact.section_heading}\n"
            )
            lines.append(f"**Severity**: {impact.severity}")
            lines.append(f"**Affected Code**: {', '.join(impact.affected_code_elements)}")
            lines.append(f"**Summary**: {impact.change_summary}")
            lines.append("")

    # Review checklist
    if guidance.review_checklist:
        lines.append("## Review Checklist\n")
        lines.extend(guidance.review_checklist)
        lines.append("")

    # Missing sections warning
    if guidance.missing_sections:
        lines.append("## ⚠️  Missing Mandatory Sections\n")
        lines.append("The following required sections are not documented:\n")
        for section in guidance.missing_sections:
            lines.append(f"- {section}")
        lines.append("")

    # Recommendations
    if guidance.recommendations:
        lines.append("## Recommendations\n")
        for rec in guidance.recommendations:
            lines.append(rec)
        lines.append("")

    # Footer
    lines.append("---")
    lines.append("*Generated by RFC Reviewer Guidance System*")
    lines.append("")

    return '\n'.join(lines)


# Utility function for testing and CLI usage
def _example_usage():
    """Example usage of reviewer_guidance module."""
    from .impact_analyzer import detect_affected_sections
    import sys

    # Detect impacts
    impacts = detect_affected_sections()

    if not impacts:
        print("✅ No RFC documentation updates needed - no reviewer guidance required")
        sys.exit(0)

    # Generate guidance
    guidance = generate_reviewer_guidance(impacts)
    report = format_guidance_report(guidance)
    print(report)

    # Exit with error if critical updates needed
    sys.exit(1 if guidance.summary['MUST_UPDATE'] > 0 else 0)


if __name__ == "__main__":
    # Setup logging for standalone execution
    logging.basicConfig(level=logging.INFO)
    _example_usage()
