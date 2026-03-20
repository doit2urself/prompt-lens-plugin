#!/usr/bin/env python3
"""PromptLens - Lightweight prompt evaluation wrapper.

Reads user prompt from stdin (UserPromptSubmit hook),
applies skip conditions, and injects PE evaluation guidance
via additionalContext for Claude to self-assess prompt clarity.
"""

import json
import os
import re
import sys

MAX_STDIN_BYTES = 65536  # 64KB
DEBUG = os.environ.get("PROMPTLENS_DEBUG") == "1"
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "promptlens.log")


def debug(msg: str) -> None:
    """Log to file and stderr when PROMPTLENS_DEBUG=1."""
    if DEBUG:
        print(f"[PromptLens] {msg}", file=sys.stderr)
        with open(LOG_FILE, "a") as f:
            f.write(f"[PromptLens] {msg}\n")

INSTRUCTION_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "evaluation-instruction.md"
)


def _load_instruction() -> str:
    """Load evaluation instruction from external MD file. Returns empty string on failure."""
    try:
        with open(INSTRUCTION_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except (OSError, IOError) as e:
        debug(f"instruction file load failed → {e}")
        return ""


EVALUATION_INSTRUCTION = _load_instruction()

# Skip patterns
CONFIRMATIONS = re.compile(
    r"^(y|n|x|k|yes|no|ok|okay|sure|yep|nope|yea|nah"
    r"|ㅇ|ㄴ|ㅋ|ㅎ|네|넵|응|아니|아뇨|좋아|그래|됐어|ㄱㄱ|ㄴㄴ"
    r"|continue|go\s*ahead|do\s*it|go\s*for\s*it|proceed|keep\s*going"
    r"|계속|진행|해줘|해\s*줘|고고|ㄱ)$",
    re.IGNORECASE,
)

SELECTIONS = re.compile(
    r"^(\d+\.?|first|second|third|last"
    r"|첫\s*번째|두\s*번째|세\s*번째|마지막"
    r"|[1-9]번|위에?\s*거|아래\s*거|그거)$",
    re.IGNORECASE,
)

FILE_PATH = re.compile(
    r"^(?:"
    r"~?/\S+"                  # Unix absolute/home: /foo, ~/bar
    r"|\./\S+"                 # Relative: ./foo
    r"|[a-zA-Z]:\\\\\\S+"      # Windows: C:\path (escaped backslash)
    r"|\S+\.(?:py|js|ts|tsx|jsx|go|rs|java|c|cpp|h|rb|php|sh|yml|yaml|json|toml|md|txt|css|html|sql|swift|kt)"
    r")$",                     # Bare filename: main.py (must be entire string)
    re.IGNORECASE,
)


CODE_LINE = re.compile(
    r"(?:^(?:import |from |def |class |function |const |let |var "
    r"|if |for |while |return |raise |throw |catch |try "
    r"|Traceback|Error:|at |File ))"
    r"|(?:[{};]$|=>$)"
    r"|(?:(?:def |class |if |elif |else|for |while |with |except )\S.*:$)",
)


def looks_like_code_paste(prompt: str) -> bool:
    """Detect pasted code or error messages.

    Only skips when the prompt is predominantly code (>=70% of lines).
    Mixed prompts (natural language + code) are NOT skipped.
    """
    lines = prompt.strip().split("\n")
    if len(lines) < 3:
        return False
    code_indicators = sum(1 for line in lines if CODE_LINE.search(line.strip()))
    # Require both absolute (3+) and relative (70%+) thresholds
    return code_indicators >= 3 and code_indicators / len(lines) >= 0.7


def should_skip(prompt: str) -> bool:
    """Check all 9 skip conditions."""
    stripped = prompt.strip()

    # 1. Empty
    if not stripped:
        return True

    # 2. Slash command
    if stripped.startswith("/"):
        return True

    # 3. Hash memo
    if stripped.startswith("#"):
        return True

    # 4. Short confirmation
    if CONFIRMATIONS.match(stripped):
        return True

    # 5. Selection response
    if SELECTIONS.match(stripped):
        return True

    # 6. File path only
    if "\n" not in stripped and FILE_PATH.search(stripped) and len(stripped) < 200:
        return True

    # 7. Code/error paste
    if looks_like_code_paste(stripped):
        return True

    # 8. Very long prompt (likely well-specified)
    if len(stripped) > 2000:
        return True

    return False


def main():
    try:
        raw = sys.stdin.buffer.read(MAX_STDIN_BYTES)
        data = json.loads(raw.decode("utf-8", errors="replace"))
        prompt = data.get("prompt", "") or ""

        # Bypass prefix: * skips evaluation
        if prompt.lstrip().startswith("*"):
            debug("bypass prefix → skip")
            json.dump({}, sys.stdout)
            sys.exit(0)

        if should_skip(prompt):
            debug(f"skip → {prompt[:40]!r}")
            json.dump({}, sys.stdout)
            sys.exit(0)

        # Inject evaluation instruction
        debug(f"inject → {prompt[:40]!r}")
        output = {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": EVALUATION_INSTRUCTION,
            }
        }
        json.dump(output, sys.stdout)
        sys.exit(0)

    except Exception as e:
        # Fail-open: any error → pass prompt through unchanged
        debug(f"error → {e}")
        json.dump({}, sys.stdout)
        sys.exit(0)


if __name__ == "__main__":
    main()
