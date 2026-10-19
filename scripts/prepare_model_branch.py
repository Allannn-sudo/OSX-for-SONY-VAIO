#!/usr/bin/env python3
"""Prepare the fixed VGN-Y18C README pair and content manifest, locally only.

This helper never creates a Git branch, commits, contacts GitHub or loads drivers.
The manually dispatched workflow owns those Git operations. Repository/model
arguments are deliberate scope guards, not a claim to authenticate a checkout.
"""

import argparse
import hashlib
import json
from pathlib import Path
import sys


REPOSITORY = "Allannn-sudo/OSX-for-SONY-VAIO"
MODEL = "vgn-y18c"
MANIFEST = "MANIFEST.sha256"
LAYOUT = "evidence/repository-layout.json"
TEMPLATES = (
    (".github/branch-readmes/vgn-y18c.zh-CN.md", "README.md"),
    (".github/branch-readmes/vgn-y18c.en.md", "README.en.md"),
)
IGNORED_COMPONENTS = {".git", "__pycache__", ".DS_Store"}


def snapshot_files(root):
    """Return all regular snapshot files; refuse ambiguous paths and symlinks."""
    root = Path(root)
    files = []
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if any(part in IGNORED_COMPONENTS for part in relative.parts):
            continue
        if path.suffix == ".pyc":
            continue
        if path.is_symlink():
            raise ValueError("Refusing symlink: " + relative.as_posix())
        if path.is_dir():
            continue
        if not path.is_file():
            raise ValueError("Not a regular file: " + relative.as_posix())
        name = relative.as_posix()
        if any(character in name for character in "\r\n\\"):
            raise ValueError("Ambiguous manifest path: " + repr(name))
        if name != MANIFEST:
            files.append((name, path))
    return sorted(files)


def manifest_bytes(root, replacements=None):
    """Calculate a deterministic sha256sum-compatible manifest."""
    replacements = replacements or {}
    rows = []
    seen = set()
    for name, path in snapshot_files(root):
        content = replacements.get(name)
        if content is None:
            content = path.read_bytes()
        rows.append((name, hashlib.sha256(content).hexdigest()))
        seen.add(name)
    for name, content in replacements.items():
        if name not in seen:
            rows.append((name, hashlib.sha256(content).hexdigest()))
    return "".join(digest + "  " + name + "\n" for name, digest in sorted(rows)).encode("utf-8")


def write_manifest(root):
    """Regenerate the archive manifest without changing the README files."""
    root = Path(root)
    content = manifest_bytes(root)
    manifest = root / MANIFEST
    if manifest.is_symlink():
        raise ValueError("Refusing symlink: " + MANIFEST)
    manifest.write_bytes(content)


def prepare_model_branch(root, repository, model):
    if repository != REPOSITORY:
        raise ValueError("This helper is scoped to " + REPOSITORY)
    if model != MODEL:
        raise ValueError("The only supported model branch is " + MODEL)
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise ValueError("Root must be an existing, non-symlink directory")
    replacements = {}
    # Validate the entire tree and both inputs before writing either README.
    snapshot_files(root)
    for source, destination in TEMPLATES:
        content = (root / source).read_bytes()
        if not content.strip():
            raise ValueError("Empty branch README: " + source)
        content.decode("utf-8")
        replacements[destination] = content
    layout = json.loads((root / LAYOUT).read_text(encoding="utf-8"))
    if (not isinstance(layout, dict) or
            layout.get("repository") != REPOSITORY or
            layout.get("project_branch") != "main" or
            not isinstance(layout.get("model_branches"), dict) or
            MODEL not in layout.get("model_branches", {})):
        raise ValueError("Repository layout does not match the fixed repository/model")
    layout["active_readme"] = MODEL
    replacements[LAYOUT] = (json.dumps(layout, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    manifest = manifest_bytes(root, replacements)
    for destination, content in replacements.items():
        (root / destination).write_bytes(content)
    (root / MANIFEST).write_bytes(manifest)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--repository", required=True)
    parser.add_argument("--model", default=MODEL)
    args = parser.parse_args(argv)
    try:
        prepare_model_branch(args.root, args.repository, args.model)
    except (OSError, UnicodeError, ValueError) as error:
        parser.exit(1, "Preparation refused: " + str(error) + "\n")
    print("Prepared VGN-Y18C READMEs, layout marker and manifest locally; no Git operation performed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
