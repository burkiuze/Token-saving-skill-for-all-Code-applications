#!/usr/bin/env python3
"""bulk_replace - repo-wide find & replace with a cheap preview, so an agent can make the
same change in many files without reading or editing each file one by one.

  bulk_replace.py PATTERN REPLACEMENT [options]          dry run: counts + a few sample diffs
  bulk_replace.py PATTERN REPLACEMENT [options] --apply  write the changes

PATTERN is a Python regex (use --fixed for a literal string). REPLACEMENT may use \\1 or
\\g<name>. Only git-tracked/unignored text files are touched; lockfiles, minified, vendored
and binary files are skipped. Python 3.8+, stdlib only.

Options:
  --glob '*.ts' (repeatable)   only files whose name/path matches
  --path src/ (repeatable)     only under these paths
  --fixed / --word / -i        literal pattern / whole-word / ignore case
  --multiline                  let . match newlines and ^/$ match per line
  --samples N                  sample diffs to show in dry run (default 3)
  --max-files N                refuse to apply to more than N files (default 500)
"""

import argparse
import fnmatch
import os
import re
import subprocess
import sys

SKIP_DIRS = {"node_modules", "vendor", "dist", "build", "target", ".git", ".codemap", "__pycache__",
             ".next", "coverage", ".venv", "venv"}
SKIP_FILES = {"package-lock.json", "yarn.lock", "pnpm-lock.yaml", "Cargo.lock", "poetry.lock",
              "Pipfile.lock", "composer.lock", "Gemfile.lock", "go.sum", "uv.lock", "bun.lockb"}
SKIP_SUFFIX = (".min.js", ".min.css", ".map", ".lock", ".snap", ".png", ".jpg", ".jpeg", ".gif",
               ".ico", ".pdf", ".zip", ".gz", ".woff", ".woff2", ".ttf", ".jar", ".exe", ".dll",
               ".so", ".dylib", ".pyc", ".class", ".wasm")


def root_dir():
    try:
        r = subprocess.run(["git", "rev-parse", "--show-toplevel"], stdout=subprocess.PIPE,
                           stderr=subprocess.DEVNULL, timeout=20)
        if r.returncode == 0:
            return r.stdout.decode("utf-8", "replace").strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return os.getcwd()


def list_files(root):
    try:
        r = subprocess.run(["git", "-C", root, "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                           stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=60)
        if r.returncode == 0:
            return [p for p in r.stdout.decode("utf-8", "surrogateescape").split("\0") if p]
    except (OSError, subprocess.SubprocessError):
        pass
    out = []
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS and not x.startswith(".")]
        out += [os.path.relpath(os.path.join(d, f), root).replace(os.sep, "/") for f in files]
    return out


def wanted(rel, globs, paths):
    parts = rel.split("/")
    base = parts[-1]
    if any(p in SKIP_DIRS for p in parts[:-1]) or base in SKIP_FILES or base.lower().endswith(SKIP_SUFFIX):
        return False
    if paths and not any(rel == p.rstrip("/") or rel.startswith(p.rstrip("/") + "/") for p in paths):
        return False
    if globs and not any(fnmatch.fnmatch(base, g) or fnmatch.fnmatch(rel, g) for g in globs):
        return False
    return True


def main(argv=None):
    ap = argparse.ArgumentParser(prog="bulk_replace.py", usage="%(prog)s PATTERN REPLACEMENT [options]",
                                 description="Repo-wide find & replace with preview (dry run by default).")
    ap.add_argument("pattern")
    ap.add_argument("replacement")
    ap.add_argument("--glob", action="append", default=[])
    ap.add_argument("--path", action="append", default=[])
    ap.add_argument("--fixed", action="store_true")
    ap.add_argument("--word", action="store_true")
    ap.add_argument("-i", "--ignore-case", action="store_true")
    ap.add_argument("--multiline", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--samples", type=int, default=3)
    ap.add_argument("--max-files", type=int, default=500)
    args = ap.parse_args(argv)

    pat = re.escape(args.pattern) if args.fixed else args.pattern
    if args.word:
        pat = r"\b(?:%s)\b" % pat
    flags = (re.I if args.ignore_case else 0) | (re.M | re.S if args.multiline else re.M)
    try:
        rx = re.compile(pat, flags)
    except re.error as e:
        print("bulk_replace: bad pattern: %s" % e)
        return 2
    repl = args.replacement
    if args.fixed:
        repl = repl.replace("\\", "\\\\")

    root = root_dir()
    paths = [os.path.relpath(os.path.abspath(p), root).replace(os.sep, "/") for p in args.path]
    changes, total, skipped = [], 0, 0
    for rel in sorted(list_files(root)):
        if not wanted(rel, args.glob, paths):
            continue
        full = os.path.join(root, rel)
        try:
            with open(full, "rb") as fh:
                data = fh.read()
        except OSError:
            continue
        if b"\0" in data[:8192] or len(data) > 5_000_000:
            continue
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            skipped += 1
            continue
        try:
            new, n = rx.subn(repl, text)
        except (re.error, IndexError) as e:
            print("bulk_replace: bad replacement: %s" % e)
            return 2
        if n:
            changes.append((rel, n, text, new))
            total += n

    if not changes:
        print("bulk_replace: no matches%s" % (" (%d non-UTF-8 files skipped)" % skipped if skipped else ""))
        return 1
    print("%d replacement(s) in %d file(s)%s" % (total, len(changes),
          " | %d non-UTF-8 files skipped" % skipped if skipped else ""))
    for rel, n, _, _ in sorted(changes, key=lambda c: -c[1])[:25]:
        print("  %4d  %s" % (n, rel))
    if len(changes) > 25:
        print("  … %d more files" % (len(changes) - 25))

    if not args.apply:
        shown = 0
        for rel, _, old, new in changes:
            if shown >= args.samples:
                break
            ol, nl = old.splitlines(), new.splitlines()
            for i, (a, b) in enumerate(zip(ol, nl)):
                if a != b:
                    print("--- %s:%d\n- %s\n+ %s" % (rel, i + 1, a.strip()[:200], b.strip()[:200]))
                    shown += 1
                    break
            else:
                print("--- %s: multi-line change (line count %d -> %d)" % (rel, len(ol), len(nl)))
                shown += 1
        print("dry run: nothing written. Re-run with --apply, then `git diff --stat` and run the tests.")
        return 0

    if len(changes) > args.max_files:
        print("bulk_replace: refusing to touch %d files (> --max-files %d)" % (len(changes), args.max_files))
        return 3
    for rel, _, _, new in changes:
        with open(os.path.join(root, rel), "wb") as fh:
            fh.write(new.encode("utf-8"))
    print("applied. Next: `git diff --stat`, grep for leftovers, run the affected tests.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:
        sys.exit(0)
