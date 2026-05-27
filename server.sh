#!/bin/sh
set -eu

REPO_RAW_URL="${USAGE_REMIND_RAW_URL:-https://raw.githubusercontent.com/ozbillwang/usage-remind/main/server.py}"
INSTALL_DIR="${USAGE_REMIND_HOME:-$HOME/.usage-remind}"
TARGET="$INSTALL_DIR/server.py"
PID_FILE="$INSTALL_DIR/server.pid"
PORT="${USAGE_REMIND_PORT:-8765}"

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" 2>/dev/null && pwd || pwd)

if [ -f "$SCRIPT_DIR/server.py" ]; then
  TARGET="$SCRIPT_DIR/server.py"
else
  mkdir -p "$INSTALL_DIR"
  curl -fsSL "$REPO_RAW_URL" -o "$TARGET"
fi

mkdir -p "$INSTALL_DIR"

if command -v lsof >/dev/null 2>&1 && lsof -ti "tcp:$PORT" >/dev/null 2>&1; then
  echo "Usage Remind already appears to be running on http://127.0.0.1:$PORT"
  echo "API: http://127.0.0.1:$PORT/api/usage"
  exit 0
fi

nohup python3 "$TARGET" >/dev/null 2>&1 &
PID=$!
echo "$PID" > "$PID_FILE"

echo "Usage Remind started in the background."
echo "PID: $PID"
echo "Page: http://127.0.0.1:$PORT"
echo "API: http://127.0.0.1:$PORT/api/usage"
