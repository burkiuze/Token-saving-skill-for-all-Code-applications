<!-- token-saver:start (managed by Token Saver Skills: edits inside this block are overwritten on reinstall) -->
## Token discipline (always on)
Same quality, far fewer tokens. Full detail is in the skills `token-saver`, `repo-map`, `smart-read`, `quiet-run` and `session-memory` (in `{{SKILLS_DIR}}`).
1. **Start.** Read `.codemap/SESSION.md` and `.codemap/NOTES.md` if they exist. Get the layout from the code map, not a tree crawl: `{{PY}} {{SKILLS_DIR}}/repo-map/scripts/repomap.py build` (incremental), then `find NAME`, `show DIR/` or `outline FILE`.
2. **Search, then read ranges.** Search before you read. Read line ranges, not whole files. Never re-read a file already in context unless it changed (check with `repomap.py status` or `git diff`).
3. **Skip noise.** Never open lockfiles, vendored, generated, minified or build-output files.
4. **Edit minimally.** Don't re-read a file to verify an edit, and don't paste code back into chat.
5. **Quiet checks.** Run tests, builds and installs at the narrowest scope with capped output: `{{PY}} {{SKILLS_DIR}}/quiet-run/scripts/quiet_run.py -- <cmd>`.
6. **Parallelize.** Send independent reads and searches together. Delegate broad exploration to sub-agents when your tool has them.
7. **Be brief.** Answer first, cite `path:line`, and skip filler and recaps.
8. **Checkpoint.** Save progress to `.codemap/SESSION.md` at milestones and before the context gets long. Durable facts go in `.codemap/NOTES.md`.

Quality comes first. Read any function you change in full, check its call sites, and verify with tests or a typecheck before you say it's done.
<!-- token-saver:end -->
