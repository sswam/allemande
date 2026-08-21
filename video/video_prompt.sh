ffprobe -v quiet -select_streams v:0 -show_entries format_tags=comment -of default=noprint_wrappers=1:nokey=1 "$1" | jq -r .prompt
