---
name: test-impact
description: Suggest focused tests from changed filenames and imports. Use after code edits for quick feedback; selection is heuristic and broader required checks still apply.
---

# Test Impact

Run the absolute path to `scripts/affected_tests.py` from the target repository.

```bash
python3 <script> --files src/auth/token.ts
python3 <script> --base main --json
python3 <script>
```

The script combines naming conventions and direct import clues. It includes changed tests and Go packages. Recommendations cover pytest, Jest/Vitest/Mocha, Go, Maven/Gradle, .NET, Ruby, Elixir, Dart, PHP and Rust. Verify the project's actual runner and commands before executing a suggestion.

1. Run mapped tests first through `quiet-run` when installed.
2. If mapping finds nothing, run the nearest package/module suite; absence of a hit does not mean absence of impact.
3. Broaden for public interfaces, shared code, configuration, dependencies, schemas and dynamic imports. Naming/import heuristics do not cover all indirect dependencies.
4. Run all checks mandated by the project and change scope before claiming completion. A full suite is appropriate when those require it; it is not mandatory for every trivial edit.

`--base` verifies the reference and uses the merge-base. Changes include staged, unstaged and untracked paths, including spaces. JSON reports selection limitations and reasons to broaden. No test process is launched by the selector.
