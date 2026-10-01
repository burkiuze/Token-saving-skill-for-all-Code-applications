#!/usr/bin/env python3
"""Cross-platform, manifest-based installation without deleting unrelated skills."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import time

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / 'skills/token-saver/scripts'))
from ts_io import VERSION, atomic_write

TOOLS = ('claude', 'codex', 'opencode', 'zcode', 'gemini', 'cursor', 'copilot')
PROFILES = {
    'minimal': ['token-saver', 'smart-read', 'quiet-run', 'context-pack', 'token-budget'],
    'balanced': ['token-saver', 'task-triage', 'repo-map', 'smart-read', 'quiet-run',
                 'context-pack', 'diff-review', 'test-impact', 'session-memory', 'token-budget'],
    'full': sorted(p.name for p in (REPO / 'skills').iterdir() if (p / 'SKILL.md').is_file()),
}
START = '<!-- token-saver:start'
END = '<!-- token-saver:end -->'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def safe_target(path, leaf_link=False):
    path = Path(os.path.abspath(str(path)))
    for candidate in [path] + list(path.parents):
        if candidate.is_symlink() and not (leaf_link and candidate == path):
            raise ValueError('symlink destination refused: %s' % path)
    return path


def snapshot(path):
    if path.is_symlink():
        return {'kind': 'link', 'target': os.readlink(str(path))}
    if not path.is_dir():
        return None
    entries = {}
    for current, dirs, files in os.walk(path, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d != '__pycache__')
        for name in dirs + sorted(f for f in files if not f.endswith('.pyc')):
            item = Path(current) / name
            rel = item.relative_to(path).as_posix()
            if item.is_symlink():
                entries[rel] = 'link:' + os.readlink(str(item))
            elif item.is_dir():
                entries[rel + '/'] = 'directory'
            else:
                entries[rel] = digest(item.read_bytes())
    return {'kind': 'copy', 'entries': entries}


def read_rule(path):
    if path.exists() and not path.is_file():
        raise ValueError('rule destination is not a file: %s' % path)
    return path.read_bytes().decode('utf-8') if path.exists() else ''


def block_span(text):
    starts = list(re.finditer(r'^<!-- token-saver:start[^\r\n]*-->(?:\r?\n)?', text, re.M))
    ends = list(re.finditer(r'^<!-- token-saver:end -->(?:\r?\n)?', text, re.M))
    if not starts and not ends:
        return None
    if len(starts) != 1 or len(ends) != 1 or starts[0].end() > ends[0].start():
        raise ValueError('invalid or duplicated managed rule markers; fix them before installation')
    return starts[0].start(), ends[0].end()


def rule_text(skills_ref, selected):
    text = (REPO / 'rules/token-saver-block.md').read_text(encoding='utf-8')
    extra = ('Map only when orientation is needed: `python3 %s/repo-map/scripts/repomap.py build`.\n'
             % skills_ref) if 'repo-map' in selected else ''
    text = text.replace('{{SKILLS_DIR}}', skills_ref).replace('{{PY}}', 'python' if os.name == 'nt' else 'python3')
    return text.replace(END, extra + END)


def plan_for(args):
    home = Path.home().resolve()
    project = Path(args.project).expanduser().resolve() if args.project else None
    if project and not project.is_dir():
        raise ValueError('--project must be an existing directory')
    base = project or home
    if args.tools:
        tools = args.tools.replace(',', ' ').split()
        if tools == ['all']:
            tools = list(TOOLS)
    elif project:
        tools = list(TOOLS)
    else:
        config = Path(os.environ.get('XDG_CONFIG_HOME', str(home / '.config')))
        probes = {'claude': home / '.claude', 'codex': Path(os.environ.get('CODEX_HOME', str(home / '.codex'))),
                  'opencode': config / 'opencode', 'zcode': home / '.zcode', 'gemini': home / '.gemini',
                  'cursor': home / '.cursor', 'copilot': home / '.copilot'}
        tools = [name for name in TOOLS if probes[name].is_dir() or shutil.which(name)]
        if not tools:
            tools = ['claude', 'codex']
    if not tools or set(tools) - set(TOOLS):
        raise ValueError('choose tools from: ' + ','.join(TOOLS))
    selected = args.skills.split(',') if args.skills else list(PROFILES[args.profile])
    selected = sorted(set(['token-saver'] + [s.strip() for s in selected if s.strip()]))
    if set(selected) - set(PROFILES['full']):
        raise ValueError('unknown skill name in --skills')
    destinations, rules, notes = {}, {}, []
    for tool in tools:
        skill_root = base / ('.claude/skills' if tool == 'claude' else '.agents/skills')
        ref = skill_root.relative_to(base).as_posix() if project else '~/' + skill_root.relative_to(home).as_posix()
        for name in selected:
            destinations[str(skill_root / name)] = name
        rule = None
        if project:
            rule = base / {'claude': 'CLAUDE.md', 'gemini': 'GEMINI.md',
                           'copilot': '.github/copilot-instructions.md'}.get(tool, 'AGENTS.md')
        else:
            config = Path(os.environ.get('XDG_CONFIG_HOME', str(home / '.config')))
            rule = {'claude': home / '.claude/CLAUDE.md',
                    'codex': Path(os.environ.get('CODEX_HOME', str(home / '.codex'))) / 'AGENTS.md',
                    'opencode': config / 'opencode/AGENTS.md',
                    'gemini': home / '.gemini/GEMINI.md',
                    'copilot': home / '.copilot/copilot-instructions.md'}.get(tool)
        if tool == 'cursor' and not project:
            notes.append('Cursor global rules are configured in its UI; project AGENTS.md is supported.')
        if tool == 'zcode':
            notes.append('ZCode uses the portable .agents copy; automatic discovery is unverified. Load SKILL.md explicitly if needed.')
            if not project:
                rule = None
        if rule and not args.no_rules:
            rules[str(rule)] = rule_text(ref, selected)
    state = base / '.token-saver-state'
    return destinations, rules, state, notes


def load_manifest(path):
    if not path.exists():
        return {'version': 1, 'skills': {}, 'rules': {}}
    data = json.loads(path.read_text(encoding='utf-8'))
    if data.get('version') != 1 or not isinstance(data.get('skills'), dict) or not isinstance(data.get('rules'), dict):
        raise ValueError('unsupported or corrupt installation manifest')
    return data


def backup(path, state):
    if not path.exists() and not path.is_symlink():
        return None
    directory = state / 'backups' / (time.strftime('%Y%m%d-%H%M%S') + '-' + str(time.time_ns()))
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / path.name
    if path.is_symlink():
        target.symlink_to(os.readlink(str(path)), target_is_directory=True)
    elif path.is_dir():
        shutil.copytree(str(path), str(target), symlinks=True)
    else:
        shutil.copy2(str(path), str(target))
    return str(target)


def replace_skill(source, target, link):
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix='.token-saver-', dir=str(target.parent)))
    staged = temporary / target.name
    old = temporary / 'previous'
    try:
        if link:
            staged.symlink_to(source, target_is_directory=True)
        else:
            shutil.copytree(str(source), str(staged), ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        if target.exists() or target.is_symlink():
            os.replace(str(target), str(old))
        try:
            os.replace(str(staged), str(target))
        except OSError:
            if old.exists() or old.is_symlink():
                os.replace(str(old), str(target))
            raise
    finally:
        shutil.rmtree(str(temporary), ignore_errors=True)


def perform(args):
    skills, rules, state, notes = plan_for(args)
    state = safe_target(state)
    manifest_path = safe_target(state / 'manifest.json')
    manifest = load_manifest(manifest_path)
    if args.uninstall:
        # Remove all managed skills in selected tool roots, regardless of the
        # profile used on a later uninstall invocation.
        selected_roots = {str(Path(raw).parent) for raw in skills}
        skills = {raw: record['name'] for raw, record in manifest['skills'].items()
                  if str(Path(raw).parent) in selected_roots}
    if args.doctor:
        problems = []
        for raw, record in manifest['skills'].items():
            path = safe_target(raw, leaf_link=True)
            if snapshot(path) != record['snapshot']:
                problems.append('missing or locally modified: ' + raw)
        for raw, record in manifest['rules'].items():
            text = read_rule(safe_target(raw))
            span = block_span(text)
            if span is None or digest(text[span[0]:span[1]].encode('utf-8')) != record['hash']:
                problems.append('missing or modified rules block: ' + raw)
        print(json.dumps({'version': VERSION, 'managed_skills': len(manifest['skills']),
                          'managed_rules': len(manifest['rules']), 'problems': problems, 'notes': notes}, indent=2))
        return 1 if problems else 0

    actions, conflicts = [], []
    for raw, name in skills.items():
        path = safe_target(raw, leaf_link=True)
        record = manifest['skills'].get(raw)
        current = snapshot(path)
        if args.uninstall:
            if not record:
                continue
            if current is not None and current != record['snapshot'] and not args.force:
                conflicts.append('locally modified managed skill: ' + raw)
            actions.append(('remove-skill', path, None))
        else:
            exists = path.exists() or path.is_symlink()
            if exists and (not record or current != record['snapshot']) and not args.force:
                conflicts.append('unmanaged or locally modified skill: ' + raw)
            actions.append(('install-skill', path, name))
    if not args.uninstall:
        selected_roots = {str(Path(raw).parent) for raw in skills}
        for raw, record in manifest['skills'].items():
            if str(Path(raw).parent) not in selected_roots or raw in skills:
                continue
            path = safe_target(raw, leaf_link=True)
            current = snapshot(path)
            if current is not None and current != record['snapshot'] and not args.force:
                conflicts.append('locally modified skill excluded by new profile: ' + raw)
            actions.append(('remove-skill', path, None))
    for raw, block in rules.items():
        path = safe_target(raw)
        text = read_rule(path)
        span = block_span(text)
        record = manifest['rules'].get(raw)
        if args.uninstall:
            if not record:
                continue
            if span and digest(text[span[0]:span[1]].encode('utf-8')) != record['hash'] and not args.force:
                conflicts.append('locally modified managed rules: ' + raw)
            actions.append(('remove-rule', path, None))
        else:
            if span and (not record or digest(text[span[0]:span[1]].encode('utf-8')) != record['hash']) and not args.force:
                conflicts.append('unmanaged or locally modified rules block: ' + raw)
            actions.append(('install-rule', path, block))
    if conflicts:
        raise ValueError('\n'.join(conflicts) + '\nUse --force to back up conflicting content before replacement.')
    if args.link and os.name == 'nt':
        raise ValueError('--link on Windows requires symlink privileges; use the default copy installation')
    print('Token Saver %s: %s (%s)' % (VERSION, 'uninstall' if args.uninstall else 'install', args.profile))
    for action, path, _ in actions:
        print('  %s%s -> %s' % ('[dry-run] ' if args.dry_run else '', action, path))
    for note in notes:
        print('  note: ' + note)
    if args.dry_run:
        return 0
    if not actions:
        print('No managed files matched; nothing changed.')
        return 0
    state.mkdir(parents=True, exist_ok=True)
    ignore = state / '.gitignore'
    if not ignore.exists():
        atomic_write(ignore, '*\n!.gitignore\n')
    # Checkpoint each operation; repeat or uninstall a partial run safely.
    for action, path, payload in actions:
        raw = str(path)
        saved_backup = backup(path, state) if args.force else None
        if action == 'install-skill':
            replace_skill(REPO / 'skills' / payload, path, args.link)
            record = {'name': payload, 'snapshot': snapshot(path)}
            if saved_backup:
                record['backup'] = saved_backup
            manifest['skills'][raw] = record
        elif action == 'remove-skill':
            if path.is_symlink() or path.is_file():
                path.unlink()
            elif path.is_dir():
                shutil.rmtree(str(path))
            manifest['skills'].pop(raw, None)
        elif action == 'install-rule':
            original = read_rule(path)
            newline = '\r\n' if '\r\n' in original else '\n'
            block = payload.replace('\r\n', '\n').replace('\n', newline)
            span = block_span(original)
            old = manifest['rules'].get(raw, {})
            separator = old.get('separator', '') if span else (newline if original else '')
            updated = original[:span[0]] + block + original[span[1]:] if span else original + separator + block
            mode = path.stat().st_mode & 0o777 if path.exists() else 0o644
            atomic_write(path, updated, mode)
            record = {'hash': digest(block.encode('utf-8')), 'separator': separator}
            if saved_backup:
                record['backup'] = saved_backup
            manifest['rules'][raw] = record
        else:
            original = read_rule(path)
            span = block_span(original)
            if span:
                start, end = span
                separator = manifest['rules'][raw].get('separator', '')
                if separator and original[:start].endswith(separator):
                    start -= len(separator)
                updated = original[:start] + original[end:]
                if updated:
                    atomic_write(path, updated, path.stat().st_mode & 0o777)
                else:
                    path.unlink()
            manifest['rules'].pop(raw, None)
        manifest['release'] = VERSION
        atomic_write(manifest_path, json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print('Done. Reload the tool\'s skill list if it is cached; backups remain in .token-saver-state/backups.')
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--project')
    ap.add_argument('--tools', help='comma-separated tools or all')
    ap.add_argument('--profile', choices=tuple(PROFILES), default='balanced')
    ap.add_argument('--skills', help='explicit skill names; token-saver is always included')
    for option in ('no-rules', 'link', 'uninstall', 'dry-run', 'doctor', 'force'):
        ap.add_argument('--' + option, action='store_true')
    args = ap.parse_args(argv)
    if sys.version_info < (3, 8):
        ap.error('Python 3.8+ required')
    return perform(args)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, TypeError) as error:
        print('install: ' + str(error), file=sys.stderr)
        sys.exit(2)
