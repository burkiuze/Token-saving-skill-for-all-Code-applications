---
name: token-saver
description: Core token-efficiency protocol for any coding task in a repository - coding, debugging, refactoring, reviewing, or answering questions about code. Use at the start of every such task and whenever you are about to explore a codebase, open files, run tests/builds, or write a long reply. Cuts token use sharply without lowering quality.
---

# Token Saver

Goal: the same or a better result with far fewer tokens. The savings come from **not reading what doesn't matter and never doing the same work twice**. They never come from skipping code that does matter.

Sibling skills are in the same skills folder: `task-triage`, `repo-map`, `smart-read`, `quiet-run`, `test-impact`, `session-memory`, `persistent-memory`, `bulk-edit`, `api-lookup` and `context-audit`. Their scripts live at `../<skill>/scripts/` relative to this file.

## The loop (every task)
0. **Size it.** XS/S tasks skip the ceremony, M/L tasks get a plan. See `task-triage`.
1. **Resume.** If `.codemap/SESSION.md` or `.codemap/NOTES.md` exist, read them first (they are short). Run `python3 ../persistent-memory/scripts/memory.py brief`, then `recall "<topic>"`. Trust verified memories. Re-check only the ones flagged `!! verify`.
2. **Orient.** Get the layout from the code map (`repo-map`), not by crawling the tree: `python3 ../repo-map/scripts/repomap.py build` re-parses only the files that changed.
3. **Locate.** Search before you read (`rg -n`, `repomap.py find NAME`). Know the file *and the line* before you open anything. For library APIs, use `api-lookup`.
4. **Read narrowly.** Read the span you need (the function or class plus about 20 lines), not the whole file. See `smart-read`.
5. **Edit minimally.** Use targeted edits or patches. Never rewrite a whole file to change a few lines. For the same change in many files, use `bulk-edit`.
6. **Verify quietly.** Run the affected tests first (`test-impact`) with capped output (`quiet-run`). Run the full suite once at the end.
7. **Checkpoint and remember.** Update `.codemap/SESSION.md` (`session-memory`). Save reusable, verified facts with `memory.py add` (`persistent-memory`).

## Hard rules
- **Never re-read** a file that is already in context unless it has changed since. If you edited it, you already know the change. If someone else changed it, use `git diff -- <file>`.
- **No verification re-reads** after an edit. The edit tool reports it when an edit fails.
- **No blind crawling.** Don't `cat` many files, don't run `ls -R` or `tree` on the whole repo, and don't open lockfiles, vendored, generated, minified or build-output files.
- **Batch.** Send independent searches and reads in parallel in one turn, not one by one.
- **Cap every command's output.** Use `| head -n 60`, `| tail -n 40`, `-q`, `--silent` or `--no-color`. Send long output to a file and grep it.
- **Delegate wide exploration** if your tool has sub-agents (Claude Code Explore/Task, and so on). Ask for conclusions with `path:line` refs, not file dumps.
- **Stop exploring once you can act.** You know enough when you can name the lines to change and how you will verify the change.
- **Don't repeat a failing action unchanged.** Change the input, the filter or the approach first.

## Output discipline
- Answer first, briefly. No preamble, no restating the task, no closing recap of what the diff already shows.
- Don't paste back code you just wrote or read. Reference it as `path:line` and show only the snippet the user actually needs.
- Plans are a few bullets, not essays. Explanations are as long as the question needs, and no longer.

## Quality guardrails (never trade these for tokens)
- Never guess about code you haven't seen. If the change depends on that code, read it.
- Before you modify a function, read its full body. Before you change a signature or its behavior, `rg` its call sites.
- If a file you will edit is small (under about 150 lines), read it whole once. That is cheaper than many slices.
- Verify with the relevant test, typecheck or build before you say the work is done.
- If a narrow approach fails twice, widen on purpose (read the whole module, check NOTES/map) rather than flailing.

## Rough costs (1 line of code ≈ 10–12 tokens)
| Action | ~Tokens |
|---|---|
| `rg -n` with 20 hits | 300–1,000 |
| 60-line span | ~700 |
| 1,000-line file | 10,000–15,000 |
| Unfiltered test/build log | 5,000–50,000+ |
| Code map of a 150-file repo (read once, then reused) | 3,000–4,000 |
