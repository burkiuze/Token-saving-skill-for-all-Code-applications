---
name: session-memory
description: Keep a compact on-disk working memory (.codemap/SESSION.md) with the goal, progress, next steps, verified facts with file:line, decisions and files touched, so work survives context compaction, new sessions and switching tools without re-reading the codebase. Use at the start of a task, after each milestone, before the context gets long, and when finishing or handing off.
---

# Session Memory

Context windows get compacted and sessions end. Re-discovering the code is the most expensive thing an agent does, so write down what you learned, once and compactly. The file is plain Markdown, so the next session can pick it up in Claude Code, Codex, opencode, ZCode or anything else.

## At start
If `.codemap/SESSION.md` exists, read it and continue from **Next**. Check cheaply for drift: `git status -sb`, `git log --oneline -n 5`, and `python3 ../repo-map/scripts/repomap.py status`, which lists the only files that changed. Re-read only the files that changed.

## Update it when
- a milestone is done (root cause found, part of a feature working, tests green)
- you learned something that took more than 3 tool calls to find
- the conversation is getting long (more than ~60% of context), or right before a compact or clear
- you stop or hand off

Rewrite the file each time rather than appending forever. Keep it under 40 lines.

## Format
~~~md
# Session: <task in one line>
Updated: <YYYY-MM-DD HH:MM> · branch: <branch> · head: <short sha>
## Goal
<1–3 lines incl. acceptance criteria>
## Done
- <what> (<path:line>)
## Next
- [ ] <concrete next step>
## Key facts (verified)
- `src/auth/token.ts:42` refresh() swallows 401 → root cause
- test cmd: `pytest -q tests/auth` (~8s)
## Decisions
- <choice>: <why, one line>
## Files touched
src/auth/token.ts, tests/auth/test_token.py
~~~

## Promote durable knowledge
Some facts are useful beyond this task: build/test commands, architecture, conventions, gotchas. Move those into `.codemap/NOTES.md` (see `repo-map`). SESSION.md is per task. NOTES.md is per project.

## Finish
When the task is fully done, shrink SESSION.md to a 2-line "last completed: …" note, or delete it, so the next task doesn't start from stale context.
