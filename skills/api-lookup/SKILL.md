---
name: api-lookup
description: Get exact library/API facts (installed version, function signature, options, types) with one precise command instead of reading dependency source, whole docs pages, or guessing. Use whenever you need to know how a third-party function, class, CLI flag or config option works.
---

# API Lookup

Guessing an API causes a failed run and a retry. Reading `node_modules` or a whole docs site burns thousands of tokens. Ask the installed package directly: it's exact for **your** version, and cheap.

## 1. Which version is installed?
- Node: `node -p "require('PKG/package.json').version"` or `npm ls PKG --depth=0`
- Python: `pip show PKG | head -3` or `python -c "import PKG; print(PKG.__version__)"`
- Go: `go list -m MODULE`
- Rust: `cargo tree -i CRATE --depth 0`
- Java/Kotlin: `mvn -q dependency:tree -Dincludes=GROUP:ART` or `gradle dependencies --configuration runtimeClasspath | rg ART`
- .NET: `dotnet list package | rg PKG`
- Ruby: `bundle info GEM`
- PHP: `composer show PKG`

## 2. Get the exact signature or docs
- TypeScript/JS: `rg -n "export (declare )?(function|const|class|interface|type) NAME" node_modules/PKG --glob '*.d.ts' | head`, then read **only that span** of the `.d.ts`
- Python: `python -c "import inspect, M; print(inspect.signature(M.F)); print((M.F.__doc__ or '')[:800])"`
- Go: `go doc PKG.Func` or `go doc -short PKG`
- Rust: `rg -n "pub fn NAME" ~/.cargo/registry/src/*/CRATE-VERSION/src | head`
- Java: `javap -cp path/to.jar com.x.Class`
- CLI tools: `TOOL --help 2>&1 | rg -i -A2 "flag"` or `man TOOL | col -b | rg -A3 -- "--flag"`

## 3. Web docs (last resort, still narrow)
- Search for the exact symbol plus the version. Open the one relevant page, not the site.
- Prefer machine-friendly sources such as `llms.txt`, `.md` versions of docs, or the changelog entry for your version.
- Pull out the few lines you need. Don't paste whole pages into context.

## 4. Remember it
Version quirks, surprising defaults and breaking changes are worth saving:
`python3 ../persistent-memory/scripts/memory.py add "zod v4: .parse errors are error.issues (not .errors)" --kind api --tags zod`

## Never
- Don't read whole files in `node_modules`, `site-packages` or vendored code. Grep for the symbol, then read the span.
- Don't answer from memory when the installed version is available to check, especially for fast-moving libraries.
