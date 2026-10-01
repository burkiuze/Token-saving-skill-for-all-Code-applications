# Toolkit workflows

Resolve the toolkit from the actual installed `token-saver/SKILL.md` directory.
Run its absolute path from the project; do not execute commands from the skill source checkout by accident.

## Discovery and complete reads

```bash
python3 <toolkit> pack "refresh token expiration" --path src/ --budget 2000
python3 <toolkit> read src/auth.py --symbol TokenService.refresh --budget 3000
python3 <toolkit> read src/auth.ts --start 80 --end 160 --budget 3000
```

Use one specific query rather than a whole pasted conversation. Packet ranking is lexical;
it does not embed code, call a model or compute a compiler call graph. The packet preserves
source paths, line spans and SHA-256 hashes. Its full serialized output fits a UTF-8-byte/4
heuristic budget. Very small budgets fail if even packet metadata cannot fit.

Python symbols use AST spans, including decorators and nested qualified names. Other
languages use complete explicit ranges. Requested reads fail rather than silently
truncate a function. Query packets can still contain partial discovery spans; check labels.

## Review evidence

```bash
python3 <toolkit> diff --staged --json --budget 3000
python3 <toolkit> diff --base main --path src/ --budget 5000
```

Working-tree mode combines tracked index/working changes relative to HEAD and new
untracked text. Branch mode compares to the merge-base and includes working changes.
Deleted source is read through the Git patch. Rename detection is disabled so additions
and deletions remain explicit. No external diff driver or textconv command executes.

Inspect omitted/truncated paths before issuing a review verdict. Risk hints are topics to
check, not findings. Binary, credential, generated and oversized content may be excluded.

## Usage records

```bash
python3 <toolkit> pack "auth refresh" --record
python3 <toolkit> budget record --label task-42 --input-tokens 12000 --output-tokens 750 --cached-input-tokens 8000
python3 <toolkit> budget report --json
```

Packet records are estimates. Manually supplied counts are reported usage and remain in
a separate total. Cached input is a subset of input, not an additional count. Logs store
no packet/prompt contents. No provider keys, telemetry or network requests are used.

To measure task savings, compare matched tasks with the same model/settings and success
criteria, count retries/subagents/output, and retain observed usage. Byte reduction alone
only measures content size.

## Failure recovery

- No matches: use the exact identifier/error or narrow to a directory.
- Packet omits the needed body: increase the budget or use `read`.
- Invalid base: fetch/identify the intended ref and rerun; never substitute silently.
- A ledger lock remains after a killed process: verify no writer is active before removing
  only `.codemap/usage.lock`. Locks are never automatically stolen based on elapsed time.
- Secret masking is heuristic. Review any artifact before sharing it; the tools do not
  guarantee a complete secret scan.
