---
name: token-budget
description: Estimate context size and keep local usage records separate from measured counts. Use when inspecting token overhead, comparing packets, or tracking reported input/output usage.
---

# Token Budget

Resolve `../token-saver/scripts/token_saver.py` and run the absolute path from the project.

```bash
python3 <toolkit> budget estimate docs/design.md --json
python3 <toolkit> budget compare before.txt after.txt --json
python3 <toolkit> budget record --label auth-fix --input-tokens 8200 --output-tokens 630 --cached-input-tokens 4000
python3 <toolkit> budget report --json
```

Use `estimate` for planning and `compare` for the size of two content artifacts. Estimates use UTF-8 bytes divided by four; language, code and tokenizers vary. A smaller packet is not proof of reduced total task cost or equal quality.

Supply `record` counts only from observed tool/provider usage. Input totals include the cached subset; cached input cannot exceed total input. Records are user-reported, not independently verified. Never estimate hidden reasoning or account balances.

Keep `reported_usage` and `estimated_context` separate. The local ledger at `.codemap/usage.jsonl` stores labels and numeric counts, no prompts or code. Writes use an exclusive lock; malformed records are counted without affecting valid totals.

For task comparisons, hold model/settings/goal constant, include retries and output, and assess acceptance criteria. Load the `token-saver` sibling dependency. Use `context-audit` when the question concerns instruction/MCP inventory.
