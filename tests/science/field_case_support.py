"""Shared, offline byte-integrity checks for the additional field cases."""

import gzip
from hashlib import sha256
import json
from pathlib import Path


FIELD_ROOT = Path(__file__).resolve().parents[1] / "fixtures/field"


def verify_case(case, directory=None):
    directory = Path(directory) if directory else FIELD_ROOT / case
    provenance = json.loads((directory / "provenance.json").read_text(encoding="utf-8"))
    for name, item in provenance["files"].items():
        content = (directory / name).read_bytes()
        if len(content) != item["bytes"] or sha256(content).hexdigest() != item["sha256"]:
            raise ValueError(f"Field-data integrity check failed: {name}")
        if "uncompressed_sha256" in item:
            if sha256(gzip.decompress(content)).hexdigest() != item["uncompressed_sha256"]:
                raise ValueError(f"Original source-content check failed: {name}")
    return directory, provenance
