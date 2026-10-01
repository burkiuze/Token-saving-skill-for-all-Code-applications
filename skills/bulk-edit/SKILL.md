---
name: bulk-edit
description: Preview and apply repeated mechanical source edits across scoped files. Use for literal/regex changes; prefer syntax-aware rename when identifier scope matters.
---

# Bulk Edit

Run the absolute path to `scripts/bulk_replace.py` from the repository. Keep its core `token-saver` sibling installed.

```bash
python3 <script> oldName newName --fixed --word --glob '*.py' --path src/
python3 <script> oldName newName --fixed --word --glob '*.py' --path src/ --apply
```

1. Count sites and read representative normal/edge cases.
2. Prefer IDE/LSP rename or an appropriate codemod for scope-sensitive identifiers. Regex is text replacement, not a semantic refactor.
3. Preview first. Check counts/sample changes; tighten `--glob`, `--path` and pattern if needed.
4. Apply, then inspect the scoped diff and check expected leftovers. Run appropriate tests/typechecks.

The script respects Git's tracked/unignored inventory, skips generated/lock/binary/credential files and symlinks, refuses excessive file counts, detects changes during preparation and atomically replaces each file while preserving mode/newlines. The operation is per-file, not a transaction across the whole repository.

`--fixed` is literal replacement; otherwise use Python regex groups. `--multiline` allows spanning lines. Existing unrelated edits must be preserved. Never use a repository-wide reset/checkout to clean up your change.

Preview redacts common credential patterns. The pattern and replacement still come from the operator; avoid placing credentials in command arguments.
