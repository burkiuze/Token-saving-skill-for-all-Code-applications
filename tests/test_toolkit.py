"""Behavioral and boundary tests against disposable Git projects; no network/provider access."""
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLKIT = ROOT / 'skills/token-saver/scripts/token_saver.py'
QUIET = ROOT / 'skills/quiet-run/scripts/quiet_run.py'
MEMORY = ROOT / 'skills/persistent-memory/scripts/memory.py'
BULK = ROOT / 'skills/bulk-edit/scripts/bulk_replace.py'
MAP = ROOT / 'skills/repo-map/scripts/repomap.py'
TESTS = ROOT / 'skills/test-impact/scripts/affected_tests.py'


class ProjectCase(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name).resolve()
        self.project = self.base / 'project'
        self.project.mkdir()
        self.memory_home = self.base / 'memory-global'
        self.environment = dict(os.environ, AGENT_MEMORY_HOME=str(self.memory_home), PYTHONIOENCODING='utf-8')
        self.git('init', '-q')
        self.git('config', 'user.name', 'Token Saver Tests')
        self.git('config', 'user.email', 'tests@example.invalid')
        self.write('src/auth.py', '@staticmethod\ndef refresh_token(value):\n    if not value:\n        raise ValueError("missing token")\n    return "renewed:" + value\n')
        self.write('tests/test_auth.py', 'from src.auth import refresh_token\n')
        self.write('docs/noise.md', 'unrelated documentation\n' * 300)
        self.write('.gitignore', 'ignored/\n')
        self.git('add', '.')
        self.git('commit', '-qm', 'fixture')

    def tearDown(self):
        self.temporary.cleanup()

    def write(self, rel, text):
        path = self.project / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
        return path

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.project)] + list(args), check=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout

    def run_script(self, script, *args, success=True):
        result = subprocess.run([sys.executable, str(script)] + list(args), cwd=str(self.project),
                                env=self.environment, capture_output=True, text=True, encoding='utf-8', timeout=20)
        if success:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result


class ContextPackTests(ProjectCase):
    def test_relevant_evidence_preserves_complete_body_and_decorator(self):
        result = self.run_script(TOOLKIT, 'pack', 'refresh_token', '--json', '--budget', '1200')
        packet = json.loads(result.stdout)
        first = packet['snippets'][0]
        self.assertEqual('src/auth.py', first['path'])
        self.assertTrue(first['complete_symbol'])
        self.assertIn('@staticmethod', first['text'])
        self.assertIn('return "renewed:"', first['text'])
        self.assertLessEqual(math.ceil(len(result.stdout.encode('utf-8')) / 4), 1200)
        self.assertNotIn('unrelated documentation', result.stdout)

    def test_unicode_budget_includes_all_serialized_metadata(self):
        self.write('src/türkçe.py', 'def hesapla():\n    return "şifre yenileme"\n' * 4)
        for output_json in (False, True):
            flags = ['--json'] if output_json else []
            result = self.run_script(TOOLKIT, 'pack', 'yenileme', '--budget', '500', *flags)
            self.assertLessEqual(math.ceil(len(result.stdout.encode('utf-8')) / 4), 500)

    def test_ignored_secret_binary_and_large_files_do_not_enter_packet(self):
        self.write('ignored/x.py', 'refresh_token = "excluded"\n')
        self.write('.env', 'API_KEY=refresh_token_super_secret\n')
        self.write('credentials.json', '{"refresh_token": "excluded"}\n')
        self.write('src/large.py', 'refresh_token = 1\n' * 40000)
        (self.project / 'src/binary.py').write_bytes(b'refresh_token\x00binary')
        packet = json.loads(self.run_script(TOOLKIT, 'pack', 'refresh_token', '--json').stdout)
        paths = {item['path'] for item in packet['snippets']}
        self.assertTrue(paths.isdisjoint({'ignored/x.py', '.env', 'credentials.json', 'src/large.py', 'src/binary.py'}))

    def test_inline_credentials_are_masked(self):
        value = 'sk-' + 'x' * 32
        self.write('src/settings.py', 'API_KEY = "%s"\n# refresh_token configuration\n' % value)
        result = self.run_script(TOOLKIT, 'pack', 'configuration', '--json')
        self.assertNotIn(value, result.stdout)
        self.assertIn('[REDACTED', result.stdout)

    def test_multiline_key_redaction_keeps_original_line_numbers(self):
        self.write('src/key_example.py', 'KEY = """-----BEGIN PRIVATE KEY-----\nABCDEF\n-----END PRIVATE KEY-----"""\n\ndef refresh_token():\n    return 1\n')
        result = self.run_script(TOOLKIT, 'read', 'src/key_example.py', '--start', '1', '--end', '6', '--json')
        data = json.loads(result.stdout)
        self.assertIn('5: def refresh_token', data['text'])
        self.assertNotIn('ABCDEF', data['text'])

    def test_path_filter_and_config_limit_are_explicit(self):
        self.write('.token-saver.json', json.dumps({'max_files': 1, 'max_snippets': 1}))
        result = self.run_script(TOOLKIT, 'pack', 'refresh_token', '--json')
        self.assertGreater(json.loads(result.stdout)['scan_omitted'], 0)
        self.write('.token-saver.json', json.dumps({'unsupported': True}))
        self.assertEqual(2, self.run_script(TOOLKIT, 'pack', 'refresh_token', success=False).returncode)

    def test_packet_is_deterministic_and_hash_changes_with_source(self):
        first = self.run_script(TOOLKIT, 'pack', 'refresh_token', '--json').stdout
        self.assertEqual(first, self.run_script(TOOLKIT, 'pack', 'refresh_token', '--json').stdout)
        original = json.loads(first)['snippets'][0]['sha256']
        with (self.project / 'src/auth.py').open('a') as handle:
            handle.write('# changed\n')
        updated = json.loads(self.run_script(TOOLKIT, 'pack', 'refresh_token', '--json').stdout)
        self.assertNotEqual(original, updated['snippets'][0]['sha256'])

    def test_path_scope_is_applied_before_file_limit(self):
        self.write('.token-saver.json', json.dumps({'max_files': 1}))
        result = self.run_script(TOOLKIT, 'pack', 'refresh_token', '--path', 'src/auth.py', '--json')
        packet = json.loads(result.stdout)
        self.assertEqual('src/auth.py', packet['snippets'][0]['path'])
        self.assertEqual(0, packet['scan_omitted'])

    def test_small_budget_never_silently_truncates_a_read(self):
        result = self.run_script(TOOLKIT, 'read', 'src/auth.py', '--symbol', 'refresh_token', '--budget', '10', success=False)
        self.assertEqual(2, result.returncode)
        self.assertIn('exceeds budget', result.stderr)
        result = self.run_script(TOOLKIT, 'pack', 'refresh_token', '--budget', '1', success=False)
        self.assertEqual(2, result.returncode)

    def test_ambiguous_symbol_requires_qualified_name(self):
        self.write('src/classes.py', 'class A:\n    def run(self):\n        return 1\nclass B:\n    def run(self):\n        return 2\n')
        self.assertEqual(2, self.run_script(TOOLKIT, 'read', 'src/classes.py', '--symbol', 'run', success=False).returncode)
        result = self.run_script(TOOLKIT, 'read', 'src/classes.py', '--symbol', 'B.run')
        self.assertIn('return 2', result.stdout)
        self.assertNotIn('return 1', result.stdout)

    def test_outside_read_and_secret_read_are_rejected(self):
        (self.base / 'outside.py').write_text('secret', encoding='utf-8')
        self.write('.env', 'secret')
        for rel in ('../outside.py', '.env'):
            self.assertEqual(2, self.run_script(TOOLKIT, 'read', rel, success=False).returncode)

    @unittest.skipIf(os.name == 'nt', 'symlink privileges vary on Windows')
    def test_source_symlinks_are_excluded_and_direct_reads_fail(self):
        outside = self.base / 'outside.py'
        outside.write_text('refresh_token = "outside_secret"', encoding='utf-8')
        (self.project / 'src/link.py').symlink_to(outside)
        self.git('add', 'src/link.py')
        result = self.run_script(TOOLKIT, 'pack', 'refresh_token', '--json')
        self.assertNotIn('outside_secret', result.stdout)
        self.assertEqual(2, self.run_script(TOOLKIT, 'read', 'src/link.py', success=False).returncode)


class DiffTests(ProjectCase):
    def test_working_diff_combines_staged_unstaged_and_untracked_paths(self):
        self.write('src/auth.py', 'def refresh_token(value):\n    return value\n')
        self.git('add', 'src/auth.py')
        self.write('tests/test_auth.py', '# changed test\n')
        self.write('src/new helper.py', 'def extra(): return 1\n')
        result = self.run_script(TOOLKIT, 'diff', '--json', '--budget', '2000')
        packet = json.loads(result.stdout)
        self.assertEqual({'src/auth.py', 'tests/test_auth.py', 'src/new helper.py'}, {f['path'] for f in packet['files']})
        staged = json.loads(self.run_script(TOOLKIT, 'diff', '--staged', '--json').stdout)
        self.assertEqual(['src/auth.py'], [f['path'] for f in staged['files']])

    def test_invalid_base_is_an_error(self):
        result = self.run_script(TOOLKIT, 'diff', '--base', '--bad-ref', success=False)
        self.assertEqual(2, result.returncode)
        result = self.run_script(TOOLKIT, 'diff', '--base', 'missing-branch', success=False)
        self.assertEqual(2, result.returncode)

    def test_deleted_file_and_budget_omissions_are_represented(self):
        (self.project / 'src/auth.py').unlink()
        self.write('docs/noise.md', 'changed\n' * 1000)
        result = self.run_script(TOOLKIT, 'diff', '--json', '--budget', '500')
        data = json.loads(result.stdout)
        self.assertLessEqual(math.ceil(len(result.stdout.encode('utf-8')) / 4), 500)
        self.assertTrue(data['truncated_patches'] or data['omitted_files'])
        narrow = self.run_script(TOOLKIT, 'diff', '--path', 'src/auth.py')
        self.assertIn('deleted file mode', narrow.stdout)

    def test_external_diff_driver_is_not_executed(self):
        marker = self.project / 'driver-was-run'
        self.environment['GIT_EXTERNAL_DIFF'] = 'touch ' + str(marker)
        self.write('src/auth.py', '# changed\n')
        self.run_script(TOOLKIT, 'diff')
        self.assertFalse(marker.exists())


class UsageTests(ProjectCase):
    def test_estimates_and_reported_usage_are_separate(self):
        self.run_script(TOOLKIT, 'pack', 'refresh_token', '--record')
        self.run_script(TOOLKIT, 'budget', 'record', '--input-tokens', '1000', '--output-tokens', '100', '--cached-input-tokens', '400')
        data = json.loads(self.run_script(TOOLKIT, 'budget', 'report', '--json').stdout)
        self.assertEqual(1000, data['reported_usage']['input_tokens'])
        self.assertEqual(400, data['reported_usage']['cached_input_tokens'])
        self.assertEqual(1, data['estimated_context']['events'])
        self.assertNotIn('def refresh_token', (self.project / '.codemap/usage.jsonl').read_text())

    def test_invalid_and_corrupt_records_cannot_pollute_totals(self):
        self.assertEqual(2, self.run_script(TOOLKIT, 'budget', 'record', '--input-tokens', '5', '--output-tokens', '1', '--cached-input-tokens', '10', success=False).returncode)
        self.write('.codemap/usage.jsonl', 'not json\n{"kind":"reported","input_tokens":-2}\n')
        data = json.loads(self.run_script(TOOLKIT, 'budget', 'report', '--json').stdout)
        self.assertEqual(2, data['invalid_events'])
        self.assertEqual(0, data['reported_usage']['events'])

    def test_concurrent_ledger_writers_do_not_lose_events(self):
        processes = [subprocess.Popen([sys.executable, str(TOOLKIT), 'budget', 'record', '--input-tokens', '1', '--output-tokens', '2'],
                     cwd=str(self.project), env=self.environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE) for _ in range(6)]
        for process in processes:
            stdout, stderr = process.communicate(timeout=15)
            self.assertEqual(0, process.returncode, stderr.decode())
        data = json.loads(self.run_script(TOOLKIT, 'budget', 'report', '--json').stdout)
        self.assertEqual(6, data['reported_usage']['events'])
        self.assertEqual(12, data['reported_usage']['output_tokens'])


class RobustnessTests(ProjectCase):
    def test_quiet_output_cap_and_child_exit_are_preserved(self):
        for cap in (1, 2, 5):
            result = self.run_script(QUIET, '--lines', str(cap), '--', sys.executable, '-c', 'print("ValueError: failed"); raise SystemExit(3)', success=False)
            self.assertEqual(3, result.returncode)
            self.assertLessEqual(len(result.stdout.splitlines()), cap)

    def test_log_cap_retains_latest_failure_evidence(self):
        result = self.run_script(QUIET, '--max-log-bytes', '100', '--', sys.executable, '-c', 'print("x"*10000); print("ValueError: final_failure"); raise SystemExit(3)', success=False)
        self.assertEqual(3, result.returncode)
        self.assertIn('log capped', result.stdout)
        self.assertIn('final_failure', result.stdout)
        self.assertLessEqual((self.project / '.codemap/logs/last.log').stat().st_size, 100)

    def test_shell_is_explicit_and_log_credentials_are_masked(self):
        result = self.run_script(QUIET, '--', 'echo hi; touch unintended', success=False)
        self.assertEqual(127, result.returncode)
        self.assertFalse((self.project / 'unintended').exists())
        key = 'sk-' + 'x' * 32
        self.run_script(QUIET, '--', sys.executable, '-c', 'print("API_KEY=%s")' % key)
        self.assertNotIn(key, (self.project / '.codemap/logs/last.log').read_text())

    def test_timeout_preserves_distinct_exit_code(self):
        result = self.run_script(QUIET, '--timeout', '0.15', '--', sys.executable, '-c', 'import time; time.sleep(5)', success=False)
        self.assertEqual(124, result.returncode)
        self.assertIn('TIMEOUT', result.stdout)

    def test_bulk_preserves_mode_and_crlf_and_ignores_credentials(self):
        path = self.project / 'src/lines.py'
        path.write_bytes(b'old_name()\r\nold_name()\r\n')
        path.chmod(0o755)
        self.write('.env', 'old_name=keep_this\n')
        self.run_script(BULK, 'old_name', 'new_name', '--fixed', '--apply')
        self.assertEqual(b'new_name()\r\nnew_name()\r\n', path.read_bytes())
        if os.name != 'nt':
            self.assertEqual(0o755, path.stat().st_mode & 0o777)
        self.assertIn('old_name', (self.project / '.env').read_text())

    @unittest.skipIf(os.name == 'nt', 'symlink privileges vary on Windows')
    def test_bulk_and_map_never_follow_source_symlinks(self):
        outside = self.base / 'outside.py'
        outside.write_text('def old_name(): pass\n', encoding='utf-8')
        (self.project / 'src/link.py').symlink_to(outside)
        self.git('add', 'src/link.py')
        self.run_script(BULK, 'old_name', 'new_name', '--apply', success=False)
        self.assertIn('old_name', outside.read_text())
        self.run_script(MAP, 'build')
        self.assertNotIn('link.py', (self.project / '.codemap/MAP.md').read_text())

    def test_memory_rejects_credentials_and_keeps_corruption_unchanged(self):
        self.assertEqual(2, self.run_script(MEMORY, 'add', 'API_KEY=top_secret_value', success=False).returncode)
        path = self.write('.codemap/memory.jsonl', 'broken json\n')
        self.assertEqual(2, self.run_script(MEMORY, 'add', 'A verified command', success=False).returncode)
        self.assertEqual('broken json\n', path.read_text())

    def test_memory_links_cannot_escape_and_new_memory_stays_local(self):
        (self.base / 'outside.txt').write_text('outside', encoding='utf-8')
        result = self.run_script(MEMORY, 'add', 'verified fact', '--files', '../outside.txt', success=False)
        self.assertEqual(2, result.returncode)
        self.run_script(MEMORY, 'add', 'Auth tests run with pytest', '--kind', 'cmd', '--files', 'src/auth.py')
        self.assertNotIn('!memory.jsonl', (self.project / '.codemap/.gitignore').read_text())

    def test_changed_paths_with_spaces_are_not_split_and_base_errors_fail(self):
        self.write('src/data parser.py', 'def parse(): pass\n')
        self.write('tests/test_data parser.py', '# fixture\n')
        result = self.run_script(TESTS, '--json')
        data = json.loads(result.stdout)
        self.assertIn('src/data parser.py', data['changed'])
        self.assertIn('tests/test_data parser.py', data['tests'])
        self.assertEqual('heuristic', data['selection'])
        self.assertTrue(data['broader_validation_reasons'])
        self.assertEqual(2, self.run_script(TESTS, '--base', 'missing', success=False).returncode)


if __name__ == '__main__':
    unittest.main()
