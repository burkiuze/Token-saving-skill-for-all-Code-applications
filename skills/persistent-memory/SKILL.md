---
name: persistent-memory
description: Store and retrieve concise verified coding facts across sessions. Use for reusable commands, fixes or decisions; check linked source hashes before trusting recalled facts.
---

# Persistent Memory

Run the absolute path to `scripts/memory.py` from the target project. The core `token-saver` sibling supplies shared I/O guards.

```bash
python3 <script> add "Auth tests: pytest -q tests/test_auth.py" --kind cmd --files tests/test_auth.py
python3 <script> recall "auth test" -n 5
python3 <script> brief --chars 1600
python3 <script> stale
python3 <script> update p1 "Reverified command: pytest -q tests/test_auth.py"
python3 <script> forget p1
```

Save atomic, verified and reusable facts. Supported kinds are fact, fix, decision, pref, gotcha, cmd, api and todo. Use global scope only for facts that intentionally apply across projects; `--global` writes `~/.agents/memory.jsonl` or `AGENT_MEMORY_HOME`.

Recall by topic rather than loading all records. Linked files are hashed and changed/missing sources produce `!! verify`; recheck before relying on them. Unlinked memories have no source-drift check. Near-duplicate facts update an existing entry.

Project memory is local by default for new `.codemap` folders. Existing ignore rules are preserved. To share selected knowledge, deliberately edit those rules or promote a reviewed fact to project documentation. Never label all memories automatically safe to commit.

Writes use an exclusive lock and atomic replacement. Detected credential text and outside-project/credential file links are rejected. Invalid stored records can be skipped on reads, but writes refuse to discard corruption silently.

Use SESSION.md for task progress and NOTES.md for a curated overview. Keep personal/credential data out of all three.
