#!/bin/sh -eu

myip_opendns() {
	dig +short myip.opendns.com @208.67.220.220
}

myip_aws() {
	curl -s https://checkip.amazonaws.com/
}

ip=$(myip_opendns)
[ -n "$ip" ] || ip=$(myip_aws)
echo "$ip"
