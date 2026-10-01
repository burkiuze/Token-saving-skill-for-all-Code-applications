"""Installer contracts: preserve user content, be repeatable, and remove only managed files."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.project = Path(self.temporary.name).resolve() / 'project with spaces'
        self.project.mkdir()

    def tearDown(self):
        self.temporary.cleanup()

    def install(self, *args, success=True):
        result = subprocess.run([sys.executable, str(ROOT / 'install.py'), '--project', str(self.project),
                                 '--tools', 'codex'] + list(args), capture_output=True, text=True,
                                encoding='utf-8', env=dict(os.environ, PYTHONIOENCODING='utf-8'), timeout=20)
        if success:
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        return result

    def target(self, skill='token-saver'):
        return self.project / '.agents/skills' / skill

    def test_minimal_profile_copies_only_selected_skills_and_core_works(self):
        self.install('--profile', 'minimal')
        self.assertEqual(5, len(list((self.project / '.agents/skills').iterdir())))
        self.assertFalse(self.target('repo-map').exists())
        result = subprocess.run([sys.executable, str(self.target() / 'scripts/token_saver.py'), '--version'],
                                 capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn('2.0.0', result.stdout)

    def test_full_install_then_default_uninstall_removes_all_managed_skills(self):
        self.install('--profile', 'full')
        self.assertEqual(14, len(list((self.project / '.agents/skills').iterdir())))
        self.install('--uninstall')
        self.assertEqual([], list((self.project / '.agents/skills').iterdir()))

    def test_profile_switch_reduces_managed_skills_without_leaving_metadata(self):
        self.install('--profile', 'full')
        self.install('--profile', 'minimal')
        self.assertEqual(5, len(list((self.project / '.agents/skills').iterdir())))
        self.assertFalse(self.target('persistent-memory').exists())
        self.assertEqual(5, json.loads(self.install('--doctor').stdout)['managed_skills'])

    def test_repeat_install_is_identical_and_doctor_checks_content(self):
        self.install()
        rule = (self.project / 'AGENTS.md').read_bytes()
        self.install()
        self.assertEqual(rule, (self.project / 'AGENTS.md').read_bytes())
        data = json.loads(self.install('--doctor').stdout)
        self.assertEqual([], data['problems'])
        path = self.target() / 'SKILL.md'
        with path.open('a') as handle:
            handle.write('local edit\n')
        self.assertEqual(1, self.install('--doctor', success=False).returncode)

    def test_install_uninstall_roundtrip_preserves_original_bytes_and_crlf(self):
        for original in (b'# mine\r\nmore rules\r\n', b'no final newline', b'# mine\n'):
            path = self.project / 'AGENTS.md'
            path.write_bytes(original)
            self.install()
            self.install()
            self.install('--uninstall')
            self.assertEqual(original, path.read_bytes())

    def test_edit_outside_block_survives_uninstall(self):
        self.install()
        path = self.project / 'AGENTS.md'
        with path.open('a', encoding='utf-8') as handle:
            handle.write('new user instructions\n')
        self.install('--uninstall')
        self.assertEqual('new user instructions\n', path.read_text())

    def test_unmanaged_skill_collision_refuses_before_any_write(self):
        self.target().mkdir(parents=True)
        path = self.target() / 'user.txt'
        path.write_text('preserve me')
        result = self.install(success=False)
        self.assertEqual(2, result.returncode)
        self.assertEqual('preserve me', path.read_text())
        self.assertFalse((self.project / 'AGENTS.md').exists())
        self.assertFalse(self.target('context-pack').exists())

    def test_force_collision_creates_backup(self):
        self.target().mkdir(parents=True)
        (self.target() / 'user.txt').write_text('preserve me')
        self.install('--force')
        backups = list((self.project / '.token-saver-state/backups').rglob('user.txt'))
        self.assertEqual(1, len(backups))
        self.assertEqual('preserve me', backups[0].read_text())

    def test_locally_modified_managed_skill_survives_default_uninstall(self):
        self.install()
        path = self.target() / 'local.py'
        path.write_text('# user edit\n')
        self.assertEqual(2, self.install('--uninstall', success=False).returncode)
        self.assertTrue(path.exists())
        self.assertTrue(self.target('context-pack').exists())

    def test_malformed_rule_markers_never_consume_following_content(self):
        path = self.project / 'AGENTS.md'
        original = '<!-- token-saver:start -->\nkeep this too\n'
        path.write_text(original)
        self.assertEqual(2, self.install(success=False).returncode)
        self.assertEqual(original, path.read_text())
        self.assertFalse(self.target().exists())

    def test_dry_run_has_no_filesystem_effect(self):
        self.install('--dry-run', '--profile', 'full')
        self.assertEqual([], list(self.project.iterdir()))

    def test_uninstall_without_manifest_never_removes_user_skills(self):
        self.target().mkdir(parents=True)
        path = self.target() / 'SKILL.md'
        path.write_text('# user skill\n')
        self.install('--uninstall')
        self.assertTrue(path.exists())

    def test_no_rules_and_explicit_selection_include_core_dependency(self):
        self.install('--no-rules', '--skills', 'bulk-edit')
        self.assertFalse((self.project / 'AGENTS.md').exists())
        self.assertEqual({'bulk-edit', 'token-saver'}, {p.name for p in (self.project / '.agents/skills').iterdir()})

    def test_copilot_uses_its_repository_instruction_file(self):
        self.install('--tools', 'copilot')
        self.assertTrue((self.project / '.github/copilot-instructions.md').is_file())
        self.assertFalse((self.project / 'AGENTS.md').exists())

    @unittest.skipIf(os.name == 'nt', 'symlink privileges vary on Windows')
    def test_symlink_parent_is_refused_without_touching_outside_directory(self):
        outside = self.project.parent / 'outside'
        outside.mkdir()
        (self.project / '.agents').symlink_to(outside, target_is_directory=True)
        self.assertEqual(2, self.install(success=False).returncode)
        self.assertEqual([], list(outside.iterdir()))

    @unittest.skipIf(os.name == 'nt', 'symlink privileges vary on Windows')
    def test_link_install_uninstall_does_not_delete_source(self):
        self.install('--profile', 'minimal', '--link')
        self.assertTrue(self.target().is_symlink())
        self.install('--uninstall')
        self.assertFalse(self.target().exists())
        self.assertTrue((ROOT / 'skills/token-saver/SKILL.md').is_file())

    @unittest.skipUnless(shutil.which('pwsh'), 'PowerShell runtime not installed')
    def test_powershell_launcher_passes_profile_and_paths_with_spaces(self):
        result = subprocess.run(['pwsh', '-NoProfile', '-File', str(ROOT / 'install.ps1'),
                                 '-Project', str(self.project), '-Tools', 'codex', '-Profile', 'minimal'],
                                 capture_output=True, text=True, timeout=20)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual(5, len(list((self.project / '.agents/skills').iterdir())))


if __name__ == '__main__':
    unittest.main()
