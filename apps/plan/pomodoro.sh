#!/bin/bash
# pomodoro:	Pomodoro timer

work=$[50*60]	# Set the working time
grace=$[4*60]	# Set the grace time
fade=$[1*60]	# Set the fade time, or 0 to 'annoy'
rest=$[5*60]	# Set the rest time
g=	# More grace (or start with rest / grace period)
q=	# Quit any running pomodoro
N=	# Take a break now, then continue with next pomodoro

ban="It's time to take a break!"	# Set the banner message
xd1="0.20 0.75"	# Set the 1st annoy screen brightness
xd2="0.30 0.50"	# Set the 2nd annoy screen brightness
xd0="0.00 0.10"	# Set the rest screen brightness
annoy=0.1	# Set the annoy interval, to switch the screen brightness
bother=1	# Allow notifications to bother the user during pomodoro; FIXME 0 breaks sleep-log
n="-n"	# Notify the user of the time remaining, sleep-log opts
test=	# Use shorter times for testing
f=	# Run in the foreground
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

# pomodoro - sleep for the pomodoro time

if [ -z "$bother" ]; then
	dunstctl set-paused true
fi

if [ -z "$g" -a -z "$N" ]; then
	log pomodoro
	sleep-log $n $work 60
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
		# Gradual fade out
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
