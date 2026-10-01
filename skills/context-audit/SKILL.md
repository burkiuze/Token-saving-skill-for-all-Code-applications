---
name: context-audit
description: Inventory instruction files, skill metadata and configured MCP servers. Use when diagnosing context overhead or choosing an installation profile; estimates depend on client behavior.
---

# Context Audit

Run the absolute path to `scripts/context_audit.py` from the project; `--json` returns a machine-readable inventory. This command is read-only.

Separate three observations:
- Instruction files and imports: approximate text size, not proof every client sends all of it every turn.
- Discovered skill descriptions: approximate metadata cost; bodies load only when selected by supporting clients.
- Configured MCP servers: names/enabled states, without schema sizes or measured token costs.

Caching, tool search, client versions, compaction and scope all affect actual usage. Counts of servers are not token measurements. Use observed provider/tool usage when making a billing claim.

For authorized changes, trim duplicate always-on rules, move conditional detail into referenced resources and choose the minimal/balanced/full installer profile that covers actual work. Keep necessary constraints and useful integration capabilities.

Do not remove integrations, global configuration or instructions simply because the inventory is large. The user's request and existing authorization determine the scope. For a read-only audit, report concrete findings and a reviewable change proposal.

Re-run after an actual configuration change and compare like-for-like text estimates. Do not present this as measured per-request savings without usage evidence.
