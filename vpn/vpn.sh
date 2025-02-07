#!/bin/bash
. get_root
set -e -u -a
netns=
timeout=120
. opts

config=$1
shift

if [ -z "$netns" ]; then
	netns=$(basename "${config%.*}")
	echo >&2 "netns=$netns"
fi

v() {
	printf >&2 "vpn: "
	printf >&2 "%q " "$@"
	echo >&2
	"$@"
}

show() {
	local var=$1
	echo >&2 "$var: ${!var}"
}

setv() {
	local var=$1 val=$2
	declare -g "$var=$val"
	show $var
}

myip=$(which myip)

wait_for_startup() {
	for try in $(seq 0 $timeout); do
		vpn_ip=$(ip netns exec "$netns" "$myip" || true)
		if [ -n "$vpn_ip" -a "$vpn_ip" != "$host_ip" ]; then
			show vpn_ip
			return 0
		fi
		sleep 1
	done
	echo >&2 "The VPN is not working, IP address did not change."
	return 1
}

setv host_ip "$(myip)"
if [ -z "$host_ip" ]; then
	echo >&2 "Could not get host IP address."
	exit 1
fi

netns_up=$(curry netns-up "$netns")
v openvpn --config "$config" --ifconfig-noexec --route-noexec --up "$netns_up" --route-up "$netns_up" --down "$netns_up" >&2 &

sleep 1
setv openvpn_pid "$(child -1 $$ openvpn)"
stty sane

wait_for_startup

if [ $# -gt 0 ]; then
	v ip netns exec "$netns" "${@:-${default_cmd[@]}}"
	v kill $openvpn_pid
else
	echo >&2 "example command: sudo ip netns exec "$netns" su \$USER"
	trap 'echo >&2 INT' INT
	wait || true
fi

stty sane
