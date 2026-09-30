#!/usr/bin/env bash
# Token Saver Skills installer for Claude Code, Codex, opencode, ZCode, Gemini CLI,
# Cursor and GitHub Copilot. Works with macOS bash 3.2, Linux, WSL and Git Bash.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_SRC="$REPO_DIR/skills"
BLOCK_SRC="$REPO_DIR/rules/token-saver-block.md"
SKILLS=(token-saver task-triage repo-map smart-read quiet-run test-impact session-memory persistent-memory bulk-edit api-lookup context-audit)
ALL_TOOLS="claude codex opencode zcode gemini cursor copilot"
START="<!-- token-saver:start"
END="<!-- token-saver:end -->"

MODE=global PROJECT="" TOOLS="" RULES=1 LINK=0 UNINSTALL=0 DRY=0

usage() {
  cat <<'EOF'
Token Saver Skills installer

Usage: ./install.sh [options]
  (no options)       install globally for every AI coding tool found on this machine
  --project DIR      install into one project instead (skills + AGENTS.md/CLAUDE.md there)
  --tools LIST       comma list or "all": claude,codex,opencode,zcode,gemini,cursor,copilot
  --no-rules         only copy skills; don't touch AGENTS.md / CLAUDE.md / GEMINI.md
  --link             symlink skills instead of copying (a `git pull` here updates them)
  --uninstall        remove the skills and the rules block
  --dry-run          show what would happen
  -h, --help         this help

Skills go to ~/.claude/skills (Claude Code) and ~/.agents/skills (Codex, opencode,
ZCode, Gemini CLI, Cursor, Copilot all read it). The rules block is added between
markers, so re-running updates it in place, and --uninstall removes it cleanly.
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --project) MODE=project; PROJECT="${2:?--project needs a directory}"; shift 2 ;;
    --project=*) MODE=project; PROJECT="${1#*=}"; shift ;;
    --tools) TOOLS="${2:?--tools needs a list}"; shift 2 ;;
    --tools=*) TOOLS="${1#*=}"; shift ;;
    --no-rules) RULES=0; shift ;;
    --link) LINK=1; shift ;;
    --uninstall) UNINSTALL=1; shift ;;
    --dry-run) DRY=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

say() { printf '%s\n' "$*"; }
run() { if [ "$DRY" = 1 ]; then say "  [dry-run] $*"; else "$@"; fi; }
has() { command -v "$1" >/dev/null 2>&1; }
contains() { local x="$1"; shift; local y; for y in "$@"; do [ "$y" = "$x" ] && return 0; done; return 1; }

CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
CODEX_DIR="${CODEX_HOME:-$HOME/.codex}"

# ------------------------------------------------------------ tool selection
if [ -z "$TOOLS" ]; then
  if [ "$MODE" = project ]; then
    TOOLS="$ALL_TOOLS"
  else
    found=""
    { [ -d "$HOME/.claude" ] || has claude; } && found="$found claude"
    { [ -d "$CODEX_DIR" ] || has codex; } && found="$found codex"
    { [ -d "$CONFIG_HOME/opencode" ] || has opencode; } && found="$found opencode"
    { [ -d "$HOME/.zcode" ] || has zcode; } && found="$found zcode"
    { [ -d "$HOME/.gemini" ] || has gemini; } && found="$found gemini"
    { [ -d "$HOME/.cursor" ] || has cursor || has cursor-agent; } && found="$found cursor"
    { [ -d "$HOME/.copilot" ] || has copilot; } && found="$found copilot"
    TOOLS="${found# }"
    if [ -z "$TOOLS" ]; then
      say "No AI coding tool detected; installing skills to ~/.claude/skills and ~/.agents/skills only."
      say "Re-run with --tools claude,codex,... to also add the always-on rules block."
      TOOLS="claude codex"
      RULES=0
    fi
  fi
fi
[ "$TOOLS" = all ] && TOOLS="$ALL_TOOLS"
TOOLS="$(printf '%s' "$TOOLS" | tr ',' ' ')"
for t in $TOOLS; do
  case " $ALL_TOOLS " in *" $t "*) ;; *) echo "unknown tool: $t (valid: $ALL_TOOLS)" >&2; exit 2 ;; esac
done

if [ "$MODE" = project ]; then
  [ -d "$PROJECT" ] || { echo "not a directory: $PROJECT" >&2; exit 2; }
  PROJECT="$(cd "$PROJECT" && pwd)"
  BASE="$PROJECT"
  CLAUDE_SKILLS="$BASE/.claude/skills";  CLAUDE_REF=".claude/skills"
  AGENTS_SKILLS="$BASE/.agents/skills";  AGENTS_REF=".agents/skills"
else
  BASE="$HOME"
  CLAUDE_SKILLS="$HOME/.claude/skills";  CLAUDE_REF="~/.claude/skills"
  AGENTS_SKILLS="$HOME/.agents/skills";  AGENTS_REF="~/.agents/skills"
fi

# ------------------------------------------------------------ plan
SKILL_DESTS=()
RULE_FILES=()
RULE_REFS=()
NOTES=()
add_skills() { contains "$1" ${SKILL_DESTS[@]+"${SKILL_DESTS[@]}"} || SKILL_DESTS+=("$1"); }
add_rule() {
  contains "$1" ${RULE_FILES[@]+"${RULE_FILES[@]}"} && return 0
  RULE_FILES+=("$1"); RULE_REFS+=("$2")
}

for t in $TOOLS; do
  if [ "$t" = claude ]; then add_skills "$CLAUDE_SKILLS"; else add_skills "$AGENTS_SKILLS"; fi
  if [ "$MODE" = project ]; then
    case "$t" in
      claude) add_rule "$BASE/CLAUDE.md" "$CLAUDE_REF" ;;
      gemini) add_rule "$BASE/GEMINI.md" "$AGENTS_REF" ;;
      *)      add_rule "$BASE/AGENTS.md" "$AGENTS_REF" ;;
    esac
  else
    case "$t" in
      claude)   add_rule "$HOME/.claude/CLAUDE.md" "$CLAUDE_REF" ;;
      codex)    add_rule "$CODEX_DIR/AGENTS.md" "$AGENTS_REF" ;;
      opencode) add_rule "$CONFIG_HOME/opencode/AGENTS.md" "$AGENTS_REF" ;;
      zcode)    add_rule "$HOME/.zcode/AGENTS.md" "$AGENTS_REF" ;;
      gemini)   add_rule "$HOME/.gemini/GEMINI.md" "$AGENTS_REF" ;;
      copilot)  add_rule "$HOME/.copilot/copilot-instructions.md" "$AGENTS_REF" ;;
      cursor)   NOTES+=("Cursor has no global rules file: paste rules/token-saver-block.md into Cursor Settings > Rules > User Rules, or use --project DIR (writes AGENTS.md).") ;;
    esac
  fi
done

# ------------------------------------------------------------ helpers
# replace (or remove, when blockfile is /dev/null) the marked block in a file
rewrite_block() {
  local file="$1" blockfile="$2" tmp
  tmp="$(mktemp)"
  # blank lines are buffered so the separator before a removed block (and trailing
  # blank lines at EOF) do not pile up across install/uninstall cycles
  awk -v s="$START" -v e="$END" -v bf="$blockfile" '
    index($0, s) == 1 {
      if (bf != "/dev/null") { printf "%s", blanks; while ((getline l < bf) > 0) print l; close(bf) }
      blanks = ""; skip = 1; next
    }
    skip { if (index($0, e) == 1) skip = 0; next }
    /^[[:space:]]*$/ { blanks = blanks $0 "\n"; next }
    { printf "%s", blanks; blanks = ""; print }' "$file" > "$tmp"
  cat "$tmp" > "$file"
  rm -f "$tmp"
}

upsert_rules() {
  local file="$1" ref="$2" blockfile
  if [ "$DRY" = 1 ]; then say "  [dry-run] rules block -> $file"; return 0; fi
  blockfile="$(mktemp)"
  sed -e "s#{{SKILLS_DIR}}#$ref#g" -e "s#{{PY}}#python3#g" "$BLOCK_SRC" > "$blockfile"
  mkdir -p "$(dirname "$file")"
  if [ -f "$file" ] && grep -qF "$START" "$file"; then
    if ! grep -qF "$END" "$file"; then
      say "  SKIPPED $file: start marker without end marker; fix it by hand"; rm -f "$blockfile"; return 0
    fi
    rewrite_block "$file" "$blockfile"
    say "  updated rules block: $file"
  elif [ -s "$file" ]; then
    { printf '\n'; cat "$blockfile"; } >> "$file"
    say "  appended rules block: $file"
  else
    cat "$blockfile" > "$file"
    say "  created: $file"
  fi
  rm -f "$blockfile"
}

remove_rules() {
  local file="$1"
  [ -f "$file" ] && grep -qF "$START" "$file" && grep -qF "$END" "$file" || return 0
  if [ "$DRY" = 1 ]; then say "  [dry-run] remove rules block from $file"; return 0; fi
  rewrite_block "$file" /dev/null
  if ! grep -q '[^[:space:]]' "$file"; then rm -f "$file"; say "  removed empty: $file"
  else say "  removed rules block: $file"; fi
}

install_skills() {
  local dest="$1" s target
  run mkdir -p "$dest"
  for s in "${SKILLS[@]}"; do
    target="${dest:?}/${s:?}"
    if [ -e "$target" ] || [ -L "$target" ]; then run rm -rf "$target"; fi
    if [ "$LINK" = 1 ]; then run ln -s "$SKILLS_SRC/$s" "$target"
    else run cp -R "$SKILLS_SRC/$s" "$target"; fi
  done
  [ "$DRY" = 1 ] || chmod +x "$dest"/*/scripts/*.py 2>/dev/null || true
  say "  skills -> $dest ($(printf '%s ' "${SKILLS[@]}"))"
}

remove_skills() {
  local dest="$1" s target
  for s in "${SKILLS[@]}"; do
    target="${dest:?}/${s:?}"
    if [ -e "$target" ] || [ -L "$target" ]; then run rm -rf "$target"; say "  removed $target"; fi
  done
  # tidy up folders we may have created (rmdir only succeeds when they are empty)
  [ "$DRY" = 1 ] || rmdir "$dest" "$(dirname "$dest")" 2>/dev/null || true
}

# ------------------------------------------------------------ go
say "Token Saver Skills: $([ "$UNINSTALL" = 1 ] && echo uninstall || echo install) (${MODE}; tools: $TOOLS)"

if [ "$UNINSTALL" = 1 ]; then
  for d in ${SKILL_DESTS[@]+"${SKILL_DESTS[@]}"}; do remove_skills "$d"; done
  for f in ${RULE_FILES[@]+"${RULE_FILES[@]}"}; do remove_rules "$f"; done
  say "Done. (.codemap/ folders inside your projects are left alone.)"
  exit 0
fi

for d in ${SKILL_DESTS[@]+"${SKILL_DESTS[@]}"}; do install_skills "$d"; done
if [ "$RULES" = 1 ]; then
  i=0
  while [ $i -lt ${#RULE_FILES[@]} ]; do
    upsert_rules "${RULE_FILES[$i]}" "${RULE_REFS[$i]}"
    i=$((i + 1))
  done
fi
for n in ${NOTES[@]+"${NOTES[@]}"}; do say "  note: $n"; done

has python3 || has python || say "  note: Python 3 not found. The skills still work (they have rg/grep fallbacks), but repomap/quiet_run need Python 3.8+."
say "Done. Restart your coding tool so it picks up the new skills."
