#!/usr/bin/env python3
"""
Schema Validator for RFC Documentation Generator

Validates JSON outputs from parser, analyzer, and formatter agents
against expected schemas to catch mismatches early and prevent
cascading failures.

Part of Phase 1 Perplexity recommendations (R-C1.2).
"""

import json
from typing import Tuple, Dict, Any, List
from jsonschema import validate, ValidationError, Draft7Validator


# JSON Schema for Parser Output
PARSER_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["summary", "files", "symbols"],
    "properties": {
        "summary": {
            "type": "object",
            "required": ["files_analyzed", "public_apis", "types"],
            "properties": {
                "files_analyzed": {"type": "integer", "minimum": 0},
                "public_apis": {"type": "integer", "minimum": 0},
                "types": {"type": "integer", "minimum": 0},
                "private_symbols_skipped": {"type": "integer", "minimum": 0},
                "phase_1_symbols": {"type": "integer", "minimum": 0},
                "phase_2_symbols": {"type": "integer", "minimum": 0}
            }
        },
        "files": {
            "type": "array",
            "items": {"type": "string"}
        },
        "symbols": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name", "type", "file", "line_start", "visibility"],
                "properties": {
                    "name": {"type": "string"},
                    "type": {"enum": ["class", "function", "module", "interface", "constant"]},
                    "file": {"type": "string"},
                    "line_start": {"type": "integer", "minimum": 1},
                    "line_end": {"type": "integer", "minimum": 1},
                    "visibility": {"enum": ["public", "private", "protected"]},
                    "docstring": {"type": "string"},
                    "signature": {"type": "string"},
                    "dependencies": {"type": "array", "items": {"type": "string"}},
                    "provenance": {"enum": ["defined_here", "re_exported", "inherited"]},
                    "parameter_constraints": {"type": "array"},
                    "deprecation_info": {"type": ["object", "null"]},
                    "usage_examples": {"type": "array", "items": {"type": "string"}},
                    "methods": {"type": "array"}
                }
            }
        },
        "interfaces": {"type": "array"},
        "types": {"type": "array"},
        "errors": {"type": "array"}
    }
}


# JSON Schema for Analyzer Output
ANALYZER_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["relationships", "behaviors", "external_standards"],
    "properties": {
        "relationships": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["source", "target", "type"],
                "properties": {
                    "source": {"type": "object"},
                    "target": {"type": "object"},
                    "type": {"enum": ["calls", "inherits", "implements", "uses", "contains"]},
                    "context": {"type": "string"}
                }
            }
        },
        "behaviors": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name", "type"],
                "properties": {
                    "name": {"type": "string"},
                    "type": {"enum": ["state_machine", "workflow", "algorithm", "pipeline"]},
                    "file": {"type": "string"},
                    "description": {"type": "string"},
                    "states": {"type": "array"},
                    "transitions": {"type": "array"}
                }
            }
        },
        "external_standards": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["standard_id", "confidence", "detection_method"],
                "properties": {
                    "standard_id": {"type": "string"},
                    "title": {"type": "string"},
                    "detected_in": {"type": "array"},
                    "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                    "detection_method": {"enum": ["config", "comment", "signature"]}
                }
            }
        },
        "design_patterns": {"type": "array"},
        "symbol_to_protocol_map": {"type": "array"},
        "errors": {"type": "array"}
    }
}


# JSON Schema for Formatter Output
FORMATTER_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["rfc_content", "mappings"],
    "properties": {
        "rfc_content": {
            "type": "string",
            "minLength": 100
        },
        "mappings": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["file", "symbol", "line", "section", "heading", "relationship"],
                "properties": {
                    "file": {"type": "string"},
                    "symbol": {"type": "string"},
                    "line": {"type": "integer", "minimum": 1},
                    "section": {"type": "string", "pattern": "^\\d+(\\.\\d+)*$"},
                    "heading": {"type": "string"},
                    "relationship": {"enum": ["describes", "implements", "references", "example"]},
                    "file_checksum": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
                    "git_commit": {"type": "string", "pattern": "^[a-f0-9]{40}$"}
                }
            }
        }
    }
}


def validate_parser_output(data: Dict[str, Any]) -> Tuple[bool, str, List[str]]:
    """
    Validate parser agent output against expected JSON schema.

    Args:
        data: Parser output JSON

    Returns:
        Tuple of (is_valid, message, error_details)
        - is_valid: True if validation passed
        - message: Success or error message
        - error_details: List of specific validation errors
    """
    try:
        validate(instance=data, schema=PARSER_SCHEMA)

        # Additional validation: Check line number consistency
        errors = []
        for symbol in data.get("symbols", []):
            if "line_end" in symbol and symbol.get("line_end", 0) < symbol.get("line_start", 0):
                errors.append(
                    f"Symbol {symbol['name']}: line_end ({symbol['line_end']}) < line_start ({symbol['line_start']})"
                )

        if errors:
            return False, "Parser output has logical inconsistencies", errors

        return True, "Parser output valid", []

    except ValidationError as e:
        error_details = [f"{e.message} at path: {'.'.join(str(p) for p in e.path)}"]
        return False, f"Parser output schema validation failed: {e.message}", error_details


def validate_analyzer_output(data: Dict[str, Any]) -> Tuple[bool, str, List[str]]:
    """
    Validate analyzer agent output against expected JSON schema.

    Args:
        data: Analyzer output JSON

    Returns:
        Tuple of (is_valid, message, error_details)
    """
    try:
        validate(instance=data, schema=ANALYZER_SCHEMA)

        # Additional validation: Check confidence scores
        errors = []
        for standard in data.get("external_standards", []):
            confidence = standard.get("confidence", 0.0)
            if confidence < 0.6:
                errors.append(
                    f"Standard {standard['standard_id']}: confidence {confidence} < 0.6 threshold"
                )

        if errors:
            return False, "Analyzer output has low-confidence detections", errors

        return True, "Analyzer output valid", []

    except ValidationError as e:
        error_details = [f"{e.message} at path: {'.'.join(str(p) for p in e.path)}"]
        return False, f"Analyzer output schema validation failed: {e.message}", error_details


def validate_formatter_output(data: Dict[str, Any]) -> Tuple[bool, str, List[str]]:
    """
    Validate formatter agent output against expected JSON schema.

    Args:
        data: Formatter output JSON

    Returns:
        Tuple of (is_valid, message, error_details)
    """
    try:
        validate(instance=data, schema=FORMATTER_SCHEMA)

        # Additional validation: Check RFC content quality
        errors = []
        rfc_content = data.get("rfc_content", "")

        # Check for mandatory sections
        required_sections = ["# Abstract", "# Terminology", "# Interfaces"]
        missing_sections = [sec for sec in required_sections if sec not in rfc_content]
        if missing_sections:
            errors.append(f"Missing required sections: {', '.join(missing_sections)}")

        # Check for security review marker
        if "# Security Considerations" in rfc_content:
            if "[NEEDS MANUAL REVIEW" not in rfc_content:
                errors.append("Security Considerations section missing manual review marker")

        # Check for RFC 2119 keyword consistency (case-sensitive)
        lowercase_keywords = ["must ", "should ", "may "]
        for keyword in lowercase_keywords:
            if keyword in rfc_content.lower() and keyword in rfc_content:
                errors.append(f"Found lowercase RFC 2119 keyword: '{keyword}' (should be uppercase)")

        if errors:
            return False, "Formatter output has quality issues", errors

        return True, "Formatter output valid", []

    except ValidationError as e:
        error_details = [f"{e.message} at path: {'.'.join(str(p) for p in e.path)}"]
        return False, f"Formatter output schema validation failed: {e.message}", error_details


def validate_agent_output(agent_name: str, data: Dict[str, Any]) -> Tuple[bool, str, List[str]]:
    """
    Dispatch validation to appropriate validator based on agent name.

    Args:
        agent_name: Name of agent ("parser", "analyzer", "formatter")
        data: Agent output JSON

    Returns:
        Tuple of (is_valid, message, error_details)
    """
    validators = {
        "parser": validate_parser_output,
        "analyzer": validate_analyzer_output,
        "formatter": validate_formatter_output
    }

    validator = validators.get(agent_name.lower())
    if not validator:
        return False, f"Unknown agent: {agent_name}", []

    return validator(data)


def get_schema(agent_name: str) -> Dict[str, Any]:
    """
    Get JSON schema for specified agent.

    Args:
        agent_name: Name of agent ("parser", "analyzer", "formatter")

    Returns:
        JSON schema dict
    """
    schemas = {
        "parser": PARSER_SCHEMA,
        "analyzer": ANALYZER_SCHEMA,
        "formatter": FORMATTER_SCHEMA
    }
    return schemas.get(agent_name.lower(), {})


# CLI for testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: schema_validator.py <agent_name> <json_file>")
        print("Example: schema_validator.py parser .claude/.checkpoints/parser-123456.json")
        sys.exit(1)

    agent_name = sys.argv[1]
    json_file = sys.argv[2]

    try:
        with open(json_file, "r") as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load JSON file: {e}")
        sys.exit(1)

    is_valid, message, errors = validate_agent_output(agent_name, data)

    if is_valid:
        print(f"✅ {message}")
        sys.exit(0)
    else:
        print(f"❌ {message}")
        if errors:
            print("\nErrors:")
            for error in errors:
                print(f"  - {error}")
        sys.exit(1)
