#!/usr/bin/env python3
"""Install one hash-verified MODFLOW 6 test executable into an explicit directory.

Linux x86-64 only. Does not use FloPy's user-level installation metadata, change
PATH, or overwrite an existing binary. Source: MODFLOW-ORG executables release 29.0.
"""

import argparse
import hashlib
import io
from pathlib import Path
import platform
from urllib.request import urlopen
import zipfile

URL = "https://github.com/MODFLOW-ORG/executables/releases/download/29.0/linux.zip"
ARCHIVE_SHA256 = "ab17192a3531dec61d4f4eab3da10f618e85d1f792d5edc71306a3e06e0e22c3"
EXECUTABLE_SHA256 = "479185be33167701696604f7bb55acb4f96476f396e9bb015cbe7da52e278ec4"


def install(directory):
    if platform.system() != "Linux" or platform.machine() != "x86_64":
        raise RuntimeError("The pinned test executable is for Linux x86-64")
    destination = Path(directory).resolve() / "mf6"
    if destination.is_symlink():
        raise ValueError("Refusing to use or replace a symlink")
    if destination.exists():
        if hashlib.sha256(destination.read_bytes()).hexdigest() != EXECUTABLE_SHA256:
            raise ValueError(f"Existing executable differs; left unchanged: {destination}")
        return destination
    with urlopen(URL, timeout=60) as response:
        archive = response.read(256 * 1024 * 1024 + 1)
    if hashlib.sha256(archive).hexdigest() != ARCHIVE_SHA256:
        raise ValueError("MODFLOW archive checksum mismatch; no executable written")
    with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
        executable = bundle.read("mf6")
    if hashlib.sha256(executable).hexdigest() != EXECUTABLE_SHA256:
        raise ValueError("MODFLOW executable checksum mismatch; no executable written")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("xb") as output:
        output.write(executable)
    destination.chmod(0o755)
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    print(install(parser.parse_args().directory))
