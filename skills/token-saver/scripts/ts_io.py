"""Bounded local I/O shared by the Token Saver toolkit; Python 3.8+, stdlib only."""
import fnmatch
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import tempfile

VERSION = "2.0.0"
SKIP_DIRS = {".git", ".codemap", ".token-saver-state", "node_modules", "vendor", "dist",
             "build", "target", "coverage", "__pycache__", ".venv", "venv", ".next"}
SKIP_FILES = {"package-lock.json", "yarn.lock", "pnpm-lock.yaml", "Cargo.lock",
              "poetry.lock", "Pipfile.lock", "composer.lock", "Gemfile.lock", "go.sum",
              "uv.lock", "bun.lockb"}
SKIP_SUFFIXES = (".min.js", ".min.css", ".map", ".lock", ".snap", ".pyc", ".zip",
                 ".png", ".jpg", ".jpeg", ".pdf", ".woff", ".wasm", ".exe")
SECRET_NAMES = {".env", ".npmrc", ".pypirc", "credentials", "credentials.json",
                "secrets.json", "secrets.yaml", "secrets.yml", "id_rsa", "id_ed25519"}
ASSIGNMENT = re.compile(
    r"(?i)(\b(?:api[_-]?key|access[_-]?token|refresh[_-]?token|secret|password|"
    r"authorization)\b[\"']?\s*[:=]\s*[\"']?)([^\s\"',;<>]{4,})")
BEARER = re.compile(r"(?i)\b(Bearer\s+)[A-Za-z0-9._~+/-]{8,}")
PROVIDER_KEY = re.compile(r"\b(?:sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|"
                          r"github_pat_[A-Za-z0-9_]{20,}|AKIA[A-Z0-9]{16})\b")
PRIVATE_KEY = re.compile(r"-----BEGIN [^-]*PRIVATE KEY-----.*?-----END [^-]*PRIVATE KEY-----", re.S)
CONFIG_DEFAULT = {"budget": 2000, "max_file_bytes": 500000, "max_files": 3000,
                  "max_snippets": 12, "context_lines": 4, "exclude": [],
                  "priority_paths": ["src/", "lib/", "app/", "tests/"]}


def run_git(root, *args, required=False):
    try:
        result = subprocess.run(["git", "-C", str(root)] + list(args), stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, timeout=30)
        if result.returncode == 0:
            return result.stdout
    except (OSError, subprocess.SubprocessError):
        pass
    if required:
        raise ValueError("Git operation failed; check the repository and reference")
    return None


def project_root(start=None):
    path = Path(start or os.getcwd()).resolve()
    if not path.is_dir():
        raise ValueError("project directory does not exist")
    output = run_git(path, "rev-parse", "--show-toplevel")
    return Path(os.fsdecode(output).strip()).resolve() if output else path


def secret_path(rel):
    name = Path(rel).name.lower()
    return (name in SECRET_NAMES or name.endswith((".pem", ".key", ".p12", ".pfx"))
            or (name.startswith(".env.") and not name.endswith(("example", "sample", "template"))))


def eligible(rel, excludes=()):
    parts = Path(rel).parts
    return (not secret_path(rel) and not any(p in SKIP_DIRS for p in parts)
            and Path(rel).name not in SKIP_FILES and not str(rel).lower().endswith(SKIP_SUFFIXES)
            and not any(fnmatch.fnmatchcase(str(rel).replace(os.sep, "/"), p) for p in excludes))


def safe_path(root, rel):
    """Refuse escape paths and symlinks, including symlinked parent directories."""
    root = Path(root).resolve()
    path = Path(os.path.abspath(str(root / rel)))
    try:
        relative = path.relative_to(root)
    except ValueError:
        raise ValueError("path is outside the project")
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("symlink paths are not supported")
    return path


def list_files(root, limit=3000, excludes=(), prefixes=()):
    output = run_git(root, "ls-files", "-z", "--cached", "--others", "--exclude-standard")
    if output is not None:
        rels = sorted(set(os.fsdecode(x) for x in output.split(b"\0") if x))
    else:
        if Path(root).resolve() in (Path.home().resolve(), Path(Path(root).anchor)):
            raise ValueError("choose a project directory, not a home or filesystem root")
        rels = []
        for directory, dirs, files in os.walk(root, followlinks=False):
            dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")
                             and not Path(directory, d).is_symlink())
            for name in sorted(files):
                rels.append(Path(directory, name).relative_to(root).as_posix())
                if len(rels) > limit * 4:
                    raise ValueError("non-Git project exceeds scan limit; narrow the project")
        rels.sort()
    result = []
    omitted = 0
    for rel in rels:
        if prefixes and not any(prefix == "." or rel == prefix or rel.startswith(prefix.rstrip("/") + "/")
                                for prefix in prefixes):
            continue
        if not eligible(rel, excludes):
            continue
        try:
            if not safe_path(root, rel).is_file():
                continue
        except ValueError:
            continue
        if len(result) < limit:
            result.append(rel)
        else:
            omitted += 1
    return result, omitted


def read_text(root, rel, max_bytes=500000):
    if secret_path(rel):
        raise ValueError("credential files are excluded")
    path = safe_path(root, rel)
    if path.stat().st_size > max_bytes:
        raise ValueError("file exceeds the configured byte limit")
    with path.open("rb") as handle:
        data = handle.read(max_bytes + 1)
    if len(data) > max_bytes or b"\0" in data:
        raise ValueError("binary or oversized file")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        raise ValueError("file is not UTF-8 text")


def redact(text):
    text = PRIVATE_KEY.sub(lambda match: "\n".join("[REDACTED PRIVATE KEY]"
                           for _ in match.group().split("\n")), text)
    text = PROVIDER_KEY.sub("[REDACTED KEY]", text)
    text = BEARER.sub(r"\1[REDACTED]", text)
    return ASSIGNMENT.sub(r"\1[REDACTED]", text)


def estimate(text):
    """UTF-8 byte / 4 heuristic, never a billed or tokenizer-exact count."""
    return math.ceil(len(text.encode("utf-8")) / 4)


def fingerprint(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def atomic_write(path, text, mode=0o600):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".token-saver-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def state_path(root, name):
    path = safe_path(root, ".codemap/" + name)
    path.parent.mkdir(parents=True, exist_ok=True)
    ignore = safe_path(root, ".codemap/.gitignore")
    if not ignore.exists():
        atomic_write(ignore, "# Token Saver local state; opt in to sharing notes explicitly\n*\n!.gitignore\n")
    return path


def load_config(root):
    config = dict(CONFIG_DEFAULT)
    path = safe_path(root, ".token-saver.json")
    if path.exists():
        data = json.loads(read_text(root, ".token-saver.json", 20000))
        if not isinstance(data, dict) or set(data) - set(config):
            raise ValueError("unknown configuration field or non-object configuration")
        config.update(data)
    for key in ("budget", "max_file_bytes", "max_files", "max_snippets", "context_lines"):
        if type(config[key]) is not int or config[key] < (0 if key == "context_lines" else 1):
            raise ValueError("configuration %s must be a valid nonnegative/positive integer" % key)
    for key in ("exclude", "priority_paths"):
        if not isinstance(config[key], list) or not all(isinstance(s, str) for s in config[key]):
            raise ValueError("configuration %s must be a list of strings" % key)
    return config
