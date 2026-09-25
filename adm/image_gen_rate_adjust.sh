#!/bin/bash
# stop the brain process while running this!
rate=0.005  # per minute
awk -F$'\t' 'BEGIN { OFS="\t"; } $3=="image_a1111" && $9 != 0 { $9=$2*'$rate'/60.0 } {print}'
