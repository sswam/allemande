#!/bin/bash
set -e -u -o pipefail

sudo -u nobodally nmap localhost | tee /dev/stderr |
ted 'exit !/^Starting Nmap .*\nNote: Host seems down.*\nNmap done: 1 IP address \(0 hosts up\) scanned .*\n$/'

# Starting Nmap 7.95 ( https://nmap.org ) at 2025-09-25 08:57 UTC
# Note: Host seems down. If it is really up, but blocking our ping probes, try -Pn
# Nmap done: 1 IP address (0 hosts up) scanned in 3.06 seconds
