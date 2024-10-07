#!/bin/bash -eu
# maskgen: generate masks for a given image
image=$1
masks=${image%.*}
masked=$masks-masked
segment-anything-auto.py --checkpoint /opt/models/sam/sam_vit_h_4b8939.pth --input "$image" --output .
image-apply-masks.py "$image" "$masks" "$masked"

# it was slow with imagemagick loading the image repeatedly
#for img in "$masks"/*.png; do \
#	basename=`basename "$img"`
#	convert "$image" "$img" -alpha Off -compose CopyOpacity -composite "$masked/$basename" ;\
#done
