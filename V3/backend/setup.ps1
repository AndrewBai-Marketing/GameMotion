# GameMotion Backend Setup Script (Windows)

Write-Host "🎮 GameMotion Setup" -ForegroundColor Cyan
Write-Host "==================="

# Check for uv, install if missing
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "📦 Installing uv (fast Python package manager)..."
    irm https://astral.sh/uv/install.ps1 | iex
}

# Create venv and install deps
Write-Host "📦 Creating virtual environment and installing dependencies..."
uv venv .venv
uv pip install -r requirements.txt

Write-Host ""
Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "To run GameMotion:"
Write-Host "  .\.venv\Scripts\activate"
Write-Host "  python -m gamemotion_backend.main --preview"
