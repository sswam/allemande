#!/usr/bin/env bats

# Test 1: Check if the script runs without errors
@test "Script execution with valid process name" {
	run ./find_xterm.sh echo
	[ "$status" -eq 0 ]
}

# Test 2: Check if the script fails when no process name is provided
@test "Script fails without process name" {
	run ./find_xterm.sh
	[ "$status" -eq 1 ]
	[[ "$output" == *"Process name is required"* ]]
}

# Test 3: Check if the script handles non-existent process
@test "Script handles non-existent process" {
	run ./find_xterm.sh non_existent_process
	[ "$status" -eq 1 ]
	[[ "$output" == *"Process not found: non_existent_process"* ]]
}

# Mock functions and utilities

xdotool() {
	if [[ "$1" == "search" ]]; then
		echo "67890"
	elif [[ "$1" == "getmouselocation" ]]; then
		echo "X=100 Y=100 SCREEN=0 WINDOW=12345"
	fi
}

i3-msg() {
	echo "i3-msg called with: $*"
}

pgrep() {
	echo "in pgrep mock\!"; exit 1
	if [[ "$2" == "echo" || "$2" == "ProcessName" ]]; then
		echo "12345"
	else
		return 1
	fi
}

ps() {
	if [[ "$@" == *"echo"* || "$@" == *"ProcessName"* ]]; then
		echo "user 12345 $2"
	fi
}

export -f xdotool i3-msg pgrep ps

# Test 4: Basic functionality
@test "Basic functionality" {
	run ./find_xterm.sh ProcessName
	[ "$status" -eq 0 ]
	[[ "$output" == *"xdotool called with:"* ]]
	[[ "$output" == *"i3-msg called with:"* ]]
}

# Test 5: Using pgrep
@test "Using pgrep to find process" {
	run ./find_xterm.sh -p ProcessName
	[ "$status" -eq 0 ]
}

# Test 6: No float
@test "No float option" {
	run ./find_xterm.sh -f ProcessName
	[ "$status" -eq 0 ]
	[[ "$output" != *"i3-msg called with: [id='"* ]]
}

# Test 7: No expose
@test "No expose option" {
	run ./find_xterm.sh -e ProcessName
	[ "$status" -eq 0 ]
	[[ "$output" != *"xdotool called with: windowactivate"* ]]
}

# Test 8: Missing process name
@test "Missing process name" {
	run ./find_xterm.sh
	[ "$status" -eq 1 ]
	[[ "$output" == *"Process name is required"* ]]
}

# Test 9: Process not found
@test "Process not found" {
	pgrep() { return 1; }
	ps() { echo ""; }
	run ./find_xterm.sh NonExistentProcess
	[ "$status" -eq 1 ]
	[[ "$output" == *"Process not found: NonExistentProcess"* ]]
}

# Test 10: XTerm not found
@test "XTerm not found" {
	xdotool() { return 1; }
	run ./find_xterm.sh ProcessName
	[ "$status" -eq 1 ]
	[[ "$output" == *"XTerm not found for process: ProcessName"* ]]
}
