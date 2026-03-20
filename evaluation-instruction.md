Before responding, evaluate this prompt using the PE principles below. Only flag HIGH-IMPACT gaps that would lead to wasted effort.

If clear: proceed immediately, no overhead.
If genuinely ambiguous with high-impact unknowns: ask 1-2 focused questions before proceeding. Suggest specific fixes, don't just flag problems.
Do not ask about low-impact details you can reasonably infer from conversation context.

---

# Prompt Quality Checklist

## Clarity & Structure
- Uses a clear action verb (Act, Analyze, Classify, Compare, Create, Describe, Extract, Generate, List, Parse, Summarize, Translate, Write, etc.)
- Is concise — no unnecessary words or complex language
- Intent is unambiguous; a reader can tell exactly what output is expected
- If the prompt is confusing to a human, it will be confusing to the model

## Specificity
- Output format is specified (JSON, bullet list, paragraph count, length constraint, etc.)
- Scope is clearly bounded (topic, number of items, length)
- Desired tone/style is stated when relevant (formal, humorous, technical, etc.)

## Framing
- Uses positive instructions ("do X") rather than negative constraints ("don't do Y")
- Tells the model what to include, not just what to exclude

## Examples
- Includes at least one example when a specific output pattern is expected
- Examples are diverse, high-quality, and relevant to the task
- For classification tasks, examples mix up the response classes (not grouped by label)

## Context
- Provides sufficient background information for the task
- Assigns a role when domain expertise would improve the response
- Uses a system prompt to define overarching behavior when appropriate

## Complexity Management
- Complex tasks are broken into explicit steps or sub-tasks
- Reasoning-heavy tasks include a "think step by step" instruction or demonstrate chain-of-thought
- Multi-part questions are separated rather than bundled into one sentence

## Output Control
- Specifies max token length or natural-language length constraint when brevity matters
- Uses variables/placeholders for reusable prompt templates

---

# Common Prompt Anti-patterns

## Vagueness
- Problem: Prompt provides only a general topic with no specifics.
- Example: "Generate a blog post about video game consoles."
- Fix: Add length, count, style, and content constraints. "Generate a 3 paragraph blog post about the top 5 video game consoles. The blog post should be informative and engaging, written in a conversational style."

## Negative-Only Framing
- Problem: Prompt tells the model what NOT to do instead of what TO do.
- Example: "Generate a 1 paragraph blog post about the top 5 video game consoles. Do not list video game names."
- Fix: Reframe as positive instructions. "Generate a 1 paragraph blog post about the top 5 video game consoles. Only discuss the console, the company who made it, the year, and total sales."

## Missing Examples When Pattern Matters
- Problem: Expecting a specific output structure (JSON, table, classification label) without demonstrating it.
- Fix: Add one-shot or few-shot examples showing the exact desired format.

## Overly Complex Single Prompt
- Problem: Packing multiple distinct tasks into one prompt without structure.
- Fix: Break into steps, use numbered sub-tasks, or chain prompts.

## No Role or Context
- Problem: Asking for domain-specific output without grounding the model.
- Example: "What places should I visit?"
- Fix: "Act as a travel guide. I am in Amsterdam and I want to visit only museums. Suggest 3 places."

## Wrong Prompt Type for the Task
- Problem: Using zero-shot when the task requires pattern matching; using verbose prompts when simple ones suffice.
- Fix: Match the prompting technique to the task complexity (see Technique Selection Guide below).

## Unordered Classification Examples
- Problem: All few-shot examples for class A appear first, then class B, causing overfitting to order.
- Fix: Interleave examples from different classes randomly.

## Ignoring Input Format
- Problem: Providing unstructured data when the model could benefit from structured input.
- Fix: Use JSON schemas or clearly labeled sections to structure the input data.

---

# Correction Strategies (ordered by impact)

## 1. Add Examples (One-shot / Few-shot)
- The single most important best practice.
- Examples act as a teaching tool: show the model desired output format and quality.
- Rule of thumb: start with 3-5 examples; start with 6 for classification tasks and test accuracy from there.
- Examples should be diverse, high-quality, and well-written. One mistake in an example will propagate.
- Include edge cases when robustness to unusual inputs is needed.

## 2. Use Action Verbs (Design with Simplicity)
- Replace conversational phrasing with direct action verbs.
- Before: "I am visiting New York right now, and I'd like to hear more about great locations. I am with two 3 year old kids. Where should we go during our vacation?"
- After: "Act as a travel guide for tourists. Describe great places to visit in New York Manhattan with a 3 year old."
- Preferred verbs: Act, Analyze, Categorize, Classify, Contrast, Compare, Create, Describe, Define, Evaluate, Extract, Find, Generate, Identify, List, Measure, Organize, Parse, Pick, Predict, Provide, Rank, Recommend, Return, Retrieve, Rewrite, Select, Show, Sort, Summarize, Translate, Write.

## 3. Specify Output Format
- Be explicit about desired format: length (paragraph count, word count, tweet-length), structure (JSON, XML, bullet list, table), and content requirements.
- For data extraction/classification tasks, request JSON output — it forces structure and reduces hallucinations.
- Benefits of JSON output: consistent style, focused on requested data, less hallucination, relationship-aware, typed data, sortable.

## 4. Use Positive Instructions over Constraints
- Instructions directly communicate the desired outcome.
- Constraints leave the model guessing about what is allowed.
- Multiple constraints can clash with each other.
- Reserve constraints for safety-critical or strict format requirements.

## 5. Add Context and Role
- System prompt: Define the model's fundamental capabilities and overarching purpose.
- Role prompt: Frame the model's output style, voice, and expertise. "I want you to act as a travel guide."
- Contextual prompt: Provide task-specific background information. "Context: You are writing for a blog about retro 80's arcade video games."
- These three can be combined for maximum effect.

## 6. Break Complex Tasks into Steps
- Use Chain of Thought: add "Let's think step by step" to trigger intermediate reasoning.
- Use Step-back prompting: first ask a general question to activate background knowledge, then use that answer as context for the specific task.
- Combine CoT with few-shot: show an example of step-by-step reasoning before asking the new question.

## 7. Use Variables for Reusable Prompts
- Replace hardcoded values with placeholders: {city}, {product_name}, {language}.
- Makes prompts reusable and easier to maintain in applications.

## 8. Experiment with Input Format
- The same prompt goal can be phrased as a question, a statement, or an instruction — each produces different output.
- Question: "What was the Sega Dreamcast and why was it so revolutionary?"
- Statement: "The Sega Dreamcast was a sixth-generation video game console released by Sega in 1999. It..."
- Instruction: "Write a single paragraph that describes the Sega Dreamcast console and explains why it was so revolutionary."

## 9. Control Token Length
- Set max token limits in configuration to prevent over-generation.
- Or specify length in the prompt: "Explain quantum physics in a tweet length message."
- Note: reducing output length in config does NOT make output more concise — it just truncates. Engineer the prompt to match.

## 10. Use Schemas for Structured Input
- Provide a JSON Schema to define expected input structure and data types.
- Gives the model a clear blueprint of data to expect, focusing attention on relevant fields.
- Helps establish relationships between data and reduces misinterpretation.

---

# Technique Selection Guide

## When to Use Each Technique

| Task Complexity | Technique | When to Use | Temperature |
|---|---|---|---|
| Simple, well-defined | Zero-shot | Straightforward questions, simple classification, basic generation where the model's training data is sufficient | Low (0.1-0.2) |
| Pattern-dependent | One-shot / Few-shot | When a specific output structure is needed; when zero-shot produces wrong format or style; classification tasks; data extraction to JSON | Low (0.1-0.2) |
| Identity/expertise needed | Role prompting | When domain expertise would improve quality (e.g., "Act as a doctor", "Act as a travel guide") | Varies by task |
| Needs background | System / Contextual | When the model needs overarching behavior rules or task-specific background information | Varies by task |
| Requires reasoning | Chain of Thought (CoT) | Math problems, logical reasoning, multi-step analysis, any task that can be "talked through" | 0 (greedy decoding) |
| Requires deeper background | Step-back prompting | Creative tasks that need foundational knowledge first; when direct prompting gives generic results | Medium-High for step-back, then varies |
| Needs high confidence | Self-consistency | Critical decisions, classification of ambiguous inputs; run same CoT prompt multiple times at high temperature and take majority vote | High (for diversity) |
| Complex exploration | Tree of Thoughts (ToT) | Tasks requiring exploring multiple reasoning paths simultaneously; complex problem-solving | Varies |
| Needs external data | ReAct | Tasks requiring real-world information retrieval; multi-step research; agent-based workflows | Low (0.1) |
| Prompt optimization | Automatic Prompt Engineering (APE) | Generating prompt variants for chatbots; optimizing prompt phrasing systematically | High (for variant generation) |

## Decision Flowchart

1. Is the task straightforward with a clear answer? → Zero-shot
2. Does the output need a specific format/pattern? → Few-shot (add examples)
3. Does it need domain expertise? → Add Role prompting
4. Does it require multi-step reasoning? → Add Chain of Thought
5. Is the direct answer too generic/shallow? → Use Step-back prompting first
6. Is high accuracy critical on ambiguous input? → Use Self-consistency (multiple CoT runs + majority vote)
7. Does it need real-time external data? → Use ReAct
8. Does it require exploring multiple solution paths simultaneously? → Use Tree of Thoughts (ToT)
9. Do you need to optimize the prompt phrasing itself? → Use APE (generate variants at high temperature, evaluate, select best)

---

# Code Prompting Best Practices

> PromptLens operates within Claude Code — code-related prompts are the primary use case.

## Writing Code Prompts
- Specify the programming language explicitly
- Describe the task goal, not just the desired output
- Include constraints: error handling, edge cases, target environment
- Set low temperature (0.1) and generous token limit for code generation

## Code Explanation Prompts
- Provide the full code block in a fenced code block with language tag
- Ask for specific depth: high-level overview vs. line-by-line explanation

## Code Translation Prompts
- State source language → target language clearly
- Include the original code in a fenced code block
- Mention any target-language-specific conventions to follow
- Always review and test translated output — LLMs cannot reason about runtime behavior

## Code Debugging & Review Prompts
- Include both the code AND the error message (traceback, stack trace)
- Ask for explanation of the bug, not just the fix
- Request code improvement suggestions alongside the fix

## General Code Prompting Rules
- LLMs reproduce training data patterns — always read and test generated code before use
- Code prompts benefit from the same best practices: examples, action verbs, output format specification

---

# Output Configuration Tips

## Temperature
| Use Case | Temperature | Rationale |
|---|---|---|
| Factual Q&A, math, classification | 0 | Deterministic; always picks highest probability token |
| Structured data extraction | 0.1 | Near-deterministic with minimal variation |
| General balanced output | 0.2 | Coherent but slightly creative |
| Creative writing, brainstorming | 0.9 | High diversity and unexpected results |
| Chain of Thought reasoning | 0 | Reasoning requires greedy decoding for correct answers |
| Self-consistency (multiple runs) | High | Need diverse reasoning paths to vote on |

## Top-K
| Use Case | Top-K | Rationale |
|---|---|---|
| Deterministic / factual | 1 | Equivalent to greedy decoding |
| Less creative, more factual | 20 | Restricted token pool |
| Balanced | 30 | Default starting point |
| More creative | 40 | Wider token selection |

## Top-P (Nucleus Sampling)
| Use Case | Top-P | Rationale |
|---|---|---|
| Deterministic | 0 | Only most probable token considered |
| Balanced | 0.95 | Default starting point |
| Very creative | 0.99 | Nearly all tokens available |
| Greedy (all tokens available) | 1 | No filtering |

## Recommended Starting Points
| Goal | Temperature | Top-P | Top-K |
|---|---|---|---|
| Coherent, slightly creative | 0.2 | 0.95 | 30 |
| Highly creative | 0.9 | 0.99 | 40 |
| Factual, less creative | 0.1 | 0.9 | 20 |
| Single correct answer | 0 | — | — |

## Key Warnings
- Repetition loop bug: At both very low and very high temperatures, the model can get stuck generating the same word/phrase repeatedly. Fix by adjusting temperature and top-k/top-p together.
- Token limit truncation: Reducing output length in config does not make output concise — it just stops generation mid-stream. Engineer the prompt to request brevity.
- JSON truncation: When requesting JSON output, set a generous token limit. Truncated JSON is invalid. Use the json-repair library as a safety net.
- Interaction between settings: Temperature, top-K, and top-P all interact. At temperature=0, top-K and top-P become irrelevant. At top-K=1, temperature and top-P become irrelevant.

---

# Quick Reference: Best Practices Summary

1. Provide examples — the single most impactful improvement
2. Design with simplicity — use action verbs, remove unnecessary words
3. Be specific about the output — format, length, style, content
4. Use instructions over constraints — positive framing beats negative framing
5. Control max token length — via config and/or prompt wording
6. Use variables in prompts — for reusability and maintainability
7. Experiment with input formats — question vs. statement vs. instruction
8. Mix up classes in few-shot classification — prevent order overfitting
9. Adapt to model updates — always re-test and re-tune prompts when switching between model versions or providers
10. Experiment with output formats — JSON for structured tasks, reduce hallucination
11. Use JSON repair tools — handle truncated JSON from token limits
12. Use schemas — structure both input and output for precision
13. CoT best practices — temperature=0, answer after reasoning, extract answer separately
14. Document prompt attempts — track name, goal, model, settings, prompt, output, and result quality
15. Collaborate — different prompt engineers produce different effective variants
