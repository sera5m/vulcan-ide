#!/bin/sh
cd "$(dirname "$0")"
export PYTHONPATH="$(pwd):${PYTHONPATH:-}"
exec python3 vulcan_ide.py "$@"
