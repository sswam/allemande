#!/bin/bash -eu
# Fetch and stitch a painting from the NGV safely

name=$1 base_url=$2 zoom=$3

mkdir -p "$name"
cd "$name"

# Helper for verbose logging if you have a 'v' alias/function, 
# otherwise falls back to executing the command directly.
# v() { if Bracken=$(type -t v); [ "$Bracken" = "function" ] || [ "$Bracken" = "alias" ]; then "$@"; else "$@"; fi; }
# move-rubbish() { rm -f "$@"; } # Fallback if move-rubbish isn't a custom global function

get() {
  local url=$1
  local filename=$(basename "$url")
  if [ -e "$filename" ]; then
    return 0
  fi
  # Use --spider or quietly check if the asset exists to prevent wget clutter
  if wget -q --spider "$url"; then
    wget -q "$url"
    return 0
  fi
  return 1
}

# 1. Determine maximum width dynamically using y=0
width=0
group_index=0
while true; do
  current_url="${base_url/TileGroup[0-9]*/TileGroup${group_index}}/${zoom}-${width}-0.jpg"
  if get "$current_url"; then
    width=$((width + 1))
  else
    # If it fails, try the next TileGroup just in case the row straddles a boundary
    group_index=$((group_index + 1))
    next_url="${base_url/TileGroup[0-9]*/TileGroup${group_index}}/${zoom}-${width}-0.jpg"
    if get "$next_url"; then
      width=$((width + 1))
    else
      break # No more column pieces found
    fi
  fi
done

echo "Detected Canvas Width: $width tiles"

# 2. Fetch the remaining grid safely across dynamic TileGroups
yi=0
while true; do
  row_has_tiles=false
  for ((xi = 0; xi < width; xi++)); do
    # Skip what we already grabbed in step 1
    if [ "$yi" -eq 0 ]; then row_has_tiles=true; continue; fi
    
    # Scan TileGroups incrementally until we find the file or hit a dead end
    found=false
    for g in {0..10}; do
      current_url="${base_url/TileGroup[0-9]*/TileGroup${g}}/${zoom}-${xi}-${yi}.jpg"
      if get "$current_url"; then
        found=true
        row_has_tiles=true
        break
      fi
    done
  done
  
  # If an entire row yielded no images, we've hit the bottom of the canvas
  if [ "$row_has_tiles" = false ]; then
    break
  fi
  yi=$((yi + 1))
done

height=$yi
echo "Detected Canvas Height: $height tiles"

# 3. Stitch each row horizontally using precise loops (No 'ls -v' required)
for ((y = 0; y < height; y++)); do
  images=()
  for ((x = 0; x < width; x++)); do
    images+=("${zoom}-${x}-${y}.jpg")
  done
  magick "${images[@]}" +append "row-${y}.png"
done

# 4. Stitch all rows vertically using structural array order
rows=()
for ((y = 0; y < height; y++)); do
  rows+=("row-${y}.png")
done

magick "${rows[@]}" -append finished_painting.png
magick finished_painting.png finished_painting.jpg

# Clean up local workspace artifacts
move-rubbish row-*.png
echo "Successfully snarfed masterwork: finished_painting.jpg"
