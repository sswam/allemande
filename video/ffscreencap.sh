#!/usr/bin/env bash

# [output_file] - Records screen or window with ffmpeg
# Default: output.mp4

# version: 0.1.6

ffscreencap() {
    local quality= q=high      # quality [low|med|high|loss]
    local mic= m=0             # record microphone audio -m or -m=0.5 etc
    local loopback= l=0        # record system audio via loopback -l or -l=0.5 etc
    local screen= s=window     # capture mode [window|full|[0-9]*)
    local decorations= d=0     # include window decorations [0|1]
    local video_rate= v=60     # video frame rate
    local audio_rate= ar=48000 # audio sample rate

    eval "$(ally)"

    local output=${1:-output.webm}
    local ext="${output##*.}"
    local video_opts=()
    local audio_opts=()
    local X=0 Y=0 WIDTH HEIGHT

    # Get screen dimensions based on mode
    case "$screen" in
        window)
            local WINDOW_ID
            WINDOW_ID=$(xdotool selectwindow)
            if [ -z "$WINDOW_ID" ]; then
                die "No window selected"
            fi
            eval "$(xdotool getwindowgeometry --shell "$WINDOW_ID")"
            # The following logic seems wrong but works for me (with i3)!
            if [ "$decorations" = 0 ]; then
                # Get border width from xwininfo for decoration adjustment
                local RELATIVE_X RELATIVE_Y
                eval "$(xwininfo -id "$WINDOW_ID" | sed -n '/Relative upper-/ {s/.*\([XY]\): *\(.*\)/RELATIVE_\1="\2"/; p;}')"
                X=$((X - RELATIVE_X))
                Y=$((Y - RELATIVE_Y))
            fi
            ;;
        full)
            read -r WIDTH HEIGHT < <(xdpyinfo | awk '/dimensions:/ {print $2}' | tr 'x' ' ')
            ;;
        [0-9]*)
            # Get specific screen geometry
            local screen_info
            screen_info=$(xrandr --current | awk -v screen="$screen" '
                / connected/ {count++; if (count == screen) {
                    match($0, /[0-9]+x[0-9]+\+[0-9]+\+[0-9]+/);
                    print substr($0, RSTART, RLENGTH)
                }}')
            if [ -z "$screen_info" ]; then
                die "Screen $screen not found"
            fi
            read -r WIDTH HEIGHT X Y <<< "${screen_info//[x+]/ }"
            ;;
        *)
            die "Invalid screen mode: $screen"
            ;;
    esac

    # Handle audio setup
    if [ "$mic" != 0 ]; then
        audio_opts+=(-f alsa -i pulse)
    fi

    if [ "$loopback" != 0 ]; then
        local loopback_src=$(pactl list short sources | grep RUNNING | grep monitor | cut -f1)
        if [ -z "$loopback_src" ]; then
            die "No running monitor source found"
        fi
        audio_opts+=(-f pulse -i "$loopback_src")
    fi

    case "$ext" in
        mp4)
            video_opts+=(-c:v libx264)
            audio_opts+=(-c:a aac)
            case "$quality" in
                low)    video_opts+=(-crf 28) ;;
                med*)   video_opts+=(-crf 23) ;;
                high)   video_opts+=(-crf 18) ;;
                loss*)  die "Lossless encoding not supported for $ext" ;;
                *)      die "Unknown quality: $quality" ;;
            esac
            ;;
        mkv|webm)
            if [ "$quality" = "lossless" ] && [ "$ext" = "webm" ]; then
                die "Lossless encoding not supported for $ext"
            fi
            video_opts=(-c:v libaom-av1)
            audio_opts=(-c:a libopus)
            case "$quality" in
                low)    video_opts+=(-crf 35) ;;
                med*)   video_opts+=(-crf 30) ;;
                high)   video_opts+=(-crf 25) ;;
                loss*)
                    video_opts+=(-c:v ffv1)
                    audio_opts+=(-c:a flac)
                    ;;
                *)      die "Unknown quality: $quality" ;;
            esac
            ;;
        *)
            video_opts=(-c:v libx264 -crf 18)
            audio_opts=(-c:a aac)
            ;;
    esac

    # allow to adjust volume for each input if using both
    if [ "$mic" != 0 ] && [ "$loopback" != 0 ]; then
        audio_opts+=(-filter_complex "[1:a]volume=$mic[a1];[2:a]volume=$loopback[a2];[a1][a2]amix=inputs=2[aout]" -map 0:v -map "[aout]")
    fi

    verbose ffmpeg -framerate "$video_rate" -f x11grab -video_size "${WIDTH}x${HEIGHT}" -i "$DISPLAY+$X,$Y" "${audio_opts[@]}" "${video_opts[@]}" "$output"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
    ffscreencap "$@"
fi
