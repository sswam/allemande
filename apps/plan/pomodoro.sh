#!/bin/bash -eu

# pomodoro: Pomodoro timer
# Version: 0.2.1

grace=$[1*60]      # Set the grace time (in seconds)
fade=$[1*60]       # Set the fade time, or 0 to 'annoy' (in seconds)
work=$[25*60]      # Set the working time (in seconds)
rest=$[3*60]       # Set the rest time (in seconds)
# grace=50             # Set the grace time (in seconds)
# fade=10              # Set the fade time, or 0 to 'annoy' (in seconds)
# work=$[8*60]         # Set the working time (in seconds)
# rest=$[1*60]         # Set the rest time (in seconds)
work_min_percent=80  # Minimum work percent, to align with the clock
g=	# More grace (or start with rest / grace period)
q=	# Quit any running pomodoro
N=	# Take a break now, then continue with next pomodoro

ban="Take a break!"	# Set the banner message
xd1="0.20 0.75"	# Set the 1st annoy screen brightness
xd2="0.30 0.50"	# Set the 2nd annoy screen brightness
xd0="0.00 0.1"	# Set the rest screen brightness
annoy=0.1	# Set the annoy interval, to switch the screen brightness
bother=1	# Allow notifications to bother the user during pomodoro; FIXME 0 breaks sleep-log
n="-n"	# Notify the user of the time remaining, sleep-log opts
test=	# Use shorter times for testing
f=	# Run in the foreground
A=	# do not align the work start to the hour

. opts

# ----------------------------------------------
# includes and startup message

. log
. sleep-log
# . daemonize

log pomodoro timer

# ----------------------------------------------

# use different values if the user is testing

if [ -n "$test" ]; then
	work=1  # for testing
	grace=2
	rest=10
fi

# ----------------------------------------------

# daemonize the script unless the user wants to run it in the foreground

if [ -z "$f" ]; then
	v daemonize "$(realpath "$0")" -f "${OPTS[@]}" "$@" &
	exit 0
fi

# ----------------------------------------------

# reset the screen brightness

function fix_xdark {
	echo "$(xdark)"
	case "$(xdark)" in
	"$xd1"|"$xd2"|"$xd0") xdark 1 ;;
	esac
}

fix_xdark

# ----------------------------------------------

# on exit, reset the screen brightness and killall .ban

trap fix_xdark EXIT
#trap 'killall .ban' EXIT

if [ -n "$q" ]; then
	echo "Got quit signal" >&2
	exit 0
fi

# ----------------------------------------------
#
# Align the work start to the hour

adjusted_work_time=$work
if [ -z "$A" ] || [ "$A" -eq 0 ]; then
	current_second=$(( 60 * $(date +%M) + $(date +%S) ))

	period=$(( work + rest + fade + grace ))

	seconds_mod_period=$(( current_second % period ))
	seconds_remain=$(( period - seconds_mod_period ))
	adjusted_work_time=$(( seconds_remain - rest - fade - grace ))

	# echovar current_second period seconds_mod_period seconds_remain adjusted_work_time

	if (( adjusted_work_time < work * work_min_percent / 100 )); then
		(( adjusted_work_time+=$period ))
	fi
	echo "$adjusted_work_time"
fi

# ----------------------------------------------

# pomodoro - sleep for the pomodoro time

if [ -z "$bother" ]; then
	dunstctl set-paused true
fi

bright=$(xdark)
bright=${bright#* }
if (( $(echo "$bright < 1" | bc -l) )); then
	xdark 1
fi

if [ -z "$g" -a -z "$N" ]; then
	log pomodoro
	sleep-log $n $adjusted_work_time 60
fi

# ----------------------------------------------

# notify the user that the pomodoro is over

log end pomodoro

if [ -z "$bother" ]; then
	dunstctl set-paused false
fi

#ban "$ban"

notify-send -u critical -t 10000 \
	-i /usr/share/icons/gnome/48x48/status/appointment-soon.png \
	"Pomodoro" "$ban"

if [ -z "$N" ]; then
	log grace
	sleep-log $n $grace 5
fi

# ----------------------------------------------

# annoy the user until they take a break

log annoy
xd_save=$(xdark)
step=0

while ! q pidof i3lock; do
	if [ "$fade" != "0" ]; then
		if [ "$step" -gt "$fade" ]; then
			continue
		fi
		# TODO the fade function might be useful for something else
		read from1 from2 <<< "$xd_save"
		read to1 to2 <<< "$xd0"
		now1=$(echo "scale=6; $from1 + ($to1 - $from1) * $step / $fade" | bc)
		now2=$(echo "scale=6; $from2 + ($to2 - $from2) * $step / $fade" | bc)
		xdark $now1 $now2
		sleep 1
		step=$((step + 1))
	else
		# Annoying behavior
		xdark $xd1
		sleep $annoy
		if q pidof i3lock; then break; fi
		xdark $xd2
		sleep $annoy
	fi
done

# ----------------------------------------------

# sleep for the rest period

xdark $xd0
sleep-log $rest

# ----------------------------------------------

# wait for the user to unlock the screen again

log wait
while q pidof i3lock; do
	sleep 1
done
log end rest
xdark $xd_save

# ----------------------------------------------

# run the script again

log restart
exec $0

# ----------------------------------------------
