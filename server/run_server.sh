#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLAY_SERVER_DIR="${SCRIPT_DIR}"

echo "Starting Play Palace v11 Server..."
cd "${PLAY_SERVER_DIR}"

VENV_DIR="${PLAY_SERVER_DIR}/.venv"
PYTHON_BIN=""
if [ -x "${VENV_DIR}/bin/python3" ]; then
    PYTHON_BIN="${VENV_DIR}/bin/python3"
elif [ -x "${VENV_DIR}/bin/python" ]; then
    PYTHON_BIN="${VENV_DIR}/bin/python"
elif [ -x "${VENV_DIR}/Scripts/python.exe" ]; then
    PYTHON_BIN="${VENV_DIR}/Scripts/python.exe"
fi

if [ -z "${PYTHON_BIN}" ]; then
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_BIN="python3"
    else
        PYTHON_BIN="python"
    fi
else
    PATH="${VENV_DIR}/bin:${VENV_DIR}/Scripts:${PATH}"
fi

"${PYTHON_BIN}" -m pip install --upgrade pip
if ! "${PYTHON_BIN}" -m pip show uv >/dev/null 2>&1; then
    echo "Installing uv into the virtual environment..."
    "${PYTHON_BIN}" -m pip install uv
fi

"${PYTHON_BIN}" -m uv sync
"${PYTHON_BIN}" -m uv run python main.py
