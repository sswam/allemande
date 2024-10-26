X=${0%.c}
if [ "$0" -nt "$X" ]; then
	make -s "$X" || exit 120
fi
exec "$X" "$@"
echo >&2 "exec failed"
exit 121
