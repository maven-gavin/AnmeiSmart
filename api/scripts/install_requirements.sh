#!/usr/bin/env bash
# Install api Python deps with long timeouts. Prefers Tsinghua mirror (China),
# falls back to Aliyun, then official PyPI.
set -euo pipefail

API_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$API_ROOT"

if [[ -x "${API_ROOT}/venv/bin/pip" ]]; then
  PIP=( "${API_ROOT}/venv/bin/pip" )
else
  PIP=( pip )
fi

: "${PIP_DEFAULT_TIMEOUT:=300}"

try_install() {
  local name="$1"
  local index="$2"
  local host="$3"
  echo "[install_requirements] Trying ${name} ..."
  "${PIP[@]}" install -r requirements.txt \
    --default-timeout="${PIP_DEFAULT_TIMEOUT}" \
    -i "${index}" \
    --trusted-host "${host}"
}

if try_install "Tsinghua mirror" "https://pypi.tuna.tsinghua.edu.cn/simple" "pypi.tuna.tsinghua.edu.cn"; then
  exit 0
fi
if try_install "Aliyun mirror" "https://mirrors.aliyun.com/pypi/simple" "mirrors.aliyun.com"; then
  exit 0
fi
echo "[install_requirements] Falling back to pypi.org ..."
"${PIP[@]}" install -r requirements.txt \
  --default-timeout="${PIP_DEFAULT_TIMEOUT}" \
  -i "https://pypi.org/simple"
