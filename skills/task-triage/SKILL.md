---
name: task-triage
description: Match coding workflow effort to scope and risk. Use before starting an edit or when new evidence expands a task; preserve acceptance criteria and required checks.
---

# Task Triage

State the desired result and choose the smallest workflow that can verify it.

| Scope | Workflow |
|---|---|
| Known tiny edit | Locate → read → edit → one relevant check |
| Local bug or feature | Reproduce → inspect implementation/callers → edit → focused tests |
| Cross-module task | Short plan → scoped evidence → implement in pieces → required checks |
| Migration/shared/security-sensitive behavior | Invariants and affected interfaces → staged implementation → broader validation |

Use task size to reduce ceremony, not to impose a fixed tool-call quota. Stop exploring when the implementation and verification path are clear. Reuse an existing helper before adding one.

Batch independent reads/checks. Keep dependencies sequential. Use subagents only under the runtime and user's authorization; account for their context and integration cost.

Ask only for missing information that changes the result, and continue independent work. Follow local conventions for routine choices. Reassess scope when a public interface, schema, shared utility or unexpected failing check is involved.

Complete the requested work and required checks. After they pass, repeat or widen testing only when new changes or unresolved concerns justify it. Checkpoint long tasks with `session-memory` when installed.
