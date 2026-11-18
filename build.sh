#!/bin/sh
# Builds dist/dragon_of_digbeth.cpr (needs python3 + Pillow and rasm on PATH)
set -e
cd "$(dirname "$0")"
python3 tools/build_assets.py
(cd src && rasm main.asm -oc ../build/digbeth && rm -f rasmoutput.sym)
mkdir -p dist
mv build/digbeth dist/dragon_of_digbeth.cpr 2>/dev/null || mv build/digbeth.cpr dist/dragon_of_digbeth.cpr
echo "built dist/dragon_of_digbeth.cpr"
