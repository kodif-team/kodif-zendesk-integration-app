#!/usr/bin/env python3
"""Validate the Kodif Zendesk Integration App package.

Checks that the package satisfies the acceptance criteria for a Zendesk
Marketing-only / Integration App submission:

- Required files exist
- manifest.json has marketingOnly: true and no forbidden fields
- translations/en.json has the required app keys
- No secrets, backend code, or internal artifacts are present
- (Optional, when run with --zip <path>) the ZIP has files at the root
"""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path

PKG_DIR = Path(__file__).resolve().parent

REQUIRED_FILES = [
    "manifest.json",
    "translations/en.json",
    "assets/logo.png",
    "assets/logo-small.png",
    "README.md",
]

FORBIDDEN_MANIFEST_KEYS = ["frameworkVersion", "location"]

REQUIRED_TRANSLATION_KEYS = [
    "name",
    "short_description",
    "long_description",
    "installation_instructions",
]

# Substrings/file names that must not appear in the package or ZIP
FORBIDDEN_PATH_FRAGMENTS = [
    ".env",
    ".git/",
    "__pycache__",
    "node_modules",
    ".DS_Store",
]


def fail(errors: list[str], msg: str) -> None:
    errors.append(msg)


def validate_directory(errors: list[str]) -> None:
    for rel in REQUIRED_FILES:
        path = PKG_DIR / rel
        if not path.is_file():
            fail(errors, f"missing required file: {rel}")

    manifest_path = PKG_DIR / "manifest.json"
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text())
        except json.JSONDecodeError as e:
            fail(errors, f"manifest.json is not valid JSON: {e}")
            return

        if manifest.get("marketingOnly") is not True:
            fail(errors, 'manifest.json must include "marketingOnly": true')
        default_locale = manifest.get("defaultLocale")
        if not default_locale:
            fail(errors, 'manifest.json must include "defaultLocale" (e.g. "en")')
        elif not (PKG_DIR / "translations" / f"{default_locale}.json").is_file():
            fail(
                errors,
                f"manifest.json defaultLocale '{default_locale}' has no matching translations/{default_locale}.json",
            )
        for key in FORBIDDEN_MANIFEST_KEYS:
            if key in manifest:
                fail(errors, f"manifest.json must not include forbidden key: {key}")
        author = manifest.get("author") or {}
        for key in ("name", "email", "url"):
            if not author.get(key):
                fail(errors, f"manifest.json author.{key} is required")
        if not manifest.get("name"):
            fail(errors, "manifest.json name is required")
        if not manifest.get("version"):
            fail(errors, "manifest.json version is required")

    tr_path = PKG_DIR / "translations/en.json"
    if tr_path.is_file():
        try:
            tr = json.loads(tr_path.read_text())
        except json.JSONDecodeError as e:
            fail(errors, f"translations/en.json is not valid JSON: {e}")
            return
        app = tr.get("app") or {}
        for key in REQUIRED_TRANSLATION_KEYS:
            if not app.get(key):
                fail(errors, f"translations/en.json missing app.{key}")


def validate_zip(zip_path: Path, errors: list[str]) -> None:
    if not zip_path.is_file():
        fail(errors, f"ZIP not found: {zip_path}")
        return
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()

    if not any(n == "manifest.json" for n in names):
        fail(errors, "ZIP must contain manifest.json at the root (no parent folder)")

    for required in REQUIRED_FILES:
        if required not in names:
            fail(errors, f"ZIP missing required entry: {required}")

    for name in names:
        for bad in FORBIDDEN_PATH_FRAGMENTS:
            if bad in name:
                fail(errors, f"ZIP contains forbidden entry: {name}")
        # Disallow validator/build scripts inside the ZIP
        if name in ("validate_package.py", "build_zip.sh"):
            fail(errors, f"ZIP must not contain: {name}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zip", type=Path, default=None, help="Optional path to ZIP to validate")
    args = parser.parse_args()

    errors: list[str] = []
    validate_directory(errors)
    if args.zip is not None:
        validate_zip(args.zip, errors)

    if errors:
        print("Validation FAILED:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("Validation OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
