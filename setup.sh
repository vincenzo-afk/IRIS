#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────
# IRIS Setup Script
# Run: bash setup.sh
# ──────────────────────────────────────────────────────────────

set -e

echo "╔═══════════════════════════════╗"
echo "║   IRIS Setup & Installation   ║"
echo "╚═══════════════════════════════╝"

# ── 1. Python version check ─────────────────────────────────
echo ""
echo "[1/5] Checking Python..."
python3 --version || { echo "Python 3 not found. Install it first."; exit 1; }

# ── 2. Virtual environment ──────────────────────────────────
echo ""
echo "[2/5] Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "     Created venv/"
else
    echo "     venv/ already exists"
fi

source venv/bin/activate

# ── 3. Upgrade pip ──────────────────────────────────────────
echo ""
echo "[3/5] Upgrading pip..."
pip install --upgrade pip --quiet

# ── 4. Install requirements ─────────────────────────────────
echo ""
echo "[4/5] Installing dependencies (this may take a few minutes)..."
pip install -r requirements.txt

# ── 5. Env file ─────────────────────────────────────────────
echo ""
echo "[5/5] Setting up .env..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "     Created .env from .env.example"
    echo ""
    echo "┌─────────────────────────────────────────────────────┐"
    echo "│  ACTION REQUIRED: Edit .env and add your API keys   │"
    echo "│  → GEMINI_API_KEY (https://aistudio.google.com)     │"
    echo "└─────────────────────────────────────────────────────┘"
else
    echo "     .env already exists"
fi

echo ""
echo "✅  IRIS setup complete!"
echo ""
echo "To run IRIS:"
echo "  source venv/bin/activate"
echo "  python main.py"
echo ""
echo "Or with a specific mode:"
echo "  python main.py --mode chat"
echo "  python main.py --mode voice"
echo "  python main.py --mode teach"
echo "  python main.py --mode do --task 'Open Chrome and search for weather'"
