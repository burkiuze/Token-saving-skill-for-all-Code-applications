---
name: diff-review
description: Build bounded evidence from staged, working-tree or branch changes. Use to review a patch, assess changed callers, or inspect a large diff without losing its scope.
---

# Diff Review

Resolve `../token-saver/scripts/token_saver.py` from this skill directory and run its absolute path from the target repository.

```bash
python3 <toolkit> diff --budget 2500
python3 <toolkit> diff --staged --json
python3 <toolkit> diff --base main --path src/auth/ --budget 4000
```

Default scope is HEAD to the current working tree, including staged and unstaged tracked changes plus untracked text. `--staged` reads only the index. `--base` uses a verified merge-base and includes current working changes. Missing/invalid refs fail; no silent fallback chooses another base.

1. Confirm scope and omitted counts before interpreting the packet.
2. Read every omitted or truncated patch relevant to the review, increasing the budget or narrowing `--path`.
3. Read complete affected bodies and callers. A hunk alone rarely proves behavior.
4. Check invariants, input boundaries, error paths and required tests. Risk hints identify review topics; they do not diagnose vulnerabilities.
5. Report findings with a concrete trigger, consequence and `path:line`. Separate checked evidence from remaining uncertainty.

The tool disables external diff drivers and textconv filters. It skips credential/generated/binary paths and redacts common inline credentials. It is a bounded evidence helper, not an automated correctness verdict. Install its `token-saver` sibling dependency.
