#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

if [ ! -x ".venv/bin/python" ]; then
    echo "No encontré el entorno virtual todavía. Preparándolo (puede tardar un minuto)..."
    python3 enzo.py
fi

exec .venv/bin/python launcher.py
