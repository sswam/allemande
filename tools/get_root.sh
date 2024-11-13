if [ `id -u` != 0 ]; then
	exec sudo -E --preserve-env=PATH,PYTHONPATH,PERL5LIB "$0" "$@"
	exit $?
fi
