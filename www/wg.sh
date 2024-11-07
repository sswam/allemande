#!/bin/bash
# this is a wget that pretends to be a browser

# You can set $REFERER to "self", or the url of the previous page, if needed.

. unset-option-vars

t=5
r=5
C=	# no content-disposition
O=	# output file
v=	# verbose

OPTS_COLLECT_UNKNOWN=1 eval "$(ally)"  # TODO this is error prone as opts already in the environment won't be passed through

timeout=$t
tries=$r

: ${CF:=} ${CF_SQLITE:=} ${REFERER:=} ${WG_OPTS:=}

if [ -n "$O" ]; then
	C=1
	O=("-O$O")
else
	O=()
fi

if [ "$v" = 1 ]; then
	v=v
fi

AGENT="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
#CF=${CF:-`echo "$HOME/.mozilla/default/"*"/cookies.txt"`}
if [ -n "$CF" ]; then
	CF_SQLITE="/bogus-$$"
elif [ -n "$CF_SQLITE" ]; then
	CF=${CF_SQLITE%.sqlite}.txt
else
	CF=`echo "$HOME/.mozilla/firefox/"*.default"/cookies.txt"`
	CF_SQLITE=`echo "$HOME/.mozilla/firefox/"*.default"/cookies.sqlite"`
	if [ ! -e "$CF" ]; then
		CF=${CF_SQLITE%.sqlite}.txt
	fi
#	CF_SQLITE_SHM=`echo "$HOME/.mozilla/firefox/"*.default"/cookies.sqlite-shm"`
#	if [ -e "$CF_SQLITE_SHM" ]; then
#		CF_SQLITE="$CF_SQLITE_SHM"
#	fi
fi
if [ -e "$CF_SQLITE" ]; then
	if [ "$CF_SQLITE" -nt "$CF" ]; then
		CF1="$CF.$$"
		v cookies-sql2txt "$CF_SQLITE" % > "$CF1"
		mv "$CF1" "$CF"
	fi
fi
if [ "$REFERER" = self ]; then
	for a; do
		case "$a" in
		*://*) REFERER="$a"; break ;;
		esac
	done
fi
# echo "cookies: $CF"

content_disposition=
if [ "$C" != 1 ]; then
	content_disposition=`wget --help | q grep 'content-disposition' && echo "--content-disposition"`
fi

if [ -n "$REFERER" ]; then
	exec $v wget -e robots=off --no-check-certificate $content_disposition -T "$timeout" --load-cookies="$CF" -U"$AGENT" --referer="$REFERER" --tries $tries $WG_OPTS "${OPTS_UNKNOWN[@]}" "${O[@]}" -- "$@"
#	wget "$HEADER" -U"$AGENT" --referer="$REFERER" "$@"
else
	exec $v wget -e robots=off --no-check-certificate $content_disposition -T "$timeout" --load-cookies="$CF" -U"$AGENT" --tries $tries $WG_OPTS "${OPTS_UNKNOWN[@]}" "${O[@]}" -- "$@"
#	wget "$HEADER" -U"$AGENT" "$@"
fi
