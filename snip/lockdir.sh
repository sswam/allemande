# prevent concurrent runs
LOCKDIR="script.lock"
if ! mkdir "$LOCKDIR" 2>/dev/null; then
    echo "Lock exists: $LOCKDIR"
    exit 1
fi
trap 'rmdir "$LOCKDIR"' EXIT
