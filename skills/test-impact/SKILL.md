---
name: test-impact
description: Find and run only the tests affected by your changes (naming conventions plus importers of the changed modules) and get a ready narrow command for pytest, Jest, Vitest, Mocha, Go, Maven, Gradle, .NET, RSpec and more. Much faster feedback and smaller logs; the full suite still runs once at the end. Use whenever you're about to run tests after an edit.
---

# Test Impact

Running the whole suite after every edit costs minutes and thousands of tokens of log. Run the tests that cover what you changed first. Run the full suite only once, before you finish.

## Command
The script is `scripts/affected_tests.py`, relative to this skill's folder.
```
python3 scripts/affected_tests.py                # working-tree changes (staged, unstaged, untracked)
python3 scripts/affected_tests.py --base main    # everything since branching from main
python3 scripts/affected_tests.py --files src/auth/token.ts
```
Sample output:
```
changed: 2 file(s): src/requests/auth.py src/requests/utils.py
tests (3):
  tests/test_lowlevel.py  (imports auth)
  tests/test_utils.py  (name ~ src/requests/utils.py)
run first:
  pytest -q -x --tb=short tests/test_lowlevel.py tests/test_utils.py
```
Run the suggested command through `quiet-run`, which prints only failures and the summary.

## How it maps changes to tests
- **Naming.** `foo.ts` → `foo.test.ts` / `foo.spec.ts` / `__tests__/foo.ts`. `foo.py` → `test_foo.py` / `foo_test.py`. `Foo.java` → `FooTest(s)/FooIT.java`. `foo.rb` → `foo_spec.rb`. `Foo.cs` → `FooTests.cs`.
- **Importers.** It finds test files that import the changed module. Generic names (`utils`, `index`) must appear with their folder, e.g. `requests.utils`.
- **Go** maps to the changed packages (`go test ./pkg/x`). A changed test file is always included.

## Loop
1. Edit, then run the affected tests. On failure: fix, then re-run the **same narrow set**.
2. Once green, widen to the package or module if the change was shared code or touched a public API.
3. Before saying done, run the full suite once (still through `quiet-run`).

## When it finds nothing
The mapping is heuristic. Examples: Express tests `require('..')`, and a Rust crate keeps its tests inline. When nothing is found, run the nearest package or module suite instead: `cargo test -p crate`, `go test ./dir/...`, `pytest tests/area`, `npx jest path/`. Save the working narrow command with `persistent-memory` (`--kind cmd`) so the next session doesn't have to work it out again.
