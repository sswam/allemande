#!/bin/bash
set -euo pipefail
url=$1 out=$2 start=$3 end=$4
user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"
. opts
len=$(hms "$(calc `hms- "$end"` - `hms- "$start"`)")
# -user_agent "$user_agent" -headers "Referer: $url" 
v ffmpeg -y -ss "$start" -i "$url" -t "$len" "$out"
