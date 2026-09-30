"""Tests for repomap.py, quiet_run.py and install.sh.  Run: python3 -m unittest discover tests"""

import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPOMAP = os.path.join(ROOT, "skills", "repo-map", "scripts", "repomap.py")
QUIET = os.path.join(ROOT, "skills", "quiet-run", "scripts", "quiet_run.py")

FIXTURES = {
    "src/server.ts": """
        import x from "y";
        export interface Req { id: string }
        export type Handler = (r: Req) => void;
        export class Router {
          private routes = [];
          constructor(private base: string) {}
          get(path: string, h: Handler) {
            if (path) { return this; }
          }
          handleClick = async (e) => { return e; };
        }
        export function createServer(port: number) {
          function inner() {}
          return inner;
        }
        export const makeApp = (opts) => new Router(opts);
        app.use = function use(fn) {};
        """,
    "pkg/svc.py": """
        import os

        class Service:
            def __init__(self, db):
                self.db = db

            async def fetch(self, key):
                def helper():
                    pass
                return key

        def main():
            pass
        """,
    "go/tree.go": """
        package tree

        type Node struct {
            path string
        }

        func (n *Node) AddRoute(path string) {
        }

        func NewNode() *Node { return &Node{} }
        """,
    "rs/lib.rs": """
        pub struct Config { a: u8 }
        impl<'a> Default for Config<'a> {
            fn default() -> Self { Config { a: 0 } }
        }
        pub fn run() {}
        """,
    "java/Owner.java": """
        package x;
        public class Owner extends Person {
            private String city;
            public Owner(String c) { this.city = c; }
            public String getCity() {
                return this.city;
            }
        }
        """,
    "tests/test_svc.py": """
        def test_fetch():
            assert True
        """,
    "package-lock.json": "{}",
    "README.md": "# Demo\n\n## Usage\n\n```\n# not a heading\n```\n",
    "logo.png": "\x89PNG",
}


def run(args, cwd, check=True):
    r = subprocess.run([sys.executable] + args, cwd=cwd, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, universal_newlines=True)
    if check and r.returncode != 0:
        raise AssertionError("exit %d: %s" % (r.returncode, r.stdout))
    return r


class RepoMapTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        for rel, body in FIXTURES.items():
            path = os.path.join(self.dir, rel)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(textwrap.dedent(body).lstrip("\n"))
        subprocess.run(["git", "init", "-q"], cwd=self.dir, check=True)
        subprocess.run(["git", "add", "-A"], cwd=self.dir, check=True)

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def map_text(self):
        with open(os.path.join(self.dir, ".codemap", "MAP.md"), encoding="utf-8") as fh:
            return fh.read()

    def test_build_extracts_symbols(self):
        out = run([REPOMAP, "build"], self.dir).stdout
        self.assertIn("repomap:", out)
        m = self.map_text()
        for expected in ("iface Req:2", "type Handler:3", "class Router:4{", "get:7",
                         "handleClick:10", "createServer:12", "makeApp:16", "app.{use:17}",
                         "class Service:3{__init__:4 fetch:7}", "main:12",
                         "type Node:3{AddRoute:7}", "NewNode:10",
                         "struct Config:1", "impl Default for Config:2{default:3}", "run:5",
                         "class Owner:2{Owner:4 getCity:5}", "# Demo:1", "## Usage:3"):
            self.assertIn(expected, m)
        self.assertNotIn("inner", m)          # nested function inside a function body
        self.assertNotIn("helper", m)
        self.assertNotIn("not a heading", m)  # inside a code fence
        self.assertNotIn("package-lock", m)   # lockfiles skipped
        self.assertIn("assets: 1", m)
        self.assertIn("test_svc.py 2L [test", m)

    def test_incremental_status_find_outline_show(self):
        run([REPOMAP, "build"], self.dir)
        self.assertIn("up to date", run([REPOMAP, "status"], self.dir).stdout)
        with open(os.path.join(self.dir, "pkg", "svc.py"), "a", encoding="utf-8") as fh:
            fh.write("\ndef added_later():\n    pass\n")
        st = run([REPOMAP, "status"], self.dir).stdout
        self.assertIn("modified (1): pkg/svc.py", st)
        self.assertIn("re-parsed 1,", run([REPOMAP, "build"], self.dir).stdout)
        self.assertIn("added_later", self.map_text())
        self.assertEqual("", run([REPOMAP, "build", "--quiet"], self.dir).stdout)
        found = run([REPOMAP, "find", "^AddRoute$"], self.dir).stdout
        self.assertIn("go/tree.go:7 fn Node.AddRoute", found)
        self.assertIn("src/server.ts:7 method Router.get", run([REPOMAP, "find", "^get$"], self.dir).stdout)
        self.assertEqual(1, run([REPOMAP, "find", "zzz_nothing"], self.dir, check=False).returncode)
        outline = run([REPOMAP, "outline", "pkg/svc.py"], self.dir).stdout
        self.assertIn("    3 class Service", outline)
        self.assertIn("      7 fetch", outline)
        shown = run([REPOMAP, "show", "go/"], self.dir).stdout
        self.assertIn("### go/", shown)
        self.assertNotIn("### pkg/", shown)
        os.remove(os.path.join(self.dir, "rs", "lib.rs"))
        self.assertIn("removed 1", run([REPOMAP, "build"], self.dir).stdout)

    def test_gitignore_created(self):
        run([REPOMAP, "build"], self.dir)
        with open(os.path.join(self.dir, ".codemap", ".gitignore"), encoding="utf-8") as fh:
            self.assertIn("!NOTES.md", fh.read())
        st = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=self.dir,
                            stdout=subprocess.PIPE, universal_newlines=True).stdout
        self.assertNotIn("MAP.md", st)
        self.assertNotIn("cache.json", st)


class QuietRunTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_failure_is_summarized(self):
        script = os.path.join(self.dir, "noisy.py")
        with open(script, "w", encoding="utf-8") as fh:
            fh.write(textwrap.dedent("""
                import sys
                for i in range(2000): print("test_%d PASSED" % i)
                print("Traceback (most recent call last):")
                print("ValueError: boom")
                for i in range(300): print("test_x_%d PASSED" % i)
                print("== 2299 passed, 1 failed ==")
                sys.exit(3)
                """))
        r = run([QUIET, "--", sys.executable, script], self.dir, check=False)
        self.assertEqual(3, r.returncode)
        lines = r.stdout.splitlines()
        self.assertLess(len(lines), 25)
        self.assertTrue(lines[0].startswith("exit=3"))
        self.assertIn("ValueError: boom", r.stdout)
        self.assertIn("1 failed", r.stdout)
        with open(os.path.join(self.dir, ".codemap", "logs", "last.log"), encoding="utf-8") as fh:
            self.assertEqual(2303, len(fh.read().splitlines()))

    def test_success_prints_tail_only(self):
        r = run([QUIET, "--lines", "20", "--", sys.executable, "-c",
                 "print('\\n'.join(str(i) for i in range(500)))"], self.dir)
        self.assertEqual(0, r.returncode)
        self.assertIn("499", r.stdout)
        self.assertNotIn("\n5\n", r.stdout)
        self.assertLess(len(r.stdout.splitlines()), 20)


@unittest.skipIf(os.name == "nt" or not shutil.which("bash"), "bash installer test")
class InstallerTest(unittest.TestCase):
    def test_install_is_idempotent_and_uninstalls(self):
        home = tempfile.mkdtemp()
        try:
            os.makedirs(os.path.join(home, ".claude"))
            os.makedirs(os.path.join(home, ".codex"))
            claude_md = os.path.join(home, ".claude", "CLAUDE.md")
            with open(claude_md, "w") as fh:
                fh.write("# mine\n")
            env = dict(os.environ, HOME=home, PATH="/usr/bin:/bin")
            env.pop("CODEX_HOME", None)
            env.pop("XDG_CONFIG_HOME", None)
            for _ in range(2):
                subprocess.run(["bash", os.path.join(ROOT, "install.sh")], env=env, check=True,
                               stdout=subprocess.DEVNULL)
            with open(claude_md) as fh:
                text = fh.read()
            self.assertEqual(1, text.count("token-saver:start"))
            self.assertIn("~/.claude/skills/repo-map/scripts/repomap.py", text)
            self.assertTrue(os.path.isfile(os.path.join(home, ".agents", "skills", "repo-map", "SKILL.md")))
            self.assertTrue(os.path.isfile(os.path.join(home, ".codex", "AGENTS.md")))
            subprocess.run(["bash", os.path.join(ROOT, "install.sh"), "--uninstall"], env=env, check=True,
                           stdout=subprocess.DEVNULL)
            with open(claude_md) as fh:
                self.assertEqual("# mine\n", fh.read())
            self.assertFalse(os.path.exists(os.path.join(home, ".codex", "AGENTS.md")))
            self.assertFalse(os.path.exists(os.path.join(home, ".claude", "skills", "token-saver")))
        finally:
            shutil.rmtree(home, ignore_errors=True)


class SkillFormatTest(unittest.TestCase):
    def test_frontmatter(self):
        skills_dir = os.path.join(ROOT, "skills")
        for name in sorted(os.listdir(skills_dir)):
            with open(os.path.join(skills_dir, name, "SKILL.md"), encoding="utf-8") as fh:
                text = fh.read()
            self.assertTrue(text.startswith("---\nname: %s\ndescription: " % name), name)
            desc = text.split("description: ", 1)[1].split("\n", 1)[0]
            self.assertLessEqual(len(desc), 1024, name)
            self.assertLess(len(text.splitlines()), 120, name)


if __name__ == "__main__":
    unittest.main()
