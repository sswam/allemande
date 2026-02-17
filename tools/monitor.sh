#!/usr/bin/env bash

# [options]
# Monitors system resources, network connectivity, and domain health

# The script monitors:
# - Disk space usage
# - System load average
# - Memory usage
# - VM usage (RAM + swap)
# - Basic network connectivity
# - Inotify max_user_watches setting
# - Domain DNS expiry
# - Domain SSL certificate expiry
#
# It outputs warnings on stdout if any of the checks fail.
#
# You can run this script via cron every 5 minutes:
#
# MAILTO="you@example.com"
#
# */15 * * * * /path/to/monitor.sh

# shellcheck disable=SC1007,SC2034 # ally options syntax

monitor() {
	local threshold_storage= s=100  # storage usage threshold percentage
	local threshold_load= l=2       # load average threshold
	local threshold_mem= m=95       # memory usage threshold percentage
	local threshold_vm= M=92        # VM (RAM + swap) usage threshold percentage
	local threshold_inotify= i=1048576  # minimum inotify max_user_watches value
	local ping_host= p=8.8.8.8      # host to ping test
	local killall_vm= K=90          # VM usage threshold to kill processes
	local killall= k=node           # Processes to kill
	local domains= n="allemande.ai" # domains to check
	local dns_days= D=14            # days before DNS expiry warning
	local ssl_days= S=14            # days before SSL expiry warning
	local config= c=1               # load config from file
	local daily= y=0                # do daily checks
	local caches= C=("/opt/allemande/rooms.extra.cache")  # cache dirs to exclude from disk space calculations

	eval "$(ally)"

	if [ "$config" = 1 ]; then
		config="${HOME}/.monitor"
	fi
	if [ -n "$config" ] && [ -e "$config" ]; then
		# shellcheck disable=SC1090
		. "$config"
	elif [ -n "$config" ]; then
		warn "could not read config file: $config"
	fi

	check_disk
	check_load
	check_memory
	check_vm
	check_inotify
	check_ping
	if [ "$daily" = 1 ]; then
		check_domains
	fi
}

check_domains() {
	local domain
	for domain in $domains; do
		check_dns_expiry "$domain"
		check_ssl_expiry "$domain"
	done
}

check_inotify() {
	local inotify_file=/proc/sys/fs/inotify/max_user_watches
	local current_value

	if [ ! -f "$inotify_file" ]; then
		warn "WARNING: Cannot read inotify max_user_watches - file not found"
		return
	fi

	current_value=$(cat "$inotify_file")
	info "INFO: Inotify max_user_watches is set to %s" "$current_value"

	if [ "$current_value" -lt "$threshold_inotify" ]; then
		warn "WARNING: Inotify max_user_watches is %s, should be at least %s!" "$current_value" "$threshold_inotify"
	fi
}

check_dns_expiry() {
	local domain=$1
	local expiry_date
	local days_left

	expiry_date=$(whois "$domain" | grep -i "Expir" | awk '{print $NF}' | head -1)
	if [ -z "$expiry_date" ]; then
		warn "WARNING: Could not fetch DNS expiry for %s" "$domain"
		return
	fi

	days_left=$(( ($(date -d "$expiry_date" +%s) - $(date +%s)) / 86400 ))

	info "INFO: Domain %s DNS expires in %d days" "$domain" "$days_left"
	if [ "$days_left" -le "$dns_days" ]; then
		warn "WARNING: Domain %s DNS expires in %d days!" "$domain" "$days_left"
	fi
}

check_ssl_expiry() {
	local domain=$1
	local expiry_date
	local days_left

	expiry_date=$(openssl s_client -connect "$domain":443 -servername "$domain" </dev/null 2>/dev/null | openssl x509 -noout -enddate | cut -d= -f2)
	if [ -z "$expiry_date" ]; then
		warn "WARNING: Could not fetch SSL expiry for %s" "$domain"
		return
	fi

	days_left=$(( ($(date -d "$expiry_date" +%s) - $(date +%s)) / 86400 ))

	info "INFO: Domain %s SSL expires in %d days" "$domain" "$days_left"
	if [ "$days_left" -le "$ssl_days" ]; then
		warn "WARNING: Domain %s SSL expires in %d days!" "$domain" "$days_left"
	fi
}

get_cache_usage() {
	local mountpoint=$1
	local cache_dir
	local total_cache=0
	local cache_usage
	local cache_mount

	for cache_dir in "${caches[@]}"; do
		if [ ! -d "$cache_dir" ]; then
			continue
		fi

		cache_mount=$(findmnt -T "$cache_dir" -no TARGET)
		if [ "$cache_mount" != "$mountpoint" ]; then
			continue
		fi
		cache_usage=$(du -sb "$cache_dir" 2>/dev/null | cut -f1)
		if [ -n "$cache_usage" ]; then
			total_cache=$((total_cache + cache_usage))
		fi
	done

	printf "%s" "$total_cache"
}

check_disk() {
	df -h | grep -E '/$|/media/|/mnt|/dev/mapper' | grep -v -E '^overlay|/docker/' |
	awk '{ print $5 " " $6 }' |
	while read -r percent mountpoint; do
		usage=$(printf "%.1f" "${percent%%%}")

		local cache_bytes
		cache_bytes=$(get_cache_usage "$mountpoint")

		if [ "$cache_bytes" -gt 0 ]; then
			local total_bytes used_bytes available_bytes adjusted_usage
			# shellcheck disable=SC2034 # available_bytes is read but not used
			read -r _ total_bytes used_bytes available_bytes _ < <(df -B1 "$mountpoint" | tail -1)

			exact_adj=$(echo "($used_bytes - $cache_bytes) * 100.0 / $total_bytes" | bc -l)
			display_adj=$(awk "BEGIN { printf \"%.1f\", int($exact_adj * 10) / 10 }")
			adjusted_usage="$display_adj"

			info "INFO: Filesystem mounted at %s is %.1f%% full (adjusted from %.1f%% after excluding cache)" "$mountpoint" "$adjusted_usage" "$usage"
			if [ "$(echo "$adjusted_usage >= $threshold_storage" | bc -l)" = 1 ]; then
				warn "WARNING: Filesystem mounted at %s is %.1f%% full (adjusted from %.1f%% after excluding cache)!" "$mountpoint" "$adjusted_usage" "$usage"
			fi
		else
			info "INFO: Filesystem mounted at %s is %.1f%% full" "$mountpoint" "$usage"
			if [ "$(echo "$usage >= $threshold_storage" | bc -l)" = 1 ]; then
				warn "WARNING: Filesystem mounted at %s is %.1f%% full!" "$mountpoint" "$usage"
			fi
		fi
	done
}

check_load() {
	local load_5min
	load_5min=$(uptime | awk -F'load average:' '{ print $2 }' | cut -d, -f2)
	load_5min=${load_5min// /}

	info "INFO: System load is %s (5-minute average)" "$load_5min"
	if (($(echo "$load_5min >= $threshold_load" | bc -l))); then
		warn "WARNING: System load is high: %s (5-minute average)" "$load_5min"
	fi
}

check_memory() {
	local memory_usage
	memory_usage=$(free | grep Mem | awk '{print ($2-$7)/$2 * 100.0}')

	info "INFO: Memory usage is at %s%%" "$memory_usage"
	if [ "$(echo "$memory_usage >= $threshold_mem" | bc -l)" = 1 ]; then
		warn "WARNING: Memory usage is at %s%%!" "$memory_usage"
	fi
}

check_vm() {
	local vm_usage
	vm_usage=$(free | awk '/Mem:/ {ram_total=$2; ram_used=$2-$7} /Swap:/ {swap_total=$2; swap_used=$3} END {print (ram_used+swap_used)/(ram_total+swap_total)*100}')

	info "INFO: VM usage is at %s%%" "$vm_usage"
	if [ "$(echo "$vm_usage >= $threshold_vm" | bc -l)" = 1 ]; then
		warn "WARNING: VM usage is at %s%%!" "$vm_usage"
	fi
	if [ "$(echo "$vm_usage >= $killall_vm" | bc -l)" = 1 ]; then
		warn "CRITICAL: VM usage is at %s%% - killing all %s processes!" "$vm_usage" "$killall"
		# shellcheck disable=SC2086 # $killall should not be quoted as per original comment
		killall $killall &>/dev/null	# note, $killall should not be quoted
	fi
}

check_ping() {
	local ping_fail=0
	ping -W 1 -c 1 "$ping_host" &>/dev/null
	ping_fail=$?
	if [ "$ping_fail" -eq 0 ]; then
		info "INFO: Server can ping %s" "$ping_host"
	else
		info "INFO: Server cannot ping %s" "$ping_host"
		warn "WARNING: Server cannot ping %s - possible network issues!" "$ping_host"
	fi
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	monitor "$@"
fi

# version: 0.1.7
