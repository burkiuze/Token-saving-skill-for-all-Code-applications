#!/usr/bin/env python3
"""Dependency-free validation for this portable skill repository."""
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]


def validate(root=ROOT):
    errors = []
    folders = sorted((root / 'skills').iterdir())
    names = []
    for folder in folders:
        if not folder.is_dir():
            continue
        skill = folder / 'SKILL.md'
        if not skill.is_file():
            errors.append(str(folder) + ': missing SKILL.md')
            continue
        text = skill.read_text(encoding='utf-8')
        match = re.match(r'^---\nname: ([a-z0-9-]{1,64})\ndescription: ([^\n]+)\n---\n', text)
        if not match:
            errors.append(folder.name + ': invalid portable frontmatter')
            continue
        name, description = match.groups()
        names.append(name)
        if name != folder.name or len(description) > 1024:
            errors.append(folder.name + ': name mismatch or oversized description')
        if len(text.splitlines()) > 120 or '[TODO' in text:
            errors.append(folder.name + ': oversized body or unfinished placeholder')
        for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', text):
            if not target.startswith(('https://', 'http://', '#')) and not (folder / target.split('#')[0]).exists():
                errors.append(folder.name + ': missing reference ' + target)
        metadata = folder / 'agents/openai.yaml'
        if not metadata.is_file():
            errors.append(folder.name + ': missing UI metadata')
            continue
        ui = {}
        try:
            for key, value in re.findall(r'^  (display_name|short_description|default_prompt): (.+)$', metadata.read_text(), re.M):
                ui[key] = json.loads(value)
            if not 25 <= len(ui['short_description']) <= 64 or '$' + name not in ui['default_prompt'] or not ui['display_name']:
                raise ValueError('invalid metadata')
        except (ValueError, KeyError):
            errors.append(folder.name + ': invalid UI metadata')
    if len(names) != len(set(names)):
        errors.append('duplicate skill names')
    return names, errors


if __name__ == '__main__':
    names, errors = validate()
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        sys.exit(1)
    print('Validated %d skills: portable frontmatter, references, metadata, no placeholders.' % len(names))
