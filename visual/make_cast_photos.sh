#!/bin/bash
# This script generates character photos for the cast using a1111-client.
N=1
limit_n_chars=10000
cd ~/cast/
jily="juggernautXL_juggXIByRundiffusion"
coni="cyberrealisticPony_v85"
poni="autismmixSDXL_autismmixConfetti"
#	"anime $poni 7 cast_anime square" \
for type_model_cfg_macro in \
	"jily $jily 4.5 cast_photo square" \
	"coni $coni 5 cast_photo square" \
	"coni1 $coni 5 cast_profile square" \
	"toon $poni 7 cast_toon square" \
	"jreal $jily 4.5 cast_real square" \
	"creal $coni 5 cast_real_pony square" \
	"sjily $jily 4.5 cast_standing portrait_tall" \
	"sconi $coni 5 cast_standing portrait_tall" \
	"topless $jily 4.5 cast_topless square" \
	"ctopless $coni 5 cast_topless square" \
	"nude $coni 5 cast_nude portrait_tall" \
	; do
	read -r type model cfg macro shape <<< "$type_model_cfg_macro"
	grep -l '^visual:' $ALLEMANDE_AGENTS/*/*.yml |
	head -n $limit_n_chars |
	while read file; do
		char=${file##*/}; char=${char%.yml}
		if [ -d "$char/$type" ]; then
			continue
		fi
		mkdir -p "$char/$type"
		(
			echo "$type - $char"
			cd "$char/$type"
			a1111-client --count "$N" --model "$model" --cfg-scale "$cfg" --pag 3 --adetailer "face_yolov8n.pt" --ad-mask-k-largest 10 --hires 1.5 --prompt "[sets char=\"$char\"] [use $macro] [use $shape] [sets steps=30]"
			sleep 1
#			a1111-client --count "$N" --model "$model" --cfg-scale "$cfg" --pag 3 --prompt "[sets char=\"$char\"] [use $macro] [use square] [sets steps=15]"
		)
	done
done
