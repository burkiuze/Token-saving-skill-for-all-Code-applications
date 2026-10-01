---
name: context-pack
description: Rank local source snippets for a task within an explicit context size budget. Use when the relevant files are unknown or broad exploration would flood context.
---

# Context Pack

Resolve the sibling toolkit's absolute path: `../token-saver/scripts/token_saver.py` relative to this skill directory. Run it from the target repository.

```bash
python3 <toolkit> pack "refresh token expiration" --budget 2000
python3 <toolkit> pack "parseResponse" --path src/ --json --budget 2500
```

Use specific symbols, errors or domain terms. The script ranks lexical matches, filenames and configured priority paths, merges duplicate symbol evidence, and skips overlapping spans. Python AST spans include decorators and complete short implementations. Other languages provide line evidence, not semantic parsing.

Inspect the omitted counts. Narrow `--path` or the query when results are irrelevant. Increase the budget or use `read` when the implementation is incomplete. Read callers and required configuration before editing; this packet is discovery evidence.

Git-backed scans respect untracked ignore rules. Credential paths, binaries, large files, generated output and symlinks are excluded. Non-Git scans use conservative directory/exclusion filters, not a complete Git ignore parser. Common secret patterns are redacted as a best effort.

The complete serialized packet, including metadata, fits the chosen UTF-8 byte/4 heuristic budget. This is not an exact model-token cap. `--record` stores only estimated counts locally, never the code packet.

Read the sibling [configuration guide](../token-saver/references/configuration.md) when tuning retrieval. The `token-saver` skill is a required sibling dependency.
