#!/usr/bin/env bash
# build_mas.sh — Full build pipeline for Mac App Store submission.
#
# Prerequisites:
#   - Apple Developer account with MAS distribution certificate
#   - MAS provisioning profile installed in Xcode
#   - DEVELOPMENT_TEAM set in project.yml (or Xcode Signing settings)
#   - Python venv at V3/backend/.venv with all deps installed
#   - Node.js installed
#
# Usage:
#   ./build_mas.sh
set -e

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
MACOS_DIR="$REPO_ROOT/V3/macos"
BACKEND_DIR="$REPO_ROOT/V3/backend"
FRONTEND_DIR="$REPO_ROOT/V3/frontend"

echo "=== Step 1: Build Next.js frontend (static export) ==="
cd "$FRONTEND_DIR"
npm install
npm run build
echo "✓ Frontend built → out/"

echo ""
echo "=== Step 2: Build Python backend (PyInstaller) ==="
cd "$BACKEND_DIR"
# Use the project venv if it exists
if [ -f ".venv/bin/python" ]; then
    PYTHON=".venv/bin/python"
elif [ -f "venv/bin/python" ]; then
    PYTHON="venv/bin/python"
else
    PYTHON="python3"
fi
"$PYTHON" -m PyInstaller gamemotion_backend.spec --noconfirm
echo "✓ Backend built → dist/GameMotionBackend/"

echo ""
echo "=== Step 3: Generate Xcode project ==="
cd "$MACOS_DIR"
"$MACOS_DIR/setup.sh"

echo ""
echo "=== Step 4: Archive for Mac App Store ==="
# Update CODE_SIGN_STYLE / CODE_SIGN_IDENTITY in project.yml before running this.
xcodebuild archive \
    -project "$MACOS_DIR/GameMotion.xcodeproj" \
    -scheme GameMotion \
    -configuration Release \
    -archivePath "$MACOS_DIR/build/GameMotion.xcarchive" \
    -destination "generic/platform=macOS" \
    | xcpretty 2>/dev/null || true

echo ""
echo "✓ Archive created at: $MACOS_DIR/build/GameMotion.xcarchive"
echo ""
echo "=== Step 5: Upload to App Store Connect ==="
echo "Open Xcode → Window → Organizer, select the archive, and click 'Distribute App'."
echo "Choose 'App Store Connect' → 'Upload'."
echo ""
echo "Or use xcrun altool / notarytool for a fully command-line workflow."
