---
name: bulk-edit
description: Make the same mechanical change across many files (API rename, import path move, deprecated call swap, config key change) with one scripted, previewed operation instead of reading and editing each file. Use when a change repeats in more than ~3 places.
---

# Bulk Edit

Opening 40 files to change the same line costs about 40 reads and 40 edits. A scripted change costs one preview, one apply and one verify. The result is the same, often more consistent, for a fraction of the tokens.

## Workflow
1. **Scope.** Count the sites: `rg -c "oldName\(" -g '*.ts' | sort -t: -k2 -nr | head`. Read **2–3 representative sites** to confirm the pattern, including an odd one.
2. **Pick the safest tool** (table below). Prefer tools that understand syntax over regex when renaming identifiers.
3. **Preview (dry run).** Check the counts and sample lines. If anything looks wrong, tighten the pattern: `--word`, `--glob`, `--path`.
4. **Apply**, then **verify**:
   - `git diff --stat` shows the expected files and counts.
   - `rg "oldName"` finds no leftovers.
   - Typecheck or build, then run the affected tests (`test-impact`, `quiet-run`).
   - Skim `git diff` for 1–2 files only, not the whole diff.
5. For special cases the script can't handle, fix those few sites by hand.

## Tools
| Change | Best tool |
|---|---|
| Rename a symbol (scope-aware) | IDE or LSP rename, `gofmt -r 'a -> b'`, `ast-grep run -p 'old($A)' -r 'new($A)' -l ts -U`, `jscodeshift`, `ts-morph`, OpenRewrite |
| Text or regex pattern across files | `python3 scripts/bulk_replace.py PATTERN REPLACEMENT [--glob '*.py'] [--path src/] [--word] [--fixed]` (dry run), then add `--apply` |
| Lint-fixable patterns | `eslint --fix`, `ruff check --fix`, `cargo clippy --fix`, `go fix`, `dotnet format`, `rubocop -a` |
| Import or module path moves | `bulk_replace.py "from old\.pkg" "from new.pkg" --glob '*.py'` |

## bulk_replace.py notes
- It's a dry run by default: it prints the number of replacements per file and a few `-`/`+` sample lines, and writes nothing.
- It uses Python regex. Groups work in the replacement (`\1`, `\g<name>`). `--fixed` makes the pattern literal, `-i` ignores case, and `--multiline` lets `.` span lines.
- It respects `.gitignore` and skips lockfiles, minified, vendored and binary files. It refuses more than 500 files unless you pass `--max-files`.

## Pitfalls
- Regex doesn't know scope. Renaming `engine` in `func (engine *Engine)` without updating its uses in the body breaks the code. Use a syntax-aware tool, or include the uses in the pattern.
- Watch for strings, comments, docs and snapshots that contain the old name. Decide whether they should change.
- Check the working tree is clean first (`git status -sb`), so the change can be reverted in one step with `git checkout -- .`.
