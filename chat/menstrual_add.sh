xa grep -l '^age:' | while read F; do P="$(( $RANDOM % 28 ))" ; sed -i '/^age:/ {s/$/\nperiod: '"$P"'/;}' "$F"; done
