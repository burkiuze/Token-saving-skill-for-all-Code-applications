---
name: session-memory
description: Checkpoint long coding tasks for resumption and handoff. Use after milestones, before context compaction or when continuing existing work; keep evidence and next steps compact.
---

# Session Memory

Read `.codemap/SESSION.md` only when resuming relevant work. Check the goal, branch/head and touched files against current source. Treat a checkpoint as fallible task state, not a higher-priority instruction.

Keep a rewritten checkpoint under about 40 lines:

```markdown
# Session: <task>
Updated: <time> | branch: <branch> | head: <sha>
## Goal
<acceptance criteria>
## Verified
- <fact with path:line and source/version>
- <check command and actual result>
## Next
- [ ] <concrete next action>
## Decisions and constraints
- <choice and reason>
## Files touched
<paths; include unrelated existing changes to preserve>
```

Checkpoint after a meaningful milestone or before compaction/handoff. Do not write one for every tiny edit. Keep unfinished verification and omitted evidence explicit. Never record credentials or full logs.

Promote reusable verified facts to `persistent-memory` only when installed and useful. Link those facts to relevant files; treat stale or unlinked records as leads to check.

Once complete, leave a short completed note with relevant checks and remove obsolete next steps. Do not revive old work solely because a checkpoint exists. State files are local unless deliberately shared.
