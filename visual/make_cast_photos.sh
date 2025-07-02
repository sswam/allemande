#!/bin/bash
# This script generates character photos for the cast using a1111-client.
N=1
cd ~/cast/
for type_model_cfg_macro in \
	"jily juggernautXL_juggXIByRundiffusion 4.5 cast_photo" \
	"coni cyberrealisticPony_v85 5 cast_photo" \
	"coni1 cyberrealisticPony_v85 5 cast_profile" \
	"poni autismmixSDXL_autismmixConfetti 7 cast_anime" \
	"jreal juggernautXL_juggXIByRundiffusion 4.5 cast_real" \
	"creal cyberrealisticPony_v85 5 cast_real_pony" \
	"topless juggernautXL_juggXIByRundiffusion 4.5 cast_topless" \
	; do
	read -r type model cfg macro <<< "$type_model_cfg_macro"
	grep -l '^visual:' $ALLEMANDE_AGENTS/*/*.yml |
	while read file; do
		char=${file##*/}; char=${char%.yml}
		if [ -d "$type/$char" ]; then
			continue
		fi
		mkdir -p "$type/$char"
		(
			echo "$type - $char"
			cd "$type/$char"
			a1111-client --count "$N" --model "$model" --cfg-scale "$cfg" --pag 3 --adetailer "face_yolov8n.pt" --ad-mask-k-largest 10 --hires 1.5 --prompt "[sets char=\"$char\"] [use $macro] [use square] [sets steps=30]"
			sleep 1
#			a1111-client --count "$N" --model "$model" --cfg-scale "$cfg" --pag 3 --prompt "[sets char=\"$char\"] [use $macro] [use square] [sets steps=15]"
		)
	done
done
