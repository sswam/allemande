#!/usr/bin/env bash
# input.png output.png "Your text here"
# Add text with drop shadow to an image
# version: 0.1.1

# shellcheck disable=SC1007,SC2034

image-add-text() {
	local font= f="DejaVu-Sans"  # font name
	local size= s=36             # font point size
	local gravity= g=Southeast   # text gravity/position
	local color= c=white         # text color
	local blur= b=2              # shadow blur radius
	local offsetx= x=20          # x offset
	local offsety= y=20          # y offset
	local shadow= S=0.8          # shadow strength

	eval "$(ally)"

	local input=${1:?input file required}
	local output=${2:?output file required}
	local text=${3:?text required}

	magick "$input" \
		\( -clone 0 -alpha transparent -fill "rgba(0,0,0,$shadow)" -font "$font" -pointsize "$size" -gravity "$gravity" -annotate "+${offsetx}+${offsety}" "$text" -blur "0x${blur}" \) \
		\( -clone 0 -alpha transparent -fill "$color" -font "$font" -pointsize "$size" -gravity "$gravity" -annotate "+${offsetx}+${offsety}" "$text" \) \
		-flatten "$output"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	image-add-text "$@"
fi
