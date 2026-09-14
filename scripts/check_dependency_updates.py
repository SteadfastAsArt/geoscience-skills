#!/usr/bin/env python3
"""Read public registry metadata and compare it with the verified test pins.

This command never invokes an installer or modifies a baseline. A different
registry version is a review candidate, not proof of compatibility or an upgrade.
"""

import argparse
import ast
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent.parent
PIN = re.compile(r'([A-Za-z0-9][A-Za-z0-9_.-]*)==([A-Za-z0-9][A-Za-z0-9_.+!-]*)')


def read_baselines(root):
    rows = []
    for path in sorted((root / 'tests/science').glob('requirements-*.txt')):
        seen = set()
        for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
            line = line.split('#', 1)[0].strip()
            if not line:
                continue
            match = PIN.fullmatch(line)
            if not match:
                raise ValueError(f'{path}:{number}: expected a single exact name==version pin')
            name, version = match.groups()
            normalized = re.sub(r'[-_.]+', '-', name).lower()
            if normalized in seen:
                raise ValueError(f'{path}:{number}: duplicate package {name}')
            seen.add(normalized)
            rows.append({'ecosystem': 'pypi', 'name': normalized, 'pinned': version,
                         'baseline': path.relative_to(root).as_posix()})
    if not rows:
        raise ValueError('No scientific dependency pins found')

    installer = root / 'scripts/check_installation.py'
    tree = ast.parse(installer.read_text(encoding='utf-8'))
    values = [node.value.value for node in tree.body
              if isinstance(node, ast.Assign)
              and any(isinstance(target, ast.Name) and target.id == 'SKILLS_CLI_VERSION'
                      for target in node.targets)
              and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)]
    if len(values) != 1 or not re.fullmatch(r'\d+\.\d+\.\d+(?:[-+][A-Za-z0-9.-]+)?', values[0]):
        raise ValueError('Expected one literal SKILLS_CLI_VERSION in check_installation.py')
    rows.append({'ecosystem': 'npm', 'name': 'skills', 'pinned': values[0],
                 'baseline': 'scripts/check_installation.py'})
    return rows


def registry_url(ecosystem, name):
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]*', name):
        raise ValueError(f'Unexpected package name: {name!r}')
    if ecosystem == 'pypi':
        return f'https://pypi.org/pypi/{name}/json'
    if ecosystem == 'npm' and name == 'skills':
        return 'https://registry.npmjs.org/skills/latest'
    raise ValueError(f'Unsupported registry: {ecosystem}')


def fetch_json(url):
    request = Request(url, headers={'Accept': 'application/json',
                                    'User-Agent': 'geoscience-skills-version-report/1'})
    with urlopen(request, timeout=20) as response:
        # Bound registry responses; none of the returned code/URLs is executed.
        limit = 20 * 1024 * 1024
        body = response.read(limit + 1)
        if len(body) > limit:
            raise ValueError('Registry response exceeds 20 MiB')
        return json.loads(body)


def build_report(rows, fetcher=fetch_json):
    keys = sorted({(row['ecosystem'], row['name']) for row in rows})

    def lookup(key):
        ecosystem, name = key
        url = registry_url(ecosystem, name)
        try:
            payload = fetcher(url)
            info = payload['info'] if ecosystem == 'pypi' else payload
            latest = info['version']
            if not isinstance(latest, str) or not latest.strip():
                raise ValueError('Registry has no nonempty version string')
            return key, {'latest': latest, 'registry_url': url}
        except Exception as error:
            return key, {'latest': None, 'registry_url': url,
                         'error': f'{type(error).__name__}: {error}'}

    with ThreadPoolExecutor(max_workers=6) as pool:
        versions = dict(pool.map(lookup, keys))
    results = []
    for row in rows:
        found = versions[(row['ecosystem'], row['name'])]
        status = ('error' if 'error' in found else
                  'same' if found['latest'] == row['pinned'] else 'different')
        results.append(dict(row, **found, status=status))
    return {
        'schema_version': 1,
        'checked_at': datetime.now(timezone.utc).isoformat(),
        'scope': 'Registry metadata only; no install, upgrade or compatibility claim',
        'summary': {status: sum(row['status'] == status for row in results)
                    for status in ('same', 'different', 'error')},
        'results': results,
    }


def write_report(path, serialized, root, rows):
    sources = {root / row['baseline'] for row in rows} | {Path(__file__).resolve()}
    for source in sources:
        if (path.resolve() == source.resolve()
                or (path.exists() and source.exists() and path.samefile(source))):
            raise ValueError('Report output must not overwrite a baseline or monitoring script')
    path.write_text(serialized, encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path, help='Write the JSON report to this file')
    args = parser.parse_args()
    try:
        root = args.root.resolve()
        rows = read_baselines(root)
        report = build_report(rows)
        serialized = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
        if args.output:
            write_report(args.output, serialized, root, rows)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(serialized, end='')
    return 1 if report['summary']['error'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
