#!/usr/bin/env bash
# setup.sh — Generate the Xcode project from project.yml
# Run this once (and again if you change project.yml).
set -e

cd "$(dirname "$0")"

if ! command -v xcodegen &>/dev/null; then
    echo "Installing XcodeGen via Homebrew…"
    brew install xcodegen
fi

xcodegen generate
echo ""
echo "✓ GameMotion.xcodeproj generated."
echo ""
echo "Next steps:"
echo "  1. Open GameMotion.xcodeproj in Xcode"
echo "  2. Set your Team ID in Signing & Capabilities (or in project.yml DEVELOPMENT_TEAM)"
echo "  3. Build and run to test locally"
echo "  4. When ready to submit: see build_mas.sh"
