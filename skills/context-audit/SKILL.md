---
name: context-audit
description: Measure and cut the fixed token overhead paid on every request - oversized CLAUDE.md/AGENTS.md/GEMINI.md (including @imports), too many skills, and enabled MCP servers whose tool schemas ride along with each message. Use when setting up a project, when sessions feel slow or costly, or when the user asks why token use is high.
---

# Context Audit

The biggest invisible cost is often not what you read but what gets sent on **every** turn. That includes instruction files, their `@imports`, skill descriptions and MCP tool schemas. A 6k-token CLAUDE.md plus four MCP servers can cost more than the task itself.

## Measure (read-only)
```
python3 scripts/context_audit.py          # current project + global config, all tools
python3 scripts/context_audit.py --json
```
For each tool (Claude Code, Codex, opencode, ZCode, Gemini CLI, Cursor, Copilot) it reports the always-loaded instruction tokens, skill metadata tokens, and which MCP servers are enabled, followed by concrete recommendations.

## Fix (ask the user before changing global config)
1. **Instruction files: aim for under 1–2k tokens each.**
   - Keep only rules every task needs: stack, commands, hard constraints.
   - Move procedures, long examples and reference docs into a skill or `docs/` file loaded on demand. Link it; don't `@import` it.
   - Delete stale or duplicated rules.
2. **MCP servers.** Enable per project only what that project uses.
   - Claude Code: `claude mcp list` / `claude mcp remove NAME`, or `/mcp`. Prefer project `.mcp.json` over user scope.
   - Codex: set `enabled = false` under `[mcp_servers.NAME]` in `~/.codex/config.toml`.
   - opencode: set `"enabled": false` in `opencode.json`.
   - Gemini and Cursor: remove the server from `settings.json` or `mcp.json`.
   - If a CLI can do the job cheaply (`gh`, `psql`, `curl`), it usually costs fewer tokens than a large MCP toolset.
3. **Skills.** Every installed skill's description is loaded each session. Remove the ones you never use, and keep descriptions to one or two sentences.
4. **Session habits.**
   - Start a fresh session (or `/clear`) between unrelated tasks.
   - Compact at natural milestones after writing `SESSION.md`.
   - Don't edit instruction files mid-session, because it invalidates prompt caching.

## Re-check
Run the audit again after trimming and report the before/after tokens per request to the user.
