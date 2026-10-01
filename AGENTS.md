# Maintaining Token Saver Skills

Use Python 3.8+ and the standard library. Keep the toolkit local/offline and preserve the Apache-2.0 license.
Keep SKILL.md metadata concise and load reference files only for the relevant workflow.
Treat budgets as output/discovery controls; never claim they establish exact model counts, task savings or correctness.
Preserve unrelated user files and never install into the real home directory while testing.

Required checks after script/installer changes:

```bash
python3 tools/validate_skills.py
python3 -m unittest discover -s tests -q
python3 benchmarks/benchmark.py
```

Use disposable fixture projects for integration tests. Validate generated ZIP inventories and checksums before release.
Do not call real providers or use credentials for tests. Document untested platform-specific behavior explicitly.
