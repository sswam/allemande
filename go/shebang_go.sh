X=${0%.go}
if [ "$0" -nt "$X" ]; then
	go build -ldflags="-s -w" -trimpath "$0" || exit 120
fi
exec "$X" "$@"
echo >&2 "exec failed"
exit 121
