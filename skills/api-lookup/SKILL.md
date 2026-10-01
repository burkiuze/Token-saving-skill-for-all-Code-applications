---
name: api-lookup
description: Check installed library versions and exact API signatures. Use when implementing unfamiliar dependencies or resolving version-specific behavior; rely on primary documentation.
---

# API Lookup

Check the installed version before choosing an API. Prefer metadata/type files over importing untrusted project code, because imports can execute initialization.

| Ecosystem | Narrow lookup |
|---|---|
| Python | `python3 -m pip show PKG`; read stubs or use `inspect.signature` only for trusted installed code |
| JS/TS | `npm ls PKG --depth=0`; locate the exact declaration in `.d.ts` files |
| Go | `go list -m MODULE`; `go doc PKG.Func` |
| Rust | `cargo tree -i CRATE --depth 0`; search the installed version's function declaration |
| JVM | Dependency metadata; `javap -cp path/to.jar package.Class` |
| .NET/Ruby/PHP | `dotnet list package`, `bundle info GEM`, `composer show PKG` |

Read only the relevant definition and necessary surrounding types. A narrow dependency read is justified when it determines the change.

For current or unresolved behavior, search the exact symbol and version in official documentation or the project's source/release notes. Open the relevant primary page and distinguish documented facts from inference. Do not assume a stable API because a package name is familiar.

Save a reusable verified version quirk with `persistent-memory` when installed; include the package/version and link to the dependency manifest. Refresh it after a dependency update.
