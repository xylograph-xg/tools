"""Global synchronization tests use disposable projects, never business APIs."""
import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
from unittest.mock import patch

import test_links

HUB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HUB / 'scripts'))
import sync_tools as sync


class GlobalSync(unittest.TestCase):
    write = test_links.LinkChecks.write

    def setUp(self):
        test_links.LinkChecks.setUp(self)
        shutil.copytree(HUB / 'all', self.root / 'all')
        shutil.copytree(HUB / 'scripts', self.root / 'scripts', ignore=shutil.ignore_patterns('__pycache__'))
        (self.root / 'docs').mkdir()
        (self.root / 'docs/跨项目接入与联动.md').write_text('Rules')

    def run_sync(self, *args):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return sync.main(['--root', str(self.root), *args])

    def files(self):
        return {str(p): p.read_bytes() for p in Path(self.temp.name).rglob('*') if p.is_file()}

    def test_check_is_readonly_and_update_is_idempotent(self):
        before = self.files()
        self.assertEqual(self.run_sync('check'), 1)
        self.assertEqual(self.files(), before)
        self.assertEqual(self.run_sync('update'), 0)
        after = self.files()
        self.assertEqual(self.run_sync('update'), 0)
        self.assertEqual(self.files(), after)
        self.assertEqual(self.run_sync('check'), 0)

    def test_copied_package_bootstraps_from_another_working_directory(self):
        project = Path(self.temp.name) / 'new project'
        shutil.copytree(self.root / 'all', project / 'all')
        (project / 'AGENTS.md').write_text('# My rules\nPreserve this.\n')
        env = dict(os.environ, TOOLS_HOME=str(self.root), PYTHONDONTWRITEBYTECODE='1')
        result = subprocess.run([sys.executable, str(project / 'all/setup.py')], cwd='/', env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Preserve this.', (project / 'AGENTS.md').read_text())
        self.assertEqual((project / 'AGENTS.md').read_text().count(sync.BEGIN), 1)
        manifest = sync.read_json(project / 'tool-dependencies.json')
        self.assertEqual(manifest['tools'], [])
        self.assertEqual(manifest['exports'], [])
        self.assertEqual(self.run_sync('install', '--project', str(project)), 0)
        self.assertEqual(len(sync.read_json(self.root / 'projects.json')['projects']), 3)
        self.assertEqual(self.run_sync('update'), 0)
        self.assertEqual(self.run_sync('check'), 0)

    def test_drift_requires_explicit_source_and_consumer_review(self):
        self.assertEqual(self.run_sync('update'), 0)
        self.code.write_text('def fetch(query, /, *, limit=5):\n    return []\n')
        (self.source / 'extra.py').write_text('def extra():\n    pass\n')
        self.assertEqual(self.run_sync('update'), 1)
        tool = sync.read_json(self.root / 'registry.json')['tools'][0]
        self.assertEqual(tool['source_files_sha256'], self.hashes)
        self.assertEqual(tool['sync_state'], 'needs_review')
        snapshot = (self.root / 'INTERFACE.generated.md').read_text()
        self.assertIn('fetch(query, /, *, limit=…)', snapshot)
        self.assertIn('added: `extra.py`', snapshot)
        self.assertEqual(self.run_sync('accept', '--tool', 'demo', '--note', 'Reviewed signature and guide; no business execution'), 1)
        tool = sync.read_json(self.root / 'registry.json')['tools'][0]
        self.assertIsNone(tool['verified_at'])
        self.assertFalse(tool['verification']['live_generation_tested'])
        self.assertEqual(self.run_sync('acknowledge', '--project', 'user', '--tool', 'demo', '--note', 'Adapter checked statically'), 0)
        consumer = sync.read_json(self.user / 'tool-dependencies.json')['tools'][0]
        self.assertEqual(consumer['status'], 'source_inspected')
        self.assertIsNone(consumer['verified_at'])
        self.assertEqual(self.run_sync('check'), 0)

    def test_accept_rejects_source_changed_after_report(self):
        self.run_sync('update')
        self.code.write_text('VALUE = 3\n')
        before = self.files()
        self.assertEqual(self.run_sync('accept', '--tool', 'demo', '--note', 'old review'), 2)
        self.assertEqual(self.files(), before)

    def test_rules_propagate_but_local_edits_are_preserved(self):
        self.run_sync('update')
        central = self.root / 'all/RULES.md'
        central.write_text(central.read_text() + '\nNew shared rule.\n')
        self.assertEqual(self.run_sync('update'), 0)
        self.assertIn('New shared rule.', (self.owner / 'all/RULES.md').read_text())
        local = self.user / 'all/RULES.md'
        local.write_text(local.read_text() + 'Local edit')
        before = self.files()
        self.assertEqual(self.run_sync('update'), 2)
        self.assertEqual(self.files(), before)

    def test_missing_backlink_is_rebuilt_from_project_manifest(self):
        self.registry['tools'][0]['consumers'] = []
        self.write(self.root / 'registry.json', self.registry)
        self.assertEqual(self.run_sync('update'), 0)
        self.assertEqual(sync.read_json(self.root / 'registry.json')['tools'][0]['consumers'][0]['project_name'], 'user')

    def test_broken_markers_and_invalid_source_abort_before_writing(self):
        (self.owner / 'AGENTS.md').write_text(sync.BEGIN)
        before = self.files()
        self.assertEqual(self.run_sync('update'), 2)
        self.assertEqual(self.files(), before)
        (self.owner / 'AGENTS.md').write_text('Custom')
        self.code.write_text('def broken(:')
        before = self.files()
        self.assertEqual(self.run_sync('update'), 2)
        self.assertEqual(self.files(), before)

    def test_removed_source_is_detected(self):
        self.code.unlink()
        self.assertEqual(sync.snapshot(self.registry['tools'][0])['changes'], [{'path': 'core.py', 'kind': 'removed'}])

    def test_lock_prevents_concurrent_update(self):
        with sync.locked(self.root):
            self.assertEqual(self.run_sync('update'), 2)
        self.assertFalse((self.root / '.tools-sync.lock').exists())

    def test_failed_write_rolls_back_already_written_files(self):
        first, second = self.root / 'first.md', self.root / 'second.md'
        first.write_text('original')
        plan = sync.Plan()
        plan.put(first, 'changed')
        plan.put(second, 'new')
        original_atomic = sync.atomic
        def failing_atomic(path, data):
            if path == second:
                raise OSError('simulated failure')
            return original_atomic(path, data)
        with patch.object(sync, 'atomic', side_effect=failing_atomic):
            with self.assertRaises(OSError):
                plan.commit(self.root)
        self.assertEqual(first.read_text(), 'original')
        self.assertFalse(second.exists())
        self.assertTrue(list((self.root / '.sync-backups').glob('*/manifest.json')))

    def test_concurrent_edit_is_not_overwritten(self):
        path = self.root / 'guide.md'
        plan = sync.Plan()
        plan.put(path, 'new guide')
        path.write_text('Concurrent user edit')
        with self.assertRaises(ValueError):
            plan.commit(self.root)
        self.assertEqual(path.read_text(), 'Concurrent user edit')


if __name__ == '__main__':
    unittest.main()
