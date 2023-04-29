if [ `id -u` != 0 ]; then
	exec sudo -E "$0" "$@"
	exit $?
fi
