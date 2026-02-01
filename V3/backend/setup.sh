#!/bin/bash
# GameMotion Backend Setup Script
# Works on macOS and Linux

set -e

echo "🎮 GameMotion Setup"
echo "==================="

# Check for uv, install if missing
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv (fast Python package manager)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Create venv and install deps with uv
echo "📦 Creating virtual environment and installing dependencies..."
uv venv .venv
uv pip install -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "To run GameMotion:"
echo "  source .venv/bin/activate"
echo "  python -m gamemotion_backend.main --preview"
