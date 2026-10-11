grep -h -o '([^)]*.jpg)' *.bb | tr -d '()' | uniqo | while read A; do mv ../"$A" .; done
