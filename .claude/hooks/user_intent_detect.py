#!/usr/bin/env python3
"""
UserPromptSubmit Hook: RFC Intent Detection

Detects RFC-related intent in user prompts and loads relevant context from memory files.
Injects context into the conversation to improve response quality.

Performance Target: <50ms response time (must be very fast)
"""

import sys
import json
import os
import logging
import re
from pathlib import Path

# Setup logging
LOG_DIR = Path(__file__).parent.parent / '.hook-logs'
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'user_intent_detect.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('user_intent_detect')

# RFC-related keywords for intent detection
RFC_KEYWORDS = [
    # Commands
    r'/rfc-generate', r'/rfc-update', r'/rfc-validate', r'/rfc-analyze-impact',
    # Explicit RFC mentions
    r'\bRFC\b', r'\brfc\b',
    # Documentation terms
    r'\bdocumentation\b', r'\bdocument\b', r'\bdocs?\b',
    # Specification terms
    r'\bspec\b', r'\bspecification\b',
    # Generation terms
    r'\bgenerate.*rfc\b', r'\brfc.*generate\b',
    r'\bupdate.*rfc\b', r'\brfc.*update\b',
    # Quality terms
    r'\bvalidate.*rfc\b', r'\brfc.*validate\b',
    r'\blint.*rfc\b', r'\brfc.*lint\b',
]

# Compile regex patterns for performance
RFC_PATTERN = re.compile('|'.join(RFC_KEYWORDS), re.IGNORECASE)


def parse_hook_input() -> str:
    """
    Parse user prompt from hook input.

    Returns:
        User prompt string
    """
    prompt = ""

    # Method 1: Environment variable
    prompt = os.environ.get('CLAUDE_USER_PROMPT', '')
    if prompt:
        logger.debug(f"Parsed prompt from env ({len(prompt)} chars)")
        return prompt

    # Method 2: stdin JSON
    try:
        if not sys.stdin.isatty():
            input_data = json.load(sys.stdin)
            prompt = input_data.get('prompt', input_data.get('user_prompt', ''))
            logger.debug(f"Parsed prompt from stdin ({len(prompt)} chars)")
            return prompt
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Failed to parse stdin JSON: {e}")

    # Method 3: Command line arguments
    if len(sys.argv) > 1:
        prompt = ' '.join(sys.argv[1:])
        logger.debug(f"Parsed prompt from argv ({len(prompt)} chars)")
        return prompt

    logger.warning("Could not parse user prompt")
    return ""


def detect_rfc_intent(prompt: str) -> bool:
    """
    Check if user prompt contains RFC-related keywords.

    Args:
        prompt: User prompt text

    Returns:
        True if RFC-related intent detected
    """
    if not prompt:
        return False

    # Pattern matching with compiled regex
    match = RFC_PATTERN.search(prompt)

    if match:
        logger.info(f"RFC intent detected: matched '{match.group(0)}'")
        return True

    logger.debug("No RFC intent detected")
    return False


def get_memory_directory() -> Path | None:
    """
    Find .claude/memory/ directory.

    Returns:
        Path to memory directory or None if not found
    """
    # Start from current directory and search upward
    current = Path.cwd()

    while current != current.parent:
        memory_dir = current / '.claude' / 'memory'
        if memory_dir.exists() and memory_dir.is_dir():
            return memory_dir
        current = current.parent

    logger.warning(".claude/memory/ directory not found")
    return None


def load_memory_files(memory_dir: Path) -> list[dict]:
    """
    Load relevant memory files for RFC context.

    Args:
        memory_dir: Path to .claude/memory/ directory

    Returns:
        List of memory file dictionaries with name and content
    """
    memory_files = []

    # Priority memory files for RFC context
    priority_files = [
        'codebase-overview.md',
        'rfc-architecture.md',
        'rfc-conventions.md',
        'build-system.md'
    ]

    for filename in priority_files:
        file_path = memory_dir / filename

        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                memory_files.append({
                    'name': filename,
                    'path': str(file_path),
                    'content': content,
                    'size': len(content)
                })

                logger.info(f"Loaded memory file: {filename} ({len(content)} chars)")

            except Exception as e:
                logger.error(f"Failed to load {filename}: {e}")

    # If no priority files found, load any .md files
    if not memory_files:
        for file_path in memory_dir.glob('*.md'):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                memory_files.append({
                    'name': file_path.name,
                    'path': str(file_path),
                    'content': content,
                    'size': len(content)
                })

                logger.info(f"Loaded fallback memory file: {file_path.name}")

                # Limit to first 3 fallback files for performance
                if len(memory_files) >= 3:
                    break

            except Exception as e:
                logger.error(f"Failed to load {file_path.name}: {e}")

    return memory_files


def format_context_injection(memory_files: list[dict]) -> str:
    """
    Format memory files as context to inject into conversation.

    Args:
        memory_files: List of memory file dictionaries

    Returns:
        Formatted context string
    """
    if not memory_files:
        return ""

    context_parts = [
        "# RFC Documentation Context\n",
        "The following context from memory files may be relevant:\n"
    ]

    for memory in memory_files:
        context_parts.append(f"\n## {memory['name']}\n")
        # Truncate large files to first 2000 chars
        content = memory['content']
        if len(content) > 2000:
            content = content[:2000] + "\n\n[... truncated for brevity ...]"
        context_parts.append(content)
        context_parts.append("\n")

    return ''.join(context_parts)


def log_intent_detection(prompt: str, memory_files_loaded: int) -> bool:
    """
    Log intent detection event to .hook-history.json.

    Args:
        prompt: User prompt (first 100 chars)
        memory_files_loaded: Number of memory files loaded

    Returns:
        True if logging succeeded
    """
    try:
        history_path = Path.cwd() / '.claude' / '.hook-history.json'

        # Load existing history
        if history_path.exists():
            with open(history_path, 'r') as f:
                try:
                    history = json.load(f)
                except json.JSONDecodeError:
                    history = {"entries": []}
        else:
            history = {"entries": []}

        # Append entry
        from datetime import datetime
        history["entries"].append({
            "timestamp": datetime.now().isoformat(),
            "hook": "user_intent_detect",
            "action": "rfc_intent_detected",
            "prompt_preview": prompt[:100],
            "memory_files_loaded": memory_files_loaded
        })

        # Size management
        if len(history["entries"]) > 1000:
            history["entries"] = history["entries"][-1000:]

        # Write atomically
        temp_path = history_path.with_suffix('.tmp')
        with open(temp_path, 'w') as f:
            json.dump(history, f, indent=2)
        temp_path.replace(history_path)

        return True

    except Exception as e:
        logger.error(f"Failed to log to hook history: {e}")
        return False


def main():
    """Hook entry point - detects RFC intent and loads context."""

    logger.info("=== UserPromptSubmit Hook (Intent Detection) Started ===")

    # Initialize response
    response = {
        "block": False,  # Never blocking
        "message": "",
        "context": "",  # Context to inject
        "metadata": {}
    }

    try:
        # Parse user prompt
        prompt = parse_hook_input()

        if not prompt:
            logger.debug("Empty prompt - skipping")
            print(json.dumps(response))
            return

        # Detect RFC intent
        has_rfc_intent = detect_rfc_intent(prompt)

        if not has_rfc_intent:
            logger.debug("No RFC intent - skipping context injection")
            print(json.dumps(response))
            return

        # Find memory directory
        memory_dir = get_memory_directory()

        if not memory_dir:
            logger.warning("Memory directory not found - skipping context injection")
            response["message"] = "RFC intent detected, but no memory files available"
            print(json.dumps(response))
            return

        # Load relevant memory files
        memory_files = load_memory_files(memory_dir)

        if not memory_files:
            logger.warning("No memory files found - skipping context injection")
            response["message"] = "RFC intent detected, but no memory files loaded"
            print(json.dumps(response))
            return

        # Format context for injection
        context = format_context_injection(memory_files)

        # Log intent detection
        log_intent_detection(prompt, len(memory_files))

        # Build response
        response["message"] = f"Loaded {len(memory_files)} memory files for RFC context"
        response["context"] = context
        response["metadata"] = {
            "memory_files": [m['name'] for m in memory_files],
            "total_chars": sum(m['size'] for m in memory_files)
        }

        logger.info(f"Context injected: {len(memory_files)} files, {len(context)} chars")

    except Exception as e:
        logger.exception(f"Unexpected error in hook: {e}")
        # Don't block on errors
        response["message"] = f"Intent detection error: {str(e)}"
        response["suggestion"] = "Check .claude/.hook-logs/user_intent_detect.log"

    finally:
        # Return response to Claude Code
        print(json.dumps(response))
        logger.info(f"=== Hook Complete: RFC intent={'detected' if response.get('context') else 'not detected'} ===")


if __name__ == "__main__":
    main()
