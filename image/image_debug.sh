qe image-params "$1" | sed '/^Negative prompt/q' | grep -v -e '^Parameters:' -e '^Negative prompt:' -e '^Steps:' -e '^$' | sort_by_max -f | grep --color -e '[0-9]*\.[0-9][0-9]*' -C 100
