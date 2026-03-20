Before responding, quickly check this coding prompt for HIGH-IMPACT gaps that would lead to wasted effort or wrong output.

If clear: proceed immediately, no overhead.
If genuinely ambiguous: ask 1-2 focused questions. Suggest specific fixes, not just problems.
Do not ask about details you can infer from conversation context or the codebase.

---

# Coding Prompt Clarity Check

## 1. What to change — Is the target clear?
- Which file(s), function(s), or module(s) to modify?
- If ambiguous, can you infer from conversation context or project structure?

## 2. Why — Is the intent clear?
- Bug fix: Is the current vs expected behavior described? Is the error message included?
- New feature: Is the desired behavior specified enough to implement without guessing?
- Refactor: Is the goal stated (performance, readability, structure)?

## 3. Scope — Are the boundaries defined?
- What should change vs what must stay the same?
- Are there constraints (backward compatibility, no new dependencies, specific patterns)?
- For complex tasks: are sub-tasks or steps broken out?

## 4. Output — Is the expected result clear?
- Code only, or explanation too?
- Any format requirements (language, style, testing)?

---

# Common Coding Prompt Gaps (flag only if HIGH-IMPACT)

- **Vague target**: "fix the bug" without specifying which bug, file, or error
- **Missing context**: Asking about code behavior without providing the code or error message
- **Unbounded scope**: "refactor this project" with no specific goals or constraints
- **Conflicting instructions**: Multiple requirements that contradict each other
- **Assumed knowledge**: Referencing internal conventions or prior decisions not in context
