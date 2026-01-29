#!/usr/bin/env python3
"""
Generate a Pooch registry file from a directory of data files.

Usage:
    python create_registry.py <directory>
    python create_registry.py <directory> -o registry.txt
    python create_registry.py <directory> --algorithm md5
    python create_registry.py <directory> --recursive
"""

import argparse
import sys
from pathlib import Path

import pooch


def create_registry(
    directory: str,
    output: str = None,
    algorithm: str = "sha256",
    recursive: bool = False,
    exclude: list = None,
) -> dict:
    """
    Generate a registry of file hashes for a directory.

    Args:
        directory: Path to directory containing data files
        output: Output file path (None for stdout)
        algorithm: Hash algorithm ('sha256' or 'md5')
        recursive: Search subdirectories
        exclude: List of patterns to exclude

    Returns:
        dict mapping relative file paths to hash strings
    """
    exclude = exclude or [".git", "__pycache__", "*.pyc", ".DS_Store"]

    directory = Path(directory)
    if not directory.is_dir():
        raise ValueError(f"Not a directory: {directory}")

    # Find all files
    pattern = "**/*" if recursive else "*"
    files = [
        f for f in directory.glob(pattern)
        if f.is_file() and not any(f.match(ex) for ex in exclude)
    ]

    if not files:
        print(f"No files found in {directory}", file=sys.stderr)
        return {}

    # Generate hashes
    registry = {}
    for filepath in sorted(files):
        rel_path = filepath.relative_to(directory)
        try:
            file_hash = pooch.file_hash(str(filepath), alg=algorithm)
            registry[str(rel_path)] = f"{algorithm}:{file_hash}"
            print(f"Processed: {rel_path}", file=sys.stderr)
        except Exception as e:
            print(f"Error processing {rel_path}: {e}", file=sys.stderr)

    # Output registry
    lines = [f"{name} {hash_val}" for name, hash_val in registry.items()]
    content = "\n".join(lines) + "\n"

    if output:
        Path(output).write_text(content)
        print(f"\nRegistry written to: {output}", file=sys.stderr)
    else:
        print(content)

    return registry


def print_python_dict(registry: dict) -> None:
    """Print registry as Python dict for copy/paste."""
    print("\n# Python dict format:")
    print("registry = {")
    for name, hash_val in registry.items():
        print(f'    "{name}": "{hash_val}",')
    print("}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate Pooch registry from directory"
    )
    parser.add_argument("directory", help="Directory containing data files")
    parser.add_argument(
        "-o", "--output",
        help="Output file (default: stdout)"
    )
    parser.add_argument(
        "-a", "--algorithm",
        default="sha256",
        choices=["sha256", "md5"],
        help="Hash algorithm (default: sha256)"
    )
    parser.add_argument(
        "-r", "--recursive",
        action="store_true",
        help="Search subdirectories"
    )
    parser.add_argument(
        "--exclude",
        nargs="+",
        default=[".git", "__pycache__", "*.pyc", ".DS_Store"],
        help="Patterns to exclude"
    )
    parser.add_argument(
        "--python",
        action="store_true",
        help="Also print as Python dict"
    )

    args = parser.parse_args()

    try:
        registry = create_registry(
            args.directory,
            args.output,
            args.algorithm,
            args.recursive,
            args.exclude,
        )

        if args.python and registry:
            print_python_dict(registry)

        print(f"\nTotal files: {len(registry)}", file=sys.stderr)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
