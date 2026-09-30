---
name: persistent-memory
description: Long-term, searchable memory across sessions and tools (project .codemap/memory.jsonl and global ~/.agents/memory.jsonl). Recall only the few relevant facts instead of re-discovering them, and flag memories whose files changed. Use at task start (brief/recall), after solving something non-obvious, and when the user states a preference.
---

# Persistent Memory

The expensive thing isn't reading a fact. It's re-discovering it every session. Save each hard-won, verified fact once, as 1–2 sentences, and later pull back only the entries that match the task. That keeps memory cheap even with hundreds of entries.

The script is `scripts/memory.py` (Python 3.8+, stdlib), relative to this skill's folder. Use `python` on Windows.

## When to use it
| Moment | Command |
|---|---|
| Session start (≈ 300 tokens) | `python3 scripts/memory.py brief` |
| Before a task in an area | `python3 scripts/memory.py recall "auth token refresh"` (top 5 matches) |
| Solved something non-obvious | `python3 scripts/memory.py add "..." --kind fix --tags jest,esm --files jest.config.js` |
| User states a preference | `python3 scripts/memory.py add "Prefers pnpm, answers in Turkish" --kind pref --global` |
| A memory turned out wrong | `update ID "corrected text"` or `forget ID` |
| Housekeeping | `stale` (entries whose files changed), `list --kind gotcha`, `export` (Markdown) |

## Kinds
- `pref`: how the user likes things done. Use `--global` when it applies to every project.
- `gotcha`: a non-obvious trap ("tests need `TZ=UTC`", "never edit generated/api.ts").
- `cmd`: an exact working command ("single test: `pnpm vitest run path -t name`").
- `fix`: error signature → cause → fix. Include the error text so `recall` finds it next time.
- `decision`: what was chosen and why, in one line.
- `api`: a library or version quirk you had to look up.
- `fact`: architecture or location facts ("payments live in `services/billing/`").
- `todo`: follow-ups for later sessions.

## What makes a good memory
- It's **verified** (you saw it work, or saw it in code) and **reusable** (it'll matter again).
- It's atomic and specific: names, paths, commands, the exact error text. "Build was tricky" is useless. Write something like "`npm run build` fails on Node 18 with `ERR_REQUIRE_ESM`; use Node 20 (.nvmrc)".
- Link it to files with `--files`. When those files change, `recall` and `brief` mark the entry `!! verify`, so a stale memory never silently misleads you. Re-check it before relying on it.
- Near-duplicates update the existing entry instead of piling up.
- Never store secrets, tokens or personal data.

## Relation to other files
- `SESSION.md` (session-memory) holds the current task's scratchpad. `memory.jsonl` holds atomic facts that outlive the task.
- `NOTES.md` (repo-map) is a curated overview for humans and agents. If something in memory gets consulted over and over, promote it to NOTES.md.
- `.codemap/memory.jsonl` is committed by default, so teammates' agents benefit too. Remove the `!memory.jsonl` line from `.codemap/.gitignore` to keep it private.

## Without Python
`rg -i "keyword" .codemap/memory.jsonl ~/.agents/memory.jsonl`. Add an entry by appending one JSON line: `{"id":"p99","kind":"gotcha","text":"...","date":"YYYY-MM-DD"}`.
