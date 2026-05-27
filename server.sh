#!/bin/sh
set -eu

REPO_RAW_URL="${USAGE_REMIND_RAW_URL:-https://raw.githubusercontent.com/ozbillwang/usage-remind/main/server.py}"
INSTALL_DIR="${USAGE_REMIND_HOME:-$HOME/.usage-remind}"
TARGET="$INSTALL_DIR/server.py"

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" 2>/dev/null && pwd || pwd)

if [ -f "$SCRIPT_DIR/server.py" ]; then
  exec python3 "$SCRIPT_DIR/server.py"
fi

mkdir -p "$INSTALL_DIR"
curl -fsSL "$REPO_RAW_URL" -o "$TARGET"
exec python3 "$TARGET"
