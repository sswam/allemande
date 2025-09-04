#!/usr/bin/env bash

# [options]
# Monitors system resources and network connectivity

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

monitor() {
  local threshold_storage= s=95 # storage usage threshold percentage
  local threshold_load= l=1     # load average threshold
  local threshold_mem= m=95     # memory usage threshold percentage
  local threshold_vm= M=80      # VM (RAM + swap) usage threshold percentage
  local ping_host= p=8.8.8.8    # host to ping test
  local killall_vm= K=90        # VM usage threshold to kill processes
  local killall= k=node         # Processes to kill
  local verbose= v=             # verbose

  eval "$(ally)"

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
  if [ "$vm_usage" -ge "$killall_vm" ]; then
    printf "CRITICAL: VM usage is at %s%% - killing all %s processes!\n" "$vm_usage" "$killall"
    killall $killall &>/dev/null
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
