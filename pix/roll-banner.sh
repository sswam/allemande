#!/bin/bash -x
# roll-banner.sh: roll banner.png to banner1.png, banner2.png, etc.

offset=256

for i in {1..7}; do
	x=$((i*offset))
	convert banner.png -roll -${x}x0 banner${i}.png
done
if [ ! -e banner0.png ]; then
	ln -s banner.png banner0.png
fi

for f in banner?.png; do
	j=${f%.png}.jpg
	v convert $f $j
done
