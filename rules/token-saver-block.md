<!-- token-saver:start (managed by Token Saver Skills: edits inside this block are overwritten on reinstall) -->
## Token discipline (always on)
Same quality, far fewer tokens. Details are in the skills in `{{SKILLS_DIR}}`.
1. **Size the task first** (`task-triage`): XS/S gets search → edit → one check. M/L gets a map, a short plan and checkpoints.
2. **Start from memory, not exploration.** Read `.codemap/SESSION.md` if it exists. Run `{{PY}} {{SKILLS_DIR}}/persistent-memory/scripts/memory.py brief`, then `recall "<topic>"`. Get the layout from `{{PY}} {{SKILLS_DIR}}/repo-map/scripts/repomap.py build` (incremental), then use `find NAME`, `show DIR/` or `outline FILE`.
3. **Search, then read ranges.** Search before you read. Read line ranges, not whole files. Never re-read a file already in context unless it changed (`repomap.py status`, `git diff`). Skip lockfiles, vendored, generated, minified and build output.
4. **Edit minimally.** Don't re-read a file to verify an edit, and don't paste code back into chat. For the same change in more than 3 places, use `bulk-edit` instead of editing file by file.
5. **Verify narrowly.** Run the affected tests first (`{{PY}} {{SKILLS_DIR}}/test-impact/scripts/affected_tests.py`), with capped output (`{{PY}} {{SKILLS_DIR}}/quiet-run/scripts/quiet_run.py -- <cmd>`). Run the full suite once before you finish.
6. **Look up APIs precisely** (`api-lookup`) instead of guessing or reading dependency source.
7. **Parallelize.** Send independent reads and searches together, and delegate broad exploration to sub-agents when available.
8. **Remember.** Save progress to `.codemap/SESSION.md`. Save reusable verified facts (commands, gotchas, fixes, preferences) with `memory.py add "..." --kind ...`.
9. **Be brief.** Answer first, cite `path:line`, and skip filler and recaps.

Quality comes first. Read any function you change in full, check its call sites, and verify with tests or a typecheck before you say it's done.
<!-- token-saver:end -->
