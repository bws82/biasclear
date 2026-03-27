#!/bin/bash
# BiasClear reviewer bootstrap
# Creates a clean reviewer venv with Python 3.11+ and runs the same install path as CI.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON_BIN="${1:-}"
VENV_DIR="${ROOT_DIR}/.venv-reviewer"

pick_python() {
  if [ -n "${PYTHON_BIN}" ]; then
    echo "${PYTHON_BIN}"
    return
  fi

  for candidate in python3.12 python3.11; do
    if command -v "${candidate}" >/dev/null 2>&1; then
      echo "${candidate}"
      return
    fi
  done

  echo ""
}

PYTHON_BIN="$(pick_python)"

if [ -z "${PYTHON_BIN}" ]; then
  echo "Error: Python 3.11+ not found."
  echo "BiasClear's canonical reviewer path requires Python 3.11+."
  echo "CI uses Python 3.12 and installs: pip install -e \".[api,dev]\""
  echo ""
  echo "Usage:"
  echo "  ./scripts/reviewer_bootstrap.sh"
  echo "  ./scripts/reviewer_bootstrap.sh /path/to/python3.12"
  exit 1
fi

"${PYTHON_BIN}" - <<'PY'
import sys
if sys.version_info < (3, 11):
    raise SystemExit("Error: BiasClear reviewer bootstrap requires Python 3.11+.")
print(f"Using Python {sys.version.split()[0]}")
PY

cd "${ROOT_DIR}"

rm -rf "${VENV_DIR}"
"${PYTHON_BIN}" -m venv "${VENV_DIR}"
source "${VENV_DIR}/bin/activate"

python -m pip install --upgrade pip
python -m pip install -e ".[api,dev]"
python -m pytest tests/ -q

echo ""
echo "Reviewer bootstrap completed successfully."
echo "Virtualenv: ${VENV_DIR}"
