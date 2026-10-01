---
name: repo-map
description: Build an incremental symbol map to orient in an unfamiliar codebase. Use for layout or definition lookup and after source/branch drift; map symbols are heuristic leads.
---

# Repo Map

Run the absolute path to `scripts/repomap.py` from the target repository.

| Need | Command suffix |
|---|---|
| Build/update | `build` |
| Detect source drift | `status` |
| Find definitions | `find Symbol` |
| Outline selected files | `outline src/file.ts` |
| Inspect a subdirectory | `show src/auth/` |

The map lives at `.codemap/MAP.md`; unchanged files reuse a cache keyed by size, mtime and ctime. Source symlinks and credential paths are excluded. Changed metadata invalidates older cache keys automatically.

The multi-language scanner uses lightweight patterns, not compiler/LSP semantic resolution. Verify definitions against current source and locate callers before changing behavior. A map is useful for missing orientation; do not rebuild/read it for a known one-line task.

Use `find`, `outline` and `show` to avoid reading the entire map. Read again when source changed or earlier evidence is missing. For an exact Python function body, use the core toolkit's AST-based `read --symbol`.

Keep reviewed architecture/build commands in `.codemap/NOTES.md`; start from `templates/NOTES.md` and keep it concise. Preserve existing ignore rules and share knowledge deliberately. Cache/log/memory state should stay local by default.

Without Python, use `git ls-files` for a bounded layout and `rg -n -w Symbol` for locations.
