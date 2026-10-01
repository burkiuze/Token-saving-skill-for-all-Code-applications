#!/usr/bin/env python3
"""Reproducible synthetic CONTENT-SIZE benchmark; never a provider-spend claim."""
import argparse
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
TOOLKIT = ROOT / 'skills/token-saver/scripts/token_saver.py'
QUIET = ROOT / 'skills/quiet-run/scripts/quiet_run.py'


def estimate_bytes(size):
    return math.ceil(size / 4)


def benchmark():
    with tempfile.TemporaryDirectory() as temporary:
        project = Path(temporary).resolve()
        source = project / 'src'
        source.mkdir()
        for index in range(40):
            body = ''.join('def transform_%d_%d(value):\n    interim = value + %d\n    return interim * 2\n\n' % (index, n, n)
                           for n in range(100))
            (source / ('module_%02d.py' % index)).write_text(body, encoding='utf-8')
        (source / 'auth.py').write_text('def refresh_expired_token(token, now):\n    if token.expiry <= now:\n        return "renew"\n    return "keep"\n', encoding='utf-8')
        subprocess.run(['git', 'init', '-q', str(project)], check=True, capture_output=True)
        raw_bytes = sum(path.stat().st_size for path in source.glob('*.py'))
        result = subprocess.run([sys.executable, str(TOOLKIT), 'pack', 'refresh_expired_token', '--json', '--budget', '1800'],
                                cwd=str(project), check=True, capture_output=True)
        packet = json.loads(result.stdout)
        relevant = next((item for item in packet['snippets'] if item['path'] == 'src/auth.py'), None)
        if relevant is None or not relevant['complete_symbol'] or 'return "keep"' not in relevant['text']:
            raise ValueError('benchmark failed its retrieval acceptance check')
        script = 'for i in range(2000): print("test_%d PASSED" % i)\nprint("Traceback: error location")\nprint("ValueError: benchmark_failure")\nprint("2000 passed, 1 failed")\nraise SystemExit(3)\n'
        command = subprocess.run([sys.executable, str(QUIET), '--', sys.executable, '-c', script],
                                  cwd=str(project), capture_output=True)
        if command.returncode != 3 or b'benchmark_failure' not in command.stdout or b'1 failed' not in command.stdout:
            raise ValueError('benchmark failed its diagnostic acceptance check')
        raw_log_bytes = (project / '.codemap/logs/last.log').stat().st_size
        return {'method': 'Synthetic content-size benchmark; UTF-8 bytes / 4 heuristic, not billed tokens or total task savings',
                'fixture': {'source_files': 41, 'noise_functions': 4000, 'noisy_log_lines': 2003},
                'context_pack': {'baseline_source_bytes': raw_bytes, 'packet_bytes': len(result.stdout),
                                 'baseline_estimated_tokens': estimate_bytes(raw_bytes),
                                 'packet_estimated_tokens': estimate_bytes(len(result.stdout)),
                                 'target_complete': True, 'budget': 1800},
                'quiet_run': {'raw_log_bytes': raw_log_bytes, 'summary_bytes': len(command.stdout),
                              'raw_estimated_tokens': estimate_bytes(raw_log_bytes),
                              'summary_estimated_tokens': estimate_bytes(len(command.stdout)),
                              'summary_lines': len(command.stdout.splitlines()), 'failure_preserved': True, 'exit_code': command.returncode}}


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', help='optional JSON result file')
    args = ap.parse_args()
    result = benchmark()
    text = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        Path(args.output).write_text(text, encoding='utf-8')
    print(text, end='')
