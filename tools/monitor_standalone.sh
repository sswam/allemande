#!/usr/bin/env bash

# [options]
# Monitors system resources and network connectivity
#
# MIT license:
#
# Copyright 2025, Sam Watkins
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the “Software”), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# The script monitors:
# - Disk space usage
# - System load average
# - Memory usage
# - VM usage (RAM + swap)
# - Basic network connectivity
#
# It outputs warnings on stdout if any of the checks fail.
#
# You can run this script via cron every 5 minutes:
#
# MAILTO="you@example.com"
#
# */15 * * * * /path/to/monitor.sh

usage() {
  cat << EOF
Usage: $(basename "$0") [options]
Monitor system resources and network connectivity

Options:
  -s PERCENT   Storage usage threshold percentage (default: 95)
  -l LOAD      Load average threshold (default: 1)
  -m PERCENT   Memory usage threshold percentage (default: 95)
  -M PERCENT   VM (RAM + swap) usage threshold percentage (default: 90)
  -p HOST      Host to ping test (default: 8.8.8.8)
  -v           Verbose mode
  -h           Display this help message
EOF
  exit 1
}

monitor() {
  local threshold_storage=95
  local threshold_load=1
  local threshold_mem=95
  local threshold_vm=90
  local ping_host="8.8.8.8"
  local verbose=

  # Parse command line options
  local OPTIND
  while getopts "s:l:m:M:p:vh" opt; do
    case $opt in
      s) threshold_storage="$OPTARG" ;;
      l) threshold_load="$OPTARG" ;;
      m) threshold_mem="$OPTARG" ;;
      M) threshold_vm="$OPTARG" ;;
      p) ping_host="$OPTARG" ;;
      v) verbose=1 ;;
      h) usage ;;
      ?) usage >&2 ;;
    esac
  done
  shift $((OPTIND-1))

  check_disk
  check_load
  check_memory
  check_vm
  check_ping
}

check_disk() {
  df -h | grep -E '/$|/media/|/mnt|/dev/mapper' | grep -v -E '^overlay|/docker/' |
  awk '{ print $5 " " $6 }' |
  while read -r percent mountpoint; do
    usage=${percent%%%}
    if [ "$verbose" ]; then
      printf "INFO: Filesystem mounted at %s is %s%% full\n" "$mountpoint" "$usage"
    fi
    if [ "$usage" -ge "$threshold_storage" ]; then
      printf "WARNING: Filesystem mounted at %s is %s%% full!\n" "$mountpoint" "$usage"
    fi
  done
}

check_load() {
  local load_5min
  load_5min=$(uptime | awk -F'load average:' '{ print $2 }' | cut -d, -f2)
  load_5min=${load_5min// /}

  if [ "$verbose" ]; then
    printf "INFO: System load is %s (5-minute average)\n" "$load_5min"
  fi
  if (($(echo "$load_5min >= $threshold_load" | bc -l))); then
    printf "WARNING: System load is high: %s (5-minute average)\n" "$load_5min"
  fi
}

check_memory() {
  local memory_usage
  memory_usage=$(free | grep Mem | awk '{print ($2-$7)/$2 * 100.0}')
  memory_usage=${memory_usage%.*}

  if [ "$verbose" ]; then
    printf "INFO: Memory usage is at %s%%\n" "$memory_usage"
  fi
  if [ "$memory_usage" -ge "$threshold_mem" ]; then
    printf "WARNING: Memory usage is at %s%%!\n" "$memory_usage"
  fi
}

check_vm() {
  local vm_usage
  vm_usage=$(free | awk '/Mem:/ {ram_total=$2; ram_used=$2-$7} /Swap:/ {swap_total=$2; swap_used=$3} END {print (ram_used+swap_used)/(ram_total+swap_total)*100}')
  vm_usage=${vm_usage%.*}

  if [ "$verbose" ]; then
    printf "INFO: VM usage is at %s%%\n" "$vm_usage"
  fi
  if [ "$vm_usage" -ge "$threshold_vm" ]; then
    printf "WARNING: VM usage is at %s%%!\n" "$vm_usage"
  fi
}

check_ping() {
  local ping_fail=0
  ping -W 1 -c 1 "$ping_host" &>/dev/null
  ping_fail=$?
  if [ "$verbose" ]; then
    if [ "$ping_fail" -eq 0 ]; then
      printf "INFO: Server can ping %s\n" "$ping_host"
    else
      printf "INFO: Server cannot ping %s\n" "$ping_host"
    fi
  fi
  if [ "$ping_fail" -ne 0 ]; then
    printf "WARNING: Server cannot ping %s - possible network issues!\n" "$ping_host"
  fi
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  monitor "$@"
fi

# version: 0.1.1
