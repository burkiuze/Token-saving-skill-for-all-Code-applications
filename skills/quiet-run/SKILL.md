---
name: quiet-run
description: Run tests, builds, linters, type-checkers, installs and other noisy commands with capped, failure-focused output while the full log goes to a file, so logs never flood the context. Use whenever you run a test suite, build, compiler, linter or package install, or any command that may print more than about 50 lines.
---

# Quiet Run

## Wrapper (recommended)
Use `python3 scripts/quiet_run.py -- <command...>`. The path is relative to this skill's folder.
- It prints one status line (exit code, duration, line count), then the error, failure and traceback lines with a little context, then the tail. That's about 60 lines at most (`--lines N`). Per-test "PASSED/ok" chatter and repeated lines are dropped.
- The full output is saved to `.codemap/logs/last.log` (the previous run goes to `prev.log`). If you need more, `rg -n "pattern" .codemap/logs/last.log`. Don't dump the whole log.
- It exits with the command's own exit code. For pipes or `&&`, use `--shell "cmd1 && cmd2"`. There's also `--timeout SEC`, and `--warnings` to surface warnings.

## Narrowest check first
| Stack | Narrow and quiet |
|---|---|
| pytest | `pytest -q -x --tb=short tests/test_x.py::test_name` |
| Jest / Vitest | `npx jest path -t "name" --silent` / `npx vitest run path -t "name" --reporter=dot` |
| Go | `go test ./pkg/... -run TestName` |
| Cargo | `cargo test -q name`, `cargo check --message-format short` |
| TypeScript | `npx tsc --noEmit --pretty false` |
| ESLint | `npx eslint --format unix path` |
| Maven / Gradle | `mvn -q -Dtest=Name test` / `gradle test --tests Name -q` |
| .NET | `dotnet test --filter Name -v q --nologo` |
| Installs | `npm ci --silent --no-audit --no-fund`, `pnpm i --silent`, `pip install -q -r requirements.txt` |
| git | `git status -sb`, `git diff --stat`, `git log --oneline -n 10`, `git --no-pager diff -- file` |

Run the full suite only as a final check, and still through the wrapper.

## Without Python
- bash: `cmd > /tmp/run.log 2>&1; echo "exit=$?"; grep -nE "error|fail|Error|FAIL|panic|Traceback|Exception" /tmp/run.log | head -n 30; tail -n 15 /tmp/run.log`
- PowerShell: `cmd *> run.log; "exit=$LASTEXITCODE"; Select-String run.log -Pattern 'error|fail|exception' | Select -First 30; Get-Content run.log -Tail 15`

## Rules
- Never stream an unbounded log into context. Don't use `-v`, `--verbose` or debug flags unless you're diagnosing, and filter the output even then.
- Don't re-run an unchanged command hoping for a different result. Change the code, the filter, or the verbosity of a single test first.
- Run dev servers and watchers in the background with output redirected to a log, and check them with `tail -n 20`.
