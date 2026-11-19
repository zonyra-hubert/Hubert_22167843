#!/usr/bin/env bash
# Runs once when the Codespace is created.
set -e

echo ">>> Installing Python libraries"
pip install --upgrade pip
pip install -r requirements.txt

echo ">>> Creating .env from .env.example (if missing)"
[ -f .env ] || cp .env.example .env

echo ">>> Refreshing dates in the sample data (expiry dates, order dates)"
python scripts/refresh_dates.py

echo ">>> Pre-downloading Chroma's local embedding model (used in Lab 5)"
python - <<'EOF' || echo "Chroma warm-up skipped; it will download on first use in Lab 5."
import chromadb
c = chromadb.EphemeralClient().get_or_create_collection("warmup")
c.add(ids=["1"], documents=["warm up"])
print("Chroma embedding model ready")
EOF

echo ">>> Done. Run: python scripts/check_setup.py"
