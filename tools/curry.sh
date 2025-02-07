#!/bin/bash
set -e -u
fn="$1" ; shift
fn_b=`basename "$fn"`
args_s=`printf "%q_" "$fn_b" "$@"`
args_s=${args_s%_}
args_s=${args_s//\//__}
wrapper=`mktemp_clean -t "$args_s.XXXXXXXXXX"`
echo "$wrapper"
exec >"$wrapper"
echo "#!/bin/sh"
printf "%q " "exec" "$fn" "$@"
echo '"$@"'
chmod +x "$wrapper"
