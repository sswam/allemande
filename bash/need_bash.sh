if [ -z "$BASH_VERSION" ] && [ -z "ZSH_VERSION" ]; then
	echo >&2 "This tool needs bash or zsh."
	exit 1
fi
