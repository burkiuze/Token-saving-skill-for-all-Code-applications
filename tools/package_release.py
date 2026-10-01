#!/usr/bin/env python3
"""Create a deterministic ZIP from Git-tracked source with SHA-256 inventory."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skills/token-saver/scripts'))
from ts_io import VERSION, eligible, safe_path, secret_path


def git(*args):
    result = subprocess.run(['git', '-C', str(ROOT)] + list(args), capture_output=True, timeout=30)
    if result.returncode:
        raise ValueError('release packaging requires a Git checkout')
    return result.stdout


def build(output, allow_dirty=False):
    if not allow_dirty and git('status', '--porcelain'):
        raise ValueError('commit the source changes before packaging, or explicitly use --allow-dirty')
    records = []
    for item in git('ls-files', '--stage', '-z').split(b'\0'):
        if not item:
            continue
        metadata, raw_path = item.split(b'\t', 1)
        mode = metadata.split()[0].decode()
        rel = os.fsdecode(raw_path)
        if mode not in ('100644', '100755') or secret_path(rel) or any(part in ('.git', '.codemap', '.token-saver-state', '__pycache__') for part in Path(rel).parts) or rel.endswith(('.pyc', '.zip')):
            raise ValueError('unexpected generated/credential/symlink path in release index: ' + rel)
        data = safe_path(ROOT, rel).read_bytes()
        records.append((rel, mode, data))
    records.sort(key=lambda row: row[0])
    inventory = {'release': VERSION, 'source_commit': git('rev-parse', 'HEAD').decode().strip(),
                 'files': [{'path': rel, 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data), 'mode': mode}
                           for rel, mode, data in records]}
    manifest = (json.dumps(inventory, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    prefix = 'Token-Saver-Skills-' + VERSION + '/'
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for rel, mode, data in records + [('RELEASE-MANIFEST.json', '100644', manifest)]:
            info = zipfile.ZipInfo(prefix + rel, date_time=(2020, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = (int(mode, 8) << 16)
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data, compresslevel=9)
    checksum = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix('.sha256').write_text(checksum + '  ' + output.name + '\n', encoding='utf-8')
    return {'file': str(output), 'files': len(records) + 1, 'bytes': output.stat().st_size, 'sha256': checksum}


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', required=True)
    ap.add_argument('--allow-dirty', action='store_true')
    args = ap.parse_args()
    try:
        print(json.dumps(build(args.output, args.allow_dirty), indent=2))
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print('package: ' + str(error), file=sys.stderr)
        sys.exit(2)
