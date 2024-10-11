#!/bin/bash
# based on https://unix.stackexchange.com/a/196116

netns=$1
shift

v() {
	printf >&2 "netns_up: "
	printf >&2 "%q " "$@"
	echo >&2
	"$@"
}

show() {
	local var=$1
	echo >&2 "netns_up: $var: ${!var}"
}

setv() {
	local var=$1 val=$2
	declare -g "$var=$val"
	show $var
}

echo >&2 "INFO: script_type=$script_type netns_up $netns $@"
case $script_type in
up)
	v ip netns add "$netns"
	v ip netns exec "$netns" ip link set dev lo up
	v mkdir -p /etc/netns/"$netns"
	v echo "nameserver 8.8.8.8" >/etc/netns/"$netns"/resolv.conf
	v ip link set dev "$1" up netns "$netns" mtu "$2"
	v ip netns exec "$netns" ip addr add dev "$1" "$4/${ifconfig_netmask:-30}" ${ifconfig_broadcast:+broadcast "$ifconfig_broadcast"}
	if [ -n "$ifconfig_ipv6_local" ]; then
		v ip netns exec "$netns" ip addr add dev "$1" "$ifconfig_ipv6_local"/112
	fi
	;;
route-up)
	v ip netns exec "$netns" ip route add default via "$route_vpn_gateway"
	if [ -n "$ifconfig_ipv6_remote" ]; then
		v ip netns exec "$netns" ip route add default via "$ifconfig_ipv6_remote"
	fi
	;;
down)
	if v ip netns delete "$netns"; then
		v rm /etc/netns/"$netns"/resolv.conf
		v rmdir /etc/netns/"$netns"
	fi
	;;
esac
