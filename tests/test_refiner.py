#!/usr/bin/env python3
"""Tests for prompt-refiner.py — runs via subprocess to match real hook behavior."""

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = str(Path(__file__).resolve().parent.parent / "scripts" / "prompt-refiner.py")


def run(prompt_or_data):
    """Run prompt-refiner.py with given input, return parsed JSON output."""
    if isinstance(prompt_or_data, str):
        data = {"prompt": prompt_or_data}
    else:
        data = prompt_or_data
    result = subprocess.run(
        [sys.executable, SCRIPT],
        input=json.dumps(data).encode(),
        capture_output=True,
        timeout=5,
    )
    assert result.returncode == 0, f"exit code {result.returncode}: {result.stderr}"
    return json.loads(result.stdout)


def is_injected(output):
    return "hookSpecificOutput" in output


def is_skipped(output):
    return output == {}


# ─── Skip conditions ───


def test_empty_prompt():
    assert is_skipped(run(""))


def test_whitespace_only():
    assert is_skipped(run("   \n\t  "))


def test_slash_command():
    assert is_skipped(run("/help"))
    assert is_skipped(run("/commit"))


def test_hash_memo():
    assert is_skipped(run("# remember this"))


def test_hash_markdown_heading_not_skipped():
    """Multi-line markdown-style prompts should NOT be skipped."""
    assert is_injected(run("# Refactor this module\nPlease restructure the auth logic"))


def test_hash_long_request_not_skipped():
    """Long single-line hash prompts (>=80 chars) should NOT be skipped."""
    assert is_injected(run("# " + "a" * 80))


def test_confirmations_en():
    for word in ["y", "n", "yes", "no", "ok", "sure", "yep", "nope", "continue",
                 "go ahead", "do it", "proceed", "keep going"]:
        assert is_skipped(run(word)), f"should skip: {word!r}"


def test_confirmations_kr():
    for word in ["ㅇ", "ㄴ", "네", "넵", "응", "아니", "좋아", "그래",
                 "계속", "진행", "해줘", "고고", "ㄱ"]:
        assert is_skipped(run(word)), f"should skip: {word!r}"


def test_selections():
    for word in ["1", "2.", "first", "second", "last",
                 "첫 번째", "두 번째", "마지막", "3번", "위에 거", "그거"]:
        assert is_skipped(run(word)), f"should skip: {word!r}"


def test_file_path_standalone():
    for path in ["./src/main.py", "main.py", "~/Documents/foo.ts",
                 "/usr/local/bin/python3", "config.json"]:
        assert is_skipped(run(path)), f"should skip: {path!r}"


def test_long_prompt():
    assert is_skipped(run("a" * 2001))


def test_bypass_prefix():
    assert is_skipped(run("* just do it"))


# ─── Should NOT skip (injection expected) ───


def test_normal_prompt():
    assert is_injected(run("fix the login bug"))


def test_prompt_with_filename():
    assert is_injected(run("fix bug in main.py"))
    assert is_injected(run("add tests for utils.ts"))
    assert is_injected(run("refactor database.go"))


def test_korean_natural_language():
    assert is_injected(run("...뭐야?"))
    assert is_injected(run("~한 느낌으로 작성해줘"))
    assert is_injected(run("이 코드 리뷰해줘"))


def test_single_letters_not_skipped():
    assert is_injected(run("o"))
    assert is_injected(run("q"))


def test_indented_list_not_code():
    assert is_injected(run("  항목 1\n  항목 2\n  항목 3\n  항목 4"))


def test_code_paste_skipped():
    code = "import os\nimport sys\nfrom pathlib import Path\ndef main():\n    pass"
    assert is_skipped(run(code))


def test_error_paste_skipped():
    error = "Traceback (most recent call last):\n  File \"main.py\"\nError: something failed"
    assert is_skipped(run(error))


def test_mixed_natural_language_and_code_not_skipped():
    # SBE-4: natural language request + error paste should NOT skip
    prompt = "이 에러 해결해줘:\n\nTraceback (most recent call last):\n  File \"main.py\", line 10\nValueError: bad input"
    assert is_injected(run(prompt)), "mixed NL+error should inject, not skip"


def test_mixed_request_with_code_snippet():
    prompt = "이 코드 리뷰해줘:\n\ndef foo():\n    return bar()\n\ndef baz():\n    pass"
    assert is_injected(run(prompt)), "mixed NL+code should inject, not skip"


def test_pure_code_still_skipped():
    # 100% code lines should still skip
    code = "import os\nimport sys\nimport json\nfrom pathlib import Path\ndef main():\n    pass"
    assert is_skipped(run(code))


# ─── Edge cases ───


def test_missing_prompt_field():
    assert is_skipped(run({}))


def test_null_prompt():
    assert is_skipped(run({"prompt": None}))


def test_prompt_with_coding_request_and_code():
    # Natural language + code snippet (< 3 indicators)
    prompt = "fix this bug\n\ndef foo():\n    pass"
    out = run(prompt)
    # 2 code indicators (def, indented) — should NOT skip
    # Actually with indentation removed, only 1 indicator (def) — should inject
    assert is_injected(out)


def test_injection_content():
    out = run("fix the login bug")
    ctx = out["hookSpecificOutput"]["additionalContext"]
    assert "HIGH-IMPACT" in ctx
    assert "Coding Prompt Clarity Check" in ctx
    assert "What to change" in ctx
    assert "Common Coding Prompt Gaps" in ctx


# ─── Boundary tests ───


def test_long_prompt_boundary_exact():
    # 2000 chars: should NOT skip (boundary)
    assert is_injected(run("a" * 2000))
    # 2001 chars: should skip
    assert is_skipped(run("a" * 2001))


def test_code_detection_boundary_lines():
    # 2 code lines (< 3 minimum): should NOT skip even at 100% ratio
    two_lines = "import os\nimport sys"
    assert is_injected(run(two_lines))
    # Exactly 3 code lines at 100%: should skip
    three_lines = "import os\nimport sys\nfrom pathlib import Path"
    assert is_skipped(run(three_lines))


def test_code_detection_boundary_ratio():
    # 3 code + 2 NL = 60% (< 70%): should NOT skip
    prompt = "import os\nimport sys\nfrom pathlib import Path\nplease review\nthis code"
    assert is_injected(run(prompt)), "60% code ratio should inject"
    # 3 code + 1 NL = 75% (>= 70%): should skip
    prompt2 = "import os\nimport sys\nfrom pathlib import Path\nplease review"
    assert is_skipped(run(prompt2)), "75% code ratio should skip"


# ─── Error handling tests ───


def test_malformed_json_input():
    """Non-JSON input should fail-open (empty JSON output, exit 0)."""
    result = subprocess.run(
        [sys.executable, SCRIPT],
        input=b"this is not json",
        capture_output=True,
        timeout=5,
    )
    assert result.returncode == 0
    assert json.loads(result.stdout) == {}


def test_empty_stdin():
    """Empty stdin should fail-open."""
    result = subprocess.run(
        [sys.executable, SCRIPT],
        input=b"",
        capture_output=True,
        timeout=5,
    )
    assert result.returncode == 0
    assert json.loads(result.stdout) == {}


def test_invalid_utf8():
    """Invalid UTF-8 bytes should fail-open."""
    bad_json = b'{"prompt": "hello \xff\xfe world"}'
    result = subprocess.run(
        [sys.executable, SCRIPT],
        input=bad_json,
        capture_output=True,
        timeout=5,
    )
    assert result.returncode == 0
    # Should either inject or skip, but never crash
    json.loads(result.stdout)  # must be valid JSON


# ─── Bypass-skip interaction tests ───


def test_bypass_with_leading_spaces():
    """Bypass prefix with leading whitespace should still bypass."""
    assert is_skipped(run("  * something"))


def test_bypass_overrides_skip_conditions():
    """Bypass prefix takes precedence over skip conditions (both produce {})."""
    assert is_skipped(run("* /help"))
    assert is_skipped(run("* y"))
    assert is_skipped(run("* 1"))


# ─── FILE_PATH edge case tests ───


def test_file_path_with_natural_language():
    """File path embedded in a sentence should NOT be skipped."""
    assert is_injected(run("main.py 파일을 수정해줘"))
    assert is_injected(run("fix bug in src/utils.ts please"))


def test_extensionless_file_not_skipped():
    """Files without recognized extensions should NOT be skipped."""
    assert is_injected(run("Makefile"))
    assert is_injected(run("Dockerfile"))


def test_windows_path():
    assert is_skipped(run("C:\\Users\\foo\\main.py"))


# ─── Confirmation edge case tests ───


def test_multiword_confirmation_variants():
    """Multi-word confirmations with varying whitespace."""
    assert is_skipped(run("go ahead"))
    assert is_skipped(run("do it"))
    assert is_skipped(run("go for it"))


# ─── Debug mode tests ───


def test_debug_mode_stderr():
    """PROMPTLENS_DEBUG=1 should produce stderr output."""
    import os
    env = os.environ.copy()
    env["PROMPTLENS_DEBUG"] = "1"
    result = subprocess.run(
        [sys.executable, SCRIPT],
        input=json.dumps({"prompt": "test debug mode"}).encode(),
        capture_output=True,
        timeout=5,
        env=env,
    )
    assert result.returncode == 0
    assert b"[PromptLens]" in result.stderr


def test_debug_mode_skip_logging():
    """Debug mode should log skip decisions to stderr."""
    import os
    env = os.environ.copy()
    env["PROMPTLENS_DEBUG"] = "1"
    result = subprocess.run(
        [sys.executable, SCRIPT],
        input=json.dumps({"prompt": "/help"}).encode(),
        capture_output=True,
        timeout=5,
        env=env,
    )
    assert result.returncode == 0
    assert b"skip" in result.stderr


# ─── Output structure tests ───


def test_skip_output_is_empty_json():
    """Skip output must be exactly {}."""
    out = run("")
    assert out == {}
    assert isinstance(out, dict)


def test_inject_output_structure():
    """Injected output must have correct nested structure."""
    out = run("fix the login bug")
    assert "hookSpecificOutput" in out
    hook = out["hookSpecificOutput"]
    assert hook["hookEventName"] == "UserPromptSubmit"
    assert isinstance(hook["additionalContext"], str)
    assert len(hook["additionalContext"]) > 0


if __name__ == "__main__":
    passed = 0
    failed = 0
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for test_fn in tests:
        try:
            test_fn()
            passed += 1
            print(f"  PASS  {test_fn.__name__}")
        except (AssertionError, Exception) as e:
            failed += 1
            print(f"  FAIL  {test_fn.__name__}: {e}")
    print(f"\n{'='*40}")
    print(f"  {passed} passed, {failed} failed, {passed + failed} total")
    if failed:
        sys.exit(1)
