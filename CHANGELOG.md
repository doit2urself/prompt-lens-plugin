# Changelog

## [1.1.0] - 2026-03-20

### Added
- Full PE principles integration into evaluation-instruction.md (Quality Checklist, Anti-patterns, Correction Strategies, Technique Selection Guide, Code Prompting, Output Configuration)
- Code Prompting Best Practices section (writing, explanation, translation, debugging)
- Decision Flowchart with 9 technique selection steps
- ref-docs: PDF-to-Markdown conversion of Google PE whitepaper
- ref-docs: Extracted PE principles reference document
- CHANGELOG.md for version tracking

### Changed
- evaluation-instruction.md: expanded from ~85 words to full PE knowledge base (~2,500 words)
- plugin.json: extended with author, repository, license, keywords, hooks path
- marketplace.json: version bump to 1.1.0

### Fixed
- Windows path regex pattern in prompt-refiner.py (session 1)
- README typo (session 1)

## [1.0.0] - 2026-03-19

### Added
- Core hook script (prompt-refiner.py) with 9 skip conditions
- UserPromptSubmit hook with additionalContext injection
- SessionStart hook with activation message
- Externalized evaluation-instruction.md
- 33 tests (skip conditions, injection, boundary, error handling)
- Fail-open error handling pattern
- Bypass prefix (*) support
- Korean language support for confirmations and selections
- Plugin marketplace configuration
- MIT License
