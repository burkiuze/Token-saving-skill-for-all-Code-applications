#!/usr/bin/env python3
"""context_audit - measure the fixed "token tax" your AI coding tools pay on EVERY request:
always-loaded instruction files (CLAUDE.md, AGENTS.md, GEMINI.md, imports), skill metadata,
and MCP servers (whose tool schemas are sent with each request unless loaded on demand).

  context_audit.py            audit the current project + your global config
  context_audit.py --json     machine-readable

Read-only: it never changes anything. Python 3.8+, stdlib only.
"""

import argparse
import glob
import json
import os
import re
import subprocess
import sys

HOME = os.path.expanduser("~")
CFG = os.environ.get("XDG_CONFIG_HOME") or os.path.join(HOME, ".config")
CODEX = os.environ.get("CODEX_HOME") or os.path.join(HOME, ".codex")
WARN_FILE_TOK = 2000
WARN_TOTAL_TOK = 5000


def tok(n_chars):
    return int(round(n_chars / 4.0))


def read(path, limit=2_000_000):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read(limit)
    except OSError:
        return None


def repo_root(start):
    try:
        r = subprocess.run(["git", "-C", start, "rev-parse", "--show-toplevel"], stdout=subprocess.PIPE,
                           stderr=subprocess.DEVNULL, timeout=20)
        if r.returncode == 0:
            return r.stdout.decode("utf-8", "replace").strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return start


def ancestors(cwd, root):
    """cwd .. root (inclusive), or just cwd when root isn't an ancestor."""
    out, d = [], os.path.abspath(cwd)
    root = os.path.abspath(root)
    while True:
        out.append(d)
        if d == root or os.path.dirname(d) == d:
            break
        d = os.path.dirname(d)
    return out if out[-1] == root else [os.path.abspath(cwd)]


IMPORT_RX = re.compile(r"(?:^|\s)@((?:~|\.{1,2}|/)?[\w./-]+\.\w+)")


def with_imports(path, depth=0, seen=None):
    """Claude Code style @path imports (resolved up to 4 levels). -> [(path, chars)]"""
    seen = seen if seen is not None else set()
    real = os.path.realpath(path)
    if real in seen or depth > 4:
        return []
    seen.add(real)
    text = read(path)
    if text is None:
        return []
    out = [(path, len(text))]
    in_code = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        for m in IMPORT_RX.finditer(line.replace("`", " ` ")):
            ref = m.group(1)
            target = os.path.expanduser(ref) if ref.startswith("~") else os.path.join(os.path.dirname(path), ref)
            if os.path.isfile(target):
                out += [(p, n) for p, n in with_imports(target, depth + 1, seen)]
    return out


def instruction_files(cwd, root):
    groups = {}  # tool -> [(path, chars)]

    def add(tool, path, imports=False):
        if os.path.isfile(path):
            items = with_imports(path) if imports else [(path, len(read(path) or ""))]
            lst = groups.setdefault(tool, [])
            for p, n in items:
                if p not in [x[0] for x in lst]:
                    lst.append((p, n))

    add("Claude Code", os.path.join(HOME, ".claude", "CLAUDE.md"), True)
    for d in reversed(ancestors(cwd, root)):
        add("Claude Code", os.path.join(d, "CLAUDE.md"), True)
        add("Claude Code", os.path.join(d, ".claude", "CLAUDE.md"), True)
        add("Claude Code", os.path.join(d, "CLAUDE.local.md"), True)
        for tool in ("Codex", "opencode", "ZCode", "Cursor", "Copilot"):
            add(tool, os.path.join(d, "AGENTS.md"))
        add("Codex", os.path.join(d, "AGENTS.override.md"))
        add("Gemini CLI", os.path.join(d, "GEMINI.md"))
    add("Codex", os.path.join(CODEX, "AGENTS.md"))
    add("opencode", os.path.join(CFG, "opencode", "AGENTS.md"))
    add("ZCode", os.path.join(HOME, ".zcode", "AGENTS.md"))
    add("Gemini CLI", os.path.join(HOME, ".gemini", "GEMINI.md"))
    add("Copilot", os.path.join(HOME, ".copilot", "copilot-instructions.md"))
    add("Copilot", os.path.join(root, ".github", "copilot-instructions.md"))
    add("Cursor", os.path.join(root, ".cursorrules"))
    for mdc in sorted(glob.glob(os.path.join(root, ".cursor", "rules", "**", "*.mdc"), recursive=True)):
        head = (read(mdc, 2000) or "")
        if re.search(r"^alwaysApply:\s*true", head, re.M):
            add("Cursor", mdc)
    add("Windsurf", os.path.join(root, ".windsurfrules"))
    return groups


SKILL_DIRS = {
    "Claude Code": ["~/.claude/skills", "{root}/.claude/skills"],
    "Codex": ["~/.agents/skills", "{root}/.agents/skills", "~/.codex/skills"],
    "opencode": ["~/.config/opencode/skills", "~/.claude/skills", "~/.agents/skills",
                 "{root}/.opencode/skills", "{root}/.claude/skills", "{root}/.agents/skills"],
    "ZCode": ["~/.zcode/skills", "~/.agents/skills", "{root}/.zcode/skills", "{root}/.agents/skills"],
    "Gemini CLI": ["~/.gemini/skills", "~/.agents/skills", "{root}/.gemini/skills", "{root}/.agents/skills"],
    "Cursor": ["~/.cursor/skills", "~/.agents/skills", "{root}/.cursor/skills", "{root}/.agents/skills"],
    "Copilot": ["~/.copilot/skills", "~/.claude/skills", "~/.agents/skills", "{root}/.github/skills",
                "{root}/.claude/skills", "{root}/.agents/skills"],
}


def skill_meta(root):
    res = {}
    for tool, dirs in SKILL_DIRS.items():
        names, chars = {}, 0
        for d in dirs:
            d = os.path.expanduser(d.replace("{root}", root))
            for f in glob.glob(os.path.join(d, "*", "SKILL.md")) + glob.glob(os.path.join(d, "*", "*", "SKILL.md")):
                text = read(f, 6000) or ""
                m = re.search(r"^---\s*\n(.*?)\n---", text, re.S)
                front = m.group(1) if m else ""
                name = (re.search(r"^name:\s*(.+)$", front, re.M) or [None, os.path.basename(os.path.dirname(f))])[1]
                if name in names:
                    continue
                desc = re.search(r"^description:\s*(.+?)(?=^\w[\w-]*:|\Z)", front, re.M | re.S)
                names[name] = len(desc.group(1)) if desc else 0
                chars += len(name) + names[name] + 20
        if names:
            res[tool] = {"count": len(names), "tokens": tok(chars)}
    return res


def jload(path):
    text = read(path)
    if text is None:
        return None
    try:
        return json.loads(text)
    except ValueError:
        # jsonc: drop // and /* */ comments and trailing commas
        text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
        text = re.sub(r"(^|[^:\"'])//[^\n]*", r"\1", text)
        text = re.sub(r",(\s*[}\]])", r"\1", text)
        try:
            return json.loads(text)
        except ValueError:
            return None


def mcp_servers(root):
    found = {}  # tool -> [(name, source, enabled)]

    def add(tool, name, src, enabled=True):
        lst = found.setdefault(tool, [])
        if name not in [x[0] for x in lst]:
            lst.append((name, src, enabled))

    cj = jload(os.path.join(HOME, ".claude.json")) or {}
    for n, cfg in (cj.get("mcpServers") or {}).items():
        add("Claude Code", n, "~/.claude.json (user)")
    proj = (cj.get("projects") or {}).get(root) or {}
    disabled = set(proj.get("disabledMcpjsonServers") or [])
    for n in (proj.get("mcpServers") or {}):
        add("Claude Code", n, "~/.claude.json (local)")
    for n in ((jload(os.path.join(root, ".mcp.json")) or {}).get("mcpServers") or {}):
        add("Claude Code", n, ".mcp.json", n not in disabled)

    for path in (os.path.join(CODEX, "config.toml"), os.path.join(root, ".codex", "config.toml")):
        text = read(path) or ""
        for m in re.finditer(r"^\[mcp_servers\.\"?([^\]\".]+)\"?\]\s*$(.*?)(?=^\[|\Z)", text, re.M | re.S):
            enabled = not re.search(r"^\s*enabled\s*=\s*false", m.group(2), re.M)
            add("Codex", m.group(1), path.replace(HOME, "~"), enabled)

    for path in (os.path.join(CFG, "opencode", "opencode.json"), os.path.join(CFG, "opencode", "opencode.jsonc"),
                 os.path.join(root, "opencode.json"), os.path.join(root, "opencode.jsonc")):
        for n, cfg in ((jload(path) or {}).get("mcp") or {}).items():
            add("opencode", n, path.replace(HOME, "~"), not (isinstance(cfg, dict) and cfg.get("enabled") is False))

    for path in (os.path.join(HOME, ".gemini", "settings.json"), os.path.join(root, ".gemini", "settings.json")):
        for n in ((jload(path) or {}).get("mcpServers") or {}):
            add("Gemini CLI", n, path.replace(HOME, "~"))
    for path in (os.path.join(HOME, ".cursor", "mcp.json"), os.path.join(root, ".cursor", "mcp.json")):
        for n in ((jload(path) or {}).get("mcpServers") or {}):
            add("Cursor", n, path.replace(HOME, "~"))
    for path, key in ((os.path.join(root, ".vscode", "mcp.json"), "servers"),
                      (os.path.join(HOME, ".copilot", "mcp-config.json"), "mcpServers")):
        for n in ((jload(path) or {}).get(key) or {}):
            add("Copilot", n, path.replace(HOME, "~"))
    return found


ROOT = [None]


def short(p):
    r = ROOT[0]
    if r and (p == r or p.startswith(r.rstrip(os.sep) + os.sep)):
        return os.path.relpath(p, r).replace(os.sep, "/")
    return p.replace(HOME, "~")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="context_audit.py", description=__doc__.split("\n")[1])
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    cwd = os.getcwd()
    root = repo_root(cwd)
    ROOT[0] = root
    inst = instruction_files(cwd, root)
    skills = skill_meta(root)
    mcp = mcp_servers(root)

    tools = sorted(set(inst) | set(skills) | set(mcp))
    summary = {}
    for t in tools:
        itok = sum(tok(n) for _, n in inst.get(t, []))
        stok = skills.get(t, {}).get("tokens", 0)
        enabled = [s for s in mcp.get(t, []) if s[2]]
        summary[t] = {"instructions": itok, "skills": stok, "mcp_enabled": len(enabled)}
    if args.json:
        print(json.dumps({"root": root, "instructions": {t: [(short(p), tok(n)) for p, n in v] for t, v in inst.items()},
                          "skills": skills, "mcp": {t: [list(x) for x in v] for t, v in mcp.items()},
                          "summary": summary}, indent=1))
        return 0

    print("Fixed context paid on every request (≈ chars/4 tokens), project: %s" % root.replace(HOME, "~"))
    if not tools:
        print("nothing found: no instruction files, skills or MCP servers")
        return 0
    print("\n%-12s %13s %9s %12s" % ("tool", "instructions", "skills", "MCP servers"))
    for t in tools:
        s = summary[t]
        mc = mcp.get(t, [])
        print("%-12s %8d tok %6d tok %5d on/%d" % (t, s["instructions"], s["skills"], s["mcp_enabled"], len(mc)))

    print("\ninstruction files:")
    seen = set()
    for t in tools:
        for p, n in inst.get(t, []):
            if p in seen:
                continue
            seen.add(p)
            flag = "  <- large" if tok(n) > WARN_FILE_TOK else ""
            print("  %6d tok  %s%s" % (tok(n), short(p), flag))
    if not seen:
        print("  (none)")

    if mcp:
        print("\nMCP servers (tool schemas are sent with each request unless your client loads them on demand):")
        for t in tools:
            for name, src, en in mcp.get(t, []):
                print("  %-11s %-24s %s%s" % (t, name, src, "" if en else "  (disabled)"))

    tips = []
    for p in seen:
        n = dict((pp, nn) for t in inst for pp, nn in inst[t]).get(p, 0)
        if tok(n) > WARN_FILE_TOK:
            tips.append("%s is ~%dk tokens: keep only rules every task needs; move procedures/reference into a skill or docs file loaded on demand." % (short(p), tok(n) // 1000))
    for t, s in summary.items():
        total = s["instructions"] + s["skills"]
        if total > WARN_TOTAL_TOK:
            tips.append("%s: ~%dk tokens of always-on text before you type anything; trim it." % (t, total // 1000))
        if skills.get(t, {}).get("count", 0) > 30:
            tips.append("%s: %d skills installed; every description is loaded each session. Remove ones you never use." % (t, skills[t]["count"]))
        if s["mcp_enabled"] >= 3:
            tips.append("%s: %d MCP servers enabled. Disable the ones this project doesn't need (Claude: `claude mcp remove NAME` or /mcp; Codex: `enabled = false`; opencode: \"enabled\": false)." % (t, s["mcp_enabled"]))
    print("\nrecommendations:" if tips else "\nlooks lean: no action needed")
    for tip in tips:
        print("  - " + tip)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:
        sys.exit(0)
