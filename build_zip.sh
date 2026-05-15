#!/usr/bin/env bash
# Build kodif-zendesk-integration-app.zip with package files at the ZIP root.
# Excludes build/validation scripts, the ZIP itself, and common dev artifacts.

set -euo pipefail

PKG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PKG_DIR"

ZIP_NAME="kodif-zendesk-integration-app.zip"

rm -f "$ZIP_NAME"

# Include manifest, translations, README, and every asset under assets/.
# Globbing assets/ means new logos/screenshots are picked up automatically.
zip -r "$ZIP_NAME" \
    manifest.json \
    translations \
    assets \
    README.md \
    -x "*.DS_Store" "__pycache__/*" "*.pyc"

echo
echo "Built $ZIP_NAME — contents:"
unzip -l "$ZIP_NAME"
