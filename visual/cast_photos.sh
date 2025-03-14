#!/bin/bash
# draw 10 photos of each cast member to choose from
N=10
while read char; do
	echo "$char"
	mkdir -p "$char"
	(
		cd "$char"
		a1111-client --count "$N" --model "juggernautXL_juggXIByRundiffusion" --cfg-scale 4.5 --pag --adetailer "face_yolov8n.pt" --ad-mask-k-largest 10 --hires 1.5 --prompt "[sets char=\"$char\"] [use cast] [use square] [sets steps=30]"
	)
done < people.txt
