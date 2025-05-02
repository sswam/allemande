#!/bin/bash -eu

# === Example Configuration ===
UNTRUSTED_UID_MIN=60000
UNTRUSTED_UID_MAX=69999
ALLOW_PORTS_MIN=60000
ALLOW_PORTS_MAX=65535
ROUTER_IPv4="192.168.1.1"
ROUTER_IPv6="fd00::1"
IF_LOCAL="lo"
IF_ETHERNET="enp6s0"
TABLE_NAME="remote_user_firewall"

. /etc/remote_user.conf

op="$1"

if [ "$op" = "delete" ]; then
	nft delete table inet "$TABLE_NAME"
	exit 0
elif [ "$op" = "list" ]; then
	nft list table inet "$TABLE_NAME"
	exit 0
elif [ "$op" != "add" ]; then
	echo >&2 "Usage: $(basename "$0") add|delete|list"
	exit 1
fi

UID_CHECK="meta skuid >= $UNTRUSTED_UID_MIN meta skuid <= $UNTRUSTED_UID_MAX"

# Order matters! Rules are evaluated top-to-bottom:
# 1. Interface restrictions (only allow lo and ethernet)
# 2. Established connections (for responses to outbound traffic)
# 3. Local services (DNS, high ports)
# 4. Router services (DNS only)
# 5. Block private networks
# 6. Allow internet

# Create fresh tables and chains
nft add table inet "$TABLE_NAME"
nft "add chain inet $TABLE_NAME input { type filter hook input priority 0; }"
nft "add chain inet $TABLE_NAME output { type filter hook output priority 0; }"

# Block interfaces that aren't local or ethernet
nft add rule inet "$TABLE_NAME" output $UID_CHECK oifname != { "$IF_LOCAL", "$IF_ETHERNET" } drop
nft add rule inet "$TABLE_NAME" input $UID_CHECK iifname != { "$IF_LOCAL", "$IF_ETHERNET" } drop

for chain in input output; do
	# input / ouput rules use different keywords for the remote address and port
	case "$chain" in
		input) addr="saddr" port="sport" ;;
		*) addr="daddr" port="dport" ;;
	esac

	# Allow established connections
	nft add rule inet "$TABLE_NAME" "$chain" $UID_CHECK ct state established,related accept

	for net_proto in ip ip6; do
		case "$net_proto" in
			ip) localhost="127.0.0.1" router="$ROUTER_IPv4" ;;
			*) localhost="::1" router="$ROUTER_IPv6" ;;
		esac

		for transport_proto in tcp udp; do
			# Localhost: Allow DNS and high ports
			nft add rule inet "$TABLE_NAME" "$chain" $UID_CHECK "$net_proto" "$addr" "$localhost" "$transport_proto" "$port" 53 accept
			nft add rule inet "$TABLE_NAME" "$chain" $UID_CHECK "$net_proto" "$addr" "$localhost" "$transport_proto" "$port" $ALLOW_PORTS_MIN-$ALLOW_PORTS_MAX accept

			# Router: Allow DNS
			if [ -n "$router" ]; then
				nft add rule inet "$TABLE_NAME" "$chain" $UID_CHECK "$net_proto" "$addr" "$router" "$transport_proto" "$port" 53 accept
			fi
		done
	done

	# Block local and private networks, including other localhost and router ports
	nft add rule inet "$TABLE_NAME" "$chain" $UID_CHECK ip "$addr" { 127.0.0.0/8, 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 169.254.0.0/16 } drop
	nft add rule inet "$TABLE_NAME" "$chain" $UID_CHECK ip6 "$addr" { ::/8, fc00::/7, fe80::/10 } drop

	# Allow everything else (internet) - chain policy is accept
done
