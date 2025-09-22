#!/usr/bin/env bats

# reaper_test.sh v1.0.1
# Tests the reaper.sh script using BATS framework

setup() {
	load 'test_helper/bats-support/load'
	load 'test_helper/bats-assert/load'
	. ./reaper.sh
}

# Helper function to count child processes
count_children() {
	local ppid=$1
	ps --ppid $ppid | grep -v "PID" | wc -l
}

@test "Basic process cleanup on exit" {
	local pid
	# Start a background process
	(
		. ./reaper.sh
		sleep 60 &
		pid=$!
		# Verify process started
		ps -p $pid
		# Exit immediately
		exit 0
	)
	# Give a moment for cleanup
	sleep 1
	# Verify process was killed
	run ps -p $pid
	[ "$status" -ne 0 ]
}

@test "Multiple process cleanup" {
	local pid1 pid2 pid3
	# Start multiple background processes
	(
		. ./reaper.sh
		sleep 60 & pid1=$!
		sleep 60 & pid2=$!
		sleep 60 & pid3=$!
		# Verify processes started
		ps -p $pid1 $pid2 $pid3
		exit 0
	)
	# Give a moment for cleanup
	sleep 1
	# Verify all processes were killed
	run ps -p $pid1 $pid2 $pid3
	[ "$status" -ne 0 ]
}

@test "Signal handling - TERM" {
	local wait_pid
	# Start process that will receive TERM
	(
		. ./reaper.sh
		sleep 60 &
		kill -TERM $$
	) & wait_pid=$!
	# Give a moment for signal handling
	sleep 1
	# Verify process was killed and correct exit code
	wait $wait_pid || [ $? -eq 143 ]  # 128 + 15 (TERM)
}

@test "Signal handling - INT" {
	local wait_pid
	(
		. ./reaper.sh
		sleep 60 &
		kill -INT $$
	) & wait_pid=$!
	sleep 1
	wait $wait_pid || [ $? -eq 130 ]  # 128 + 2 (INT)
}

@test "Nested process cleanup" {
	local initial_children
	local subshell_pid

	# Start a subshell and capture its PID
	(
		subshell_pid=$$
		echo "$subshell_pid" > /tmp/subshell_pid

		. ./reaper.sh
		(sleep 60 & sleep 70 &) &
		sleep 80 &
		# Give a moment to start processes
		sleep 1
		# Count initial children
		initial_children=$(count_children $$)
		[ "$initial_children" -gt 0 ]
		exit 0
	)

	# Read the subshell PID
	subshell_pid=$(</tmp/subshell_pid)
	rm -f /tmp/subshell_pid

	sleep 1
	# Verify all processes were cleaned up for the specific subshell PID
	[ "$(pgrep -P "$subshell_pid" | wc -l)" -eq 0 ]
}
