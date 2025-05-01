#!/bin/bash
for s; do
f=${s#*.}
if [ "$f" != "$s" ]; then
	f=".$f"
	s=${s%%.*}
else
	f=
fi
sign=""
if [ $s -lt 0 ]; then
	sign=-
	s=$((-$s))
fi
s=${s%.*}
m=$(($s / 60))
s=$(($s % 60))
h=$(($m / 60))
m=$(($m % 60))
printf "%s%02d:%02d:%02d%s\n" "$sign" "$h" "$m" "$s" "$f"
done
