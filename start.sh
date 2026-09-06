#!/bin/sh
cd "$(dirname "$0")"
if [ ! -f vulcan_ide.py ]; then
  echo "vulcan_ide.py missing — git pull" >&2
  exit 1
fi
export PYTHONPATH="$(pwd):${PYTHONPATH:-}"
exec python3 vulcan_ide.py "$@"
