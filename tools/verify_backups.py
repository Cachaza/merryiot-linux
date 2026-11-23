#!/usr/bin/env python3
"""Verify regular backup image files against trusted acquisition records."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat


def verify(root, manifest):
    root = Path(root).resolve(strict=True)
    if not root.is_dir():
        raise ValueError('Backup root must be a directory.')
    records = manifest.get('files') if isinstance(manifest, dict) else None
    if not isinstance(records, list) or not records:
        raise ValueError('Manifest must contain a nonempty files list.')
    checked, seen = [], set()
    for item in records:
        if not isinstance(item, dict):
            raise ValueError('Each manifest record must be an object.')
        name, size, digest = item.get('path'), item.get('bytes'), item.get('sha256')
        if not isinstance(name, str) or not name or Path(name).is_absolute() or '..' in Path(name).parts:
            raise ValueError('Image paths must be relative and stay under the backup root.')
        relative = Path(name)
        if not relative.parts:
            raise ValueError('Image path must name a regular file, not the root directory.')
        if relative in seen:
            raise ValueError(f'Duplicate image path: {name}')
        seen.add(relative)
        if type(size) is not int or size < 0 or not isinstance(digest, str) or not re.fullmatch(r'[0-9a-fA-F]{64}', digest):
            raise ValueError(f'Invalid byte length or SHA-256 for {name}. Use trusted acquisition records.')
        # Walk without following symlinks, including parent directories. dir_fd and
        # O_NOFOLLOW also prevent a path being swapped to a symlink during verification.
        parent_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
        fd = None
        try:
            for part in relative.parts[:-1]:
                child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent_fd)
                os.close(parent_fd)
                parent_fd = child
            fd = os.open(relative.parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent_fd)
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode):
                raise ValueError(f'{name} is not a regular image file; block devices are not accepted.')
            if info.st_size != size:
                raise ValueError(f'{name}: expected {size} bytes, found {info.st_size}. Recheck the image and acquisition manifest.')
            with os.fdopen(fd, 'rb') as source:
                fd = None
                actual = hashlib.file_digest(source, 'sha256').hexdigest()
            if actual != digest.lower():
                raise ValueError(f'{name}: SHA-256 mismatch (expected {digest.lower()}, found {actual}). Preserve the file and investigate; do not flash it.')
            checked.append(name)
        finally:
            if fd is not None:
                os.close(fd)
            os.close(parent_fd)
    return checked


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--manifest', required=True, type=Path)
    args = parser.parse_args()
    try:
        checked = verify(args.root, json.loads(args.manifest.read_text()))
    except (OSError, ValueError, IndexError) as exc:
        parser.exit(1, f'Verification failed: {exc}\n')
    for name in checked:
        print(f'OK {name}')
    print('All listed files match the manifest. This is not a restore test.')


if __name__ == '__main__':
    main()
