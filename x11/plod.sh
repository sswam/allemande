#!/bin/bash

# plod - plot data using gnuplot

: "${w:=640}" "${h:=480}"
: "${pause:=sleep 1e9}"
: "${using:=1:2}"
: "${title:=}"
: "${style:=lines}"
: "${lines=}"
: "${gnuplot_opts=}"  # Initialize gnuplot_opts to avoid shellcheck warning

if [ -n "$x0" ] && [ -n "$x1" ]; then
    xrange="set xrange[$x0:$x1];"
fi
if [ -n "$y0" ] && [ -n "$y1" ]; then
    yrange="set yrange[$y0:$y1];"
fi

if [ -n "$dx" ]; then
    xtics="set xtics $dx;"
fi
if [ -n "$dy" ]; then
    ytics="set ytics $dy;"
fi

if [ -z "$terminal" ]; then
    if [ -t 1 ]; then
        terminal="x11 size $w,$h"
    else
        terminal="png size $w,$h"
        pause=
    fi
fi

tmp=$(mktemp)
# Check if there's any input before trying to process it
if ! sed 's/[,;]/\t/g' >"$tmp"; then
    rm "$tmp"
    echo >&2 "no input data"
    exit 1
fi

# Check if the temp file is empty
if [ ! -s "$tmp" ]; then
    rm "$tmp"
    echo >&2 "empty input"
    exit 1
fi

if [ "$lines" = '' ]; then
    lines=$(head -n1 "$tmp" | tr -s ' \t' '\t' | tr -dc '\t' | wc -c)
    if [ "$lines" = 0 ]; then
        lines=1
        <"$tmp" nl | sed 's/^ *//' >"$tmp.1"
        mv "$tmp.1" "$tmp"
    fi
fi

(sleep 2; rm "$tmp") &
(
echo "
    set terminal $terminal;
    $xrange $yrange
    $xtics $ytics
#    bind Close 'exit gnuplot';
    plot \\"
    for A in $(seq 1 "$lines"); do
        echo -n "    '$tmp' using 1:$((A+1)) title '$title' with $style"  # Removed unnecessary ${} around arithmetic
        if [ "$A" -lt "$lines" ]; then
            echo ", \\"
        else
            echo ';'
        fi
    done
$pause
) | #tee /dev/stderr |
gnuplot $gnuplot_opts
