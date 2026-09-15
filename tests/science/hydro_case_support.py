"""Load actual hydro workflow/example code and local licensed field fixtures."""
import importlib.util
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / 'tests/fixtures/workflows/hydro'
WORKFLOW = ROOT / 'workflows/hydrogeological-analysis'


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def example(path, heading):
    text = (ROOT / path).read_text()
    section = re.search(rf'^## {re.escape(heading)}\n(.*?)(?=^## |\Z)', text, re.M | re.S)
    if section is None:
        raise AssertionError(f'Missing example section: {path}:{heading}')
    block = re.search(r'^```python\n(.*?)^```', section[1], re.M | re.S)
    if block is None:
        raise AssertionError(f'Missing Python block: {path}:{heading}')
    namespace = {}
    exec(compile(block[1], f'{path}:{heading}', 'exec'), namespace)
    return namespace


PIPELINE = module('hydro_pipeline', WORKFLOW / 'scripts/run_pastas_workflow.py')
HELPER = module('pastas_helper', ROOT / 'pastas/scripts/groundwater_model.py')


def inputs():
    return (PIPELINE.read_series(FIXTURE / 'head.csv'),
            PIPELINE.read_series(FIXTURE / 'rain.csv'),
            PIPELINE.read_series(FIXTURE / 'evap.csv'),
            json.loads((FIXTURE / 'design.json').read_text()))
