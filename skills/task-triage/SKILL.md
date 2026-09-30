---
name: task-triage
description: Size every coding task first (XS/S/M/L) and use the lightest workflow that still guarantees a correct, verified result, so small tasks finish in a few tool calls and big ones get just enough planning. Use at the start of any request that involves changing code.
---

# Task Triage

Most wasted time and tokens come from putting a one-line fix through a big-task process, or starting a big task without a plan and then redoing it. Pick the size in one glance and move. If you learn something that changes the size, re-size up. Never cut verification to save effort.

| Size | Looks like | Workflow | Budget |
|---|---|---|---|
| **XS** | typo, rename in one file, config value, a message you can find | `rg` → read the span → edit → one quick check (lint, test or run). No map, no plan, no memory writes. | ≤ 5 tool calls |
| **S** | bug in a known area; small feature in 1–3 files | `memory recall <area>` → `repomap find` / `rg` → read spans → edit → targeted tests (`test-impact`) | ≤ 15 calls |
| **M** | feature across modules; bug with unknown cause | `memory brief`, map (`repo-map`), a 3–7 bullet plan in `SESSION.md`, then implement in slices and test each one | checkpoint every slice |
| **L** | refactor, migration, new subsystem, mass change | Everything in M, plus: confirm the plan with the user if requirements are ambiguous. Do mechanical parts with `bulk-edit`, run parallel exploration through sub-agents, and checkpoint often. | plan first |

## Speed rules (same quality, less time)
- **Parallelize.** Send independent searches and reads in one turn, and run independent checks together.
- **Don't ask what the code can answer.** If you must ask, ask everything in one message, and keep working on the parts that don't depend on the answer.
- **Decide fast between equivalent options.** Follow the surrounding code's conventions and note the choice in one line.
- **No speculative work.** Don't refactor, add features or "improve" things that weren't asked for. Mention them instead.
- **Stop at done.** Once the acceptance criteria are met and verified, stop. Don't polish in extra rounds.
- **Reuse before you build.** Search for an existing helper or util before writing a new one.
- **Fail fast.** Run the quickest check that could prove you wrong first (typecheck or a single test) before the slow ones.

## Escalate, never de-scope
Move up a size when the fix touches more files than expected, when tests fail for reasons you don't understand, or when the change affects a public API, data, security or money. When unsure between two sizes, pick the larger one's verification and the smaller one's ceremony.
