find "$@" -maxdepth 1 -mindepth 1 -type d \! -name '.*' | sed 's,^\./,,' | LC_ALL=C sort
