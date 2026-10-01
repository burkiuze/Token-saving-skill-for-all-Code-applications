---
name: quiet-run
description: Run noisy tests/builds with bounded failure-focused output and retained local logs. Use when command output would flood context; keep exit codes and explicit timeouts.
---

# Quiet Run

Run the absolute path to `scripts/quiet_run.py` from the target project.

```bash
python3 <script> --lines 40 --timeout 120 -- python3 -m unittest discover -s tests
python3 <script> --lines 30 --warnings -- npm test
python3 <script> --shell "npm test && npm run build"
```

Pass executable and arguments after `--`. Shell syntax is accepted only through explicit `--shell`; on Windows use it for batch commands such as npm.cmd when needed.

Output, including the status line, is capped by `--lines`. Errors, traceback context and a tail are selected. The child exit code is preserved; timeouts return 124, interrupted runs 130, missing executables 127, capture failure 125. POSIX timeouts terminate the child process group; Windows uses taskkill for its process tree.

Each run keeps a unique local log and publishes `last.log`/`prev.log` atomically. Ten recent default run logs are retained. `--max-log-bytes` caps disk capture while draining output; `--max-read-bytes` bounds summary memory. Capping/omission is labelled. Inspect the retained log before rerunning just for output.

Common credential patterns are redacted when the core sibling is installed. Redaction is a best effort, not proof a log is safe to share. Never use a short success summary as evidence that unrelated verification happened.
