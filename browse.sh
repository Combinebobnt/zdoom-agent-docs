#!/bin/sh
# Opens the docs browser (tools/browse.py). First run creates .venv with the optional renderer.
set -e
cd "$(dirname "$0")"
PY=.venv/bin/python
if [ ! -x "$PY" ]; then
    python3 -m venv .venv
fi
if ! "$PY" -c "import markdown_it, mdit_py_plugins, pygments" 2>/dev/null; then
    "$PY" -m pip install --quiet markdown-it-py mdit-py-plugins pygments \
        || echo "Renderer install failed; pages will show as plain text." >&2
fi
exec "$PY" tools/browse.py --open "$@"
