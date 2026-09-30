---
name: repo-map
description: Build and use a persistent, incrementally updated code map (.codemap/MAP.md lists every file with its classes, functions and line numbers) plus durable project notes (.codemap/NOTES.md), so the codebase is never re-explored from scratch. Use when starting work in a repo, when you need to know where something lives, or after a pull or branch switch.
---

# Repo Map

A compact index replaces exploration. The first build takes seconds. After that, only files whose size or mtime changed are re-parsed.

## Commands
The script is `scripts/repomap.py` (Python 3.8+, standard library only). Run it from anywhere inside the repo.

| Need | Command |
|---|---|
| Build or refresh (incremental) | `python3 scripts/repomap.py build` |
| What changed since I last looked? | `python3 scripts/repomap.py status` |
| Where is X defined? | `python3 scripts/repomap.py find X` (regex, case-insensitive) |
| Outline a file without reading it | `python3 scripts/repomap.py outline path/to/file` |
| Map of one directory only | `python3 scripts/repomap.py show src/api/` |

(Paths are relative to this skill's folder. Use `python` on Windows if `python3` is missing.)

It writes `.codemap/MAP.md` and `cache.json`. Both are git-ignored automatically through `.codemap/.gitignore`. Only `NOTES.md` is meant to be committed.

## Reading the map
- `build` prints one line with the map's size. If it's small (under about 300 lines or 5k tokens), read MAP.md once. Otherwise read only the **Directory index** at the top, then use `show DIR/` or `find NAME`.
- Here is an example line: `server.ts 212L: createServer:12 · class Router:40{get:52 post:70} · app.{use:90}`. The numbers are the lines where each symbol is defined. `{...}` holds members, and `name:10,20` means overloads. Jump straight to a symbol with a ranged read.
- Test files are collapsed to a symbol count. Run `outline` on one when you need it.
- Don't re-read MAP.md in the same session. Use `status` to see which files changed. Those are the only ones that need re-reading.

## NOTES.md: durable knowledge (commit it)
`.codemap/NOTES.md` holds what a map can't. That is the purpose, the architecture in 5–15 lines, entry points, the exact build/test/lint commands, conventions and gotchas. Create it after your first real dive into a repo, starting from `templates/NOTES.md`. Update it whenever you learn something that took effort to find. Keep it under about 80 lines, with facts, not prose. Any future session, in any tool, starts from it instead of re-exploring.

## Without Python
- Layout: `git ls-files | sed 's|/[^/]*$||' | sort | uniq -c | sort -rn | head -40`
- Symbols: `rg -n "^\s*(export\s+)?(pub\s+)?(async\s+)?(def|class|function|func|fn|interface|type|struct|enum|trait|impl)\s" -g '!*.min.*' | head -100`
- Locate: `rg -n -w Name`

Put what you learn into NOTES.md so the next session doesn't pay for it again.
