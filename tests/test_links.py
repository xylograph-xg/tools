"""Exercise missing links and drift in disposable projects, without business calls."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/check_links.py'
spec = importlib.util.spec_from_file_location('check_links', SCRIPT)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class LinkChecks(unittest.TestCase):
    def write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.root, self.owner, self.user = [base / x for x in ['tools', 'owner', 'user']]
        self.source = self.owner / 'package'
        self.source.mkdir(parents=True)
        self.code = self.source / 'core.py'
        self.code.write_text('VALUE = 1\n')
        self.hashes = {'core.py': hashlib.sha256(self.code.read_bytes()).hexdigest()}
        self.root.mkdir()
        (self.root / 'guide.md').write_text('A tool guide.')
        self.rule_path = self.root / 'rules.md'
        self.rule_path.write_text('Linking rules.')
        projects = []
        for name, folder in [('owner', self.owner), ('user', self.user)]:
            folder.mkdir(exist_ok=True)
            (folder / 'AGENTS.md').write_text(f'{self.root / "registry.json"}\ncheck_links.py\n')
            manifest = {'project_name': name, 'project_root': str(folder),
                        'registry_path': str(self.root / 'registry.json'),
                        'projects_index_path': str(self.root / 'projects.json'),
                        'rules_path': str(self.rule_path), 'exports': [], 'tools': [], 'module_dependencies': []}
            if name == 'owner':
                manifest['exports'] = [{'id': 'demo', 'source_dir': str(self.source), 'guide_path': str(self.root / 'guide.md')}]
            else:
                manifest['tools'] = [{'id': 'demo', 'source_dir': str(self.source), 'status': 'source_inspected',
                                      'integration': 'python', 'verified_at': None, 'inspected_at': '2026-09-18',
                                      'observed_source_files_sha256': self.hashes}]
            self.write(folder / 'tool-dependencies.json', manifest)
            projects.append({'name': name, 'root': str(folder), 'rules_file': 'AGENTS.md', 'manifest_file': 'tool-dependencies.json'})
        self.write(self.root / 'projects.json', {'projects': projects})
        self.registry = {'tools': [{'id': 'demo', 'source_dir': str(self.source), 'guide': 'guide.md', 'source_docs': [],
                                  'source_files_sha256': self.hashes,
                                  'owner_project': {'name': 'owner', 'root': str(self.owner), 'rules_file': 'AGENTS.md', 'manifest_file': 'tool-dependencies.json'},
                                  'consumers': [{'project_name': 'user', 'project_root': str(self.user), 'dependency_file': 'tool-dependencies.json', 'status': 'source_inspected', 'integration': 'python', 'verified_at': None}]}]}
        self.write(self.root / 'registry.json', self.registry)

    def errors(self):
        return '\n'.join(checker.check(self.root)[0])

    def test_valid_static_relationship_is_not_live_verification(self):
        errors, notes, counts = checker.check(self.root)
        self.assertEqual(errors, [])
        self.assertIn('尚未完成真实接入验收', notes[0])
        self.assertEqual(counts['source_files'], 1)

    def test_changed_source_is_detected_without_refreshing_registry(self):
        before = (self.root / 'registry.json').read_bytes()
        self.code.write_text('VALUE = 2\n')
        self.assertIn('源码基线过期', self.errors())
        self.assertEqual((self.root / 'registry.json').read_bytes(), before)

    def test_new_source_requires_registration(self):
        (self.source / 'new_api.py').write_text('VALUE = 3\n')
        self.assertIn('新文件尚未登记基线', self.errors())

    def test_missing_provider_export_is_detected(self):
        p = self.owner / 'tool-dependencies.json'
        data = json.loads(p.read_text()); data['exports'] = []
        self.write(p, data)
        self.assertIn('exports 反向登记', self.errors())

    def test_missing_consumer_reverse_link_is_detected(self):
        self.registry['tools'][0]['consumers'] = []
        self.write(self.root / 'registry.json', self.registry)
        self.assertIn('consumers 反向登记', self.errors())

    def test_consumer_snapshot_cannot_lag_updated_tool(self):
        p = self.user / 'tool-dependencies.json'
        data = json.loads(p.read_text()); data['tools'][0]['observed_source_files_sha256'] = {}
        self.write(p, data)
        self.assertIn('使用方记录落后', self.errors())

    def test_missing_project_rules_are_detected(self):
        (self.owner / 'AGENTS.md').unlink()
        self.assertIn('缺少规则文件', self.errors())

    def test_module_dependency_path_is_checked(self):
        p = self.user / 'tool-dependencies.json'
        data = json.loads(p.read_text())
        data['module_dependencies'] = [{'project_name': 'owner', 'source_files': ['missing.py'], 'used_by': []}]
        self.write(p, data)
        self.assertIn('模块路径失效', self.errors())

    def test_invalid_json_returns_configuration_error(self):
        (self.root / 'registry.json').write_text('{invalid')
        process = subprocess.run([sys.executable, str(SCRIPT), '--root', str(self.root)], capture_output=True, text=True)
        self.assertEqual(process.returncode, 2)
        self.assertIn('检查配置失败', process.stdout)


if __name__ == '__main__':
    unittest.main()
