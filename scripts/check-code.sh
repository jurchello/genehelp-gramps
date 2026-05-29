#!/usr/bin/env bash
set -euo pipefail

PY_FILES=(
    Genehelp.py
    Genehelp.gpr.py
    genehelp/*.py
    genehelp/extractors/*.py
    tests/*.py
)

MYPY_FILES=(
    genehelp/api_client.py
    genehelp/api_contract.py
    genehelp/config.py
    genehelp/countries.py
    genehelp/diagnostics.py
    genehelp/gramps_context.py
    genehelp/help_offer.py
    genehelp/models.py
    genehelp/payloads.py
    genehelp/genealogy_requests.py
    genehelp/themes.py
    genehelp/extractors/*.py
    tests/*.py
)

python3 -m py_compile "${PY_FILES[@]}"
python3 -c "import sys; sys.path.insert(0, '.'); import Genehelp; print('import ok')"

for file in "${PY_FILES[@]}"; do
    black --check "$file"
done

ruff check "${PY_FILES[@]}"
mypy "${MYPY_FILES[@]}"
XDG_CACHE_HOME="${XDG_CACHE_HOME:-/tmp}" pylint \
    Genehelp.py genehelp/*.py genehelp/extractors/*.py tests/*.py
pytest tests
