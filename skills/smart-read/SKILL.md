---
name: smart-read
description: Locate source and read complete relevant spans with evidence. Use for symbol lookup, call tracing or large source files; avoid unrelated full-file dumps.
---

# Smart Read

Resolve `../token-saver/scripts/token_saver.py` from this skill directory and run its absolute path in the target repository.

1. Find the file and definition: `rg -n -w Symbol src/`, or `repo-map find Symbol` when installed.
2. Read the complete implementation before editing. A small file can be cheaper to read once than many fragments.
3. Check callers and imports that affect the behavior being changed. Follow one dependency at a time.

```bash
python3 <toolkit> read src/auth.py --symbol TokenService.refresh
python3 <toolkit> read src/auth.ts --start 120 --end 190 --budget 3000
```

Python symbol reads use AST boundaries including decorators and async bodies. Ambiguous names require a qualified class/function name. Other languages use explicit line ranges; `repo-map outline FILE` can help locate them.

A requested span that exceeds the budget fails clearly. Increase `--budget` or choose deliberate smaller ranges; never treat a truncated body as complete. The output includes source hash and original line numbers. Changed source or lost context warrants a fresh read.

Skip generated, vendored, minified, lock and build files unless they are the subject of the task. Read configuration/schema/fixtures when they determine behavior. The reader rejects credential files, symlinks, outside-project paths, binaries and oversized files; common inline credentials are redacted.

Without Python, use a bounded read tool or `sed -n '120,190p' FILE`, ensuring the complete function is visible. Install the `token-saver` sibling for the executable reader.
