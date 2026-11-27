#!/bin/sh
set -eu
TASK_TOOLS_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [ "$#" -eq 0 ]; then
  set -- update
fi
exec python3 "$TASK_TOOLS_ROOT/scripts/sync_tools.py" "$@"
