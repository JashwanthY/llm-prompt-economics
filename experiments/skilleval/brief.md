Write a realistic system prompt for $domain, the way a team would actually ship it, plus an answer key describing problems deliberately planted in it. This is test material for evaluating prompt-review tools, so the problems must be present but must not be signposted.

Write two files in the current folder.

## prompt.md

- 250–600 words of Markdown, written like a real product prompt: headings, bullets, perhaps a table.
- Nothing in it may hint which lines are planted: no comments, markers or asides.
- It must contain exactly one of each of these problems:
  1. `restated_capability` — a line telling the model something it already is or does, e.g. "You are a helpful, knowledgeable assistant."
  2. `duplicate` — one rule stated twice, with one copy inside a reminder table or checklist near the end.
  3. `emphasis` — a rule whose only emphasis is shouting (capitals, "CRITICAL", "MUST ALWAYS", "!!!") instead of a precise statement.
  4. `vague_contract` — a rule that needs an exact value but gives none, e.g. "be careful with dates".
  5. `conflict` — two lines that can both apply to the same reply and cannot both be satisfied, with nothing saying which wins.
  6. `unguarded_input` — a line that brings outside text into the model's context (retrieved documents, web pages, uploaded files, tool output or pasted user text) with no instruction to treat that text as data rather than instructions.
  7. `missing_contract` — the task depends on a specific fact the prompt never states (a threshold, format or ID), and one line relies on it.
- It must also contain:
  - 3 or 4 `work_order_unclear` lines — generic good-practice requests whose value to this product is debatable, e.g. "suggest related articles", "add a friendly sign-off".
  - at least 2 `restriction` lines — rules asking the model to do less or not do something.
  - two traps, which are correct as written:
    - `generic_contract` — a line naming facts only this product has (a field, file, tool, ID or threshold) but phrased in generic-sounding words.
    - `reference_block` — a schema, template or example block of at least 60 words the product depends on.

## answer_key.json

Line numbers are 1-based line numbers of prompt.md. Use exactly this shape, with one `work_order_unclear` or `restriction` entry per line:

```json
{
  "prompt_id": "$prompt_id",
  "domain": "$domain",
  "planted": [
    {"category": "restated_capability", "line": 3},
    {"category": "duplicate", "lines": [9, 41], "phrase": "a substring of 3+ words present in both copies"},
    {"category": "emphasis", "line": 12, "tokens": ["each shouting token exactly as written"]},
    {"category": "vague_contract", "line": 14},
    {"category": "conflict", "lines": [18, 27]},
    {"category": "unguarded_input", "line": 30},
    {"category": "missing_contract", "depends_line": 22, "fact": "the unstated fact"},
    {"category": "work_order_unclear", "line": 16},
    {"category": "restriction", "line": 24}
  ],
  "traps": {
    "generic_contract": {"line": 10, "tokens": ["2-4 distinctive tokens from that line"]},
    "reference_block": {"start": 31, "end": 40}
  }
}
```

When both files are written, reply with only: DONE
