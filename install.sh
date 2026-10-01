#!/usr/bin/env bash
# Thin launcher: the same tested installer handles every platform.
set -euo pipefail
TOKEN_SAVER_REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if command -v python3 >/dev/null 2>&1; then
  exec python3 "$TOKEN_SAVER_REPO_DIR/install.py" "$@"
elif command -v python >/dev/null 2>&1; then
  exec python "$TOKEN_SAVER_REPO_DIR/install.py" "$@"
else
  printf '%s\n' 'Token Saver requires Python 3.8+ for installation.' >&2
  exit 2
fi
