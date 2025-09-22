#!/bin/zsh -y
setopt KSH_ARRAYS

# runs "lock" to dissuade the user from working at night

conf_file=~/.hopeofsleepatnightrc

# hopeofsleeptonight settings
sleep_time=2300
wake_time=0500
poll_interval_night=5s
poll_interval_day=1m
override_duration=10m
override_file=~/.emergency_override
lock_process=i3lock
lock_command=lock

# diu (diurnal) blue- and red-shift settings

diu_wake_time=0500
diu_morning_time=0800
diu_evening_time=2000
diu_night_time=2300

# Morning (bluest) endpoint (index 0)
diu_r0=0.95
diu_g0=0.98
diu_b0=1.05
diu_bright0=0.90
diu_black0=0.00

# Day (neutral) plateau (index 1)
diu_r1=1.00
diu_g1=1.00
diu_b1=1.00
diu_bright1=1.00
diu_black1=0.00

# Night (warmest) endpoint (index 2)
diu_r2=1.00
diu_g2=0.70
diu_b2=0.60
diu_bright2=0.60
diu_black2=0.15

if [ -f "$conf_file" ]; then
	. "$conf_file"
fi

trap '' SIGTERM  # kill with kill -INT

# Convert HHMM time format to decimal hours
function hhmm_to_hours() {
	local time=$1
	local -i hours=$(( time / 100 ))
	local -i minutes=$(( time % 100 ))
	printf "%.2f" $(( hours + minutes/60.0 ))
}

# Simple smooth easing: smoothstep(t) = t*t*(3 - 2*t)
# We use the same easing for morning/evening
function diu() {
	local now=$1
	local -F hour=$(hhmm_to_hours "$now")

	# Convert times using the shared function
	local -F t0=$(hhmm_to_hours "$diu_wake_time")     # wake
	local -F t1=$(hhmm_to_hours "$diu_morning_time")  # end of morning ramp
	local -F t2=$(hhmm_to_hours "$diu_evening_time")  # start of evening ramp
	local -F t3=$(hhmm_to_hours "$diu_night_time")    # end of evening ramp

	# Normalize times to a continuous timeline starting from t0
	# This correctly handles schedules that cross midnight.
	(( t1 > t0 )) || t1=$(( t1 + 24.0 ))
	(( t2 > t1 )) || t2=$(( t2 + 24.0 ))
	(( t3 > t2 )) || t3=$(( t3 + 24.0 ))

	# Adjust current hour to be on the same continuous timeline
	(( hour > t0 )) || hour=$(( hour + 24.0 ))

	# Arrays for endpoints (indices 0,1,2). KSH_ARRAYS -> index from 0.
	typeset -a R=( $diu_r0 $diu_r1 $diu_r2 )
	typeset -a G=( $diu_g0 $diu_g1 $diu_g2 )
	typeset -a B=( $diu_b0 $diu_b1 $diu_b2 )
	typeset -a BR=( $diu_bright0 $diu_bright1 $diu_bright2 )
	typeset -a BL=( $diu_black0  $diu_black1  $diu_black2 )

	# Determine which segment we're in and compute t in [0,1]
	local idx1
	local idx2
	local -F t seg_len

	if (( hour < t0 )); then
		idx1=2; idx2=2; t=0.0
	elif (( hour < t1 )); then
		idx1=0; idx2=1; seg_len=$(( t1 - t0 )); (( seg_len > 0 )) || seg_len=1.0
		t=$(( (hour - t0) / seg_len ))
	elif (( hour < t2 )); then
		idx1=1; idx2=1; t=0.0
	elif (( hour < t3 )); then
		idx1=1; idx2=2; seg_len=$(( t3 - t2 )); (( seg_len > 0 )) || seg_len=1.0
		t=$(( (hour - t2) / seg_len ))
	else
		idx1=2; idx2=2; t=0.0
	fi

	# Clamp and ease
	(( t < 0 )) && t=0
	(( t > 1 )) && t=1
	local -F te=$(( t*t*(3 - 2*t) ))  # smoothstep

	# Interpolate between endpoints idx1 -> idx2 with eased t
	local -F r=$(( R[idx1]  + (R[idx2]  - R[idx1])  * te ))
	local -F g=$(( G[idx1]  + (G[idx2]  - G[idx1])  * te ))
	local -F b=$(( B[idx1]  + (B[idx2]  - B[idx1])  * te ))
	local -F brightness=$(( BR[idx1] + (BR[idx2] - BR[idx1]) * te ))
	local -F black_level=$(( BL[idx1] + (BL[idx2] - BL[idx1]) * te ))

	# Apply brightness and contrast compression
	r=$(( black_level + r * (brightness - black_level) ))
	g=$(( black_level + g * (brightness - black_level) ))
	b=$(( black_level + b * (brightness - black_level) ))

	printf '%.8f %.8f %.8f\n' $r $g $b
}

function is_day() {
	local now=$1
	if [ $wake_time -lt $sleep_time ] && [ $now -ge $wake_time -a $now -lt $sleep_time ]; then
		return 0
	elif [ $wake_time -ge $sleep_time ] && [ $now -ge $wake_time -o $now -lt $sleep_time ]; then
		return 0
	else
		return 1
	fi
}

function lock_at_night() {
	# Single date call; evaluates as a float hour = H + M/60.0
	# local hour min
	# read -r hour min <<< $(date +'%H %M')
	# local -F now=$(( hour + min/60.0 ))
	# local hhmm="$hour$min"
	local now=$(date +'%H%M')
	if is_day "$now"; then
		xramp $(diu "$now")
		sleep $poll_interval_day
	elif [ -e "$override_file" ]; then
		xramp $(diu "$now")
		override_val=$(cat "$override_file")
		rm -f "$override_file"
		sleep "${override_val:-$override_duration}"
	else
		pidof "$lock_process" >/dev/null || $lock_command
		sleep $poll_interval_night
	fi
}

function hopeofsleeptonight() {
	if [ "$1" = "--abandon-all" ]; then
		echo "$2" > "$override_file"
		echo "Override set for ${2:-${override_duration}}."
		exit 0
	fi

	while true; do
		lock_at_night
	done
}

hopeofsleeptonight "$@"
