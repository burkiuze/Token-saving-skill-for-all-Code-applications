---
name: smart-read
description: Locate-then-read protocol for reading exactly the code you need (search, then outline, then line-range reads) instead of opening whole files. Use whenever you are about to open, cat or view a source file, look for where something is implemented, trace a bug through calls, or review a diff.
---

# Smart Read

Read like a debugger, not like a novel. The order is **find, then outline, then read the span**.

## 1. Find (no file opened yet)
- Definition: `python3 ../repo-map/scripts/repomap.py find Name`, or `rg -n "(def|function|class|func|fn|interface|type|struct) +Name\b"`
- Usages: `rg -n -w Name -g '!**/*test*' | head -n 40`. Narrow with `--type ts` or `-g 'src/**'`.
- An error or text string: `rg -n -F "exact message"`
- If you're unsure how widespread something is, count first: `rg -c pattern | sort -t: -k2 -nr | head`
- `rg` already skips git-ignored files. Add `-g '!*.min.*' -g '!**/dist/**'` if needed.

## 2. Outline (still cheap)
`python3 ../repo-map/scripts/repomap.py outline path/file` lists every symbol with its line number.
Fallback: `rg -n "^\s*(export |pub |public |private |static |async )*(def|class|function|func|fn|interface|type|struct|enum|impl) " path/file`

## 3. Read the span
- Use your read tool's offset/limit, or `sed -n '120,180p' file`. Take the symbol plus about 10–20 lines of context, and extend only if the code continues.
- Read the file header or imports (first ~30 lines) only when you need types or dependencies.
- Read the whole file only when it's small (under about 150 lines), when you'll restructure it, or when three slices still miss context.

## Tracing
Go one hop at a time. Read the function, `rg` the one callee you need, then read that span. Don't pre-load a call graph "just in case".

## Reviewing changes
Start with `git diff --stat`, then `git diff -U3 -- <file>` one file at a time. Don't dump a diff of more than about 300 lines at once. For a PR, list the files first and read the risky ones.

## Never read (unless the task is about them)
- Lockfiles (package-lock, yarn.lock, pnpm-lock, Cargo.lock, poetry.lock, go.sum)
- `node_modules`, `vendor`, `dist`, `build`, `target`, `.next`, coverage
- Minified or bundled files, source maps, snapshots
- Generated code (protobuf, OpenAPI clients)

For big data files (JSON, CSV, logs), sample instead: `head -n 20`, `wc -l`, `jq 'keys'`.

## Memory hygiene
Keep a running list of what you've read: `path:lines → key fact`, in your working notes or `.codemap/SESSION.md`. Check that list before reading anything. Re-reading costs the full price again.
