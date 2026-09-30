#!/usr/bin/env python3
"""affected_tests - which tests cover the files you changed? Run those first.

  affected_tests.py                 changes in the working tree (staged + unstaged + untracked)
  affected_tests.py --base main     changes since a ref (e.g. the branch point)
  affected_tests.py --files a.py b.ts

Finds tests by naming convention (foo.ts -> foo.test.ts / foo.spec.ts, foo.py -> test_foo.py,
Foo.java -> FooTest.java, foo.go -> package dir, ...) and by test files that import the
changed module. Prints the test files and a ready-to-run narrow command per framework.
Heuristic: run the full suite once before you finish. Python 3.8+, stdlib only.
"""

import argparse
import json
import os
import re
import subprocess
import sys

TEST_RX = re.compile(r"(^|/)(tests?|__tests__|specs?|e2e|integration_tests?)/|(^|/)test_[^/]+$"
                     r"|_(test|spec)\.[^/.]+$|[.-](test|spec)s?\.[^/]+$|(Tests?|IT|Spec)\.(java|kt|cs|swift|scala|php|groovy)$")
GENERIC = {"index", "main", "mod", "lib", "__init__", "utils", "util", "helpers", "types", "common",
           "app", "config", "constants", "init", "core", "base"}
CODE_EXT = {"py", "js", "jsx", "ts", "tsx", "mjs", "cjs", "mts", "cts", "vue", "svelte", "go", "rs",
            "java", "kt", "cs", "rb", "php", "swift", "dart", "ex", "exs", "scala", "c", "cc",
            "cpp", "h", "hpp", "m", "mm"}
GENERIC_DIRS = {"src", "lib", "pkg", "internal", "source", "sources", "app", "main", "java", "kotlin", ""}
IMPORT_HINT = re.compile(r"\b(import|from|require|use|using|include|load|require_relative)\b")


def git(root, *args):
    try:
        r = subprocess.run(["git", "-C", root] + list(args), stdout=subprocess.PIPE,
                           stderr=subprocess.DEVNULL, timeout=60)
        return r.stdout.decode("utf-8", "replace") if r.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def root_dir():
    out = git(os.getcwd(), "rev-parse", "--show-toplevel")
    return out.strip() if out else os.getcwd()


def changed_files(root, base):
    files = set()
    if base:
        out = git(root, "diff", "--name-only", base + "...HEAD") or git(root, "diff", "--name-only", base) or ""
        files.update(out.split())
    for args in (("diff", "--name-only"), ("diff", "--name-only", "--cached"),
                 ("ls-files", "--others", "--exclude-standard")):
        files.update((git(root, *args) or "").split())
    return sorted(files)


def all_files(root):
    out = git(root, "ls-files", "--cached", "--others", "--exclude-standard")
    if out is not None:
        return [f for f in out.splitlines() if f and "node_modules/" not in f]
    res = []
    for d, dirs, fs in os.walk(root):
        dirs[:] = [x for x in dirs if not x.startswith(".") and x not in ("node_modules", "vendor", "dist", "build", "target")]
        res += [os.path.relpath(os.path.join(d, f), root).replace(os.sep, "/") for f in fs]
    return res


def split(rel):
    d, base = (rel.rsplit("/", 1) if "/" in rel else ("", rel))
    stem, ext = (base.rsplit(".", 1) if "." in base else (base, ""))
    return d, stem, ext.lower()


def candidate_names(stem, ext):
    s = stem
    names = {
        "%s.test.%s" % (s, ext), "%s.spec.%s" % (s, ext), "%s_test.%s" % (s, ext),
        "test_%s.%s" % (s, ext), "%s_spec.%s" % (s, ext), "%sTest.%s" % (s, ext),
        "%sTests.%s" % (s, ext), "%sIT.%s" % (s, ext), "%sSpec.%s" % (s, ext),
    }
    if ext != "py":  # same name inside a tests/ or __tests__/ dir (python needs test_ prefix)
        names.add("%s.%s" % (s, ext))
    if ext in ("ts", "js", "tsx", "jsx", "mts", "mjs", "cts", "cjs", "vue", "svelte"):
        for e in ("ts", "tsx", "js", "jsx", "mts", "mjs"):
            names |= {"%s.test.%s" % (s, e), "%s.spec.%s" % (s, e)}
    if ext == "ex":
        names.add("%s_test.exs" % s)
    return names


def find_tests(root, changed, files):
    tests = [f for f in files if TEST_RX.search(f)]
    by_base = {}
    for t in tests:
        by_base.setdefault(t.rsplit("/", 1)[-1], []).append(t)
    hits = {}  # test file -> reason
    go_pkgs, rust = set(), False
    contents = {}

    def content(t):
        if t not in contents:
            try:
                with open(os.path.join(root, t), encoding="utf-8", errors="replace") as fh:
                    contents[t] = fh.read(200_000)
            except OSError:
                contents[t] = ""
        return contents[t]

    for rel in changed:
        d, stem, ext = split(rel)
        if ext not in CODE_EXT:
            continue
        if TEST_RX.search(rel):
            if os.path.exists(os.path.join(root, rel)):
                hits.setdefault(rel, "changed test")
            if ext == "go":
                go_pkgs.add(d or ".")
            continue
        if ext == "go":
            go_pkgs.add(d or ".")
            continue
        if ext == "rs":
            rust = True
        # 1) naming convention
        for name in candidate_names(stem, ext):
            for t in by_base.get(name, []):
                if name == "%s.%s" % (stem, ext) and not TEST_RX.search(t):
                    continue
                hits.setdefault(t, "name ~ " + rel)
        # 2) test files that import the module. Generic stems (utils, index, ...) must
        #    appear together with their folder name: `requests.utils`, `../lib/utils`.
        key, folder = stem, ""
        if stem.lower() in GENERIC:
            folder = d.rsplit("/", 1)[-1] if d else ""
            if folder.lower() in GENERIC_DIRS:
                continue
        if len(key) < 3:
            continue
        word = re.compile(r"(?<![\w-])%s(?![\w-])" % re.escape(key))
        fword = re.compile(r"(?<![\w-])%s(?![\w-])" % re.escape(folder)) if folder else None
        for t in tests:
            if t in hits:
                continue
            text = content(t)
            if key not in text or (folder and folder not in text):
                continue
            for line in text.splitlines()[:400]:
                if key in line and IMPORT_HINT.search(line) and word.search(line) \
                        and (fword is None or fword.search(line)):
                    hits[t] = "imports " + ((folder + "/") if folder else "") + key
                    break
    return hits, sorted(go_pkgs), rust


def detect(root):
    have = lambda p: os.path.exists(os.path.join(root, p))
    fw = set()
    pkg = {}
    if have("package.json"):
        try:
            with open(os.path.join(root, "package.json"), encoding="utf-8") as fh:
                pkg = json.load(fh)
        except (OSError, ValueError):
            pkg = {}
        deps = dict(pkg.get("devDependencies", {}), **pkg.get("dependencies", {}))
        for name in ("vitest", "jest", "mocha", "@playwright/test"):
            if name in deps:
                fw.add(name)
    if have("pytest.ini") or have("conftest.py") or have("pyproject.toml") or have("setup.cfg") or have("tox.ini"):
        fw.add("pytest")
    if have("Gemfile"):
        fw.add("rspec" if have("spec") else "minitest")
    if have("pom.xml"):
        fw.add("maven")
    if have("build.gradle") or have("build.gradle.kts"):
        fw.add("gradle")
    if have("mix.exs"):
        fw.add("mix")
    if have("pubspec.yaml"):
        fw.add("dart")
    return fw


def commands(root, hits, go_pkgs, rust, fw):
    tests = sorted(hits)
    by_ext = {}
    for t in tests:
        by_ext.setdefault(split(t)[2], []).append(t)
    cmds = []
    py = by_ext.get("py", [])
    if py:
        cmds.append("pytest -q -x --tb=short " + " ".join(py))
    js = [t for e in ("ts", "tsx", "js", "jsx", "mjs", "cjs", "mts", "cts") for t in by_ext.get(e, [])]
    if js:
        if "vitest" in fw:
            cmds.append("npx vitest run " + " ".join(js))
        elif "jest" in fw:
            cmds.append("npx jest --silent " + " ".join(js))
        elif "mocha" in fw:
            cmds.append("npx mocha --reporter dot " + " ".join(js))
        else:
            cmds.append("<your js test runner> " + " ".join(js))
    if go_pkgs:
        cmds.append("go test " + " ".join("./" + p if p != "." else "." for p in go_pkgs))
    jv = [split(t)[1] for e in ("java", "kt", "scala", "groovy") for t in by_ext.get(e, [])]
    if jv:
        if "maven" in fw:
            cmds.append("mvn -q -Dtest=%s test" % ",".join(jv))
        else:
            cmds.append("gradle test -q " + " ".join("--tests '*%s'" % c for c in jv))
    cs = [split(t)[1] for t in by_ext.get("cs", [])]
    if cs:
        cmds.append('dotnet test -v q --nologo --filter "%s"' % "|".join("FullyQualifiedName~" + c for c in cs))
    rb = by_ext.get("rb", [])
    if rb:
        cmds.append(("bundle exec rspec " if "rspec" in fw else "bundle exec ruby -Itest ") + " ".join(rb))
    ex = by_ext.get("exs", [])
    if ex:
        cmds.append("mix test " + " ".join(ex))
    dart = by_ext.get("dart", [])
    if dart:
        cmds.append("dart test " + " ".join(dart))
    php = by_ext.get("php", [])
    if php:
        cmds.append("vendor/bin/phpunit " + " ".join(php))
    if rust:
        cmds.append("cargo test -q  (narrow with -p <crate> or a test-name filter)")
    return cmds


def main(argv=None):
    ap = argparse.ArgumentParser(prog="affected_tests.py", description=__doc__.split("\n")[1])
    ap.add_argument("--base", help="compare against this ref (branch/sha), e.g. main or origin/main")
    ap.add_argument("--files", nargs="+", help="explicit changed files instead of git")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args(argv)
    root = root_dir()
    if args.files:
        changed = sorted({os.path.relpath(os.path.abspath(f), root).replace(os.sep, "/") for f in args.files})
    else:
        changed = [f for f in changed_files(root, args.base) if not f.startswith(".codemap/")]
    if not changed:
        print("affected_tests: no changed files (use --base REF or --files)")
        return 0
    hits, go_pkgs, rust = find_tests(root, changed, all_files(root))
    fw = detect(root)
    cmds = commands(root, hits, go_pkgs, rust, fw)
    if args.json:
        print(json.dumps({"changed": changed, "tests": hits, "go_packages": go_pkgs, "commands": cmds}, indent=1))
        return 0
    print("changed: %d file(s): %s%s" % (len(changed), " ".join(changed[:12]), " …" if len(changed) > 12 else ""))
    if hits:
        print("tests (%d):" % len(hits))
        for t in sorted(hits)[:40]:
            print("  %s  (%s)" % (t, hits[t]))
        if len(hits) > 40:
            print("  … %d more" % (len(hits) - 40))
    if cmds:
        print("run first:")
        for c in cmds:
            print("  " + c)
    else:
        print("no mapped tests found -> run the nearest package/module test suite, then the full suite before finishing")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:
        sys.exit(0)
