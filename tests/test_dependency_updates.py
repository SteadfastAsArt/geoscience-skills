"""Version monitoring checks registries without executing package managers."""

import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('dependency_updates', ROOT / 'scripts/check_dependency_updates.py')
monitor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(monitor)


class DependencyUpdateTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / 'tests/science').mkdir(parents=True)
        (self.root / 'scripts').mkdir()
        (self.root / 'scripts/check_installation.py').write_text(
            'raise RuntimeError("must not execute installer source")\nSKILLS_CLI_VERSION = "1.5.25"\n')

    def pinfile(self, name, content):
        path = self.root / 'tests/science' / f'requirements-{name}.txt'
        path.write_text(content)
        return path

    def test_multiple_baselines_keep_distinct_pins_and_read_installer_as_data(self):
        self.pinfile('core', 'NumPy==1.26.4\n')
        self.pinfile('models', 'numpy==2.4.6\n')
        rows = monitor.read_baselines(self.root)
        self.assertEqual([row['pinned'] for row in rows], ['1.26.4', '2.4.6', '1.5.25'])
        self.assertEqual([row['name'] for row in rows], ['numpy', 'numpy', 'skills'])

    def test_unpinned_or_duplicate_requirements_fail(self):
        for content in ('numpy>=1.26\n', 'numpy==1.26.4\nNumPy==1.26.4\n', '-r another.txt\n'):
            with self.subTest(content=content):
                self.pinfile('core', content)
                with self.assertRaises(ValueError):
                    monitor.read_baselines(self.root)

    def test_empty_scientific_baseline_fails(self):
        with self.assertRaisesRegex(ValueError, 'No scientific'):
            monitor.read_baselines(self.root)

    def test_registry_lookup_is_deduplicated_and_never_changes_pins(self):
        paths = [self.pinfile('core', 'numpy==1.26.4\n'),
                 self.pinfile('models', 'numpy==2.4.6\n')]
        before = [path.read_bytes() for path in paths]
        calls = []

        def fetch(url):
            calls.append(url)
            return {'info': {'version': '2.4.6'}} if 'pypi.org' in url else {'version': '1.5.25'}

        report = monitor.build_report(monitor.read_baselines(self.root), fetch)
        self.assertEqual(len(calls), 2)
        self.assertEqual(report['summary'], {'same': 2, 'different': 1, 'error': 0})
        self.assertEqual(before, [path.read_bytes() for path in paths])

    def test_failures_and_malformed_registry_responses_remain_errors(self):
        self.pinfile('core', 'numpy==1.26.4\n')

        def fetch(url):
            if 'pypi.org' in url:
                raise TimeoutError('registry unavailable')
            return {'version': None}

        report = monitor.build_report(monitor.read_baselines(self.root), fetch)
        self.assertEqual(report['summary']['error'], 2)
        self.assertTrue(all(row['latest'] is None for row in report['results']))

    def test_report_output_cannot_overwrite_its_inputs(self):
        baseline = self.pinfile('core', 'numpy==1.26.4\n')
        rows = monitor.read_baselines(self.root)
        before = baseline.read_bytes()
        with self.assertRaisesRegex(ValueError, 'must not overwrite'):
            monitor.write_report(baseline, '{}\n', self.root, rows)
        self.assertEqual(baseline.read_bytes(), before)
        report = self.root / 'report.json'
        monitor.write_report(report, '{}\n', self.root, rows)
        self.assertEqual(report.read_text(), '{}\n')


if __name__ == '__main__':
    unittest.main()
