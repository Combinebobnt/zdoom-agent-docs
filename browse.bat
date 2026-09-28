@echo off
rem Opens the docs browser (tools\browse.py). First run creates .venv with the optional renderer.
cd /d "%~dp0"
set PY=.venv\Scripts\python.exe
if not exist "%PY%" (
    py -3 -m venv .venv 2>nul || python -m venv .venv
)
if not exist "%PY%" (
    echo Could not create .venv. Is Python 3 installed and on PATH?
    pause
    exit /b 1
)
"%PY%" -c "import markdown_it, mdit_py_plugins, pygments" 2>nul
if errorlevel 1 (
    "%PY%" -m pip install --quiet markdown-it-py mdit-py-plugins pygments || echo Renderer install failed; pages will show as plain text.
)
"%PY%" tools\browse.py --open %*
if errorlevel 1 pause
