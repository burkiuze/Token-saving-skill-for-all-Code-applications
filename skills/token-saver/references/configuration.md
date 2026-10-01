# Local retrieval configuration

Place `.token-saver.json` at the project root. All fields are optional; unknown fields and
invalid types fail rather than silently changing retrieval.

```json
{
  "budget": 2000,
  "max_file_bytes": 500000,
  "max_files": 3000,
  "max_snippets": 12,
  "context_lines": 4,
  "exclude": ["fixtures/large/**", "generated/**"],
  "priority_paths": ["src/", "lib/", "app/", "tests/"]
}
```

`budget` is a UTF-8-byte/4 heuristic for the complete packet, including metadata and
numbered text. `--budget` overrides it. It is not an exact model token count.

`max_file_bytes` bounds each file read. `max_files` bounds inventory selection and the
packet reports how many candidate files were omitted. `max_snippets` bounds selected
spans. `context_lines` applies to line evidence; complete short Python AST symbols can
cover more lines when they fit. Priority paths boost only already matched candidates.

Exclusions use case-sensitive shell-style `fnmatch` patterns on slash-separated relative
paths; they are not a full Git-ignore language. In a Git repository, untracked candidates
also respect `.gitignore` through `git ls-files --exclude-standard`. Tracked files remain
eligible unless explicitly excluded by these rules or the built-in filters.

Built-in filters exclude vendor/build/cache/lock/minified/binary content, common credential
paths, all source symlinks and outside-project paths. Inline redaction recognizes common
assignment, bearer, provider key and private-key patterns; it can miss unusual credentials
or mask benign strings. It does not authorize publishing a packet automatically.

The toolkit scans plain local UTF-8 data. It does not execute project imports, parse
unsafe serialized objects, send source to a service or install dependencies.
