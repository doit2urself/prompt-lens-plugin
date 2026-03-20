# PromptLens

Claude Code plugin that silently evaluates prompt clarity and asks focused clarifying questions when needed.

## How it works

PromptLens hooks into every `UserPromptSubmit` event and injects a lightweight coding-focused evaluation checklist (~400 tokens) via `additionalContext`. Claude uses this checklist to decide whether to proceed immediately or ask 1-2 clarifying questions before starting work.

You won't see the plugin working — it's designed to be invisible. Claude just becomes better at catching ambiguous requests.

## Install

```bash
claude plugin add /path/to/prompt-lens-plugin
```

Or clone and add:

```bash
git clone https://github.com/doit2urself/prompt-lens-plugin.git
claude plugin add ./prompt-lens-plugin
```

## Skip conditions

PromptLens automatically skips evaluation for prompts that don't benefit from it:

| # | Condition | Example |
|---|-----------|---------|
| 1 | Empty / whitespace | `""`, `"  "` |
| 2 | Slash commands | `/help`, `/commit` |
| 3 | Short hash memos | `# note to self` |
| 4 | Confirmations | `y`, `ok`, `네`, `go ahead` |
| 5 | Selections | `1`, `first`, `두 번째` |
| 6 | Standalone file paths | `main.py`, `./src/utils.ts` |
| 7 | Code/error pastes (>=70% code lines) | Pure code blocks, tracebacks |
| 8 | Long prompts (>2000 chars) | Already well-specified |

## Bypass

Prefix any prompt with `*` to skip evaluation:

```
* just do it without checking
```

## Debug

Set the environment variable to enable logging:

```bash
export PROMPTLENS_DEBUG=1
```

Logs go to `promptlens.log` in the plugin root and `stderr`.

## Tests

```bash
python3 -m pytest tests/ -v
```

## Requirements

- Python 3.6+
- Claude Code with plugin support

## License

MIT
