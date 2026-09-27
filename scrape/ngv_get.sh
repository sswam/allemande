#!/bin/bash -eu
# fetch a painting from the NGV

name=$1 base_url=$2 zoom=$3

mkdir -p "$name"
cd "$name"

get() {
  local url=$1
  local name=$(basename "$url")
  if [ -e "$name" ]; then
    return
  fi
  wget "$url"
}

# Determine width: loop x until wget fails on first row (y=0)
x=0
while get "${base_url}/${zoom}-${x}-0.jpg"; do
  x=$((x + 1))
done
width=$x

# Fetch remaining tiles (skipping first row and first column, already fetched)
state=0
yi=0
while true; do
  for ((xi = 0; xi < width; xi++)); do
    if ! get "${base_url}/${zoom}-${xi}-${yi}.jpg"; then
      if [ "$state" = 1 ]; then
        state=2
        break
      fi
      state=1
      base_url=${base_url/TileGroup0/TileGroup1}
      if ! get "${base_url}/${zoom}-${xi}-${yi}.jpg"; then
        state=2
        break
      fi
    fi
  done
  if [ "$state" = 2 ]; then
    break
  fi
  yi=$((yi + 1))
done

height=$yi

for ((y = 0; y < height; y++)); do
  v magick $(ls -v ${zoom}-*-${y}.jpg) +append row-${y}.png
done

# 2. Stitch all rows vertically
v magick $(ls -v row-*.png) -append finished_painting.png
v magick finished_painting.png finished_painting.jpg

move-rubbish row-*.png
